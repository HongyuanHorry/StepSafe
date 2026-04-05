# StepSafe Technical Handover (Backend Iteration)

Last updated: 2026-04-05

Current strict completion snapshot (after latest UI updates):

- US completed: 0 / 4
- AC completed: 7 / 16

## 1. Purpose and Scope

This document is for backend engineers who will continue StepSafe iteration work.

Current delivered capability:

- Frontend can accept text, link, and PDF input.
- PDF text extraction is integrated with a FastAPI + PyMuPDF service.
- Scam scoring and classification currently run in frontend JavaScript logic.

Important scope boundary:

- This is not yet a true backend-driven detection engine.
- The backend currently only performs PDF parsing (plus optional OCR fallback).

---

## 2. Current Architecture (As Implemented)

## 2.1 Frontend

- Framework: Vue 3 + Vite.
- Core page orchestration: src/App.vue
- Submission UI: src/components/SubmissionPanel.vue
- Result UI: src/components/ResultPanel.vue
- Detection logic (currently frontend-side): src/services/scamAnalysisEngine.js
- Rule/taxonomy constants: src/constants/scamRules.js

## 2.2 Backend

- Framework: FastAPI + Uvicorn
- File: backend/main.py
- Endpoint:
  - GET /api/pymupdf/health
  - POST /api/pymupdf/parse
- Purpose: Parse PDF text via PyMuPDF, with OCR fallback per page when no embedded text is found.

## 2.3 Runtime wiring

- Vite dev proxy forwards /api to http://127.0.0.1:8000 (vite.config.js).
- Frontend calls /api/pymupdf/parse for PDF only.
- Text/link analysis does not call backend currently.

---

## 3. Core Data Flow

## 3.1 Text input path

1. User submits recruiter message in SubmissionPanel.
2. App calls extractTextFromSubmission with inputType=text.
3. Returned text is analyzed by analyzeTextContent in frontend.
4. ResultPanel renders score, type, indicators, and explanation.

Backend participation: none.

## 3.2 Link input path

1. User submits link in SubmissionPanel.
2. App calls extractTextFromSubmission with inputType=link.
3. Raw link string is analyzed directly by analyzeTextContent in frontend.
4. ResultPanel renders output.

Backend participation: none.

## 3.3 PDF input path

1. User uploads PDF in SubmissionPanel.
2. App calls extractTextFromSubmission with inputType=pdf.
3. Frontend sends multipart request to POST /api/pymupdf/parse.
4. Backend extracts text page-by-page (and OCR fallback when enabled).
5. Frontend receives text and runs analyzeTextContent in frontend.
6. ResultPanel renders output and a collapsible extracted-text preview.

---

## 4. API Contract (Current)

## 4.1 GET /api/pymupdf/health

Response:
{
"status": "ok"
}

## 4.2 POST /api/pymupdf/parse

Request:

- multipart/form-data
- file: UploadFile (.pdf)
- query params:
  - enable_ocr: bool (default true)
  - ocr_language: str (default env PYMUPDF_OCR_LANGUAGE or eng)
  - ocr_dpi: int (default env PYMUPDF_OCR_DPI or 150)

Success response fields:

- text: string
- pageCount: number
- extractedPages: number
- hasText: boolean
- ocrEnabled: boolean
- ocrLanguage: string
- ocrDpi: number
- ocrAttemptedPages: number
- ocrSucceededPages: number
- warnings: string[]

Error behavior:

- 400 for non-PDF/empty file/parse exception.
- Frontend maps 502 to parser-unavailable message when backend is down.

---

## 5. Detection Logic (Current Frontend Implementation)

Location: src/services/scamAnalysisEngine.js and src/constants/scamRules.js

## 5.1 Rule model

Each rule contains:

- id
- label
- regex pattern
- severity
- weight
- typeVotes (for scam type classification)

Current taxonomy:

- task-based scam
- job scam
- payment scam
- unknown or unclear (fallback)

## 5.2 Risk scoring

Simple version (recommended for handover reading):

1. Add up all matched warning-sign weights.
2. If high-severity matches are 3 or more, add 12.
3. If total matched warning signs are 4 or more, add 6.
4. If the final number is above 100, set it to 100.
5. If the final number is below 0, set it to 0.

Compact formula (same logic as code):

$$
\mathrm{RiskScore} = \max\left(0, \min\left(100, \sum_{i=1}^{N} w_i + [H \ge 3] \cdot 12 + [N \ge 4] \cdot 6\right)\right)
$$

Where:

- N = total matched warning signs
- H = matched warning signs with high severity
- w_i = weight of the i-th matched warning sign
- [condition] = 1 if true, otherwise 0

Worked examples:

- Example A: matched weights 34 + 22 = 56, H=1, N=2 -> score = 56.
- Example B: matched weights 34 + 34 + 30 = 98, H=3, N=3 -> +12 -> 110 -> capped to 100.
- Example C: matched weights 22 + 20 + 34 + 30 = 106, H=2, N=4 -> +6 -> 112 -> capped to 100.

## 5.3 Suspicious label logic

- suspicious = (riskScore >= 40) OR (matched indicators >= 2)

Current UI note:

- ResultPanel now shows an explicit binary status label: "Suspicious" or "Not suspicious".

## 5.4 Scam type classification

- Aggregate weighted votes into taxonomy buckets.
- confidence = topScore / totalScore.
- If confidence < threshold (0.5) or no score, return "unknown or unclear".

---

## 6. Ops Runbook (Local)

## 6.1 Frontend

1. npm install
2. npm run dev

## 6.2 Backend

1. Create and activate venv
2. pip install -r backend/requirements.txt
3. uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

## 6.3 OCR prerequisites

- Install Tesseract runtime in deployment environment.
- Ensure tessdata available; set TESSDATA_PREFIX when required.

---

## 7. Strict Epic Completion Matrix (US/AC)

Definition used here:

- US is counted as completed only when all AC under that US are fully satisfied in implementation.
- Any partial/missing/ambiguous AC means US is not completed.

## 7.1 Epic 1.0

### US 1.1 Submit Content for Scam Analysis

- US 1.1 overall status: Not completed (strict)

AC status:

- AC 1.1.1: Not completed (strict)
  - Reason: all three input types are accepted in UI, and PDF uses PyMuPDF parse; however text/link are not routed to a backend detection engine, only frontend analysis.
- AC 1.1.2: Completed
  - Reason: result page now shows an explicit binary status label ("Suspicious" / "Not suspicious").
- AC 1.1.3: Completed
  - Reason: indicators such as payment, urgency, sensitive info are detected and rendered.

### US 1.2 Scam Risk Score

- US 1.2 overall status: Not completed (strict)

AC status:

- AC 1.2.1: Not completed (strict)
  - Reason: risk score is computed by frontend JS, not backend detection engine.
- AC 1.2.2: Completed
  - Reason: factors contributing to score are listed and surfaced.
- AC 1.2.3: Completed
  - Reason: additive weighting with multi-flag bonus is implemented.
- AC 1.2.4: Completed
  - Reason: result text was simplified to plain-language wording and technical phrasing was removed from the result view.

### US 1.3 Identify Scam Type

- US 1.3 overall status: Not completed (strict)

AC status:

- AC 1.3.1: Not completed (strict)
  - Reason: fixed taxonomy exists, but it is hard-coded in frontend constants rather than maintained in a database.
- AC 1.3.2: Completed
  - Reason: scam type is displayed in result summary near score panel.
- AC 1.3.3: Completed
  - Reason: confidence threshold and unknown/unclear fallback are implemented.

## 7.2 Epic 3.0 Recruiter & Business Legitimacy Verification

### US 3.1 Verify Recruiter or Business

- US 3.1 overall status: Not completed (strict)

AC status:

- AC 3.1.1: Not completed
  - Reason: no implemented legitimacy engine and no dedicated legitimacy reasoning output.
- AC 3.1.2: Not completed
  - Reason: no ABN/business registry lookup implementation.
- AC 3.1.3: Not completed
  - Reason: no explicit limited-result messaging logic tied to incomplete recruiter/company data.
- AC 3.2.1: Not completed
  - Reason: no domain verification pipeline (domain age/reputation/consistency) implemented.
- AC 3.2.2: Not completed
  - Reason: no domain risk warning path implemented from actual domain intelligence source.
- AC 3.2.3: Not completed
  - Reason: no positive trust indicator path based on verified domain-business matching.

---

## 8. What Paths Are Still Not Fully Run Through

1. End-to-end backend-driven detection path (text/link/pdf -> backend scoring/classification -> frontend render) is not implemented.
2. Production deployment path (frontend + backend + OCR runtime) has not been fully verified as a single reproducible deployment runbook.
3. OCR success path on true scanned PDFs has not been consistently validated in this repository with pinned fixture cases.
4. ABN lookup path and domain legitimacy path are not implemented.
5. No automated unit/integration/e2e test suite exists to prove AC compliance continuously.
6. No persistence/database layer exists for taxonomy/rules/versioning/audit.

---

## 9. Recommended Backend Iteration Plan

Priority P0 (to make Epic 1 strict-complete path possible):

1. Add backend analysis endpoint (for all input types):
   - POST /api/analyze
   - Input: normalized text content + metadata
   - Output: suspicious(boolean), binaryLabel, riskScore, scamType, indicators, factors, explanation
2. Move scoring/classification logic from frontend to backend service.
3. Add explicit binary label field and make frontend display it prominently.
4. Add API-level contract tests for score/type/threshold behavior.

Priority P1 (Epic 3 baseline):

1. Add ABN verification service abstraction (provider-swappable).
2. Add domain checks (age, registrar confidence, mismatch checks).
3. Add legitimacy result model with limited-evidence state.

Priority P2 (engineering quality):

1. Add test pyramid:
   - backend unit tests for scoring/classification
   - API integration tests for /api/pymupdf/parse and /api/analyze
   - frontend e2e happy paths for text/link/pdf
2. Add observability:
   - request IDs
   - parse/analyze timing
   - OCR warnings metrics
3. Add deployment artifacts:
   - Dockerfile(s)
   - env templates
   - health/readiness checks

---

## 10. Known Risks and Notes

1. Current trust boundary risk: analysis in frontend can be bypassed or altered by client-side changes.
2. OCR dependency risk: Tesseract missing in runtime will reduce extraction quality for scanned PDFs.
3. UX consistency issue: SubmissionPanel text says parse may fallback to local reading, but current engine intentionally removed raw local PDF text fallback to avoid binary-gibberish output.
4. Dataset under datasets/ exists, but no backend training/inference pipeline currently consumes it.

---

## 11. Handover Checklist for Next Engineer

1. Confirm local startup for both frontend and backend.
2. Confirm /api/pymupdf/health and /api/pymupdf/parse with at least one text PDF and one scanned PDF.
3. Implement /api/analyze and migrate rule engine server-side.
4. Wire frontend submission to /api/analyze for text/link/pdf.
5. Add strict AC validation checklist in test cases.
6. Implement Epic 3 legitimacy verification endpoints and UI model.

---

## 12. Repository Upload Boundary and venv Notes

1. Git repository root is the StepSafe folder.
2. Parent folder artifacts (for example Iteration 1/.venv/) are outside this repository and are not committed when pushing StepSafe.
3. StepSafe/.gitignore now includes Python virtual environment and cache patterns:

- .venv/
- venv/
- **pycache**/
- \*.py[cod]

4. Current verification: no venv files are tracked in the StepSafe git index.
