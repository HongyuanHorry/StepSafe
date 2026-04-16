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
from backend.services.pdf_analysis import parse_pdf_bytes
from backend.services.analyze_core import analyze_payload

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
    data = await file.read()

    try:
        return parse_pdf_bytes(
            data=data,
            filename=filename,
            enable_ocr=enable_ocr,
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
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

@app.post("/api/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    enable_ocr: bool = True,
    ocr_language: str = DEFAULT_OCR_LANGUAGE,
    ocr_dpi: int = DEFAULT_OCR_DPI,
) -> dict[str, object]:
    filename = file.filename or "uploaded.pdf"
    data = await file.read()

    try:
        parsed = parse_pdf_bytes(
            data=data,
            filename=filename,
            enable_ocr=enable_ocr,
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
        )

        payload = {
            "inputType": "pdf",
            "text": parsed["text"],
            "message_type": "Email",
            "platform": "Gmail",
            "job_type": "Remote",
        }

        analysis = analyze_payload(payload)

        return {
            "inputType": "pdf",
            "filename": filename,
            "parse": parsed,
            "analysis": analysis,
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyze PDF failed: {exc}") from exc