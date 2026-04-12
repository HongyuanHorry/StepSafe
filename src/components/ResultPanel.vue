<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true,
  },
  highlightKeySignals: {
    type: Boolean,
    default: false,
  },
  extractedTextPreview: {
    type: String,
    default: '',
  },
})

const riskPercent = computed(() => {
  const raw = Number(props.result?.riskScore ?? 0)
  return Math.max(0, Math.min(100, Math.round(raw)))
})

const normalizedTier = computed(() => {
  const score = riskPercent.value
  if (score >= 80) return 'critical'
  if (score >= 60) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
})

const riskColor = computed(() => {
  if (normalizedTier.value === 'low') return 'rgb(6, 119, 59)'
  if (normalizedTier.value === 'medium') return 'rgb(245, 199, 44)'
  return 'rgb(188, 29, 12)'
})

const riskTierLabel = computed(() => {
  if (normalizedTier.value === 'critical') return 'Critical'
  if (normalizedTier.value === 'high') return 'High'
  if (normalizedTier.value === 'medium') return 'Medium'
  return 'Low'
})

const binaryStatusLabel = computed(() => {
  return props.result?.suspicious ? 'Suspicious' : 'Not suspicious'
})

const binaryStatusNote = computed(() => {
  if (props.result?.suspicious) {
    return 'This message has clear scam warning signs.'
  }
  return 'This message has no clear scam warning signs right now.'
})

const evidenceStrength = computed(() => {
  const factors = Array.isArray(props.result?.factors) ? props.result.factors : []
  const indicators = Array.isArray(props.result?.indicators) ? props.result.indicators : []

  const highCount = factors.filter((factor) => String(factor?.severity).toLowerCase() === 'high').length
  const mediumCount = factors.filter(
    (factor) => String(factor?.severity).toLowerCase() === 'medium',
  ).length

  if (!highCount && !mediumCount && indicators.length) {
    return `${indicators.length} medium signal${indicators.length > 1 ? 's' : ''}`
  }

  return `${highCount} high / ${mediumCount} medium signals`
})

const recommendedActionLevel = computed(() => {
  if (normalizedTier.value === 'critical') return 'Stop payment immediately and verify identity now'
  if (normalizedTier.value === 'high') return 'Stop payment and verify identity before any next step'
  if (normalizedTier.value === 'medium') return 'Verify identity before any transfer'
  return 'Proceed carefully and continue monitoring'
})

const analysisIntroLine = computed(() => {
  return `${riskTierLabel.value} risk (${riskPercent.value}/100). ${recommendedActionLevel.value}.`
})

const confidencePercent = computed(() => {
  return Number(props.result?.classificationConfidence ?? 0) * 100
})

const thresholdPercent = computed(() => {
  return Number(props.result?.classificationConfidenceThreshold ?? 0) * 100
})

function severityLabel(severity) {
  const level = String(severity ?? '').toLowerCase()
  if (level === 'high') return 'Strong warning sign'
  if (level === 'medium') return 'Moderate warning sign'
  if (level === 'low') return 'Minor warning sign'
  return 'Warning sign'
}

const nextActions = [
  { label: 'View scam progression', href: '#learn-section' },
  { label: 'Verify recruiter details', href: '#recruiterName' },
  { label: 'See trend insights', href: '#insights-section' },
]
</script>

<template>
  <section
    class="result-panel"
    :class="{ 'result-panel--focus': highlightKeySignals }"
    aria-label="Result panel"
  >
    <div class="result-split">
      <aside class="score-sidebar" aria-label="Risk score block">
        <div class="score-chip" aria-hidden="true"></div>
        <p class="status-kicker">Status</p>
        <p class="status-value" role="status">{{ binaryStatusLabel }}</p>
        <p class="status-note">{{ binaryStatusNote }}</p>

        <p class="score-kicker">Risk score</p>
        <p class="score-value">{{ riskPercent }}<span>%</span></p>
        <p class="score-tier">{{ riskTierLabel }} risk, {{ riskPercent }}/100</p>

        <div
          class="score-gauge"
          role="progressbar"
          aria-label="Risk score gauge"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-valuenow="riskPercent"
        >
          <div
            class="score-gauge__fill"
            :style="{ width: `${riskPercent}%`, backgroundColor: riskColor }"
          ></div>
        </div>

        <div class="score-stats">
          <p><span>Scam type</span>{{ result.scamType }}</p>
          <p><span>Warning signs found</span>{{ evidenceStrength }}</p>
          <p><span>What to do now</span>{{ recommendedActionLevel }}</p>
        </div>

        <p class="score-tech">
          How sure this result is: {{ confidencePercent.toFixed(0) }}%.
        </p>
      </aside>

      <div class="result-main">
        <header class="result-head">
          <h2 id="result-heading" tabindex="-1">Analysis Result</h2>
          <p role="status">{{ analysisIntroLine }}</p>
        </header>

        <div class="content-row">
          <section class="content-card content-card--signal">
            <div class="card-head">
              <span class="card-inset card-inset--warn" aria-hidden="true">
                <img src="https://img.icons8.com/cotton/64/mission-of-a-company--v2.png" alt="" />
              </span>
              <h3>Why this looks risky</h3>
            </div>
            <div v-if="result.indicators.length" class="detail-list">
              <div
                v-for="(item, index) in result.indicators"
                :key="item"
                class="detail-row"
                :class="{ 'detail-row--highlight': highlightKeySignals && index < 2 }"
              >
                <span class="detail-token detail-token--warn" aria-hidden="true"></span>
                <p>{{ item }}</p>
              </div>
            </div>
            <p v-else class="plain-block">No major warning signs were found.</p>
          </section>

          <section class="content-card content-card--mid content-card--signal">
            <div class="card-head">
              <span class="card-inset card-inset--ok" aria-hidden="true">
                <img src="https://img.icons8.com/cotton/64/checklist--v1.png" alt="" />
              </span>
              <h3>Warning signs by strength</h3>
            </div>
            <div v-if="result.factors.length" class="detail-list">
              <div
                v-for="(factor, index) in result.factors"
                :key="factor.label"
                class="detail-row"
                :class="{ 'detail-row--highlight': highlightKeySignals && index < 2 }"
              >
                <span class="detail-token detail-token--ok" aria-hidden="true"></span>
                <p>{{ factor.label }} · {{ severityLabel(factor.severity) }}</p>
              </div>
            </div>
            <p v-else class="plain-block">No warning sign affected the score.</p>
          </section>
        </div>

        <section class="actions-block" aria-label="More options">
          <h3>Next actions</h3>
          <div class="actions-grid">
            <a
              v-for="action in nextActions"
              :key="action.label"
              class="action-card"
              :href="action.href"
            >
              <span>{{ action.label }}</span>
              <span class="action-arrow" aria-hidden="true"></span>
            </a>
          </div>
        </section>

        <details v-if="extractedTextPreview" class="extracted-preview" aria-label="Extracted text preview">
          <summary>Extracted text preview</summary>
          <p>{{ extractedTextPreview }}</p>
        </details>
      </div>
    </div>
  </section>
</template>

<style scoped>
.result-panel {
  background: var(--ms-color-surface-page-start);
}

.result-panel--focus {
  box-shadow: inset 0 0 0 2px rgba(15, 82, 186, 0.35);
}

.result-split {
  display: grid;
  grid-template-columns: minmax(260px, 30%) minmax(0, 70%);
  min-height: 100%;
}

.score-sidebar {
  background: rgb(26, 25, 24);
  color: rgb(255, 255, 255);
  padding: 56px 48px;
}

.score-chip {
  background: var(--ms-color-brand);
  height: 18px;
  margin-bottom: 16px;
  width: 52px;
}

.score-kicker {
  color: rgb(255, 255, 255);
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  margin: 0 0 14px;
  text-transform: uppercase;
}

.score-value {
  color: rgb(255, 255, 255);
  font-size: clamp(4rem, 8vw, 7rem);
  font-weight: 300;
  line-height: 0.9;
  margin: 0 0 14px;
}

.score-value span {
  font-size: 1.45rem;
}

.score-tier {
  color: rgb(255, 255, 255);
  font-size: 1.22rem;
  margin: 0 0 22px;
}

.score-gauge {
  background: rgba(255, 255, 255, 0.2);
  height: 16px;
  margin-bottom: 20px;
  width: 100%;
}

.score-gauge__fill {
  height: 100%;
  transition: width 0.3s ease;
}

.score-stats {
  display: grid;
  gap: 14px;
}

.score-stats p {
  margin: 0;
}

.score-stats span {
  color: rgba(255, 255, 255, 0.74);
  display: block;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  margin-bottom: 2px;
  text-transform: uppercase;
}

.score-tech {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.78rem;
  line-height: 1.5;
  margin: 14px 0 0;
}

.result-main {
  background: var(--ms-color-surface-page-start);
  padding: 56px 48px;
}

.result-head {
  margin-bottom: 30px;
}

h2 {
  font-size: clamp(2.2rem, 4vw, 3.2rem);
  font-weight: 300;
  margin: 0 0 20px;
}

.result-head p {
  color: var(--ms-color-text-secondary);
  margin: 0;
}

h3 {
  font-size: 1.2rem;
  font-weight: 400;
  margin: 0;
}

.content-row {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr 1fr;
  margin-bottom: 16px;
}

.content-card {
  background: var(--ms-color-surface-page-start);
  min-height: 220px;
  padding: 24px;
}

.content-card--mid {
  background: var(--ms-color-surface-page-mid);
}

.content-card--signal .card-head h3 {
  font-size: 1.34rem;
  font-weight: 500;
}

.content-card--signal .detail-row p {
  color: var(--ms-color-text-secondary);
  font-size: 0.92rem;
  line-height: 1.45;
}

.card-head {
  align-items: center;
  display: grid;
  gap: 14px;
  grid-template-columns: 56px minmax(0, 1fr);
  margin-bottom: 12px;
}

.card-inset {
  align-items: center;
  background: var(--ms-color-surface-page-mid);
  display: inline-flex;
  height: 56px;
  justify-content: center;
  width: 56px;
}

.card-inset img {
  height: 32px;
  width: 32px;
}

.card-inset--warn {
  background: var(--ms-color-danger-soft);
}

.card-inset--ok {
  background: var(--ms-color-success-soft);
}

.card-inset--info {
  background: var(--ms-color-surface-page-mid);
}

.detail-list {
  display: grid;
  gap: 6px;
}

.detail-row {
  align-items: flex-start;
  background: rgba(255, 255, 255, 0.7);
  display: grid;
  gap: 8px;
  grid-template-columns: 12px minmax(0, 1fr);
  min-height: 0;
  padding: 10px 10px;
}

.detail-row--highlight {
  background: rgba(255, 239, 192, 0.8);
  box-shadow: inset 0 0 0 1px rgba(188, 29, 12, 0.25);
  animation: signalPulse 1.2s ease-in-out 2;
}

.detail-row p {
  line-height: 1.34;
  margin: 0;
}

.detail-token {
  background: var(--ms-color-brand);
  display: inline-block;
  height: 14px;
  margin-top: 2px;
  width: 14px;
}

.detail-token--warn {
  background: var(--ms-color-danger);
  height: 9px;
  margin-top: 5px;
  width: 9px;
}

.detail-token--ok {
  background: var(--ms-color-success);
  height: 9px;
  margin-top: 5px;
  width: 9px;
}

.actions-block {
  background: var(--ms-color-surface-page-mid);
  margin: 0 0 16px;
  padding: 24px;
}

.actions-block h3 {
  margin-bottom: 14px;
}

.actions-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: 1fr 1fr;
}

.action-card {
  align-items: center;
  background: var(--ms-color-surface-page-start);
  color: var(--ms-color-text-primary);
  display: flex;
  font-weight: 500;
  justify-content: space-between;
  min-height: 58px;
  padding: 16px;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.action-card:hover,
.action-card:focus-visible {
  background: var(--ms-color-border-soft);
}

.extracted-preview {
  background: var(--ms-color-surface-subtle);
  margin: 0 0 16px;
  padding: 14px 16px;
}

.extracted-preview summary {
  color: var(--ms-color-text-primary);
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.extracted-preview p {
  color: var(--ms-color-text-secondary);
  font-size: 0.88rem;
  line-height: 1.5;
  margin: 10px 0 0;
  white-space: pre-wrap;
}

.action-arrow {
  background: var(--ms-color-surface-page-mid);
  display: inline-flex;
  height: 26px;
  position: relative;
  width: 26px;
}

.action-arrow::after {
  border-right: 2px solid var(--ms-color-brand-hover);
  border-top: 2px solid var(--ms-color-brand-hover);
  content: '';
  height: 8px;
  left: 7px;
  position: absolute;
  top: 8px;
  transform: rotate(45deg);
  width: 8px;
}

.plain-block {
  background: rgba(255, 255, 255, 0.7);
  line-height: 1.38;
  margin: 0;
  min-height: 88px;
  padding: 12px;
}

@keyframes signalPulse {
  0% {
    box-shadow: inset 0 0 0 1px rgba(188, 29, 12, 0.25);
  }

  50% {
    box-shadow: inset 0 0 0 2px rgba(188, 29, 12, 0.45);
  }

  100% {
    box-shadow: inset 0 0 0 1px rgba(188, 29, 12, 0.25);
  }
}

@media (max-width: 980px) {
  .result-split {
    grid-template-columns: 1fr;
  }

  .score-sidebar,
  .result-main {
    padding: 40px 24px;
  }

  .content-row {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
