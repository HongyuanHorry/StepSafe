<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

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
  analysisSourceText: {
    type: String,
    default: '',
  },
})

const animatedScore = ref(0)
let scoreAnimationFrame = null
const isTierTransitioning = ref(false)
let tierTransitionTimer = null

const scoreArcPath = 'M8 114 A106 106 0 0 1 232 114'

const TIER = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
}

const RISK_TIER_CONFIG_BY_TIER = {
  [TIER.CRITICAL]: { label: 'Critical risk' },
  [TIER.HIGH]: { label: 'High risk' },
  [TIER.MEDIUM]: { label: 'Medium risk' },
  [TIER.LOW]: { label: 'Low risk' },
}

const SCORE_ARC_COLOR_BY_TIER = {
  [TIER.CRITICAL]: '#D0312D',
  [TIER.HIGH]: '#D0312D',
  [TIER.MEDIUM]: '#B45309',
  [TIER.LOW]: '#1F2D6B',
}

const SIDE_RISK_LABEL_BY_TIER = {
  [TIER.CRITICAL]: 'HIGH RISK',
  [TIER.HIGH]: 'HIGH RISK',
  [TIER.MEDIUM]: 'MEDIUM RISK',
  [TIER.LOW]: 'LOW RISK',
}

const SIDE_RISK_CLASS_BY_TIER = {
  [TIER.CRITICAL]: 'side-risk--critical',
  [TIER.HIGH]: 'side-risk--critical',
  [TIER.MEDIUM]: 'side-risk--medium',
  [TIER.LOW]: 'side-risk--low',
}

const CONCERN_LABEL_BY_TIER = {
  [TIER.CRITICAL]: 'Severe concern',
  [TIER.HIGH]: 'Severe concern',
  [TIER.MEDIUM]: 'Moderate concern',
  [TIER.LOW]: 'Low concern',
}

const RECOMMENDED_ACTION_BY_TIER = {
  [TIER.CRITICAL]:
    "Stop here, don't pay anything, and verify the business through official channels.",
  [TIER.HIGH]: "Stop here, don't pay anything, and verify the business through official channels.",
  [TIER.MEDIUM]: 'Pause now and verify this recruiter before you reply.',
  [TIER.LOW]: 'Continue carefully and keep verifying key details before sharing any data.',
}

const WARNING_DEFAULT_ADVICE =
  'This signal pattern appears in scam scripts and should be verified before replying.'

const WARNING_ADVICE_RULES = [
  {
    keywords: ['payment', 'deposit'],
    advice: 'Upfront payment requests are a common extraction tactic before contact disappears.',
  },
  {
    keywords: ['urgent', 'pressure'],
    advice: 'Scammers create artificial deadlines to block normal verification.',
  },
  {
    keywords: ['task-based'],
    advice: 'Task-reward loops can normalize repeated top-ups before withdrawal is blocked.',
  },
  {
    keywords: ['sensitive', 'identity', 'bank'],
    advice: 'Identity or banking requests can be used for account takeover and fraud.',
  },
  {
    keywords: ['unrealistic', 'easy income'],
    advice: 'Overstated low-effort earnings are often used to trigger fast decisions.',
  },
]

const WARNING_SEVERITY_META = {
  high: { badge: 'CRITICAL', color: '#D0312D' },
  medium: { badge: 'MEDIUM', color: '#B45309' },
  low: { badge: 'LOW', color: '#1F2D6B' },
}

function normalizeRiskTier(rawTier) {
  if (rawTier === TIER.CRITICAL) return TIER.CRITICAL
  if (rawTier === TIER.HIGH) return TIER.HIGH
  if (rawTier === TIER.MEDIUM) return TIER.MEDIUM
  return ''
}

function resolveRiskTierByScore(score) {
  if (score >= 80) return TIER.CRITICAL
  if (score >= 60) return TIER.HIGH
  if (score >= 40) return TIER.MEDIUM
  return TIER.LOW
}

function resolveWarningAdvice(normalizedLabel) {
  const matchedRule = WARNING_ADVICE_RULES.find((rule) =>
    rule.keywords.some((keyword) => normalizedLabel.includes(keyword)),
  )
  return matchedRule?.advice ?? WARNING_DEFAULT_ADVICE
}

function resolveWarningSeverityMeta(severity) {
  if (severity === 'high') return WARNING_SEVERITY_META.high
  if (severity === 'medium') return WARNING_SEVERITY_META.medium
  return WARNING_SEVERITY_META.low
}

const riskPercent = computed(() => {
  const raw = Number(props.result?.riskScore ?? 0)
  return Math.max(0, Math.min(100, Math.round(raw)))
})

const backendRiskTier = computed(() => {
  const rawTier = String(props.result?.riskTier ?? '')
    .trim()
    .toLowerCase()
  return normalizeRiskTier(rawTier) || resolveRiskTierByScore(riskPercent.value)
})

const riskTierConfig = computed(() => {
  return RISK_TIER_CONFIG_BY_TIER[backendRiskTier.value] ?? RISK_TIER_CONFIG_BY_TIER[TIER.LOW]
})

const scoreArcColor = computed(() => {
  return SCORE_ARC_COLOR_BY_TIER[backendRiskTier.value] ?? SCORE_ARC_COLOR_BY_TIER[TIER.LOW]
})

const isSuspicious = computed(() => {
  if (typeof props.result?.suspicious === 'boolean') {
    return props.result.suspicious
  }
  return riskPercent.value >= 40
})

const binaryStatusLabel = computed(() => (isSuspicious.value ? 'Suspicious' : 'Not suspicious'))
const scamType = computed(() => String(props.result?.scamType ?? 'unknown or unclear').trim())
const isScamTypeUnknown = computed(() => scamType.value.toLowerCase() === 'unknown or unclear')

const readableScamType = computed(() => {
  if (isScamTypeUnknown.value) return 'Unknown type'

  return scamType.value
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase())
})

const warningRows = computed(() => {
  const factors = Array.isArray(props.result?.factors) ? props.result.factors : []

  return factors.slice(0, 6).map((factor) => {
    const severity = String(factor?.severity ?? 'low').toLowerCase()
    const label = String(factor?.label ?? 'Risk signal')
    const normalizedLabel = label.toLowerCase()
    const severityMeta = resolveWarningSeverityMeta(severity)
    return {
      label,
      badge: severityMeta.badge,
      color: severityMeta.color,
      advice: resolveWarningAdvice(normalizedLabel),
    }
  })
})

const indicatorList = computed(() => {
  const indicators = Array.isArray(props.result?.indicators) ? props.result.indicators : []
  return indicators
    .slice(0, 6)
    .map((item) => String(item).trim())
    .filter(Boolean)
})

const warningSignalCount = computed(() =>
  Math.max(indicatorList.value.length, warningRows.value.length),
)

const heroHeadline = computed(() => {
  if (backendRiskTier.value === 'critical') return 'High chance this is a scam'
  if (backendRiskTier.value === 'high') return 'Many warning signs were found'
  if (backendRiskTier.value === 'medium') return 'Some signs look suspicious'
  return 'No strong scam signs detected'
})

const heroSubline = computed(() => {
  const signalUnit = warningSignalCount.value === 1 ? 'signal' : 'signals'
  const typeText = isScamTypeUnknown.value
    ? 'Scam type unclear'
    : `Scam type ${readableScamType.value}`
  return `${warningSignalCount.value} ${signalUnit} detected · ${typeText}`
})

const matchedPhraseRecords = computed(() => {
  const rows = Array.isArray(props.result?.matchedPhrases) ? props.result.matchedPhrases : []
  const unique = new Map()

  rows.forEach((row) => {
    const phrase = typeof row === 'string' ? row.trim() : String(row?.phrase ?? '').trim()
    if (!phrase) return

    const label = typeof row === 'string' ? '' : String(row?.label ?? '').trim()
    const key = phrase.toLowerCase()
    if (!unique.has(key)) {
      unique.set(key, { phrase, label })
    }
  })

  return Array.from(unique.values()).slice(0, 8)
})

const messageExcerpt = computed(() => {
  const excerpt = String(props.result?.analysisExcerpt ?? '').trim()
  if (excerpt) return excerpt

  const source = String(props.analysisSourceText ?? '').trim()
  if (!source) return ''

  if (source.length <= 420) return source
  return `${source.slice(0, 420)}...`
})

const highlightedExcerpt = computed(() => {
  const text = messageExcerpt.value
  if (!text) return ''

  const escapeHtml = (value) =>
    value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

  const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  const escaped = escapeHtml(text)
  if (!matchedPhraseRecords.value.length) return escaped

  const encoded = matchedPhraseRecords.value
    .map((item) => ({ phrase: escapeHtml(item.phrase), label: item.label }))
    .sort((a, b) => b.phrase.length - a.phrase.length)

  const labelByPhrase = new Map(encoded.map((item) => [item.phrase.toLowerCase(), item.label]))
  const pattern = new RegExp(
    `(${encoded.map((item) => escapeRegExp(item.phrase)).join('|')})`,
    'gi',
  )

  return escaped.replace(pattern, (match) => {
    const label = labelByPhrase.get(match.toLowerCase()) || ''
    if (!label) {
      return `<span class="flag-highlight">${match}</span>`
    }

    const encodedLabel = escapeHtml(label)
    return `<span class="flag-highlight" title="${encodedLabel}" aria-label="${encodedLabel}">${match}</span>`
  })
})

const reasonParagraphs = computed(() => {
  const explanation = Array.isArray(props.result?.explanation) ? props.result.explanation : []
  const clean = explanation.map((item) => String(item).trim()).filter(Boolean)
  if (clean.length > 1) return clean.slice(1, 3)
  if (clean.length === 1) return clean
  return ['Risk scoring is based on matched warning signals and pattern confidence.']
})

const sideRiskLabel = computed(() => {
  return SIDE_RISK_LABEL_BY_TIER[backendRiskTier.value] ?? SIDE_RISK_LABEL_BY_TIER[TIER.LOW]
})

const sideRiskClass = computed(() => {
  return SIDE_RISK_CLASS_BY_TIER[backendRiskTier.value] ?? SIDE_RISK_CLASS_BY_TIER[TIER.LOW]
})

const concernLabel = computed(() => {
  return CONCERN_LABEL_BY_TIER[backendRiskTier.value] ?? CONCERN_LABEL_BY_TIER[TIER.LOW]
})

const scoreBandLabel = computed(() => `${animatedScore.value} · ${concernLabel.value}`)

const recommendedAction = computed(() => {
  return RECOMMENDED_ACTION_BY_TIER[backendRiskTier.value] ?? RECOMMENDED_ACTION_BY_TIER[TIER.LOW]
})

const arcDashOffset = computed(() => {
  const normalized = Math.max(0, Math.min(100, animatedScore.value))
  return 100 - normalized
})

const scamTypeConfidence = computed(() => {
  const candidates = [
    props.result?.scamTypeConfidence,
    props.result?.classificationConfidence,
    props.result?.confidence,
  ]

  for (const value of candidates) {
    const numeric = Number(value)
    if (!Number.isFinite(numeric)) continue
    if (numeric > 0 && numeric <= 1) return clamp(Math.round(numeric * 100), 1, 100)
    if (numeric > 1 && numeric <= 100) return clamp(Math.round(numeric), 1, 100)
  }

  const base = isScamTypeUnknown.value ? 30 : 46
  const signalBoost = Math.min(26, warningSignalCount.value * 5)
  const scoreBoost = Math.round(riskPercent.value * 0.2)
  return clamp(base + signalBoost + scoreBoost, 15, 96)
})

const scamTypeConfidenceLine = computed(
  () => `${readableScamType.value} · ${scamTypeConfidence.value}% confidence`,
)

const scamTypeConfidenceHint = computed(
  () => 'Confidence is estimated from signal consistency and phrase overlap in this submission.',
)

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

function easeOut(progress) {
  return 1 - (1 - progress) ** 3
}

function animateRiskScore(target) {
  if (scoreAnimationFrame) {
    cancelAnimationFrame(scoreAnimationFrame)
  }

  const duration = 1000
  const start = performance.now()

  const run = (time) => {
    const progress = Math.min((time - start) / duration, 1)
    animatedScore.value = Math.round(target * easeOut(progress))

    if (progress < 1) {
      scoreAnimationFrame = requestAnimationFrame(run)
      return
    }

    scoreAnimationFrame = null
  }

  animatedScore.value = 0
  scoreAnimationFrame = requestAnimationFrame(run)
}

watch(
  riskPercent,
  (value) => {
    animateRiskScore(value)
  },
  { immediate: true },
)

watch(
  backendRiskTier,
  () => {
    isTierTransitioning.value = true
    if (tierTransitionTimer) {
      clearTimeout(tierTransitionTimer)
    }
    tierTransitionTimer = window.setTimeout(() => {
      isTierTransitioning.value = false
    }, 320)
  },
  { immediate: false },
)

onBeforeUnmount(() => {
  if (scoreAnimationFrame) {
    cancelAnimationFrame(scoreAnimationFrame)
  }

  if (tierTransitionTimer) {
    clearTimeout(tierTransitionTimer)
  }
})

const nextActions = [
  { label: 'Learn', href: '#learn-section' },
  { label: 'Insights', href: '#insights-section' },
  { label: 'Support', href: '#support-section' },
]
</script>

<template>
  <section
    class="result-panel"
    :class="{ 'result-panel--focus': highlightKeySignals }"
    :style="{
      '--arc-color': scoreArcColor,
    }"
    aria-label="Check alerts result"
  >
    <div class="result-layout">
      <div class="result-main">
        <header class="analysis-hero" :class="{ 'analysis-hero--transition': isTierTransitioning }">
          <div class="analysis-hero__meta">
            <span
              class="status-pill"
              :class="isSuspicious ? 'status-pill--alert' : 'status-pill--safe'"
            >
              {{ binaryStatusLabel }}
            </span>
            <span class="tier-pill" :class="`tier-pill--${backendRiskTier}`">{{
              riskTierConfig.label
            }}</span>
          </div>
          <h2 id="result-heading" class="analysis-hero__title" tabindex="-1">{{ heroHeadline }}</h2>
          <p class="analysis-hero__subtitle">{{ heroSubline }}</p>
        </header>

        <section class="reason-copy" aria-label="Risk explanation">
          <p v-for="(paragraph, index) in reasonParagraphs" :key="`reason-${index}`">
            {{ paragraph }}
          </p>
        </section>

        <section class="evidence-block" aria-label="Evidence excerpt and highlights">
          <p class="section-label">Message evidence</p>
          <blockquote class="evidence-shell">
            <p v-if="highlightedExcerpt" class="evidence-quote" v-html="highlightedExcerpt"></p>
            <p v-else class="evidence-quote">No excerpt available for this submission.</p>
          </blockquote>
        </section>

        <section
          v-if="warningRows.length"
          class="warning-grid-section"
          aria-label="Warning signs list"
        >
          <p class="section-label">Warning signs we spotted</p>
          <div class="warning-list">
            <article
              v-for="(item, index) in warningRows"
              :key="`${item.label}-${index}`"
              class="warning-item"
              :style="{
                '--warning-color': item.color,
                '--warning-delay': `${index * 100}ms`,
              }"
            >
              <div class="warning-item__head">
                <span class="warning-item__bar" aria-hidden="true"></span>
                <div class="warning-item__copy">
                  <h3 class="warning-item__title">{{ item.label }}</h3>
                  <p class="warning-item__desc">{{ item.advice }}</p>
                </div>
              </div>
            </article>
          </div>
        </section>

        <nav class="next-links" aria-label="What to do next">
          <a
            v-for="(action, index) in nextActions"
            :key="action.label"
            :href="action.href"
            class="next-links__item"
          >
            {{ action.label }}
            <span v-if="index < nextActions.length - 1" aria-hidden="true">|</span>
          </a>
        </nav>

        <details
          v-if="extractedTextPreview"
          class="extracted-preview"
          aria-label="Extracted text preview"
        >
          <summary>Extracted text preview</summary>
          <p>{{ extractedTextPreview }}</p>
        </details>
      </div>

      <aside class="result-side">
        <div class="side-panel" aria-label="Risk details sidebar">
          <section class="side-section side-section--score" aria-label="Risk score dashboard">
            <p class="side-block__title">Risk Score</p>

            <div class="score-arc-wrap">
              <svg class="score-arc" viewBox="0 0 240 132" role="presentation" aria-hidden="true">
                <path class="score-arc__track" :d="scoreArcPath" pathLength="100"></path>
                <path
                  class="score-arc__progress"
                  :d="scoreArcPath"
                  pathLength="100"
                  :stroke-dasharray="100"
                  :stroke-dashoffset="arcDashOffset"
                ></path>

                <g class="score-svg__text" transform="translate(120 98)">
                  <text class="score-svg__value" text-anchor="end">{{ animatedScore }}</text>
                  <text class="score-svg__unit" x="8" y="-2" text-anchor="start">/100</text>
                </g>
              </svg>
            </div>

            <p class="side-score__band">{{ scoreBandLabel }}</p>
            <span class="side-risk" :class="sideRiskClass">{{ sideRiskLabel }}</span>
          </section>

          <section class="side-section side-section--type" aria-label="Scam type confidence">
            <p class="side-block__title">Scam Type</p>
            <p class="scam-type-badge">{{ scamTypeConfidenceLine }}</p>
            <p class="scam-type-note">{{ scamTypeConfidenceHint }}</p>
          </section>

          <section class="side-section side-section--action" aria-label="Priority action">
            <p class="action-card__title">Priority Action</p>
            <p class="action-card__text">{{ recommendedAction }}</p>
          </section>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.result-panel {
  background: #f5f2ee;
  border: 1px solid #d5d1ca;
  border-top: 2px solid #d5d1ca;
  padding: 0 0 20px;
}

.result-panel--focus {
  outline: 2px solid rgba(31, 45, 107, 0.2);
  outline-offset: 6px;
}

.result-layout {
  display: grid;
  gap: 28px;
  grid-template-columns: minmax(0, 11fr) minmax(300px, 9fr);
  padding: 20px;
}

.result-main {
  min-width: 0;
}

.analysis-hero {
  background: #ede9e3;
  border-left: 4px solid #d0312d;
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  transition: transform 0.28s ease;
}

.analysis-hero--transition {
  transform: translateY(-2px);
}

.analysis-hero__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-pill,
.tier-pill {
  border-radius: 999px;
  display: inline-flex;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  padding: 4px 10px;
  text-transform: uppercase;
}

.status-pill--alert {
  background: #d0312d;
  color: #ffffff;
}

.status-pill--safe {
  background: #1f2d6b;
  color: #ffffff;
}

.tier-pill {
  background: #1f2d6b;
  color: #ffffff;
}

.tier-pill--critical,
.tier-pill--high {
  background: #d0312d;
}

.tier-pill--medium {
  background: #b45309;
}

.analysis-hero__title {
  color: #1a1a2a;
  font-size: clamp(30px, 3.8vw, 44px);
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.04;
  margin: 0;
}

.analysis-hero__subtitle {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.reason-copy {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.reason-copy p {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.72;
  margin: 0;
}

.section-label {
  color: #6b7280;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.evidence-block {
  margin-top: 18px;
}

.evidence-shell {
  background: #f9fafb;
  border-left: 3px solid #d1d5db;
  border-radius: 10px;
  margin: 0;
  padding: 14px 14px 14px 16px;
  position: relative;
}

.evidence-shell::before {
  color: #9ca3af;
  content: '"';
  font-size: 28px;
  left: 10px;
  line-height: 1;
  position: absolute;
  top: 8px;
}

.evidence-quote {
  color: #1a1a2a;
  font-size: 15px;
  line-height: 1.9;
  margin: 0;
  padding-left: 10px;
}

:deep(.flag-highlight) {
  background: #fef08a;
  border-radius: 3px;
  color: #111111;
  cursor: help;
  padding: 1px 4px;
}

.warning-grid-section {
  margin-top: 20px;
}

.warning-list {
  display: grid;
  gap: 0;
}

.warning-item {
  animation: warningItemIn 280ms ease both;
  animation-delay: var(--warning-delay);
  border-bottom: 1px solid #e5e7eb;
  padding: 14px 0;
}

.warning-item__head {
  align-items: flex-start;
  display: grid;
  gap: 12px;
  grid-template-columns: 3px minmax(0, 1fr) auto;
}

.warning-item__bar {
  background: var(--warning-color);
  border-radius: 999px;
  display: inline-flex;
  min-height: 46px;
}

.warning-item__copy {
  display: grid;
  gap: 7px;
}

.warning-item__title {
  color: #1a1a2a;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.4;
  margin: 0;
}

.warning-item__badge {
  background: transparent;
  color: var(--warning-color);
  display: inline-flex;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  line-height: 1.3;
  text-transform: uppercase;
  white-space: nowrap;
}

.warning-item__desc {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
}

.result-side {
  min-width: 0;
}

.side-panel {
  display: grid;
  gap: 0;
  min-height: 460px;
  position: sticky;
  top: 24px;
}

.side-section {
  background: transparent;
  border: 0;
  border-radius: 0;
  padding: 0;
}

.side-block__title {
  color: #6b7280;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.side-section--score {
  border-bottom: 1px solid #e5e7eb;
  padding: 0 0 16px;
  text-align: center;
}

.score-arc-wrap {
  margin-top: 2px;
}

.score-arc {
  display: block;
  margin: 0 auto;
  max-width: 100%;
  width: 100%;
}

.score-arc__track {
  fill: none;
  stroke: #d1d5db;
  stroke-linecap: round;
  stroke-width: 6;
}

.score-arc__progress {
  fill: none;
  stroke: var(--arc-color);
  stroke-linecap: round;
  stroke-width: 6;
  transition:
    stroke-dashoffset 1s ease,
    stroke 0.2s ease;
}

.score-svg__text {
  fill: var(--arc-color);
}

.score-svg__value {
  font-size: 56px;
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1;
  paint-order: stroke;
  stroke: transparent;
}

.score-svg__unit {
  fill: #6b7280;
  font-size: 15px;
  font-weight: 600;
  line-height: 1;
}

.side-score__band {
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
  margin: -6px 0 0;
}

.side-risk {
  border-radius: 999px;
  color: #ffffff;
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  justify-content: center;
  letter-spacing: 0.09em;
  margin: 10px auto 0;
  min-height: 34px;
  min-width: 170px;
  padding: 8px 14px;
  text-transform: uppercase;
}

.side-risk--critical {
  background: #d0312d;
}

.side-risk--medium {
  background: #b45309;
}

.side-risk--low {
  background: #1f2d6b;
}

.side-section--type {
  padding: 16px 0;
}

.scam-type-badge {
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  color: #1a1a2a;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  margin: 0;
  padding: 6px 10px;
}

.scam-type-note {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.6;
  margin: 8px 0 0;
}

.side-section--action {
  background: #d0312d;
  border: 0;
  border-radius: 0;
  margin: 0;
  padding: 16px 14px;
}

.action-card__title {
  color: rgba(255, 255, 255, 0.85);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.action-card__text {
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.65;
  margin: 0;
}

.next-links {
  border-top: 1px solid #e3dfd8;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 18px 0 0;
  padding-top: 12px;
}

.next-links__item {
  color: #1f2d6b;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
}

.next-links__item:hover,
.next-links__item:focus-visible {
  text-decoration: underline;
}

.next-links__item span {
  color: #6b7280;
  margin-left: 8px;
}

.extracted-preview {
  border-top: 1px solid #e5e2dc;
  margin-top: 16px;
  padding-top: 12px;
}

.extracted-preview summary {
  color: #1a1a2a;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.extracted-preview p {
  color: #6b7280;
  line-height: 1.6;
  margin: 10px 0 0;
  white-space: pre-wrap;
}

@keyframes warningItemIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1080px) {
  .result-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    min-height: auto;
    position: static;
  }
}

@media (max-width: 760px) {
  .score-svg__value {
    font-size: 50px;
  }

  .warning-item__head {
    grid-template-columns: 3px minmax(0, 1fr);
  }

  .warning-item__badge {
    grid-column: 2;
    margin-top: -2px;
  }
}
</style>
