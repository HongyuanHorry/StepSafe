from __future__ import annotations

import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pymupdf

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


@app.get("/api/pymupdf/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
