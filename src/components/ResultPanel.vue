<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true,
  },
  requestSummary: {
    type: String,
    required: true,
  },
})

const riskPercent = computed(() => {
  const raw = Number(props.result?.riskScore ?? 0)
  return Math.max(0, Math.min(100, Math.round(raw)))
})

const riskColor = computed(() => {
  const tier = String(props.result?.riskTier ?? '').toLowerCase()
  if (tier === 'low') return 'rgb(6, 119, 59)'
  if (tier === 'medium') return 'rgb(245, 199, 44)'
  return 'rgb(188, 29, 12)'
})

const nextActions = [
  { label: 'View scam progression', href: '#result-section' },
  { label: 'Verify recruiter details', href: '#check-section' },
  { label: 'See trend insights', href: '#home' },
]
</script>

<template>
  <section class="result-panel" aria-label="Result panel">
    <div class="result-split">
      <aside class="score-sidebar" aria-label="Risk score block">
        <div class="score-chip" aria-hidden="true"></div>
        <p class="score-kicker">Risk score</p>
        <p class="score-value">{{ riskPercent }}<span>%</span></p>
        <p class="score-tier">{{ result.riskTier }} risk</p>

        <div class="score-gauge" role="progressbar" aria-label="Risk score gauge">
          <div
            class="score-gauge__fill"
            :style="{ width: `${riskPercent}%`, backgroundColor: riskColor }"
          ></div>
        </div>

        <div class="score-stats">
          <p><span>Type</span>{{ result.scamType }}</p>
          <p><span>Confidence</span>{{ (result.classificationConfidence * 100).toFixed(0) }}%</p>
          <p>
            <span>Threshold</span>{{ (result.classificationConfidenceThreshold * 100).toFixed(0) }}%
          </p>
        </div>
      </aside>

      <div class="result-main">
        <header class="result-head">
          <h2>Analysis Result</h2>
          <p>Core signals, scam stage factors, and the next actions for verification.</p>
        </header>

        <div class="content-row">
          <section class="content-card content-card--signal">
            <div class="card-head">
              <span class="card-inset card-inset--warn" aria-hidden="true">
                <img src="https://img.icons8.com/cotton/64/mission-of-a-company--v2.png" alt="" />
              </span>
              <h3>Why this was flagged</h3>
            </div>
            <div v-if="result.indicators.length" class="detail-list">
              <div v-for="item in result.indicators" :key="item" class="detail-row">
                <span class="detail-token detail-token--warn" aria-hidden="true"></span>
                <p>{{ item }}</p>
              </div>
            </div>
            <p v-else class="plain-block">No major indicator was triggered.</p>
          </section>

          <section class="content-card content-card--mid content-card--signal">
            <div class="card-head">
              <span class="card-inset card-inset--ok" aria-hidden="true">
                <img src="https://img.icons8.com/cotton/64/checklist--v1.png" alt="" />
              </span>
              <h3>Detected stage of scam</h3>
            </div>
            <div v-if="result.factors.length" class="detail-list">
              <div v-for="factor in result.factors" :key="factor.label" class="detail-row">
                <span class="detail-token detail-token--ok" aria-hidden="true"></span>
                <p>{{ factor.label }} ({{ factor.severity }}, +{{ factor.weight }})</p>
              </div>
            </div>
            <p v-else class="plain-block">No factor contributed to the score.</p>
          </section>
        </div>

        <section class="actions-block" aria-label="More options">
          <h3>Next actions</h3>
          <a
            v-for="action in nextActions"
            :key="action.label"
            class="action-card"
            :href="action.href"
          >
            <span>{{ action.label }}</span>
            <span class="action-arrow" aria-hidden="true"></span>
          </a>
        </section>

        <div class="content-row">
          <section class="content-card content-card--mid content-card--full">
            <div class="card-head">
              <span class="card-inset" aria-hidden="true">
                <img src="https://img.icons8.com/cotton/64/edit--v2.png" alt="" />
              </span>
              <h3>Submitted input snapshot</h3>
            </div>
            <p class="plain-block">{{ requestSummary }}</p>
          </section>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.result-panel {
  background: var(--ms-color-surface-page-start);
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

.action-card {
  align-items: center;
  background: var(--ms-color-surface-page-start);
  color: var(--ms-color-text-primary);
  display: flex;
  font-weight: 500;
  justify-content: space-between;
  margin-bottom: 12px;
  min-height: 58px;
  padding: 16px;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.action-card:hover,
.action-card:focus-visible {
  background: var(--ms-color-border-soft);
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

.content-card--full {
  grid-column: 1 / -1;
  min-height: 0;
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
}
</style>
