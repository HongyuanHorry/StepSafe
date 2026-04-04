<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  quickMode: {
    type: String,
    default: 'text',
  },
})

const emit = defineEmits(['submit'])

const form = reactive({
  text: '',
  link: '',
  pdfFile: null,
  recruiterName: '',
})

const inputType = ref('text')
const errorMessage = ref('')

const inputLabel = computed(() => {
  if (inputType.value === 'text') return 'Recruiter message'
  if (inputType.value === 'link') return 'Recruitment link'
  return 'PDF file'
})

function useDemoText() {
  inputType.value = 'text'
  form.text =
    'Hi friend, simple remote task. Earn 500 dollars quickly. You only need to pay a small verification fee first.'
  errorMessage.value = ''
}

function clearCurrentInput() {
  form.text = ''
  form.link = ''
  form.pdfFile = null
  errorMessage.value = ''
}

function onFileChange(event) {
  const selected = event.target.files?.[0] ?? null
  form.pdfFile = selected
  errorMessage.value = ''
}

function validatePayload() {
  if (inputType.value === 'text' && !form.text.trim()) {
    return 'Please paste a recruiter message before analysis.'
  }

  if (inputType.value === 'link' && !form.link.trim()) {
    return 'Please enter a link before analysis.'
  }

  if (inputType.value === 'pdf' && !form.pdfFile) {
    return 'Please select a PDF file before analysis.'
  }

  return ''
}

function submitForAnalysis() {
  const validationError = validatePayload()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  errorMessage.value = ''
  emit('submit', {
    inputType: inputType.value,
    text: form.text,
    link: form.link,
    pdfFile: form.pdfFile,
    recruiterName: form.recruiterName,
  })
}

watch(
  () => props.quickMode,
  (mode) => {
    if (!mode || !['text', 'pdf', 'link'].includes(mode)) {
      return
    }
    inputType.value = mode
    errorMessage.value = ''
  },
  { immediate: true },
)
</script>

<template>
  <section class="submission-panel" aria-label="Submission panel">
    <div class="submission-head">
      <div class="head-inset" aria-hidden="true">
        <img src="https://img.icons8.com/cotton/64/security-checked--v1.png" alt="" />
      </div>
      <div>
        <p class="head-kicker">Core workflow</p>
        <h2>Check scam</h2>
        <p class="head-summary">
          Pick one input mode, provide evidence, then run analysis to receive a risk result and scam
          stage explanation.
        </p>
      </div>
    </div>

    <div class="editor-grid">
      <aside class="mode-rail" role="tablist" aria-label="Input type tabs">
        <button
          type="button"
          class="mode-button"
          :class="{ 'mode-button--active': inputType === 'text' }"
          @click="inputType = 'text'"
        >
          Paste recruiter message
        </button>
        <button
          type="button"
          class="mode-button"
          :class="{ 'mode-button--active': inputType === 'pdf' }"
          @click="inputType = 'pdf'"
        >
          Upload PDF
        </button>
        <button
          type="button"
          class="mode-button"
          :class="{ 'mode-button--active': inputType === 'link' }"
          @click="inputType = 'link'"
        >
          Paste website link
        </button>

        <div class="rail-assist-actions">
          <button type="button" class="assist-btn" @click="useDemoText">Use demo text</button>
          <button type="button" class="assist-btn assist-btn--muted" @click="clearCurrentInput">
            Clear
          </button>
        </div>

        <div class="mode-field">
          <label class="mode-input-row" for="recruiterName">Recruiter name</label>
          <input
            id="recruiterName"
            v-model="form.recruiterName"
            type="text"
            placeholder="Optional"
          />
        </div>
      </aside>

      <div class="compose-pane">
        <div class="compose-head">
          <p>Evidence Input</p>
          <p class="compose-head__mode">{{ inputLabel }}</p>
        </div>

        <div v-if="inputType === 'text'" class="input-card">
          <label for="messageText">Paste recruiter content</label>
          <textarea
            id="messageText"
            v-model="form.text"
            rows="6"
            placeholder="Paste recruiter content here"
          />
        </div>

        <div v-if="inputType === 'link'" class="input-card">
          <label for="messageLink">Paste website URL</label>
          <input
            id="messageLink"
            v-model="form.link"
            type="url"
            placeholder="https://example.com/job-offer"
          />
        </div>

        <div v-if="inputType === 'pdf'" class="input-card input-card--pdf">
          <label for="pdfInput">Upload PDF file</label>
          <input id="pdfInput" type="file" accept=".pdf,application/pdf" @change="onFileChange" />
          <p v-if="form.pdfFile" class="small-note">Selected: {{ form.pdfFile.name }}</p>
          <p class="small-note">
            PDF text extraction tries the backend PyMuPDF endpoint first, then falls back to local
            reading.
          </p>
        </div>

        <p class="privacy-note">
          Privacy note: We only analyze content you submit to detect scam patterns.
        </p>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

        <button type="button" class="analyze-btn" @click="submitForAnalysis">Analyze now</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
*,
*::before,
*::after {
  box-sizing: border-box;
}

.submission-panel {
  background: var(--ms-color-surface-page-start);
  padding: 24px;
}

.submission-head {
  align-items: center;
  background: var(--ms-color-surface-subtle);
  display: grid;
  gap: 18px;
  grid-template-columns: 96px minmax(0, 1fr);
  margin-bottom: 18px;
  padding: 24px;
}

.head-inset {
  align-items: center;
  background: var(--ms-color-surface-page-mid);
  display: flex;
  height: 96px;
  justify-content: center;
  width: 96px;
}

.head-inset img {
  height: 46px;
  width: 46px;
}

.head-kicker {
  color: var(--ms-color-brand-hover);
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  margin: 0 0 12px;
  text-transform: uppercase;
}

h2 {
  font-size: clamp(2rem, 4vw, 3.1rem);
  font-weight: 300;
  line-height: 0.95;
  margin: 0 0 20px;
}

.head-summary {
  color: var(--ms-color-text-secondary);
  line-height: 1.55;
  margin: 0;
  max-width: 760px;
}

.editor-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(240px, 0.68fr) minmax(0, 1.32fr);
}

.mode-rail {
  background: var(--ms-color-surface-page-mid);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 24px;
}

.mode-button {
  background: var(--ms-color-surface-page-start);
  border: 0;
  color: var(--ms-color-text-primary);
  cursor: pointer;
  font-size: 0.96rem;
  font-weight: 500;
  min-height: 48px;
  padding: 12px 14px;
  text-align: left;
  transition: background-color 0.2s ease;
}

.mode-button--active {
  background: var(--ms-color-brand);
  color: rgb(255, 255, 255);
}

.mode-button:hover,
.mode-button:focus-visible {
  background: var(--ms-color-brand-hover);
  color: rgb(255, 255, 255);
}

.rail-assist-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.assist-btn {
  background: rgb(26, 25, 24);
  border: 0;
  color: rgb(255, 255, 255);
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 500;
  min-height: 40px;
  padding: 8px 12px;
}

.assist-btn:hover,
.assist-btn:focus-visible {
  background: rgb(46, 44, 43);
}

.assist-btn--muted {
  background: rgb(84, 83, 82);
}

.mode-field {
  background: var(--ms-color-surface-page-start);
  margin-top: 12px;
  padding: 20px;
}

.mode-input-row {
  color: var(--ms-color-text-secondary);
  display: block;
  font-size: 0.84rem;
  font-weight: 500;
  margin-bottom: 10px;
  text-transform: uppercase;
}

.mode-field input {
  display: block;
  max-width: 100%;
  width: 100%;
}

.compose-pane {
  background: var(--ms-color-surface-page-start);
  display: grid;
  gap: 14px;
  padding: 24px;
}

.compose-head {
  align-items: baseline;
  display: flex;
  justify-content: space-between;
}

.compose-head p {
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  margin: 0;
  text-transform: uppercase;
}

.compose-head__mode {
  color: var(--ms-color-brand-hover);
}

.input-card {
  background: var(--ms-color-surface-subtle);
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 188px;
  padding: 24px;
}

label {
  color: var(--ms-color-text-secondary);
  font-size: 0.86rem;
  font-weight: 500;
}

input,
textarea {
  background: var(--ms-color-surface-page-start);
  box-sizing: border-box;
  color: var(--ms-color-text-primary);
  min-height: 44px;
  width: 100%;
  padding: 12px 14px;
}

input:hover,
textarea:hover,
input:focus,
textarea:focus {
  outline: 2px solid var(--ms-color-brand);
  outline-offset: 0;
}

textarea {
  min-height: 170px;
}

.input-card--pdf {
  min-height: auto;
}

.small-note {
  color: var(--ms-color-text-tertiary);
  font-size: 0.88rem;
  margin: 0;
}

.privacy-note {
  background: var(--ms-color-surface-page-mid);
  color: var(--ms-color-text-secondary);
  line-height: 1.6;
  margin: 0;
  padding: 20px;
}

.error-text {
  background: var(--ms-color-danger-soft);
  color: var(--ms-color-danger);
  margin: 0;
  padding: 20px;
}

.analyze-btn {
  background: var(--ms-color-brand);
  border: 0;
  color: rgb(255, 255, 255);
  cursor: pointer;
  display: inline-flex;
  font-size: 1.02rem;
  font-weight: 600;
  justify-content: center;
  min-height: 52px;
  min-width: 260px;
  padding: 16px 32px;
  text-transform: uppercase;
  transition: background-color 0.2s ease;
}

.analyze-btn:hover,
.analyze-btn:focus-visible {
  background: var(--ms-color-brand-hover);
}

.analyze-btn:active {
  background: var(--ms-color-brand-active);
}

@media (max-width: 920px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .submission-head {
    grid-template-columns: 1fr;
  }

  .analyze-btn {
    width: 100%;
  }
}
</style>
