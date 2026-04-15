from __future__ import annotations

import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymupdf

from backend.ml.inference import predict_message
from backend.ml.rules import build_analysis_response

app = FastAPI(title="StepSafe PyMuPDF API", version="1.0.0")

DEFAULT_OCR_LANGUAGE = os.getenv("PYMUPDF_OCR_LANGUAGE", "eng")
DEFAULT_OCR_DPI = int(os.getenv("PYMUPDF_OCR_DPI", "150"))
ABN_API_GUID = os.getenv("ABN_API_GUID", "").strip()
ABR_BASE_URL = "https://abr.business.gov.au/ABRXMLSearch/AbrXmlSearch.asmx"

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


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _first_text(node: ET.Element, names: set[str]) -> str:
    lowered = {name.lower() for name in names}
    for child in node.iter():
        if _local_name(child.tag).lower() in lowered:
            value = (child.text or "").strip()
            if value:
                return value
    return ""


def _parse_abn_payload(xml_bytes: bytes, query: str) -> dict[str, object]:
    root = ET.fromstring(xml_bytes)

    usage = _first_text(root, {"usageStatement", "exceptionDescription"})

    if query.isdigit() and len(query) == 11:
        abn = _first_text(root, {"identifierValue", "abn"}) or query
        name = _first_text(root, {"entityName", "mainName", "organisationName", "name"})
        status = _first_text(root, {"entityStatusCode", "status"})
        state = _first_text(root, {"stateCode", "addressStateCode"})
        postcode = _first_text(root, {"postcode", "addressPostcode"})

        if not name and not status and not state and not postcode and not usage:
            return {
                "query": query,
                "results": [],
                "count": 0,
                "message": "No ABN record found.",
            }

        return {
            "query": query,
            "results": [
                {
                    "abn": abn,
                    "name": name or "Unknown",
                    "status": status or "Unknown",
                    "state": state,
                    "postcode": postcode,
                    "matchScore": 100,
                }
            ],
            "count": 1,
            "message": usage,
        }

    records: list[dict[str, object]] = []
    for record in root.iter():
        if _local_name(record.tag) != "searchResultsRecord":
            continue

        abn = _first_text(record, {"ABN", "identifierValue", "abn"})
        name = _first_text(
            record,
            {"mainName", "organisationName", "businessName", "name"},
        )
        status = _first_text(record, {"entityStatusCode", "status"})
        score = _first_text(record, {"score", "matchScore"})

        records.append(
            {
                "abn": abn,
                "name": name or "Unknown",
                "status": status or "Unknown",
                "state": "",
                "postcode": "",
                "matchScore": int(score) if score.isdigit() else None,
            }
        )

    return {
        "query": query,
        "results": records,
        "count": len(records),
        "message": usage,
    }


def _fetch_abr_xml(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "StepSafe/1.0"})
    with urlopen(request, timeout=15) as response:
        return response.read()


@app.get("/api/abn/lookup")
def lookup_abn(query: str) -> dict[str, object]:
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    if not ABN_API_GUID:
        raise HTTPException(
            status_code=503,
            detail=(
                "ABN lookup is not configured. Set ABN_API_GUID in backend environment "
                "before using /api/abn/lookup."
            ),
        )

    try:
        if query.isdigit() and len(query) == 11:
            params = urlencode(
                {
                    "searchString": query,
                    "includeHistoricalDetails": "Y",
                    "authenticationGuid": ABN_API_GUID,
                }
            )
            url = f"{ABR_BASE_URL}/ABRSearchByABN?{params}"
        else:
            params = urlencode(
                {
                    "name": query,
                    "postcode": "",
                    "legalName": "Y",
                    "tradingName": "Y",
                    "businessName": "Y",
                    "activeABNsOnly": "Y",
                    "NSW": "Y",
                    "SA": "Y",
                    "ACT": "Y",
                    "VIC": "Y",
                    "WA": "Y",
                    "NT": "Y",
                    "QLD": "Y",
                    "TAS": "Y",
                    "authenticationGuid": ABN_API_GUID,
                    "searchWidth": "typical",
                    "minimumScore": "0",
                    "maxSearchResults": "10",
                }
            )
            url = f"{ABR_BASE_URL}/ABRSearchByNameAdvancedSimpleProtocol2017?{params}"

        xml_payload = _fetch_abr_xml(url)
        return _parse_abn_payload(xml_payload, query)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ABN lookup failed: {exc}") from exc


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

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {exc}") from exc
