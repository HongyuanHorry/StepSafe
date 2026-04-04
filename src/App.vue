<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ResultPanel from './components/ResultPanel.vue'
import SubmissionPanel from './components/SubmissionPanel.vue'
import { analyzeTextContent, extractTextFromSubmission } from './services/scamAnalysisEngine'

const isAnalyzing = ref(false)
const requestSummary = ref('')
const result = ref(null)
const submissionQuickMode = ref('text')
const isMenuOpen = ref(false)

const topActions = [
  { label: 'Suspicious message', mode: 'text', action: 'preview-high' },
  { label: 'Upload job PDF', mode: 'pdf', action: 'open-check' },
  { label: 'Verify recruiter', mode: 'link', action: 'open-check' },
]

const primarySections = [
  { label: 'Insights', id: 'insights-section' },
  { label: 'Learn', id: 'learn-section' },
  { label: 'Support', id: 'support-section' },
]

const quickTips = [
  {
    title: 'Task scam warning signs',
    summary: 'Fast red flags for step-by-step simple task scams and fake commission loops.',
    href: 'https://www.scamwatch.gov.au/types-of-scams/jobs-and-employment-scams',
    source: 'Scamwatch',
    icon: 'https://img.icons8.com/cotton/64/idea.png',
  },
  {
    title: 'How to spot fake remote jobs',
    summary: 'FTC guidance for fake checks, upfront fee traps, and high-pay low-effort bait.',
    href: 'https://consumer.ftc.gov/articles/job-scams',
    source: 'FTC Consumer Advice',
    icon: 'https://img.icons8.com/cotton/64/idea.png',
  },
]

const learningCards = [
  {
    title: "Employment scams are on the rise. Here's what to look out for",
    summary: 'Coverage of warning signs and recent scam growth trends in Australia.',
    href: 'https://www.sbs.com.au/news/article/employment-scams-are-on-the-rise-heres-what-to-look-out-for/2xgyuapu0',
    source: 'SBS News',
    icon: 'https://img.icons8.com/cotton/64/literature--v2.png',
  },
  {
    title: "'An elaborate ruse': The scam that's surging in Australia",
    summary: 'Explainer on task scam mechanics and how to protect yourself from losses.',
    href: 'https://www.sbs.com.au/news/article/an-elaborate-ruse-the-scam-thats-surging-in-australia-and-how-to-protect-yourself/fxvbsllo7',
    source: 'SBS News',
    icon: 'https://img.icons8.com/cotton/64/literature--v2.png',
  },
  {
    title: 'Sam thought he had a marketing job — it was actually a task-based scam',
    summary: 'Case study with concrete red flags from a real task-based scam timeline.',
    href: 'https://www.abc.net.au/news/2025-07-26/employment-scams-work-marketing-messages/105089062',
    source: 'ABC News',
    icon: 'https://img.icons8.com/cotton/64/literature--v2.png',
  },
]

const footerFriendLinks = [
  {
    label: 'Scamwatch (Australian Government)',
    href: 'https://www.scamwatch.gov.au/',
    icon: 'https://www.google.com/s2/favicons?domain=scamwatch.gov.au&sz=64',
  },
  {
    label: 'Australian Competition and Consumer Commission (ACCC)',
    href: 'https://www.accc.gov.au/',
    icon: 'https://www.google.com/s2/favicons?domain=accc.gov.au&sz=64',
  },
  {
    label: 'ASIC MoneySmart (Australia)',
    href: 'https://moneysmart.gov.au/',
    icon: 'https://www.google.com/s2/favicons?domain=moneysmart.gov.au&sz=64',
  },
  {
    label: 'Federal Trade Commission (FTC)',
    href: 'https://consumer.ftc.gov/',
    icon: 'https://www.google.com/s2/favicons?domain=consumer.ftc.gov&sz=64',
  },
]

const footerOfficialLinks = [
  {
    label: 'Scamwatch: Jobs and employment scams',
    href: 'https://www.scamwatch.gov.au/types-of-scams/jobs-and-employment-scams',
    icon: 'https://www.google.com/s2/favicons?domain=scamwatch.gov.au&sz=64',
  },
  {
    label: 'Scamwatch: Report a scam',
    href: 'https://www.scamwatch.gov.au/report-a-scam',
    icon: 'https://www.google.com/s2/favicons?domain=scamwatch.gov.au&sz=64',
  },
  {
    label: 'FTC: Job scams guide',
    href: 'https://consumer.ftc.gov/articles/job-scams',
    icon: 'https://www.google.com/s2/favicons?domain=consumer.ftc.gov&sz=64',
  },
]

const previewModes = [
  { label: 'Low Risk Preview', tier: 'low' },
  { label: 'Medium Risk Preview', tier: 'medium' },
  { label: 'High Risk Preview', tier: 'high' },
]

const showResult = computed(() => result.value !== null)

let revealObserver = null

function scrollToSection(sectionId) {
  const node = document.getElementById(sectionId)
  if (!node) return

  const header = document.querySelector('.top-strip')
  const headerHeight = header instanceof HTMLElement ? header.offsetHeight : 0
  const top = node.getBoundingClientRect().top + window.scrollY - headerHeight - 8

  window.scrollTo({ top, behavior: 'smooth' })
}

function navigateToSection(sectionId) {
  isMenuOpen.value = false
  scrollToSection(sectionId)
}

function buildPreviewResult(tier) {
  if (tier === 'low') {
    return {
      riskScore: 18,
      riskTier: 'Low',
      scamType: 'Low-confidence anomaly',
      indicators: ['Language is mostly normal with only a weak urgency cue.'],
      factors: [{ label: 'Minor urgency wording', severity: 'low', weight: 8 }],
      explanation: ['This sample demonstrates a low risk outcome for UI preview only.'],
      classificationConfidence: 0.58,
      classificationConfidenceThreshold: 0.55,
    }
  }

  if (tier === 'medium') {
    return {
      riskScore: 57,
      riskTier: 'Medium',
      scamType: 'Task commission escalation',
      indicators: [
        'Promises high return for simple repetitive tasks.',
        'Pushes users to keep topping up before withdrawal.',
      ],
      factors: [
        { label: 'High-pay low-effort framing', severity: 'medium', weight: 18 },
        { label: 'Top-up dependency', severity: 'medium', weight: 15 },
      ],
      explanation: ['This sample demonstrates a medium risk outcome for UI preview only.'],
      classificationConfidence: 0.74,
      classificationConfidenceThreshold: 0.6,
    }
  }

  return {
    riskScore: 88,
    riskTier: 'High',
    scamType: 'Step-by-step simple tasks scam',
    indicators: [
      'Demands upfront deposit before any payout.',
      'Uses urgency and countdown language to force immediate payment.',
      'Claims guaranteed commission for repeated clicks and transfers.',
    ],
    factors: [
      { label: 'Advance-fee demand', severity: 'high', weight: 28 },
      { label: 'Urgency pressure', severity: 'high', weight: 22 },
      { label: 'Unverifiable recruiter identity', severity: 'high', weight: 18 },
    ],
    explanation: ['This sample demonstrates a high risk outcome for UI preview only.'],
    classificationConfidence: 0.91,
    classificationConfidenceThreshold: 0.65,
  }
}

function previewRiskState(tier) {
  result.value = buildPreviewResult(tier)
  requestSummary.value =
    'Preview mode: simulated suspicious employment and task message for risk-state visualization.'

  nextTick(() => {
    scrollToSection('result-section')
  })
}

function clearPreviewState() {
  result.value = null
  requestSummary.value = ''
}

function triggerTopAction(action) {
  isMenuOpen.value = false
  submissionQuickMode.value = action.mode
  scrollToSection('check-section')

  if (action.action === 'preview-high') {
    previewRiskState('high')
  }
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function initRevealObserver() {
  if (revealObserver) {
    revealObserver.disconnect()
  }

  const candidates = Array.from(document.querySelectorAll('.reveal-on-scroll'))

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          revealObserver?.unobserve(entry.target)
        }
      })
    },
    {
      threshold: 0.2,
      rootMargin: '0px 0px -8% 0px',
    },
  )

  candidates.forEach((node) => revealObserver?.observe(node))
}

onMounted(() => {
  initRevealObserver()
})

watch(showResult, async (visible) => {
  if (!visible) return
  await nextTick()
  initRevealObserver()
})

onBeforeUnmount(() => {
  if (revealObserver) {
    revealObserver.disconnect()
  }
})

async function handleSubmission(payload) {
  isAnalyzing.value = true
  result.value = null

  const textContent = await extractTextFromSubmission(payload)
  requestSummary.value = textContent.slice(0, 1200)

  setTimeout(() => {
    result.value = analyzeTextContent(textContent)
    isAnalyzing.value = false
  }, 250)
}
</script>

<template>
  <main id="home" class="page-shell">
    <header class="top-strip" aria-label="Top action bar">
      <div class="container-shell top-strip__inner">
        <a class="brand-home" href="#home-section" aria-label="Go to Home section">
          <img src="/icons/stepsafe_logo.svg" alt="StepSafe" />
          <span>StepSafe</span>
        </a>

        <button
          type="button"
          class="top-hamburger"
          aria-label="Toggle navigation"
          :aria-expanded="isMenuOpen"
          @click="toggleMenu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <nav
          class="top-menu"
          :class="{ 'top-menu--open': isMenuOpen }"
          aria-label="Site navigation"
        >
          <div class="top-menu__inner">
            <button type="button" class="menu-link" @click="navigateToSection('home-section')">
              Home
            </button>

            <div class="menu-group">
              <button
                type="button"
                class="menu-link menu-link--check"
                @click="navigateToSection('check-section')"
              >
                Check Scam
              </button>
              <div class="menu-subactions" role="group" aria-label="Check scam quick actions">
                <button
                  v-for="action in topActions"
                  :key="action.label"
                  type="button"
                  class="menu-sublink"
                  @click="triggerTopAction(action)"
                >
                  {{ action.label }}
                </button>
              </div>
            </div>

            <button
              v-for="section in primarySections"
              :key="section.id"
              type="button"
              class="menu-link"
              @click="navigateToSection(section.id)"
            >
              {{ section.label }}
            </button>
          </div>
        </nav>
      </div>
    </header>

    <div class="flow-wrapper">
      <section
        id="home-section"
        class="hero-band layer-start reveal-on-scroll"
        aria-label="Hero section"
      >
        <div class="container-shell hero-band__inner">
          <div class="hero-copy">
            <p class="hero-eyebrow">StepSafe Employment Scam Alert</p>
            <h1>Stay safe from fake jobs and task scams</h1>
            <p class="hero-summary copy-block">
              Submit a suspicious message, PDF posting, or recruitment link. The prototype returns a
              risk tier, confidence, indicators, and plain-language reason.
            </p>
            <a class="cta-primary" href="#check-section">Check scam now</a>
          </div>
          <div class="hero-art" aria-hidden="true">
            <img src="/icons/EmploymentScamWarningPic.png" alt="" />
          </div>
        </div>
      </section>

      <section class="info-grid layer-mid" aria-label="Guidance blocks">
        <div class="container-shell info-grid__inner">
          <article class="info-block reveal-on-scroll">
            <h2>Quick Tips</h2>
            <p class="info-summary">Fast scam checks for step-by-step simple tasks fraud.</p>
            <div class="info-layout">
              <div class="info-rows">
                <a
                  v-for="item in quickTips"
                  :key="item.href"
                  class="resource-row"
                  :href="item.href"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span class="resource-inset" aria-hidden="true">
                    <img :src="item.icon" alt="" />
                  </span>
                  <div class="resource-main">
                    <p class="resource-title">{{ item.title }}</p>
                    <p class="resource-copy">{{ item.summary }}</p>
                    <span class="resource-source">{{ item.source }}</span>
                  </div>
                </a>
              </div>
            </div>
          </article>

          <article class="info-block reveal-on-scroll">
            <h2>Related News</h2>
            <p class="info-summary">
              Recent news coverage and case reports on employment and task scams.
            </p>
            <div class="info-layout">
              <div class="info-rows">
                <a
                  v-for="item in learningCards"
                  :key="item.href"
                  class="resource-row"
                  :href="item.href"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span class="resource-inset resource-inset--learn" aria-hidden="true">
                    <img :src="item.icon" alt="" />
                  </span>
                  <div class="resource-main">
                    <p class="resource-title">{{ item.title }}</p>
                    <p class="resource-copy">{{ item.summary }}</p>
                    <span class="resource-source">{{ item.source }}</span>
                  </div>
                </a>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section
        id="check-section"
        class="flow-section flow-section--check layer-start reveal-on-scroll"
        aria-label="Check section"
      >
        <div class="container-shell">
          <SubmissionPanel :quick-mode="submissionQuickMode" @submit="handleSubmission" />
        </div>
      </section>

      <section class="preview-band layer-mid reveal-on-scroll" aria-label="Risk preview tools">
        <div class="container-shell">
          <p class="preview-band__title">Risk State Preview</p>
          <div class="preview-band__actions">
            <button
              v-for="item in previewModes"
              :key="item.tier"
              type="button"
              class="preview-chip"
              @click="previewRiskState(item.tier)"
            >
              {{ item.label }}
            </button>
            <button
              type="button"
              class="preview-chip preview-chip--muted"
              @click="clearPreviewState"
            >
              Clear Preview
            </button>
          </div>
        </div>
      </section>

      <section
        v-if="isAnalyzing"
        class="panel layer-start loading-panel reveal-on-scroll"
        aria-label="Analyzing status"
      >
        <div class="container-shell">
          <h2>Analyzing now</h2>
          <p class="copy-block">The content is being processed now.</p>
        </div>
      </section>

      <section
        v-if="showResult"
        id="result-section"
        class="flow-section layer-start reveal-on-scroll"
        aria-label="Result section"
      >
        <div class="container-shell">
          <ResultPanel :result="result" :request-summary="requestSummary" />
        </div>
      </section>

      <section
        id="insights-section"
        class="panel layer-mid reveal-on-scroll"
        aria-label="Insights section"
      >
        <div class="container-shell">
          <h2>Insights</h2>
          <p class="section-copy copy-block">
            Weekly trends show where scam activity is rising. Use this section to prioritize
            warnings.
          </p>
          <div class="section-visual">
            <img src="/icons/job-scams-blue.jpg" alt="Scam trend illustration" />
          </div>
        </div>
      </section>

      <section
        id="learn-section"
        class="panel layer-start reveal-on-scroll"
        aria-label="Learn section"
      >
        <div class="container-shell">
          <h2>Learn</h2>
          <p class="section-copy copy-block">
            Learn common scripts used in fake employment outreach and how to challenge them.
          </p>
          <div class="section-visual">
            <img src="/icons/employmentScamsYellow.png" alt="Employment scam learning card" />
          </div>
        </div>
      </section>

      <section
        id="support-section"
        class="panel layer-mid reveal-on-scroll"
        aria-label="Support section"
      >
        <div class="container-shell">
          <h2>Support</h2>
          <p class="section-copy copy-block">
            Report suspicious recruiters and keep evidence snapshots to help follow-up
            investigation.
          </p>
          <div class="section-visual">
            <img src="/icons/TeamIcon.png" alt="Support resources icon" />
          </div>
        </div>
      </section>

      <footer class="site-footer" aria-label="Site information">
        <div class="container-shell site-footer__inner">
          <div class="site-footer__brand">
            <img src="/icons/stepsafe_logo.svg" alt="StepSafe" />
            <span>StepSafe</span>
          </div>
          <p>
            StepSafe provides practical signals to identify employment and task scams quickly.
            Always verify recruiter identity and never transfer money before confirming legitimacy.
          </p>

          <section class="site-footer__links" aria-label="Footer links">
            <div class="site-footer__col">
              <p class="site-footer__heading">
                <span class="site-footer__heading-icon" aria-hidden="true"></span>
                <span>Friend Links</span>
              </p>
              <div class="site-footer__link-list">
                <a
                  v-for="item in footerFriendLinks"
                  :key="item.href"
                  class="site-footer__link"
                  :href="item.href"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <img
                    v-if="item.icon"
                    class="site-footer__link-logo"
                    :src="item.icon"
                    alt=""
                    aria-hidden="true"
                    loading="lazy"
                  />
                  <span v-else class="site-footer__link-icon" aria-hidden="true"></span>
                  <span>{{ item.label }}</span>
                </a>
              </div>
            </div>

            <div class="site-footer__col">
              <p class="site-footer__heading">
                <span class="site-footer__heading-icon" aria-hidden="true"></span>
                <span>Official References</span>
              </p>
              <div class="site-footer__link-list">
                <a
                  v-for="item in footerOfficialLinks"
                  :key="item.href"
                  class="site-footer__link"
                  :href="item.href"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <img
                    v-if="item.icon"
                    class="site-footer__link-logo"
                    :src="item.icon"
                    alt=""
                    aria-hidden="true"
                    loading="lazy"
                  />
                  <span v-else class="site-footer__link-icon" aria-hidden="true"></span>
                  <span>{{ item.label }}</span>
                </a>
              </div>
            </div>

            <div class="site-footer__team">
              <img src="/icons/TeamIcon.png" alt="FIT5020TA09 High Five" />
              <div>
                <p class="site-footer__heading">
                  <span class="site-footer__heading-icon" aria-hidden="true"></span>
                  <span>Project Team</span>
                </p>
                <p class="site-footer__team-name">FIT5020TA09 High Five</p>
              </div>
            </div>
          </section>

          <p class="site-footer__meta">©2026 StepSafe. Built for scam awareness and prevention.</p>
        </div>
      </footer>
    </div>
  </main>
</template>

<style scoped>
.page-shell {
  background: var(--ms-color-surface-subtle);
  color: var(--ms-color-text-primary);
  min-height: 100vh;
  padding: 0;
}

.container-shell {
  margin: 0 auto;
  max-width: 1200px;
  padding: 0 48px;
}

.flow-wrapper {
  display: grid;
  gap: 0;
}

.layer-start {
  background: var(--ms-color-surface-page-start);
}

.layer-mid {
  background: var(--ms-color-surface-page-mid);
}

.copy-block {
  line-height: 1.6;
  margin: 0;
  max-width: 65ch;
}

.top-strip {
  background: rgb(26, 25, 24);
  color: rgb(255, 255, 255);
  padding: 5px 0;
  position: sticky;
  top: 0;
  z-index: 30;
}

.top-strip__inner {
  align-items: center;
  display: flex;
  gap: 12px;
  min-height: 30px;
  position: relative;
}

.brand-home {
  align-items: center;
  color: rgb(255, 255, 255);
  display: inline-flex;
  font-size: 0.9rem;
  font-weight: 500;
  gap: 8px;
  margin-right: 8px;
  text-decoration: none;
}

.brand-home img {
  background: transparent;
  display: block;
  height: 24px;
  object-fit: contain;
  width: auto;
}

.top-hamburger {
  background: transparent;
  border: 0;
  cursor: pointer;
  display: inline-block;
  height: 28px;
  margin-left: auto;
  padding: 6px 4px;
  width: 28px;
}

.top-hamburger span {
  background: rgb(255, 255, 255);
  display: block;
  height: 2px;
  margin-bottom: 4px;
  width: 16px;
}

.top-hamburger span:last-child {
  margin-bottom: 0;
}

.top-menu {
  background: rgb(26, 25, 24);
  inset: calc(100% + 4px) 48px auto;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
  position: absolute;
  transition:
    max-height 0.24s ease,
    opacity 0.2s ease;
}

.top-menu--open {
  max-height: 560px;
  opacity: 1;
  pointer-events: auto;
}

.top-menu__inner {
  display: grid;
  gap: 2px;
  padding: 12px 0;
}

.menu-link,
.menu-sublink {
  background: transparent;
  border: 0;
  color: rgb(255, 255, 255);
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 400;
  min-height: 44px;
  padding: 10px 40px;
  text-align: left;
  transition: background-color 0.2s ease;
  width: 100%;
}

.menu-link:hover,
.menu-link:focus-visible,
.menu-sublink:hover,
.menu-sublink:focus-visible {
  background: rgba(255, 255, 255, 0.16);
}

.menu-link--check {
  font-weight: 500;
}

.menu-group {
  display: grid;
  gap: 2px;
}

.menu-subactions {
  display: grid;
  gap: 2px;
  padding-left: 0;
}

.menu-sublink {
  color: rgb(214, 227, 245);
  font-size: 0.8rem;
  padding-left: 56px;
}

.hero-band {
  padding: 56px 0;
}

.hero-band__inner {
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
}

.hero-copy {
  background: var(--ms-color-surface-page-start);
  padding: 24px;
}

.hero-eyebrow {
  color: var(--ms-color-brand-hover);
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0.11em;
  margin: 0 0 16px;
  text-transform: uppercase;
}

h1 {
  font-size: clamp(3rem, 6.2vw, 5.2rem);
  font-weight: 300;
  line-height: 0.92;
  margin: 0 0 24px;
  max-width: 980px;
}

.hero-summary {
  color: var(--ms-color-text-secondary);
  font-size: 1.02rem;
  margin: 0 0 22px;
}

.cta-primary {
  background: var(--ms-color-brand);
  color: rgb(255, 255, 255);
  display: inline-flex;
  font-size: 0.9rem;
  font-weight: 600;
  min-height: 48px;
  padding: 16px 32px;
  text-decoration: none;
  text-transform: uppercase;
}

.cta-primary:hover,
.cta-primary:focus-visible {
  background: var(--ms-color-brand-hover);
  color: rgb(255, 255, 255);
}

.cta-primary:active {
  background: var(--ms-color-brand-active);
}

.hero-art {
  align-items: center;
  background: var(--ms-color-surface-page-mid);
  display: flex;
  justify-content: center;
  min-height: 380px;
  padding: 24px;
}

.hero-art img {
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.info-grid {
  padding: 38px 0;
}

.info-grid__inner {
  display: grid;
  align-items: start;
  gap: 12px;
  grid-template-columns: 1fr 1fr;
}

.info-block,
.panel {
  background: var(--ms-color-surface-page-start);
  padding: 24px;
}

.info-block {
  padding: 20px;
}

.info-block h2 {
  font-size: 1.5rem;
  font-weight: 400;
  margin: 0 0 10px;
}

.info-summary {
  color: var(--ms-color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0 0 14px;
}

.info-layout {
  display: block;
}

.info-rows {
  display: grid;
  gap: 10px;
}

.resource-row {
  background: var(--ms-color-surface-page-start);
  color: var(--ms-color-text-primary);
  display: grid;
  gap: 12px;
  grid-template-columns: 52px minmax(0, 1fr);
  min-height: 94px;
  padding: 20px;
  text-decoration: none;
  transition: background-color 0.22s ease;
}

.resource-row:hover,
.resource-row:focus-visible {
  background: var(--ms-color-border-soft);
}

.resource-inset {
  align-items: center;
  background: var(--ms-color-danger-soft);
  display: flex;
  height: 52px;
  justify-content: center;
  width: 52px;
}

.resource-inset--learn {
  background: var(--ms-color-surface-page-mid);
}

.resource-inset img {
  height: 24px;
  width: 24px;
}

.resource-main {
  align-self: center;
}

.resource-title {
  font-size: 0.96rem;
  font-weight: 500;
  margin: 0 0 6px;
}

.resource-copy {
  color: var(--ms-color-text-secondary);
  font-size: 0.86rem;
  line-height: 1.35;
  margin: 0 0 6px;
}

.resource-source {
  color: var(--ms-color-brand-hover);
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.flow-section {
  scroll-margin-top: 84px;
}

.flow-section--check {
  padding: 56px 0;
}

.preview-band {
  padding: 42px 0;
}

.preview-band__title {
  font-size: 0.88rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  margin: 0 0 14px;
  text-transform: uppercase;
}

.preview-band__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-chip {
  background: var(--ms-color-brand);
  border: 0;
  color: rgb(255, 255, 255);
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 500;
  min-height: 44px;
  padding: 10px 16px;
  transition: background-color 0.2s ease;
}

.preview-chip:hover,
.preview-chip:focus-visible {
  background: var(--ms-color-brand-hover);
}

.preview-chip--muted {
  background: rgb(74, 108, 149);
}

.preview-chip--muted:hover,
.preview-chip--muted:focus-visible {
  background: rgb(53, 81, 115);
}

.panel {
  padding: 56px 0;
}

.loading-panel h2,
#insights-section h2,
#learn-section h2,
#support-section h2 {
  font-size: clamp(2rem, 4vw, 3.2rem);
  font-weight: 300;
  margin: 0 0 20px;
}

.section-copy {
  color: var(--ms-color-text-secondary);
  line-height: 1.6;
  margin: 0 0 22px;
}

.section-visual {
  background: var(--ms-color-surface-page-start);
  display: flex;
  justify-content: center;
  min-height: 200px;
  overflow: hidden;
  padding: 24px;
}

.section-visual img {
  max-height: 240px;
  object-fit: cover;
  width: 100%;
}

.site-footer {
  background: rgb(26, 25, 24);
  color: rgb(255, 255, 255);
  padding: 40px 0 54px;
}

.site-footer__inner {
  display: grid;
  gap: 16px;
}

.site-footer__brand {
  align-items: center;
  display: inline-flex;
  font-size: 1.08rem;
  font-weight: 500;
  gap: 10px;
}

.site-footer__brand img {
  height: 40px;
  object-fit: contain;
  width: auto;
}

.site-footer p {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.65;
  margin: 0;
  max-width: 78ch;
}

.site-footer__links {
  display: grid;
  gap: 14px;
  grid-template-columns: 1fr 1fr 0.9fr;
}

.site-footer__heading {
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.24);
  color: rgba(255, 255, 255, 0.72);
  display: flex;
  font-size: 0.74rem;
  font-weight: 500;
  gap: 8px;
  letter-spacing: 0.08em;
  margin: 0 0 10px;
  padding-bottom: 8px;
  text-transform: uppercase;
}

.site-footer__heading-icon {
  background: rgb(74, 108, 149);
  display: inline-block;
  flex: 0 0 10px;
  height: 10px;
}

.site-footer__link-list {
  display: grid;
  gap: 6px;
}

.site-footer__link {
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  color: rgb(255, 255, 255);
  display: inline-flex;
  font-size: 0.8rem;
  gap: 8px;
  line-height: 1.35;
  min-height: 38px;
  padding: 9px 10px;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.site-footer__link-logo {
  border-radius: 2px;
  display: inline-block;
  flex: 0 0 14px;
  height: 14px;
  object-fit: contain;
  width: 14px;
}

.site-footer__link-icon {
  background: rgba(255, 255, 255, 0.88);
  display: inline-block;
  flex: 0 0 6px;
  height: 6px;
}

.site-footer__link:hover,
.site-footer__link:focus-visible {
  background: rgba(255, 255, 255, 0.18);
}

.site-footer__team {
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  display: grid;
  gap: 10px;
  grid-template-columns: 62px minmax(0, 1fr);
  min-height: 96px;
  padding: 14px;
}

.site-footer__team img {
  height: 56px;
  object-fit: contain;
  width: 56px;
}

.site-footer__team-name {
  color: rgb(255, 255, 255);
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1.35;
  margin: 0;
}

.site-footer__meta {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.86rem;
}

.reveal-on-scroll {
  opacity: 0;
  transform: translateY(24px);
  transition:
    opacity 0.65s ease,
    transform 0.65s ease;
}

.reveal-on-scroll.is-visible {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 980px) {
  .container-shell {
    padding: 0 24px;
  }

  .top-menu {
    inset: calc(100% + 4px) 24px auto;
  }

  .hero-band__inner,
  .info-grid__inner {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .top-strip {
    padding: 4px 0;
  }

  .top-strip__inner {
    min-height: 28px;
    flex-wrap: nowrap;
  }

  .top-menu {
    inset: calc(100% + 4px) 16px auto;
  }

  .menu-link,
  .menu-sublink {
    padding: 10px 26px;
  }

  .menu-sublink {
    padding-left: 40px;
  }

  h1 {
    font-size: clamp(2.2rem, 10vw, 3.2rem);
  }

  .hero-band,
  .info-grid,
  .flow-section--check,
  .preview-band,
  .panel,
  .site-footer {
    padding: 42px 0;
  }

  .site-footer__links {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .reveal-on-scroll,
  .reveal-on-scroll.is-visible {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
