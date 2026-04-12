# .

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## PyMuPDF Backend (for PDF text extraction)

The frontend already calls `/api/pymupdf/parse` when uploading a PDF.

This repository now includes a Python backend at [backend/main.py](backend/main.py).

### 1) Create and activate a Python virtual environment

Windows (PowerShell):

```sh
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2) Install backend dependencies

```sh
pip install -r backend/requirements.txt
```

### 3) Start backend API

```sh
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4) Start frontend

```sh
npm run dev
```

Vite is configured to proxy `/api/*` to `http://127.0.0.1:8000`, so no frontend code changes are needed.

### Behavior notes

- Text-based PDFs: content is extracted and sent to the scam analysis engine.
- Scanned/image-only PDFs: extracted text may be empty unless OCR is added (for example Tesseract).

### OCR support (optional but recommended)

The backend now attempts OCR automatically for PDF pages where regular text extraction is empty.

OCR relies on Tesseract being installed on the deployment/runtime machine.

1. Install Tesseract OCR:
  - Windows: install from official Tesseract builds and ensure the `tessdata` folder exists.
  - Linux: install with your package manager (for example `apt install tesseract-ocr`).

2. Configure language data path if needed:
  - Set environment variable `TESSDATA_PREFIX` to your `tessdata` directory.

3. Optional environment tuning:
  - `PYMUPDF_OCR_LANGUAGE` (default: `eng`)
  - `PYMUPDF_OCR_DPI` (default: `150`)

When OCR runs, `/api/pymupdf/parse` also returns:
- `ocrAttemptedPages`
- `ocrSucceededPages`
- `warnings`
