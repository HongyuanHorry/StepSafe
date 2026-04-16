import os
import pymupdf


DEFAULT_OCR_LANGUAGE = os.getenv("PYMUPDF_OCR_LANGUAGE", "eng")
DEFAULT_OCR_DPI = int(os.getenv("PYMUPDF_OCR_DPI", "150"))


def parse_pdf_bytes(
    data: bytes,
    filename: str = "uploaded.pdf",
    enable_ocr: bool = True,
    ocr_language: str = DEFAULT_OCR_LANGUAGE,
    ocr_dpi: int = DEFAULT_OCR_DPI,
) -> dict[str, object]:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")

    if not data:
        raise ValueError("Uploaded file is empty.")

    with pymupdf.open(stream=data, filetype="pdf") as doc:
        total_pages = doc.page_count
        page_texts = []
        ocr_pages = 0
        ocr_attempted = 0
        warnings: list[str] = []

        for page in doc:
            text = page.get_text("text", sort=True).strip()

            if not text and enable_ocr:
                ocr_attempted += 1
                try:
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