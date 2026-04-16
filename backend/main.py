from __future__ import annotations

import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymupdf
from backend.db.postgres import get_conn
from backend.ml.inference import predict_message
from backend.ml.rules import build_analysis_response
from backend.services.link_analysis import analyze_link_input

app = FastAPI(title="StepSafe PyMuPDF API", version="1.0.0")

DEFAULT_OCR_LANGUAGE = os.getenv("PYMUPDF_OCR_LANGUAGE", "eng")
DEFAULT_OCR_DPI = int(os.getenv("PYMUPDF_OCR_DPI", "150"))

# Vite dev server usually proxies /api to this service.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    inputType: str
    text: str
    message_type: str = "Email"
    platform: str = "Unknown"
    job_type: str = "Unknown"
    contains_link: int | None = None
    contains_email: int | None = None
    has_payment_request: int | None = None
    asks_personal_info: int | None = None


@app.get("/api/pymupdf/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/debug-db")
def debug_db():
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user;")
                row = cur.fetchone()
                return {
                    "ok": True,
                    "database": row[0],
                    "user": row[1],
                }
        finally:
            conn.close()
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }

@app.post("/api/pymupdf/parse")
async def parse_pdf(
    file: UploadFile = File(...),
    enable_ocr: bool = True,
    ocr_language: str = DEFAULT_OCR_LANGUAGE,
    ocr_dpi: int = DEFAULT_OCR_DPI,
) -> dict[str, object]:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            total_pages = doc.page_count
            page_texts = []
            ocr_pages = 0
            ocr_attempted = 0
            warnings: list[str] = []

            for page in doc:
                # sort=True helps produce a more natural reading order.
                text = page.get_text("text", sort=True).strip()

                if not text and enable_ocr:
                    ocr_attempted += 1
                    try:
                        # OCR fallback for scanned / image-only pages.
                        ocr_textpage = page.get_textpage_ocr(
                            language=ocr_language,
                            dpi=ocr_dpi,
                            full=True,
                        )
                        text = page.get_text("text", textpage=ocr_textpage, sort=True).strip()
                        if text:
                            ocr_pages += 1
                    except Exception as ocr_exc:
                        warnings.append(
                            f"OCR unavailable on page {page.number + 1}: {ocr_exc}"
                        )

                if text:
                    page_texts.append(text)

            merged_text = "\n\n".join(page_texts).strip()

        return {
            "text": merged_text,
            "pageCount": total_pages,
            "extractedPages": len(page_texts),
            "hasText": bool(merged_text),
            "ocrEnabled": enable_ocr,
            "ocrLanguage": ocr_language,
            "ocrDpi": ocr_dpi,
            "ocrAttemptedPages": ocr_attempted,
            "ocrSucceededPages": ocr_pages,
            "warnings": warnings,
        }
    except Exception as exc:  # pragma: no cover - defensive API guard
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict[str, object]:
    try:
        payload = req.model_dump()

        row, scam_pred, scam_prob, type_pred = predict_message(payload)
        result = build_analysis_response(row, scam_pred, scam_prob, type_pred)

        if req.inputType == "link":
            link_result = analyze_link_input(req.text)

            result["domain"] = link_result["domain"]
            result["domainInfo"] = link_result["domainInfo"]
            result["linkPrediction"] = link_result["linkPrediction"]
            result["linkProbability"] = link_result["linkProbability"]

            result["indicators"] = result.get("indicators", []) + link_result["linkIndicators"]
            result["factors"] = result.get("factors", []) + link_result["linkIndicators"]

            extra_explanation = " ".join(link_result["linkExplanation"]).strip()
            if extra_explanation:
                result["explanation"] = f"{result['explanation']} {extra_explanation}".strip()

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {exc}") from exc
