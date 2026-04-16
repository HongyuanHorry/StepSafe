<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { lookupAbnByBackend } from '@/services/scamAnalysisEngine'
const props = defineProps({
  quickMode: {
    type: String,
    default: 'text',
  },
  isAnalyzing: {
    type: Boolean,
    default: false,
  },
  abnQuery: {
    type: String,
    default: '',
  },
  abnResults: {
    type: Array,
    default: () => [],
  },
  abnLoading: {
    type: Boolean,
    default: false,
  },
  abnError: {
    type: String,
    default: '',
  },
  confirmedAbn: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits([
  'submit',
  'update:abn-query',
  'search-abn',
  'clear-abn',
  'confirm-abn',
])

const STORAGE_LAST_MODE_KEY = 'stepsafe:last-input-mode'
const STORAGE_RECENT_CHECKS_KEY = 'stepsafe:recent-checks'
const MAX_TEXT_LENGTH = 6000
const MAX_LINK_LENGTH = 2048
const MAX_NAME_LENGTH = 80
const MAX_PDF_SIZE_BYTES = 8 * 1024 * 1024
const ABN_RESULTS_LIMIT = 8

const form = reactive({
  text: '',
  link: '',
  pdfFile: null,
  recruiterName: '',
})

const inputType = ref(readStoredInputMode())
const pdfInputRef = ref(null)
const errorMessage = ref('')
const recentChecks = ref(readStoredRecentChecks())
const isQuickControlsOpen = ref(false)
const abnLookupState = reactive({
  loading: false,
  error: '',
  queried: false,
  usageMessage: '',
  previewTier: '',
  selectedAbn: '',
  results: [],
})

const abnPreviewModes = [
  { label: 'Exact match', tier: 'exact' },
  { label: 'Name match', tier: 'name' },
  { label: 'Inactive ABN', tier: 'inactive' },
]

const sampleInputs = {
  low: 'Hello, thank you for your application. Please respond before the deadline today so we can confirm interview slots this week. No payment is required for this role.',
  medium:
    'This role promises easy money and no experience needed high income. Act now because this offer is today only.',
  high: 'Urgent: complete simple task batches now and earn guaranteed income. Transfer a registration fee immediately to release your payout today only.',
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
  window.localStorage.setItem(
    STORAGE_RECENT_CHECKS_KEY,
    JSON.stringify(recentChecks.value.slice(0, 3)),
  )
}

function applySampleInput(level) {
  inputType.value = 'text'
  form.text = sampleInputs[level] ?? sampleInputs.high
  errorMessage.value = ''
}

function clearCurrentInput() {
  form.text = ''
  form.link = ''
  clearSelectedPdf()
  errorMessage.value = ''
}

function clearSelectedPdf() {
  form.pdfFile = null
  if (pdfInputRef.value instanceof HTMLInputElement) {
    pdfInputRef.value.value = ''
  }
}

function clearAbnLookupState() {
  abnLookupState.loading = false
  abnLookupState.error = ''
  abnLookupState.queried = false
  abnLookupState.usageMessage = ''
  abnLookupState.previewTier = ''
  abnLookupState.selectedAbn = ''
  abnLookupState.results = []
}

function resetAbnLookup() {
  form.recruiterName = ''
  clearAbnLookupState()
}

async function searchAbn() {
  const query = normalizeInput(form.recruiterName)
  if (!query) {
    abnLookupState.error = 'Enter ABN or business name before searching.'
    return
  }

  if (query.length > MAX_NAME_LENGTH) {
    abnLookupState.error = `ABN query must be ${MAX_NAME_LENGTH} characters or fewer.`
    return
  }

  abnLookupState.loading = true
  abnLookupState.error = ''
  abnLookupState.usageMessage = ''
  abnLookupState.previewTier = ''
  abnLookupState.results = []
  abnLookupState.queried = true

  try {
    const result = await lookupAbnByBackend(query)
    const payload = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(payload?.detail || 'ABN lookup request failed.')
    }

    const results = Array.isArray(payload?.results) ? payload.results : []
    abnLookupState.results = results.slice(0, ABN_RESULTS_LIMIT)
    abnLookupState.usageMessage = String(payload?.message ?? '').trim()

    if (!abnLookupState.results.length) {
      abnLookupState.error = 'No matching ABN records were returned.'
    }
  } catch (error) {
    abnLookupState.error = error instanceof Error ? error.message : 'ABN lookup failed.'
  } finally {
    abnLookupState.loading = false
  }
}

function buildAbnPreviewResults(tier) {
  if (tier === 'exact') {
    return [
      {
        abn: '51824753556',
        name: 'STEPSAFE PTY LTD',
        status: 'Active',
        state: 'VIC',
        postcode: '3000',
        matchScore: 100,
      },
    ]
  }

  if (tier === 'inactive') {
    return [
      {
        abn: '78640259366',
        name: 'SAMPLE RECRUITMENT GROUP',
        status: 'Cancelled',
        state: 'NSW',
        postcode: '2000',
        matchScore: 88,
      },
    ]
  }

  return [
    {
      abn: '92631844090',
      name: 'SAMPLE EMPLOYMENT SERVICES',
      status: 'Active',
      state: 'QLD',
      postcode: '4000',
      matchScore: 91,
    },
    {
      abn: '90144568903',
      name: 'SAMPLE EMPLOYMENT CONSULTING',
      status: 'Active',
      state: 'VIC',
      postcode: '3004',
      matchScore: 79,
    },
  ]
}

function previewAbnResult(tier) {
  abnLookupState.loading = false
  abnLookupState.error = ''
  abnLookupState.queried = true
  abnLookupState.previewTier = tier
  abnLookupState.selectedAbn = ''
  abnLookupState.results = buildAbnPreviewResults(tier)
  abnLookupState.usageMessage = 'Preview mode: expected ABN display before backend integration.'
}

function confirmAbn(record) {
  const abn = normalizeInput(record?.abn)
  if (!abn) {
    abnLookupState.error = 'This record does not contain a usable ABN value.'
    return
  }

  form.recruiterName = abn
  abnLookupState.selectedAbn = abn
  abnLookupState.error = ''
}

function normalizeInput(value) {
  return String(value ?? '')
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, ' ')
    .trim()
}

function isLocalOrPrivateHostname(hostname) {
  const host = String(hostname ?? '')
    .trim()
    .toLowerCase()
  if (!host) return true
  if (host === 'localhost' || host.endsWith('.local')) return true
  if (host === '0.0.0.0' || host.startsWith('127.')) return true
  if (host.startsWith('10.') || host.startsWith('192.168.')) return true
  if (host.startsWith('169.254.')) return true
  if (host.startsWith('172.')) {
    const block = Number(host.split('.')[1])
    if (!Number.isNaN(block) && block >= 16 && block <= 31) return true
  }
  return false
}

function onFileChange(event) {
  const selected = event.target.files?.[0] ?? null

  if (!selected) {
    clearSelectedPdf()
    return
  }

  if (selected && selected.size > MAX_PDF_SIZE_BYTES) {
    clearSelectedPdf()
    errorMessage.value = 'PDF must be smaller than 8MB.'
    return
  }

  if (
    selected &&
    selected.type !== 'application/pdf' &&
    !String(selected.name ?? '')
      .toLowerCase()
      .endsWith('.pdf')
  ) {
    clearSelectedPdf()
    errorMessage.value = 'Only PDF files are accepted.'
    return
  }

  form.pdfFile = selected
  errorMessage.value = ''
}

function validatePayload() {
  const normalizedText = normalizeInput(form.text)
  const normalizedLink = normalizeInput(form.link)

  if (normalizeInput(form.recruiterName).length > MAX_NAME_LENGTH) {
    return `ABN query must be ${MAX_NAME_LENGTH} characters or fewer.`
  }

  if (inputType.value === 'text' && !normalizedText) {
    return 'Please paste a recruiter message before analysis.'
  }

  if (inputType.value === 'text' && normalizedText.length > MAX_TEXT_LENGTH) {
    return `Message is too long. Keep it within ${MAX_TEXT_LENGTH} characters.`
  }

  if (inputType.value === 'link' && !normalizedLink) {
    return 'Please enter a link before analysis.'
  }

  if (inputType.value === 'link' && normalizedLink.length > MAX_LINK_LENGTH) {
    return `Link is too long. Keep it within ${MAX_LINK_LENGTH} characters.`
  }

  if (inputType.value === 'link') {
    let parsed
    try {
      parsed = new URL(normalizedLink)
    } catch {
      return 'Please enter a valid URL starting with https:// or http://.'
    }

    if (!['https:', 'http:'].includes(parsed.protocol)) {
      return 'Only http/https links are allowed.'
    }

    if (isLocalOrPrivateHostname(parsed.hostname)) {
      return 'Local or private network addresses are blocked for security.'
    }
  }

  if (inputType.value === 'pdf' && !form.pdfFile) {
    return 'Please select a PDF file before analysis.'
  }

  return ''
}

function submitForAnalysis() {
  if (props.isAnalyzing) return

  const validationError = validatePayload()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  errorMessage.value = ''
  const safeText = normalizeInput(form.text).slice(0, MAX_TEXT_LENGTH)
  const safeLink = normalizeInput(form.link).slice(0, MAX_LINK_LENGTH)
  const safeRecruiterName = normalizeInput(form.recruiterName).slice(0, MAX_NAME_LENGTH)

  const payload = {
    inputType: inputType.value,
    text: safeText,
    link: safeLink,
    pdfFile: form.pdfFile,
    recruiterName: safeRecruiterName,
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
    item.inputType === 'pdf' ? 'PDF records require re-uploading the file before analysis.' : ''
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

watch(
  () => form.text,
  (value) => {
    if (value.length > MAX_TEXT_LENGTH) {
      form.text = value.slice(0, MAX_TEXT_LENGTH)
    }
  },
)

watch(
  () => form.link,
  (value) => {
    if (value.length > MAX_LINK_LENGTH) {
      form.link = value.slice(0, MAX_LINK_LENGTH)
    }
  },
)

watch(
  () => form.recruiterName,
  (value) => {
    if (value.length > MAX_NAME_LENGTH) {
      form.recruiterName = value.slice(0, MAX_NAME_LENGTH)
    }

    if (abnLookupState.selectedAbn && normalizeInput(value) !== abnLookupState.selectedAbn) {
      abnLookupState.selectedAbn = ''
    }
  },
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
        <h2>Paste a message, link, or PDF</h2>
        <p class="head-summary">
          Choose Text, Link, or PDF. Then run a quick scan to get your risk result and next steps.
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
          role="tab"
          :aria-selected="inputType === 'text'"
          aria-controls="messageText"
          @click="inputType = 'text'"
        >
          Text
        </button>
        <button
          type="button"
          class="mode-button"
          :class="{ 'mode-button--active': inputType === 'link' }"
          role="tab"
          :aria-selected="inputType === 'link'"
          aria-controls="messageLink"
          @click="inputType = 'link'"
        >
          Link
        </button>
        <button
          type="button"
          class="mode-button"
          :class="{ 'mode-button--active': inputType === 'pdf' }"
          role="tab"
          :aria-selected="inputType === 'pdf'"
          aria-controls="pdfInput"
          @click="inputType = 'pdf'"
        >
          PDF
        </button>

        <div class="mode-field">
          <label class="mode-input-row" for="recruiterName">ABN lookup</label>
          <input
            id="recruiterName"
            :value="abnQuery"
            type="text"
            placeholder="Enter ABN (11 digits) or business name"
            maxlength="80"
            autocomplete="off"
            @input="emit('update:abn-query', $event.target.value)"
            @keydown.enter.prevent="emit('search-abn')"
          />
          <p class="field-helper">Search ABN registry, confirm a match, then continue analysis.</p>

          <div class="abn-actions">
            <button
              type="button"
              class="abn-search-btn"
              :disabled="abnLoading"
              @click="emit('search-abn')"
            >
              {{ abnLoading ? 'Searching ABN...' : 'Search ABN' }}
            </button>
            <button
              v-if="abnResults.length > 0 || abnError"
              type="button"
              class="abn-reset-btn"
              @click="emit('clear-abn')"
            >
              Clear
            </button>
          </div>

          <div>
            <!--
              <div class="abn-preview" aria-label="ABN preview controls">
                <p class="abn-preview__title">ABN preview</p>
              <div class="abn-preview__chips">
              <button
                v-for="mode in abnPreviewModes"
                :key="mode.tier"
                type="button"
                class="abn-preview-chip"
                :class="{ 'abn-preview-chip--active': abnLookupState.previewTier === mode.tier }"
                @click="previewAbnResult(mode.tier)"
              >
                {{ mode.label }}
              </button>
              </div>
              </div>
            -->
          </div>

          <div v-if="abnError" class="abn-error" role="alert">
            {{ abnError }}
          </div>

          <div v-if="abnResults.length" class="abn-results" aria-label="ABN search results">
            <p class="abn-results__title">ABN results</p>
            <article
              v-for="record in abnResults"
              :key="record.abn || `${record.name}-${record.matchScore}`"
              class="abn-result-card"
              :class="{ 'abn-result-card--selected': confirmedAbn?.abn === record.abn }"
            >
              <p class="abn-result-card__name">{{ record.name || 'Unknown business' }}</p>
              <p class="abn-result-card__meta">
                ABN: {{ record.abn || 'N/A' }} | Status: {{ record.status || 'Unknown' }}
                <span v-if="record.state"> | {{ record.state }}</span>
                <span v-if="record.postcode"> {{ record.postcode }}</span>
                <span v-if="record.matchScore !== undefined && record.matchScore !== null">
                  | Match {{ record.matchScore }}
                </span>
              </p>
              <button type="button" class="abn-confirm-btn" @click="emit('confirm-abn', record)">
                {{ confirmedAbn?.abn === record.abn ? 'Confirmed' : 'Confirm ABN' }}
              </button>
            </article>
          </div>

          <div v-if="confirmedAbn" class="abn-confirmed">
            <strong>Confirmed ABN for this session</strong>
            <div>{{ confirmedAbn.name }}</div>
            <div>ABN: {{ confirmedAbn.abn }}</div>
            <div>Status: {{ confirmedAbn.status }}</div>
          </div>
        </div>
      </aside>

      <div
        class="compose-pane"
        :class="{ 'compose-pane--scanning': isAnalyzing }"
        @keydown="handleComposeKeydown"
      >
        <div class="compose-head">
          <p>Evidence input</p>
          <p class="compose-head__mode">{{ inputLabel }}</p>
        </div>

        <div v-if="inputType === 'text'" class="input-card">
          <label for="messageText">Paste recruiter content</label>
          <textarea
            id="messageText"
            v-model="form.text"
            rows="6"
            placeholder="Paste the message you received"
            maxlength="6000"
            spellcheck="false"
          />
          <p class="textarea-counter">{{ form.text.length }}/6000 chars</p>
        </div>

        <div v-if="inputType === 'link'" class="input-card">
          <label for="messageLink">Paste website URL</label>
          <input
            id="messageLink"
            v-model="form.link"
            type="url"
            placeholder="https://example.com/job-offer"
            maxlength="2048"
            spellcheck="false"
          />
          <p class="field-helper">Allowed: public http/https URLs only.</p>
        </div>

        <div v-if="inputType === 'pdf'" class="input-card input-card--pdf">
          <label for="pdfInput">Upload PDF file</label>
          <input
            id="pdfInput"
            ref="pdfInputRef"
            type="file"
            accept=".pdf,application/pdf"
            @change="onFileChange"
          />
          <div v-if="form.pdfFile" class="pdf-actions">
            <p class="small-note">Selected: {{ form.pdfFile.name }}</p>
            <button type="button" class="pdf-clear-btn" @click="clearSelectedPdf">
              Remove selected PDF
            </button>
          </div>
          <p class="small-note">
            PDF text extraction tries the backend PyMuPDF endpoint first, then falls back to local
            reading.
          </p>
          <p class="small-note">Max size: 8MB. Encrypted PDFs may fail to parse.</p>
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
            <span class="quick-controls__toggle-text">{{
              isQuickControlsOpen ? 'Hide' : 'Show'
            }}</span>
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
              <button type="button" class="assist-btn assist-btn--muted" @click="clearCurrentInput">
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

        <p v-if="errorMessage" class="error-text" role="alert" aria-live="assertive">
          {{ errorMessage }}
        </p>

        <button
          type="button"
          class="analyze-btn"
          :disabled="isAnalyzing"
          @click="submitForAnalysis"
        >
          <span v-if="isAnalyzing" class="analyze-btn__loading">
            <span class="analyze-btn__spinner" aria-hidden="true"></span>
            <span>Scanning...</span>
          </span>
          <span v-else>Analyze now</span>
        </button>
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
  background: transparent;
  padding: 0;
}

.submission-head {
  align-items: center;
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(26, 26, 42, 0.06);
  display: grid;
  gap: 12px;
  grid-template-columns: 76px minmax(0, 1fr);
  margin-bottom: 14px;
  padding: 16px;
}

.head-inset {
  align-items: center;
  background: #fef2f2;
  border: 1px solid #e5e2dc;
  border-radius: 12px;
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
  color: #6b7280;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0 0 12px;
  text-transform: uppercase;
}

h2 {
  border-left: 3px solid #d0312d;
  color: #1f2d6b;
  font-size: clamp(1.8rem, 3.5vw, 2.6rem);
  font-weight: 800;
  line-height: 1.08;
  margin: 0 0 12px;
  padding-left: 12px;
}

h2::after {
  background: #d0312d;
  content: '';
  display: block;
  height: 3px;
  margin-top: 8px;
  width: 40px;
}

.head-summary {
  color: #6b7280;
  line-height: 1.55;
  margin: 0;
  max-width: 760px;
}

.editor-grid {
  align-items: start;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(220px, 0.56fr) minmax(0, 1.44fr);
}

.mode-rail {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(26, 26, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
}

.mode-hint {
  color: #6b7280;
  font-size: 0.76rem;
  line-height: 1.45;
  margin: 0 0 2px;
}

.mode-button {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  color: #1f2d6b;
  cursor: pointer;
  font-size: 0.96rem;
  font-weight: 600;
  min-height: 48px;
  padding: 12px 14px;
  text-align: left;
  transition: all 0.2s ease;
}

.mode-button--active {
  background: #1f2d6b;
  border-color: #1f2d6b;
  border-left: 3px solid #d0312d;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.14);
  color: #ffffff;
}

.mode-button:hover,
.mode-button:focus-visible {
  border-color: #d0312d;
}

.rail-assist-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 0;
}

.assist-btn {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  color: #1f2d6b;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 500;
  min-height: 40px;
  padding: 8px 12px;
}

.assist-btn:hover,
.assist-btn:focus-visible {
  border-color: #d0312d;
  color: #d0312d;
}

.assist-btn--muted {
  background: #fef2f2;
  border-color: #d0312d;
  color: #d0312d;
}

.mode-field {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  margin-top: 8px;
  padding: 16px;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.mode-field:hover {
  border-color: #1f2d6b;
  box-shadow: 0 10px 20px rgba(44, 62, 140, 0.16);
}

.field-helper {
  color: #6b7280;
  font-size: 0.76rem;
  margin: 8px 0 0;
}

.abn-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.abn-preview {
  margin-top: 10px;
}

.abn-preview__title {
  color: #6b7280;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin: 0 0 8px;
  text-transform: uppercase;
}

.abn-preview__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.abn-preview-chip {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 999px;
  color: #1f2d6b;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  min-height: 30px;
  padding: 4px 12px;
}

.abn-preview-chip:hover,
.abn-preview-chip:focus-visible {
  border-color: #d0312d;
  color: #d0312d;
}

.abn-preview-chip--active {
  background: #1f2d6b;
  border-color: #1f2d6b;
  color: #ffffff;
}

.abn-search-btn,
.abn-reset-btn,
.abn-confirm-btn {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  color: #1f2d6b;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  min-height: 34px;
  padding: 7px 12px;
}

.abn-search-btn {
  background: #1f2d6b;
  border-color: #1f2d6b;
  color: #ffffff;
}

.abn-search-btn:hover,
.abn-search-btn:focus-visible {
  background: #1f2d6b;
}

.abn-search-btn:disabled {
  cursor: not-allowed;
  opacity: 0.75;
}

.abn-reset-btn:hover,
.abn-reset-btn:focus-visible,
.abn-confirm-btn:hover,
.abn-confirm-btn:focus-visible {
  border-color: #d0312d;
  color: #d0312d;
}

.abn-note {
  color: #6b7280;
  font-size: 0.76rem;
  line-height: 1.45;
  margin: 8px 0 0;
}

.abn-note--error {
  color: #d0312d;
}

.abn-results {
  border-top: 1px solid #e5e2dc;
  display: grid;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
}

.abn-results__title {
  color: #6b7280;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin: 0;
  text-transform: uppercase;
}

.abn-result-card {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  display: grid;
  gap: 6px;
  padding: 10px;
}

.abn-result-card--selected {
  border-color: #1f2d6b;
  box-shadow: 0 0 0 2px rgba(31, 45, 107, 0.18);
}

.abn-result-card__name {
  color: #1f2d6b;
  font-size: 0.84rem;
  font-weight: 700;
  margin: 0;
}

.abn-result-card__meta {
  color: #6b7280;
  font-size: 0.76rem;
  margin: 0;
}

.recent-checks {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  margin-top: 8px;
  padding: 12px;
}

.quick-controls {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  margin-top: 2px;
  padding: 12px;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.quick-controls:hover {
  border-color: #1f2d6b;
  box-shadow: 0 8px 18px rgba(44, 62, 140, 0.14);
}

.quick-controls__toggle {
  align-items: center;
  background: transparent;
  border: 0;
  color: #1f2d6b;
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
  color: #d0312d;
  font-size: 0.72rem;
  font-weight: 600;
}

.quick-controls__panel {
  margin-top: 10px;
}

.recent-checks__title {
  color: #6b7280;
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.recent-check-btn {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  color: #1f2d6b;
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
  border-color: #d0312d;
}

.mode-input-row {
  color: #6b7280;
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
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(26, 26, 42, 0.06);
  display: grid;
  gap: 10px;
  min-width: 0;
  overflow: hidden;
  padding: 18px;
  position: relative;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.compose-pane--scanning::after {
  animation: scanSweepPanel 800ms linear both;
  background: linear-gradient(90deg, transparent, #d0312d, transparent);
  content: '';
  height: 2px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.compose-pane:hover {
  border-color: #1f2d6b;
  box-shadow: 0 12px 24px rgba(44, 62, 140, 0.18);
}

.compose-head {
  align-items: baseline;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.compose-head p {
  color: #6b7280;
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  margin: 0;
  text-transform: uppercase;
}

.compose-head__mode {
  color: #d0312d;
}

.input-card {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 150px;
  padding: 18px;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.input-card:hover {
  border-color: #1f2d6b;
  box-shadow: 0 8px 18px rgba(44, 62, 140, 0.14);
}

label {
  color: #6b7280;
  font-size: 0.86rem;
  font-weight: 500;
}

input,
textarea {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 6px;
  box-sizing: border-box;
  color: #1f2d6b;
  min-height: 44px;
  width: 100%;
  padding: 12px 14px;
}

textarea {
  border: 1px solid #e5e2dc;
  min-height: 170px;
}

input:hover,
textarea:hover,
input:focus,
textarea:focus {
  border-color: #d0312d;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.14);
  outline: none;
}

.textarea-counter {
  color: #6b7280;
  font-size: 12px;
  font-weight: 500;
  margin: 0;
  text-align: right;
}

.input-card--pdf {
  min-height: auto;
}

.small-note {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
}

.pdf-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.pdf-clear-btn {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  color: #1f2d6b;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  min-height: 32px;
  padding: 6px 10px;
}

.pdf-clear-btn:hover,
.pdf-clear-btn:focus-visible {
  border-color: #d0312d;
  color: #d0312d;
}

.privacy-note {
  background: #f9f7f4;
  border: 1px solid #e5e2dc;
  border-radius: 8px;
  color: #6b7280;
  font-size: 0.74rem;
  letter-spacing: 0.01em;
  line-height: 1.6;
  margin: 0;
  padding: 14px;
}

.error-text {
  background: rgba(220, 38, 38, 0.12);
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: 8px;
  color: #d0312d;
  margin: 0;
  padding: 20px;
}

.analyze-btn {
  background: #1f2d6b;
  border: 0;
  border-radius: 10px;
  color: #ffffff;
  cursor: pointer;
  display: inline-grid;
  font-size: 1rem;
  font-weight: 700;
  justify-content: center;
  align-items: center;
  height: 52px;
  width: 100%;
  padding: 14px 28px;
  text-transform: none;
  transition: background-color 0.2s ease;
}

.analyze-btn:hover,
.analyze-btn:focus-visible {
  background: #1f2d6b;
  box-shadow: 0 10px 20px rgba(44, 62, 140, 0.28);
  transform: translateY(-2px);
}

.analyze-btn:active {
  background: #1f2d6b;
}

.analyze-btn:disabled {
  cursor: not-allowed;
  opacity: 0.9;
}

.analyze-btn__loading {
  align-items: center;
  display: inline-flex;
  gap: 10px;
}

.analyze-btn__spinner {
  animation: spin 0.9s linear infinite;
  border: 2px solid rgba(255, 255, 255, 0.32);
  border-right-color: #ffffff;
  border-radius: 50%;
  display: inline-block;
  height: 16px;
  width: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes scanSweepPanel {
  from {
    transform: translateY(0);
  }

  to {
    transform: translateY(calc(100% - 2px));
  }
}

@media (max-width: 1080px) {
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

@media (max-width: 520px) {
  .mode-rail,
  .compose-pane {
    padding: 14px;
  }

  .mode-field,
  .input-card,
  .quick-controls,
  .privacy-note {
    padding: 12px;
  }

  .compose-head {
    align-items: flex-start;
    flex-direction: column;
    justify-content: flex-start;
  }

  .compose-head p {
    font-size: 0.72rem;
    letter-spacing: 0.06em;
  }

  .assist-btn,
  .abn-preview-chip {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
  }

  .abn-actions {
    flex-wrap: wrap;
  }

  .abn-search-btn,
  .abn-reset-btn,
  .abn-confirm-btn {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
  }

  .input-card textarea {
    min-height: 132px;
  }
}

@media (max-width: 420px) {
  .submission-head,
  .mode-rail,
  .compose-pane {
    border-radius: 8px;
    padding: 10px;
  }

  .head-inset {
    height: 60px;
    width: 60px;
  }

  .head-inset img {
    height: 30px;
    width: 30px;
  }

  .input-card,
  .quick-controls,
  .privacy-note,
  .mode-field {
    border-radius: 8px;
    padding: 10px;
  }

  .assist-btn,
  .abn-search-btn,
  .abn-reset-btn,
  .abn-confirm-btn {
    font-size: 0.72rem;
    min-height: 34px;
    padding: 6px 8px;
  }

  input,
  textarea {
    min-height: 40px;
    padding: 10px;
  }

  .input-card textarea {
    min-height: 116px;
  }

  .analyze-btn {
    font-size: 0.9rem;
    height: 46px;
    padding: 10px 14px;
  }
}
</style>
