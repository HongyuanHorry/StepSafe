<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  quickMode: {
    type: String,
    default: 'text',
  },
})

const emit = defineEmits(['submit'])

const STORAGE_LAST_MODE_KEY = 'stepsafe:last-input-mode'
const STORAGE_RECENT_CHECKS_KEY = 'stepsafe:recent-checks'

const form = reactive({
  text: '',
  link: '',
  pdfFile: null,
  recruiterName: '',
})

const inputType = ref(readStoredInputMode())
const errorMessage = ref('')
const recentChecks = ref(readStoredRecentChecks())
const isQuickControlsOpen = ref(false)

const sampleInputs = {
  low:
    'Hello, we saw your profile and invite you to apply. Interview details are on our official site. No upfront payment is required.',
  medium:
    'Great part-time task role. Complete simple review tasks and receive commission quickly. You can unlock more rewards after the first recharge.',
  high:
    'Urgent: complete these simple tasks now and earn guaranteed commission. Transfer a verification fee immediately to release your payout.',
}

const inputLabel = computed(() => {
  if (inputType.value === 'text') return 'Recruiter message'
  if (inputType.value === 'link') return 'Recruitment link'
  return 'PDF file'
})

function readStoredInputMode() {
  if (typeof window === 'undefined') return 'text'

  const saved = window.localStorage.getItem(STORAGE_LAST_MODE_KEY)
  if (saved === 'text' || saved === 'pdf' || saved === 'link') {
    return saved
  }

  return 'text'
}

function readStoredRecentChecks() {
  if (typeof window === 'undefined') return []

  const raw = window.localStorage.getItem(STORAGE_RECENT_CHECKS_KEY)
  if (!raw) return []

  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.slice(0, 3)
  } catch {
    return []
  }
}

function persistRecentChecks() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_RECENT_CHECKS_KEY, JSON.stringify(recentChecks.value.slice(0, 3)))
}

function applySampleInput(level) {
  inputType.value = 'text'
  form.text = sampleInputs[level] ?? sampleInputs.high
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
  const payload = {
    inputType: inputType.value,
    text: form.text,
    link: form.link,
    pdfFile: form.pdfFile,
    recruiterName: form.recruiterName,
  }

  emit('submit', payload)

  const recentEntry = {
    id: Date.now(),
    inputType: payload.inputType,
    recruiterName: payload.recruiterName,
    text: payload.text?.slice(0, 480) ?? '',
    link: payload.link?.slice(0, 280) ?? '',
    createdAt: new Date().toISOString(),
  }

  recentChecks.value = [recentEntry, ...recentChecks.value].slice(0, 3)
  persistRecentChecks()
}

function reuseRecentCheck(item) {
  if (!item) return

  inputType.value = item.inputType === 'pdf' ? 'text' : item.inputType
  form.recruiterName = item.recruiterName ?? ''
  form.text = item.text ?? ''
  form.link = item.link ?? ''
  form.pdfFile = null
  errorMessage.value =
    item.inputType === 'pdf'
      ? 'PDF records require re-uploading the file before analysis.'
      : ''
}

function getRecentLabel(item) {
  if (item.inputType === 'link') {
    return item.link ? `Link: ${item.link}` : 'Link record'
  }

  if (item.inputType === 'pdf') {
    return 'PDF record (re-upload required)'
  }

  if (item.text) {
    return `Text: ${item.text.slice(0, 64)}${item.text.length > 64 ? '...' : ''}`
  }

  return 'Text record'
}

function handleComposeKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    submitForAnalysis()
  }
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
)

watch(
  inputType,
  (mode) => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(STORAGE_LAST_MODE_KEY, mode)
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
        <p class="mode-hint">Choose one input mode first (3 options), then add evidence below.</p>

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

      <div class="compose-pane" @keydown="handleComposeKeydown">
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

        <section class="quick-controls" aria-label="Sample inputs and recent checks">
          <button
            type="button"
            class="quick-controls__toggle"
            aria-controls="quick-controls-panel"
            :aria-expanded="isQuickControlsOpen"
            @click="isQuickControlsOpen = !isQuickControlsOpen"
          >
            <span>Quick controls</span>
            <span class="quick-controls__toggle-text">{{ isQuickControlsOpen ? 'Hide' : 'Show' }}</span>
          </button>

          <div v-if="isQuickControlsOpen" id="quick-controls-panel" class="quick-controls__panel">
            <div class="rail-assist-actions" aria-label="Sample inputs">
              <button type="button" class="assist-btn" @click="applySampleInput('low')">
                Low sample
              </button>
              <button type="button" class="assist-btn" @click="applySampleInput('medium')">
                Medium sample
              </button>
              <button type="button" class="assist-btn" @click="applySampleInput('high')">
                High sample
              </button>
              <button
                type="button"
                class="assist-btn assist-btn--muted"
                @click="clearCurrentInput"
              >
                Clear
              </button>
            </div>

            <div v-if="recentChecks.length" class="recent-checks" aria-label="Recent checks">
              <p class="recent-checks__title">Recent checks</p>
              <button
                v-for="item in recentChecks"
                :key="item.id"
                type="button"
                class="recent-check-btn"
                @click="reuseRecentCheck(item)"
              >
                {{ getRecentLabel(item) }}
              </button>
            </div>
          </div>
        </section>

        <p class="privacy-note">
          Privacy note: Your submitted text, link, or extracted PDF content is used only for this
          risk assessment workflow. Please avoid uploading highly sensitive personal data such as
          bank credentials, identity numbers, or private account secrets.
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
  padding: 18px;
}

.submission-head {
  align-items: center;
  background: var(--ms-color-surface-subtle);
  display: grid;
  gap: 12px;
  grid-template-columns: 76px minmax(0, 1fr);
  margin-bottom: 12px;
  padding: 16px;
}

.head-inset {
  align-items: center;
  background: var(--ms-color-surface-page-mid);
  display: flex;
  height: 76px;
  justify-content: center;
  width: 76px;
}

.head-inset img {
  height: 36px;
  width: 36px;
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
  margin: 0 0 12px;
}

.head-summary {
  color: var(--ms-color-text-secondary);
  line-height: 1.55;
  margin: 0;
  max-width: 760px;
}

.editor-grid {
  align-items: start;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(240px, 0.68fr) minmax(0, 1.32fr);
}

.mode-rail {
  background: var(--ms-color-surface-page-mid);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
}

.mode-hint {
  color: var(--ms-color-text-secondary);
  font-size: 0.76rem;
  line-height: 1.45;
  margin: 0 0 2px;
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
  margin-top: 0;
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
  margin-top: 8px;
  padding: 16px;
}

.recent-checks {
  background: var(--ms-color-surface-page-start);
  margin-top: 8px;
  padding: 12px;
}

.quick-controls {
  background: var(--ms-color-surface-page-mid);
  border-top: 1px solid rgba(26, 25, 24, 0.12);
  margin-top: 2px;
  padding: 12px;
}

.quick-controls__toggle {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--ms-color-text-primary);
  cursor: pointer;
  display: flex;
  font-size: 0.78rem;
  font-weight: 600;
  justify-content: space-between;
  letter-spacing: 0.07em;
  padding: 0;
  text-transform: uppercase;
  width: 100%;
}

.quick-controls__toggle-text {
  color: var(--ms-color-brand-hover);
  font-size: 0.72rem;
  font-weight: 600;
}

.quick-controls__panel {
  margin-top: 10px;
}

.recent-checks__title {
  color: var(--ms-color-text-secondary);
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.recent-check-btn {
  background: var(--ms-color-surface-subtle);
  border: 0;
  color: var(--ms-color-text-primary);
  cursor: pointer;
  display: block;
  font-size: 0.8rem;
  margin-bottom: 8px;
  min-height: 36px;
  overflow: hidden;
  padding: 8px 10px;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.recent-check-btn:last-child {
  margin-bottom: 0;
}

.recent-check-btn:hover,
.recent-check-btn:focus-visible {
  background: var(--ms-color-border-soft);
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

#recruiterName {
  scroll-margin-top: 84px;
}

.compose-pane {
  background: var(--ms-color-surface-page-start);
  display: grid;
  gap: 10px;
  padding: 18px;
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
  gap: 8px;
  min-height: 150px;
  padding: 18px;
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
  font-size: 0.74rem;
  letter-spacing: 0.01em;
  line-height: 1.6;
  margin: 0;
  padding: 14px;
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
  min-height: 48px;
  min-width: 260px;
  padding: 14px 28px;
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
