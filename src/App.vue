<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { DotLottieVue } from '@lottiefiles/dotlottie-vue'
import { AlertTriangle, ArrowRight, BookOpen, LifeBuoy, ShieldCheck } from 'lucide-vue-next'
import ResultPanel from './components/ResultPanel.vue'
import SubmissionPanel from './components/SubmissionPanel.vue'
import { analyzeTextContent, extractTextFromSubmission } from './services/scamAnalysisEngine'

const isAnalyzing = ref(false)
const result = ref(null)
const extractedTextPreview = ref('')
const submissionQuickMode = ref('text')
const isMenuOpen = ref(false)
const highlightKeySignals = ref(false)
const menuToggleButton = ref(null)
const isNavElevated = ref(false)
const activeNavId = ref('home-section')
const isPageFading = ref(false)
const statsBandRef = ref(null)
const heroParticlesCanvas = ref(null)
const isHeroLottieFailed = ref(false)
const statsAnimated = ref(false)
const statsLossValue = ref('$0B')
const statsVictimValue = ref('0')
const statsTaskValue = ref('0%')
const latestAnalyzedInput = ref('')
const NAV_SCROLL_GAP = 18
const CHECK_SCAM_TARGET_ID = 'check-scam-panel'
const EXTRACTED_PREVIEW_MAX_CHARS = 420
const SCROLL_SECTION_IDS = [
  'home-section',
  'check-section',
  'insights-section',
  'learn-section',
  'support-section',
]

const FEMALE_LOTTIE_SRC =
  'https://lottie.host/9075ec25-d2b0-4f31-b387-fb48af7f4314/ZycTb7dy1X.lottie'
const MOBILE_LOTTIE_EMBED_SRC =
  'https://lottie.host/embed/45c9792a-b3b7-41c5-9b43-660af864ea8a/aBV7C2loCT.lottie'

let highlightTimer = null
let pageFadeTimer = null
let statsObserver = null
let particleAnimationFrame = null
let particleReduceMotionQuery = null
let particleReduceMotionHandler = null
let particleResizeHandler = null
let stageMotionFrame = null

const heroParticleState = {
  canvas: null,
  context: null,
  host: null,
  width: 0,
  height: 0,
  dpr: 1,
  particles: [],
}

const topActions = [
  { label: 'Suspicious message', mode: 'text', action: 'open-check' },
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
    stripColor: '#D0312D',
    image: '/icons/Task scam warning signs.png',
    fallback: '/icons/StepSafeIcon.png',
  },
  {
    title: 'How to spot fake remote jobs',
    summary: 'FTC guidance for fake checks, upfront fee traps, and high-pay low-effort bait.',
    href: 'https://consumer.ftc.gov/articles/job-scams',
    source: 'FTC Consumer Advice',
    stripColor: '#1F2D6B',
    image: '/icons/job-scams-blue.jpg',
    fallback: '/icons/StepSafeIcon.png',
  },
]

const learningCards = [
  {
    title: "Employment scams are on the rise. Here's what to look out for",
    summary: 'Coverage of warning signs and recent scam growth trends in Australia.',
    href: 'https://www.sbs.com.au/news/article/employment-scams-are-on-the-rise-heres-what-to-look-out-for/2xgyuapu0',
    source: 'SBS News',
    stripColor: '#1F2D6B',
    image: "/icons/Employment scams are on the rise. Here's what to look out for.avif",
    fallback: '/icons/StepSafeIcon.png',
  },
  {
    title: "'An elaborate ruse': The scam that's surging in Australia",
    summary: 'Explainer on task scam mechanics and how to protect yourself from losses.',
    href: 'https://www.sbs.com.au/news/article/an-elaborate-ruse-the-scam-thats-surging-in-australia-and-how-to-protect-yourself/fxvbsllo7',
    source: 'SBS News',
    stripColor: '#D0312D',
    image: "/icons/An elaborate ruse The scam that's surging in Australia.avif",
    fallback: '/icons/StepSafeIcon.png',
  },
  {
    title: 'Sam thought he had a marketing job - it was actually a task-based scam',
    summary: 'Case study with concrete red flags from a real task-based scam timeline.',
    href: 'https://www.abc.net.au/news/2025-07-26/employment-scams-work-marketing-messages/105089062',
    source: 'ABC News',
    stripColor: '#1F2D6B',
    image: '/icons/sam-thought-marketing-job-task-scam.avif',
    fallback: '/icons/StepSafeIcon.png',
  },
]

quickTips.forEach((item) => {
  item.image = item.image?.startsWith('/') ? item.image : '/icons/job-scams-blue.jpg'
  item.fallback = item.fallback || '/icons/StepSafeIcon.png'
})

learningCards.forEach((item) => {
  item.image = item.image?.startsWith('/') ? item.image : '/icons/EmploymentScamWarningPic.png'
  item.fallback = item.fallback || '/icons/StepSafeIcon.png'
})

const resourceImageStatus = reactive({})

const urgencyStats = [
  {
    key: 'loss',
    target: 2.2,
    label: 'lost to scams in Australia in 2025',
  },
  {
    key: 'victims',
    label: 'people aged 18-30 may be caught in job scams',
  },
  {
    key: 'task',
    target: 47,
    label: 'Task scams up year on year',
  },
]

const statsEvidenceNote =
  'Source: ACCC media release (30 Mar 2026) and Scamwatch Targeting Scams Report 2025 infographic text.'

const howItWorksSteps = [
  {
    number: '1',
    title: 'Paste, upload, or link.',
    description: 'Submit a recruiter message, PDF job posting, or suspicious URL.',
  },
  {
    number: '2',
    title: 'We scan it instantly.',
    description:
      'Our detection engine checks for known scam patterns, risky phrases, and unverified business details.',
  },
  {
    number: '3',
    title: 'Get your risk result.',
    description: 'See your risk score, flagged indicators, and what to do next, all in one screen.',
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

const footerProductLinks = [
  { label: 'Home', href: '#home-section' },
  { label: 'Check Scam', href: '#check-section' },
  { label: 'Insights', href: '#insights-section' },
  { label: 'Learn', href: '#learn-section' },
  { label: 'Support', href: '#support-section' },
]

const footerLegalLinks = [
  { label: 'Privacy', href: '#' },
  { label: 'Terms', href: '#' },
]

const showResult = computed(() => result.value !== null)

let revealObserver = null

function scrollToSection(sectionId) {
  const node = document.getElementById(sectionId)
  if (!node) return

  const header = document.querySelector('.top-strip')
  const headerHeight = header instanceof HTMLElement ? header.offsetHeight : 0
  const stickyTopInset =
    header instanceof HTMLElement
      ? Number.parseFloat(window.getComputedStyle(header).top || '0') || 0
      : 0
  const top =
    node.getBoundingClientRect().top +
    window.scrollY -
    headerHeight -
    stickyTopInset -
    NAV_SCROLL_GAP

  window.scrollTo({ top, behavior: 'smooth' })
}

function navigateToSection(sectionId) {
  isMenuOpen.value = false
  activeNavId.value = sectionId
  isPageFading.value = true
  if (pageFadeTimer) {
    clearTimeout(pageFadeTimer)
  }
  pageFadeTimer = window.setTimeout(() => {
    isPageFading.value = false
  }, 200)
  scrollToSection(sectionId)
}

function goToCheckScam() {
  navigateToSection(CHECK_SCAM_TARGET_ID)
}

function externalAriaLabel(label) {
  return `${label} (opens in a new tab)`
}

function getResourceKey(item) {
  return item.href
}

function isResourceImageReady(item) {
  const key = getResourceKey(item)
  return resourceImageStatus[key] === 'loaded'
}

function markResourceImageLoaded(item) {
  const key = getResourceKey(item)
  resourceImageStatus[key] = 'loaded'
}

function markResourceImageError(event, item) {
  const image = event?.target
  if (!(image instanceof HTMLImageElement)) {
    markResourceImageLoaded(item)
    return
  }

  const fallback = item.fallback || '/icons/StepSafeIcon.png'
  if (image.getAttribute('src') !== fallback) {
    image.setAttribute('src', fallback)
    return
  }

  markResourceImageLoaded(item)
}

function onHeroLottieError() {
  isHeroLottieFailed.value = true
}

function triggerTopAction(action) {
  isMenuOpen.value = false
  submissionQuickMode.value = action.mode
  goToCheckScam()
}

function syncActiveSectionByViewport() {
  const header = document.querySelector('.top-strip')
  const headerHeight = header instanceof HTMLElement ? header.offsetHeight : 0
  const threshold = headerHeight + 80

  let selected = 'home-section'
  for (const id of SCROLL_SECTION_IDS) {
    const node = document.getElementById(id)
    if (!node) continue

    const top = node.getBoundingClientRect().top
    if (top <= threshold) {
      selected = id
    }
  }

  activeNavId.value = selected
}

function updateSnapStageMotion() {
  const stages = document.querySelectorAll('.snap-stage')
  const viewportCenter = window.innerHeight * 0.56

  stages.forEach((node) => {
    if (!(node instanceof HTMLElement)) return

    const rect = node.getBoundingClientRect()
    const center = rect.top + rect.height * 0.5
    const delta = center - viewportCenter
    const normalized = Math.max(-1, Math.min(1, delta / window.innerHeight))
    const offset = Math.round(normalized * 46)
    const scale = Math.max(0.91, 1 - Math.abs(normalized) * 0.06)
    const dim = Math.min(0.36, 0.1 + Math.abs(normalized) * 0.28)
    const curtainProgress = Math.max(0, Math.min(1, -rect.top / (rect.height * 0.68)))
    const curtainShift = Math.round(curtainProgress * 24)

    node.style.setProperty('--parallax-offset', `${offset}px`)
    node.style.setProperty('--stack-scale', `${scale.toFixed(3)}`)
    node.style.setProperty('--stack-dim', `${dim.toFixed(3)}`)
    node.style.setProperty('--curtain-progress', `${curtainProgress.toFixed(3)}`)
    node.style.setProperty('--curtain-shift', `${curtainShift}`)
  })
}

function scheduleSnapStageMotion() {
  if (stageMotionFrame) return

  stageMotionFrame = requestAnimationFrame(() => {
    stageMotionFrame = null
    updateSnapStageMotion()
  })
}

function animateValue({ from, to, duration, onTick, onDone }) {
  const start = performance.now()
  const frame = (now) => {
    const progress = Math.min((now - start) / duration, 1)
    const eased = 1 - (1 - progress) ** 3
    onTick(from + (to - from) * eased)

    if (progress < 1) {
      requestAnimationFrame(frame)
      return
    }

    onDone?.()
  }

  requestAnimationFrame(frame)
}

function runStatsAnimation() {
  if (statsAnimated.value) return
  statsAnimated.value = true

  animateValue({
    from: 0,
    to: urgencyStats[0].target,
    duration: 1500,
    onTick: (value) => {
      statsLossValue.value = `$${Math.max(0, value).toFixed(2)}B`
    },
    onDone: () => {
      statsLossValue.value = '$2.18B'
    },
  })

  statsVictimValue.value = '1 in 3'

  animateValue({
    from: 0,
    to: urgencyStats[2].target,
    duration: 1500,
    onTick: (value) => {
      statsTaskValue.value = `${Math.max(0, Math.round(value))}%`
    },
    onDone: () => {
      statsTaskValue.value = '47%'
    },
  })
}

function initStatsObserver() {
  if (!(statsBandRef.value instanceof HTMLElement)) return
  if (statsObserver) {
    statsObserver.disconnect()
  }

  statsObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return
        runStatsAnimation()
        statsObserver?.disconnect()
        statsObserver = null
      })
    },
    { threshold: 0.15 },
  )

  statsObserver.observe(statsBandRef.value)
}

function handleWindowScroll() {
  isNavElevated.value = window.scrollY > 8
  syncActiveSectionByViewport()
  scheduleSnapStageMotion()
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function handleGlobalKeydown(event) {
  if (event.key !== 'Escape') return
  if (!isMenuOpen.value) return

  isMenuOpen.value = false
  nextTick(() => {
    if (menuToggleButton.value instanceof HTMLElement) {
      menuToggleButton.value.focus()
    }
  })
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
      threshold: 0.15,
      rootMargin: '0px 0px -8% 0px',
    },
  )

  candidates.forEach((node) => revealObserver?.observe(node))
}

function randomBetween(min, max) {
  return min + Math.random() * (max - min)
}

function createHeroParticles(count) {
  heroParticleState.particles = Array.from({ length: count }).map(() => ({
    x: randomBetween(0, heroParticleState.width),
    y: randomBetween(0, heroParticleState.height),
    radius: randomBetween(1.2, 2.9),
    alpha: randomBetween(0.35, 0.72),
    vx: randomBetween(-0.18, 0.18),
    vy: randomBetween(-0.14, 0.14),
  }))
}

function resizeHeroParticleCanvas() {
  if (!(heroParticleState.canvas instanceof HTMLCanvasElement)) return
  if (!(heroParticleState.host instanceof HTMLElement)) return

  const width = Math.max(1, heroParticleState.host.clientWidth)
  const height = Math.max(1, heroParticleState.host.clientHeight)
  const dpr = window.devicePixelRatio || 1

  heroParticleState.width = width
  heroParticleState.height = height
  heroParticleState.dpr = dpr

  heroParticleState.canvas.width = Math.floor(width * dpr)
  heroParticleState.canvas.height = Math.floor(height * dpr)
  heroParticleState.canvas.style.width = `${width}px`
  heroParticleState.canvas.style.height = `${height}px`

  if (heroParticleState.context) {
    heroParticleState.context.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  const count = Math.floor(randomBetween(40, 61))
  createHeroParticles(count)
}

function drawHeroParticles() {
  const ctx = heroParticleState.context
  if (!ctx) return

  ctx.clearRect(0, 0, heroParticleState.width, heroParticleState.height)
  ctx.fillStyle = '#D4CFC8'

  heroParticleState.particles.forEach((particle) => {
    ctx.globalAlpha = particle.alpha * 0.4
    ctx.beginPath()
    ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2)
    ctx.fill()
  })

  ctx.globalAlpha = 1
}

function stepHeroParticles() {
  heroParticleState.particles.forEach((particle) => {
    particle.x += particle.vx
    particle.y += particle.vy

    if (particle.x < -8) particle.x = heroParticleState.width + 8
    if (particle.x > heroParticleState.width + 8) particle.x = -8
    if (particle.y < -8) particle.y = heroParticleState.height + 8
    if (particle.y > heroParticleState.height + 8) particle.y = -8
  })
}

function stopHeroParticles() {
  if (particleAnimationFrame) {
    cancelAnimationFrame(particleAnimationFrame)
    particleAnimationFrame = null
  }
}

function runHeroParticleFrame() {
  stepHeroParticles()
  drawHeroParticles()
  particleAnimationFrame = requestAnimationFrame(runHeroParticleFrame)
}

function initHeroParticles() {
  const canvas = heroParticlesCanvas.value
  if (!(canvas instanceof HTMLCanvasElement)) return

  const context = canvas.getContext('2d')
  if (!context) return

  heroParticleState.canvas = canvas
  heroParticleState.context = context
  heroParticleState.host = canvas.parentElement

  resizeHeroParticleCanvas()
  stopHeroParticles()

  const prefersReducedMotion =
    particleReduceMotionQuery instanceof MediaQueryList && particleReduceMotionQuery.matches

  drawHeroParticles()
  if (!prefersReducedMotion) {
    runHeroParticleFrame()
  }
}

onMounted(() => {
  particleReduceMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  particleReduceMotionHandler = () => initHeroParticles()
  particleResizeHandler = () => resizeHeroParticleCanvas()

  particleReduceMotionQuery.addEventListener('change', particleReduceMotionHandler)
  window.addEventListener('resize', particleResizeHandler)

  initHeroParticles()
  initRevealObserver()
  initStatsObserver()
  updateSnapStageMotion()
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('scroll', handleWindowScroll, { passive: true })
  handleWindowScroll()
})

watch(showResult, async (visible) => {
  if (!visible) {
    highlightKeySignals.value = false
    return
  }

  await nextTick()
  scrollToSection('result-section')
  initRevealObserver()

  const resultHeading = document.getElementById('result-heading')
  if (resultHeading instanceof HTMLElement) {
    window.setTimeout(() => {
      resultHeading.focus({ preventScroll: true })
    }, 260)
  }

  highlightKeySignals.value = true

  if (highlightTimer) {
    clearTimeout(highlightTimer)
  }

  if (stageMotionFrame) {
    cancelAnimationFrame(stageMotionFrame)
    stageMotionFrame = null
  }

  highlightTimer = window.setTimeout(() => {
    highlightKeySignals.value = false
  }, 3200)
})

onBeforeUnmount(() => {
  if (revealObserver) {
    revealObserver.disconnect()
  }

  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('scroll', handleWindowScroll)

  if (statsObserver) {
    statsObserver.disconnect()
  }

  if (pageFadeTimer) {
    clearTimeout(pageFadeTimer)
  }

  if (highlightTimer) {
    clearTimeout(highlightTimer)
  }

  stopHeroParticles()

  if (particleReduceMotionQuery && particleReduceMotionHandler) {
    particleReduceMotionQuery.removeEventListener('change', particleReduceMotionHandler)
  }

  if (particleResizeHandler) {
    window.removeEventListener('resize', particleResizeHandler)
  }
})

async function handleSubmission(payload) {
  isAnalyzing.value = true
  result.value = null

  const textContent = await extractTextFromSubmission(payload)
  if (payload.inputType === 'pdf') {
    extractedTextPreview.value = textContent.slice(0, EXTRACTED_PREVIEW_MAX_CHARS)
    if (textContent.length > EXTRACTED_PREVIEW_MAX_CHARS) {
      extractedTextPreview.value += '...'
    }
  } else {
    extractedTextPreview.value = ''
  }

  setTimeout(() => {
    result.value = analyzeTextContent(textContent)
    latestAnalyzedInput.value = textContent
    isAnalyzing.value = false
  }, 850)
}
</script>

<template>
  <main id="home" class="page-shell">
    <header
      class="top-strip"
      :class="{ 'top-strip--elevated': isNavElevated }"
      aria-label="Top action bar"
    >
      <div class="top-strip__inner">
        <a class="brand-home" href="#home-section" aria-label="Go to Home section">
          <img src="/icons/stepsafe_logo.svg" alt="StepSafe" />
          <span>StepSafe</span>
        </a>

        <nav class="top-nav-desktop" aria-label="Primary navigation">
          <button
            type="button"
            class="top-nav-link"
            :class="{ 'top-nav-link--active': activeNavId === 'home-section' }"
            @click="navigateToSection('home-section')"
          >
            Home
          </button>
          <button
            v-for="section in primarySections"
            :key="`desktop-${section.id}`"
            type="button"
            class="top-nav-link"
            :class="{ 'top-nav-link--active': activeNavId === section.id }"
            @click="navigateToSection(section.id)"
          >
            {{ section.label }}
          </button>
          <button
            type="button"
            class="top-nav-cta"
            :class="{
              'top-nav-cta--active':
                activeNavId === CHECK_SCAM_TARGET_ID || activeNavId === 'check-section',
            }"
            @click="goToCheckScam"
          >
            Check scam
          </button>
        </nav>

        <button
          ref="menuToggleButton"
          type="button"
          class="top-hamburger"
          aria-label="Toggle navigation"
          aria-controls="mobile-site-menu"
          :aria-expanded="isMenuOpen"
          @click="toggleMenu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <nav
          id="mobile-site-menu"
          class="top-menu"
          :class="{ 'top-menu--open': isMenuOpen }"
          aria-label="Site navigation"
        >
          <div class="top-menu__inner">
            <button type="button" class="menu-link" @click="navigateToSection('home-section')">
              Home
            </button>

            <div class="menu-group">
              <button type="button" class="menu-link menu-link--check" @click="goToCheckScam">
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

    <div class="flow-wrapper" :class="{ 'flow-wrapper--fading': isPageFading }">
      <section
        id="home-section"
        class="hero-band section-a section-fade section-fade--hero reveal-on-scroll"
        aria-label="Hero section"
      >
        <canvas ref="heroParticlesCanvas" class="hero-particles" aria-hidden="true"></canvas>
        <div class="container-shell hero-band__inner">
          <div class="hero-copy">
            <p class="hero-eyebrow">StepSafe Employment Scam Alert</p>
            <h1>
              Spot job
              <span class="hero-wordmark"
                >scams
                <svg viewBox="0 0 170 22" aria-hidden="true">
                  <path d="M2 16C25 5 42 20 62 12C84 3 103 20 126 12C141 7 152 8 168 13" />
                </svg>
              </span>
              before they cost you.
            </h1>
            <p class="hero-summary copy-block">
              Paste a message, drop a link, or upload a PDF. We'll tell you if something looks off.
            </p>
            <div class="hero-tags" aria-label="Scam scope tags">
              <span>Task scams</span>
              <span>📩 Fake Recruiters</span>
              <span>💸 Upfront Fee Traps</span>
            </div>
            <a class="cta-primary" href="#check-section" @click.prevent="goToCheckScam">
              Check scam now
              <ArrowRight :size="16" aria-hidden="true" />
            </a>
          </div>
          <div class="hero-art" aria-hidden="true">
            <div class="hero-art__card">
              <DotLottieVue
                v-if="!isHeroLottieFailed"
                class="hero-lottie"
                :src="FEMALE_LOTTIE_SRC"
                autoplay
                loop
                @error="onHeroLottieError"
              />
              <img
                v-else
                class="hero-lottie-fallback hero-lottie-fallback--visible"
                src="/icons/female-employee-data-security.gif"
                alt="Female security illustration"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </section>

      <section
        ref="statsBandRef"
        class="stats-strip section-fade section-fade--stats reveal-on-scroll reveal-slide-left"
        aria-label="Scam impact stats"
      >
        <div class="container-shell stats-strip__inner">
          <article class="stat-tile">
            <p class="stat-tile__value">{{ statsLossValue }}</p>
            <p class="stat-tile__label">{{ urgencyStats[0].label }}</p>
          </article>
          <article class="stat-tile">
            <p class="stat-tile__value" :class="{ 'stat-tile__value--flip': statsAnimated }">
              {{ statsVictimValue }}
            </p>
            <p class="stat-tile__label">{{ urgencyStats[1].label }}</p>
          </article>
          <article class="stat-tile">
            <p class="stat-tile__value">{{ statsTaskValue }}</p>
            <p class="stat-tile__label">{{ urgencyStats[2].label }}</p>
          </article>
        </div>
        <p class="stats-strip__source">{{ statsEvidenceNote }}</p>
      </section>

      <section class="how-it-works section-c section-fade section-fade--how">
        <div class="container-shell">
          <h2 class="section-title">How StepSafe Works</h2>
          <div class="how-grid">
            <svg
              class="how-grid__connector"
              viewBox="0 0 100 10"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <line x1="0" y1="5" x2="100" y2="5"></line>
            </svg>
            <article
              v-for="step in howItWorksSteps"
              :key="step.number"
              class="how-step reveal-on-scroll reveal-fade-up"
              :class="`how-step--${step.number}`"
              :style="{ '--reveal-delay': `${(Number(step.number) - 1) * 150}ms` }"
            >
              <p class="how-step__number" :data-step="step.number">{{ step.number }}</p>
              <h3>{{ step.title }}</h3>
              <p>{{ step.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <section
        id="check-section"
        class="flow-section flow-section--check snap-stage section-a section-fade section-fade--check reveal-on-scroll"
        aria-label="Check section"
      >
        <div id="check-scam-panel" class="container-shell">
          <SubmissionPanel
            :quick-mode="submissionQuickMode"
            :is-analyzing="isAnalyzing"
            @submit="handleSubmission"
          />
        </div>
      </section>

      <section
        id="check-alerts-section"
        class="preview-band preview-band--animated section-b section-fade section-fade--preview reveal-on-scroll"
        aria-label="Check alerts and risk preview tools"
      >
        <div class="container-shell">
          <div class="preview-band__inner">
            <figure class="preview-band__visual" aria-hidden="true">
              <iframe
                class="preview-band__lottie"
                :src="MOBILE_LOTTIE_EMBED_SRC"
                title="Smartphone UI animation"
                loading="lazy"
              ></iframe>
            </figure>
            <div>
              <p class="preview-band__title">Check alerts</p>
            </div>
          </div>
        </div>
      </section>

      <section
        v-if="isAnalyzing"
        class="panel section-b loading-panel reveal-on-scroll"
        aria-label="Analyzing status"
      >
        <div class="container-shell">
          <h2 class="section-title">Analyzing now</h2>
          <p class="copy-block">The content is being processed now.</p>
        </div>
      </section>

      <section
        v-if="showResult"
        id="result-section"
        class="flow-section section-c section-fade section-fade--result reveal-on-scroll result-section-enter"
        aria-label="Result section"
      >
        <div class="container-shell">
          <ResultPanel
            :result="result"
            :highlight-key-signals="highlightKeySignals"
            :extracted-text-preview="extractedTextPreview"
            :analysis-source-text="latestAnalyzedInput"
          />
        </div>
      </section>

      <section
        class="info-grid section-c section-fade section-fade--news"
        aria-label="Guidance blocks"
      >
        <div class="container-shell info-grid__inner">
          <article
            class="info-block info-block--warning reveal-on-scroll reveal-slide-left"
            style="--reveal-delay: 0ms"
          >
            <h2 class="section-title">Quick tips</h2>
            <p class="info-summary">Fast scam checks for step-by-step simple tasks fraud.</p>
            <div class="info-layout">
              <div class="info-rows">
                <a
                  v-for="item in quickTips"
                  :key="item.href"
                  class="resource-row"
                  :style="{ '--strip-accent': item.stripColor || '#D0312D' }"
                  :href="item.href"
                  :aria-label="externalAriaLabel(item.title)"
                  title="Opens in a new tab"
                  target="_blank"
                  rel="noopener noreferrer"
                  referrerpolicy="no-referrer"
                >
                  <span class="resource-accent" aria-hidden="true"></span>
                  <div class="resource-main">
                    <p class="resource-title">{{ item.title }}</p>
                    <p class="resource-copy">{{ item.summary }}</p>
                    <span class="resource-source">{{ item.source }}</span>
                  </div>
                  <figure
                    class="resource-media"
                    :class="{ 'resource-media--loading': !isResourceImageReady(item) }"
                    aria-hidden="true"
                  >
                    <img
                      :src="item.image"
                      alt=""
                      loading="lazy"
                      referrerpolicy="no-referrer"
                      @load="markResourceImageLoaded(item)"
                      @error="markResourceImageError($event, item)"
                    />
                  </figure>
                </a>
              </div>
            </div>
          </article>

          <article
            class="info-block info-block--safe reveal-on-scroll reveal-slide-right"
            style="--reveal-delay: 120ms"
          >
            <h2 class="section-title">Scam alerts</h2>
            <p class="info-summary">
              Recent news coverage and case reports on employment and task scams.
            </p>
            <div class="info-layout">
              <div class="info-rows">
                <a
                  v-for="item in learningCards"
                  :key="item.href"
                  class="resource-row"
                  :style="{ '--strip-accent': item.stripColor || '#1F2D6B' }"
                  :href="item.href"
                  :aria-label="externalAriaLabel(item.title)"
                  title="Opens in a new tab"
                  target="_blank"
                  rel="noopener noreferrer"
                  referrerpolicy="no-referrer"
                >
                  <span class="resource-accent" aria-hidden="true"></span>
                  <div class="resource-main">
                    <p class="resource-title">{{ item.title }}</p>
                    <p class="resource-copy">{{ item.summary }}</p>
                    <span class="resource-source">{{ item.source }}</span>
                  </div>
                  <figure
                    class="resource-media"
                    :class="{ 'resource-media--loading': !isResourceImageReady(item) }"
                    aria-hidden="true"
                  >
                    <img
                      :src="item.image"
                      alt=""
                      loading="lazy"
                      referrerpolicy="no-referrer"
                      @load="markResourceImageLoaded(item)"
                      @error="markResourceImageError($event, item)"
                    />
                  </figure>
                </a>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section
        id="insights-section"
        class="panel snap-stage section-a section-fade section-fade--insights reveal-on-scroll"
        aria-label="Insights section"
      >
        <div class="container-shell">
          <h2 class="section-title">Insights</h2>
          <p class="section-copy copy-block">
            Weekly trends show where scam activity is rising. Use this section to prioritize
            warnings.
          </p>
          <div class="preview-placeholder" role="status" aria-live="polite">
            <p class="preview-placeholder__subtitle">
              <em>Scam scripts and tactics - arriving in Iteration 2</em>
            </p>
            <div class="preview-placeholder__grid" aria-hidden="true">
              <span class="preview-placeholder__card"></span>
              <span class="preview-placeholder__card"></span>
              <span class="preview-placeholder__card"></span>
            </div>
          </div>
        </div>
      </section>

      <section
        id="learn-section"
        class="panel snap-stage section-b section-fade section-fade--learn reveal-on-scroll"
        aria-label="Learn section"
      >
        <div class="container-shell">
          <h2 class="section-title">Learn</h2>
          <p class="section-copy copy-block">
            Learn common scripts used in fake employment outreach and how to challenge them.
          </p>
          <div class="preview-placeholder" role="status" aria-live="polite">
            <div class="feature-preview-grid" role="status" aria-live="polite">
              <article
                class="feature-preview feature-preview--learn reveal-on-scroll reveal-fade-up"
                style="--reveal-delay: 0ms"
              >
                <BookOpen :size="48" aria-hidden="true" />
                <h3>Script breakdowns</h3>
                <span>Coming in Iteration 2</span>
              </article>
              <article
                class="feature-preview feature-preview--learn reveal-on-scroll reveal-fade-up"
                style="--reveal-delay: 120ms"
              >
                <ShieldCheck :size="48" aria-hidden="true" />
                <h3>Scam timeline maps</h3>
                <span>Coming in Iteration 2</span>
              </article>
              <article
                class="feature-preview feature-preview--learn reveal-on-scroll reveal-fade-up"
                style="--reveal-delay: 240ms"
              >
                <AlertTriangle :size="48" aria-hidden="true" />
                <h3>Phrase libraries</h3>
                <span>Coming in Iteration 2</span>
              </article>
            </div>
            <p class="feature-preview-note">
              <em>Scam scripts and tactics - arriving in Iteration 2</em>
            </p>
          </div>
        </div>
      </section>

      <section
        id="support-section"
        class="panel snap-stage section-a section-fade section-fade--support reveal-on-scroll"
        aria-label="Support section"
      >
        <div class="container-shell">
          <h2 class="section-title">Support</h2>
          <p class="section-copy copy-block">
            Report suspicious recruiters and keep evidence records to help follow-up investigation.
          </p>
          <div class="feature-preview-grid" role="status" aria-live="polite">
            <article
              class="feature-preview feature-preview--support reveal-on-scroll reveal-fade-up"
              style="--reveal-delay: 0ms"
            >
              <LifeBuoy :size="48" aria-hidden="true" />
              <h3>Recovery playbooks</h3>
              <span>Coming in Iteration 2</span>
            </article>
            <article
              class="feature-preview feature-preview--support reveal-on-scroll reveal-fade-up"
              style="--reveal-delay: 120ms"
            >
              <ShieldCheck :size="48" aria-hidden="true" />
              <h3>Verification toolkit</h3>
              <span>Coming in Iteration 2</span>
            </article>
            <article
              class="feature-preview feature-preview--support reveal-on-scroll reveal-fade-up"
              style="--reveal-delay: 240ms"
            >
              <BookOpen :size="48" aria-hidden="true" />
              <h3>Reporting guides</h3>
              <span>Coming in Iteration 2</span>
            </article>
          </div>
          <p class="feature-preview-note">
            <em>Scam scripts and tactics - arriving in Iteration 2</em>
          </p>
        </div>
      </section>

      <footer class="site-footer" aria-label="Site information">
        <div class="container-shell site-footer__inner">
          <div class="site-footer__brand">
            <img src="/icons/stepsafe_logo.svg" alt="StepSafe" />
            <span>StepSafe</span>
          </div>
          <p class="site-footer__summary">Built for scam awareness and recovery.</p>

          <section class="site-footer__links" aria-label="Footer links and legal">
            <div class="site-footer__col site-footer__col--product">
              <p class="site-footer__heading">Product</p>
              <div class="site-footer__link-list">
                <a
                  v-for="item in footerProductLinks"
                  :key="item.href"
                  class="site-footer__link"
                  :href="item.href"
                >
                  <span>{{ item.label }}</span>
                </a>
              </div>
            </div>

            <div class="site-footer__col">
              <p class="site-footer__heading">Resources</p>
              <div class="site-footer__link-list">
                <a
                  v-for="item in footerFriendLinks"
                  :key="item.href"
                  class="site-footer__link"
                  :href="item.href"
                  :aria-label="externalAriaLabel(item.label)"
                  title="Opens in a new tab"
                  target="_blank"
                  rel="noopener noreferrer"
                  referrerpolicy="no-referrer"
                >
                  <span>{{ item.label }}</span>
                </a>
              </div>
            </div>

            <div class="site-footer__col">
              <p class="site-footer__heading">Legal</p>
              <div class="site-footer__link-list">
                <a
                  v-for="item in footerLegalLinks"
                  :key="item.label"
                  class="site-footer__link"
                  :href="item.href"
                >
                  <span>{{ item.label }}</span>
                </a>
              </div>
              <p class="site-footer__meta">©2026 StepSafe</p>
            </div>
          </section>

          <div class="site-footer__team" aria-label="StepSafe team">
            <img src="/icons/TeamIcon.png" alt="StepSafe team icon" />
            <img src="/icons/TeamNameIcon.png" alt="StepSafe team" />
          </div>
        </div>
      </footer>
    </div>
  </main>
</template>

<style scoped>
.page-shell {
  background: #f9f7f4;
  color: #6b7280;
  min-height: 100vh;
  overflow-x: hidden;
  padding: 0;
  position: relative;
}

:global(html),
:global(body) {
  scroll-behavior: smooth;
  scroll-snap-type: y mandatory;
}

.container-shell {
  margin: 0 auto;
  max-width: 1200px;
  padding: 0 48px;
}

.flow-wrapper {
  display: grid;
  gap: 0;
  opacity: 1;
  padding-top: 76px;
  position: relative;
  z-index: 1;
  transition: opacity 0.2s ease;
}

.flow-wrapper--fading {
  opacity: 0.86;
}

.section-a {
  background-color: #f9f7f4;
  background-image: none;
}

.section-b {
  background-color: #f2efe8;
  background-image: none;
}

.section-c {
  background-color: #eaf7f3;
  background-image: none;
}

.hero-band {
  background-size: 32px 32px;
}

.flow-section--check {
  background-size: 20px 20px;
}

.section-fade {
  position: relative;
}

.section-fade::after {
  content: '';
  height: 60px;
  left: 0;
  pointer-events: none;
  position: absolute;
  right: 0;
}

.section-fade--hero::after {
  background: linear-gradient(to bottom, rgba(249, 247, 244, 0), #f9f7f4);
  bottom: -60px;
}

.section-fade--stats::after {
  background: linear-gradient(to bottom, rgba(220, 38, 38, 0), #f2efe8);
  bottom: -60px;
}

.section-fade--news::after,
.section-fade--how::after,
.section-fade--check::after,
.section-fade--preview::after,
.section-fade--result::after,
.section-fade--insights::after,
.section-fade--learn::after,
.section-fade--support::after {
  display: none;
}

.copy-block {
  line-height: 1.6;
  margin: 0;
  max-width: 65ch;
}

.top-strip {
  color: #1a1a2a;
  left: 0;
  padding: 10px 0;
  position: fixed;
  right: 0;
  top: 0;
  z-index: 90;
}

.top-strip__inner {
  align-items: center;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #e5e2dc;
  border-radius: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  display: flex;
  gap: 14px;
  margin: 0 auto;
  max-width: 1200px;
  min-height: 43px;
  padding: 7px 24px;
  position: relative;
  transition: box-shadow 0.24s ease;
  width: calc(100% - 96px);
}

.top-strip--elevated .top-strip__inner {
  box-shadow: 0 8px 22px rgba(44, 62, 140, 0.18);
}

.brand-home {
  align-items: center;
  color: #1f2d6b;
  display: inline-flex;
  font-size: 0.9rem;
  font-weight: 700;
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

.top-nav-desktop {
  align-items: center;
  display: inline-flex;
  gap: 8px;
  margin-left: auto;
}

.top-nav-link {
  background: transparent;
  border: 0;
  border-radius: 20px;
  color: #1f2d6b;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  min-height: 28px;
  padding: 6px 14px;
  transition: all 200ms ease;
}

.top-nav-link:hover,
.top-nav-link:focus-visible {
  background: rgba(44, 62, 140, 0.12);
  color: #1f2d6b;
}

.top-nav-link--active {
  background: #1f2d6b;
  color: #ffffff;
}

.top-nav-cta {
  background: #1f2d6b;
  border: 0;
  border-radius: 24px;
  color: #ffffff;
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 700;
  min-height: 28px;
  padding: 6px 16px;
  transition: background 0.25s ease;
}

.top-nav-cta:hover,
.top-nav-cta:focus-visible {
  background: #1f2d6b;
}

.top-nav-cta--active {
  box-shadow: 0 6px 18px rgba(44, 62, 140, 0.28);
}

.top-hamburger {
  background: transparent;
  border: 0;
  cursor: pointer;
  display: none;
  height: 28px;
  margin-left: auto;
  padding: 6px 4px;
  width: 28px;
}

.top-hamburger span {
  background: #1f2d6b;
  display: block;
  height: 2px;
  margin-bottom: 4px;
  width: 16px;
}

.top-hamburger span:last-child {
  margin-bottom: 0;
}

.top-menu {
  background: #ffffff;
  border: 1px solid #e5e2dc;
  border-radius: 16px;
  display: none;
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
  color: #1f2d6b;
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
  background: rgba(44, 62, 140, 0.1);
}

.menu-link--check {
  color: #1f2d6b;
  font-weight: 700;
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
  color: #6b7280;
  font-size: 0.8rem;
  padding-left: 56px;
}

.hero-band {
  overflow: hidden;
  padding: 82px 0 52px;
  position: relative;
  isolation: isolate;
}

.hero-particles {
  inset: 0;
  opacity: 0.4;
  pointer-events: none;
  position: absolute;
  z-index: 0;
}

.hero-band__inner {
  display: grid;
  gap: 26px;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  position: relative;
  z-index: 1;
}

.hero-copy {
  background: transparent;
  padding: 0;
  position: relative;
  z-index: 2;
}

.hero-eyebrow {
  color: #6b7280;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.11em;
  margin: 0 0 16px;
  text-transform: uppercase;
}

h1 {
  color: #1a1a2a;
  font-size: clamp(2.6rem, 5.3vw, 52px);
  font-weight: 800;
  line-height: 1.04;
  margin: 0 0 24px;
  max-width: 980px;
}

.hero-wordmark {
  color: #1f2d6b;
  display: inline-flex;
  font-size: 1.08em;
  font-style: italic;
  margin: 0 4px;
  position: relative;
}

.hero-wordmark svg {
  bottom: -10px;
  left: -2px;
  position: absolute;
  width: 100%;
}

.hero-wordmark path {
  fill: none;
  stroke: #d0312d;
  stroke-linecap: round;
  stroke-width: 3;
}

.hero-highlight {
  color: #1f2d6b;
}

.hero-summary {
  color: #6b7280;
  font-size: 1.02rem;
  margin: 0 0 16px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0 0 22px;
}

.hero-tags span {
  background: #eef2ff;
  border-radius: 20px;
  color: #1f2d6b;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 12px;
}

.cta-primary {
  align-items: center;
  background: #1f2d6b;
  border-radius: 12px;
  color: #ffffff;
  display: inline-flex;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 700;
  min-height: 48px;
  padding: 14px 24px;
  text-decoration: none;
  transition: transform 0.2s ease;
}

.cta-primary:hover,
.cta-primary:focus-visible {
  background: #1f2d6b;
  color: #ffffff;
  transform: translateY(-1px);
}

.cta-primary:active {
  background: #1f2d6b;
}

.hero-art {
  align-items: center;
  background: transparent;
  display: flex;
  justify-content: center;
  min-height: 300px;
  pointer-events: none;
  padding: 8px;
  position: relative;
  z-index: 0;
}

.hero-art__card {
  align-items: center;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  display: flex;
  justify-content: center;
  min-height: auto;
  overflow: visible;
  padding: 0;
  position: relative;
}

.hero-lottie {
  display: block;
  height: min(360px, 68vw);
  transform: scale(1.9);
  transform-origin: center;
  width: min(340px, 100%);
}

.hero-lottie-fallback {
  display: none;
  height: min(360px, 68vw);
  object-fit: cover;
  width: min(340px, 100%);
}

.hero-lottie-fallback--visible {
  display: block;
}

.preview-band__inner {
  align-items: center;
  display: grid;
  gap: 14px;
  grid-template-columns: auto minmax(0, 1fr);
}

.preview-band__visual {
  border-radius: 12px;
  justify-self: start;
  margin: 0;
  overflow: hidden;
}

.preview-band__lottie {
  animation: previewFloat 3.2s ease-in-out infinite;
  border: 0;
  display: block;
  height: 84px;
  width: 130px;
}

.stats-strip {
  background: #d0312d;
  border-top: 4px solid #d0312d;
  border-radius: 16px 16px 0 0;
  color: #ffffff;
  margin-top: -24px;
  overflow: hidden;
  position: relative;
  z-index: 4;
}

.stats-strip::before {
  background-image: radial-gradient(circle, rgba(255, 255, 255, 0.28) 1px, transparent 1px);
  background-size: 14px 14px;
  content: '';
  inset: 0;
  opacity: 0.05;
  pointer-events: none;
  position: absolute;
}

.stats-strip__inner {
  align-items: stretch;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding-bottom: 22px;
  padding-top: 22px;
  position: relative;
  z-index: 1;
}

.stats-strip__source {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.78rem;
  line-height: 1.5;
  margin: 8px auto 0;
  max-width: 1280px;
  padding: 0 28px 14px;
  position: relative;
  word-break: break-word;
  z-index: 1;
}

.stat-tile {
  border-right: 1px solid rgba(255, 255, 255, 0.32);
  padding-right: 16px;
}

.stat-tile:last-child {
  border-right: 0;
  padding-right: 0;
}

.stat-tile__value {
  color: #ffffff;
  font-size: clamp(1.45rem, 2.3vw, 2.1rem);
  font-weight: 800;
  line-height: 1;
  margin: 0 0 6px;
}

.stat-tile__value--flip {
  animation: statFlip 0.6s ease;
}

.stat-tile__label {
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0;
}

.how-it-works {
  background: #f2efe8;
  padding: 62px 0;
}

.how-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  position: relative;
}

.how-grid__connector {
  height: 10px;
  left: 12%;
  position: absolute;
  right: 12%;
  top: 27px;
  width: 76%;
  z-index: 0;
}

.how-grid__connector line {
  animation: howDashFlow 2s linear infinite;
  fill: none;
  opacity: 0.65;
  stroke: #1f2d6b;
  stroke-dasharray: 6 8;
  stroke-width: 1.8;
}

.how-step {
  background: transparent;
  border-radius: 0;
  padding: 18px;
  position: relative;
  z-index: 1;
}

.how-step__number {
  align-items: center;
  background: #f2efe8;
  border: 2px solid #1f2d6b;
  border-radius: 999px;
  color: #1f2d6b;
  display: inline-flex;
  font-size: 16px;
  font-weight: 800;
  height: 42px;
  justify-content: center;
  line-height: 1;
  margin: 0 0 12px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
  width: 42px;
}

.how-step:hover .how-step__number,
.how-step:focus-within .how-step__number {
  background: #1f2d6b;
  color: #ffffff;
  transform: scale(1.1);
}

.how-step h3 {
  color: #1a1a2a;
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 10px;
}

.how-step p {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

.info-grid {
  padding: 68px 0 56px;
}

.section-title {
  border-left: 3px solid #1f2d6b;
  color: #1a1a2a;
  font-size: 36px;
  font-weight: 800;
  line-height: 1.12;
  margin: 0 0 14px;
  padding-left: 12px;
}

.section-title::after {
  background: #1f2d6b;
  content: '';
  display: block;
  height: 3px;
  margin-top: 8px;
  width: 40px;
}

.info-grid__inner {
  display: grid;
  align-items: start;
  gap: 28px;
  grid-template-columns: 1fr 1fr;
}

.info-block,
.panel {
  background: transparent;
  padding: 0;
}

.info-block {
  padding: 0;
}

.info-summary {
  color: #6b7280;
  font-size: 15px;
  line-height: 1.4;
  margin: 0 0 14px;
}

.info-layout {
  display: block;
}

.info-rows {
  display: grid;
  gap: 0;
}

.resource-row {
  align-items: stretch;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #d5d1ca;
  border-radius: 0;
  box-shadow: 0 0 0 rgba(26, 26, 42, 0);
  color: #6b7280;
  display: grid;
  gap: 14px;
  grid-template-columns: 3px minmax(0, 1fr) 120px;
  min-height: 0;
  padding: 18px 12px;
  text-decoration: none;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.resource-row:hover,
.resource-row:focus-visible {
  border-color: #bab4ab;
  box-shadow: 0 14px 24px rgba(26, 26, 42, 0.14);
  transform: translateY(-4px);
}

.resource-row:hover .resource-accent,
.resource-row:focus-visible .resource-accent {
  filter: saturate(1.12) brightness(1.03);
}

.resource-accent {
  background: linear-gradient(180deg, var(--strip-accent, #d0312d), #1a1a2a);
  border-radius: 999px;
  display: inline-flex;
  height: calc(100% - 6px);
  margin-top: 3px;
  min-height: 80px;
  transition: filter 0.2s ease;
}

.resource-inset {
  align-items: center;
  background: #eef2ff;
  color: #1f2d6b;
  border-radius: 12px;
  display: flex;
  height: 52px;
  justify-content: center;
  width: 52px;
}

.resource-inset--learn {
  background: #eef2ff;
  color: #1f2d6b;
}

.resource-main {
  align-self: center;
  display: grid;
  gap: 8px;
  min-width: 0;
}

.resource-title {
  color: #1a1a2a;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 6px;
}

.resource-copy {
  color: #6b7280;
  font-size: 15px;
  font-weight: 400;
  line-height: 1.35;
  margin: 0 0 6px;
}

.resource-source {
  align-self: start;
  background: transparent;
  border: 1px solid #c9d4ff;
  border-radius: 999px;
  color: #1f2d6b;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  max-width: max-content;
  padding: 4px 10px;
  white-space: nowrap;
  text-transform: uppercase;
}

.resource-media {
  align-self: center;
  border-radius: 8px;
  height: 80px;
  margin: 0;
  overflow: hidden;
  width: 120px;
}

.resource-media img {
  display: block;
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.resource-media--loading {
  background: #f2efe8;
}

.flow-section {
  scroll-margin-top: 112px;
}

.snap-stage {
  align-items: center;
  display: flex;
  min-height: calc(100vh - 52px);
  overflow: clip;
  position: relative;
  --parallax-offset: 0px;
  --stack-scale: 1;
  --stack-dim: 0.08;
  --curtain-progress: 0;
  --curtain-shift: 0;
  scroll-margin-top: 62px;
  scroll-snap-align: start;
  scroll-snap-stop: always;
}

.snap-stage::before {
  background: linear-gradient(
    180deg,
    rgba(26, 26, 42, var(--stack-dim)) 0%,
    rgba(26, 26, 42, calc(var(--stack-dim) * 0.45)) 20%,
    rgba(26, 26, 42, 0) 48%
  );
  content: '';
  inset: 0;
  pointer-events: none;
  position: absolute;
  transform: translateY(var(--parallax-offset));
  transition:
    transform 0.28s ease,
    opacity 0.28s ease;
  z-index: 0;
}

.snap-stage::after {
  background:
    linear-gradient(
      180deg,
      rgba(26, 26, 42, 0.42) 0%,
      rgba(26, 26, 42, 0.22) 46%,
      rgba(26, 26, 42, 0) 100%
    ),
    repeating-linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.08) 0 2px,
      rgba(255, 255, 255, 0) 2px 8px
    );
  content: '';
  inset: 0;
  opacity: calc(var(--curtain-progress) * 0.88);
  pointer-events: none;
  position: absolute;
  transform: translateY(calc(var(--curtain-shift) * 1px))
    scaleY(calc(0.08 + var(--curtain-progress) * 0.92));
  transform-origin: top;
  transition:
    transform 0.26s ease,
    opacity 0.26s ease;
  z-index: 2;
}

.snap-stage .container-shell {
  filter: brightness(calc(1 - var(--stack-dim) * 0.4));
  position: relative;
  transform: translateY(calc(var(--parallax-offset) * -0.24)) scale(var(--stack-scale));
  transform-origin: center top;
  transition:
    transform 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    filter 0.34s ease;
  width: 100%;
  z-index: 1;
}

.snap-stage.reveal-on-scroll {
  --reveal-duration: 0.48s;
  --reveal-y: 18vh;
  opacity: 0;
  transform: translate3d(0, var(--reveal-y), 0) scale(0.95);
}

.snap-stage.reveal-on-scroll.is-visible {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
}

.flow-section--check {
  padding: 76px 0 56px;
  position: relative;
}

.flow-section--check::before {
  background: linear-gradient(to bottom, rgba(242, 239, 232, 0), #f2efe8 78%);
  content: '';
  height: 40px;
  left: 0;
  position: absolute;
  right: 0;
  top: -40px;
}

.preview-band {
  background: #f5f2ee;
  border-bottom: 1px solid rgba(31, 45, 107, 0.16);
  border-top: 1px solid rgba(31, 45, 107, 0.16);
  overflow: hidden;
  padding: 11px 0;
  position: relative;
}

.preview-band--animated::before {
  animation: previewSweep 2.8s ease-in-out infinite;
  background: linear-gradient(120deg, rgba(31, 45, 107, 0.12), rgba(31, 45, 107, 0));
  content: '';
  inset: 0;
  pointer-events: none;
  position: absolute;
}

.preview-band__title {
  color: #1f2d6b;
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.panel {
  padding: 62px 0;
}

.section-copy {
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 22px;
}

.preview-placeholder {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(229, 226, 220, 0.9);
  border-radius: 12px;
  box-shadow: none;
  padding: 22px;
}

.preview-placeholder__subtitle {
  color: #6b7280;
  margin: 0 0 16px;
}

.preview-placeholder__grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.preview-placeholder__card {
  animation: shimmerSkeleton 1.5s ease-in-out infinite;
  background: linear-gradient(90deg, #f2efe8 0%, #e5e2dc 50%, #f2efe8 100%);
  background-size: 200% 100%;
  border-radius: 10px;
  display: block;
  height: 120px;
}

.feature-preview-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.feature-preview {
  align-items: center;
  background: #ffffff;
  border-left: 4px solid #1f2d6b;
  border-radius: 0;
  color: #1a1a2a;
  display: grid;
  gap: 8px;
  min-height: 120px;
  padding: 16px 18px;
  position: relative;
}

.feature-preview h3 {
  color: #1a1a2a;
  margin: 0;
}

.feature-preview span {
  background: transparent;
  border-radius: 0;
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
  padding: 0;
  position: static;
}

.feature-preview-note {
  color: #6b7280;
  margin: 14px 0 0;
}

.site-footer {
  background: #1c2b1e;
  border-top: 0;
  color: #f2efe8;
  padding: 44px 0 46px;
}

.site-footer__inner {
  display: grid;
  gap: 14px;
}

.site-footer__brand {
  align-items: center;
  display: inline-flex;
  font-size: 1.08rem;
  font-weight: 700;
  gap: 10px;
}

.site-footer__summary {
  color: #f2efe8;
  margin: 0;
}

.site-footer__brand img {
  height: 40px;
  object-fit: contain;
  width: auto;
}

.site-footer__links {
  border-bottom: 1px solid rgba(242, 239, 232, 0.2);
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding-bottom: 12px;
}

.site-footer__col--product .site-footer__link-list {
  align-items: center;
  column-gap: 14px;
  display: flex;
  flex-wrap: wrap;
  row-gap: 8px;
}

.site-footer__heading {
  color: #e5e2dc;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  margin: 0 0 8px;
  text-transform: uppercase;
}

.site-footer__link-list {
  display: grid;
  gap: 6px;
}

.site-footer__link {
  color: #f2efe8;
  display: inline-block;
  font-size: 14px;
  line-height: 1.35;
  min-height: 0;
  padding: 0;
  text-decoration: none;
}

.site-footer__link:hover,
.site-footer__link:focus-visible {
  color: #1f2d6b;
  text-decoration: underline;
}

.site-footer__meta {
  color: #f2efe8;
  font-size: 0.86rem;
  margin: 8px 0 0;
}

.site-footer__team {
  align-items: center;
  display: inline-flex;
  gap: 10px;
  justify-content: flex-end;
}

.site-footer__team img:first-child {
  border-radius: 999px;
  height: 40px;
  object-fit: cover;
  width: 40px;
}

.site-footer__team img:last-child {
  height: 22px;
  object-fit: contain;
  width: auto;
}

@keyframes scanSweep {
  0% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(252px);
  }

  100% {
    transform: translateY(0);
  }
}

@keyframes resultFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes statFlip {
  0% {
    opacity: 0;
    transform: rotateX(90deg);
  }

  100% {
    opacity: 1;
    transform: rotateX(0);
  }
}

@keyframes shieldPulse {
  0% {
    opacity: 0;
    transform: scale(0.75);
    transform-origin: 140px 138px;
  }

  25% {
    opacity: 0.8;
  }

  100% {
    opacity: 0;
    transform: scale(1.32);
    transform-origin: 140px 138px;
  }
}

@keyframes shieldGridFlicker {
  0%,
  100% {
    opacity: 0.2;
  }

  50% {
    opacity: 0.85;
  }
}

@keyframes shieldCheckTrace {
  0% {
    stroke-dashoffset: 86;
  }

  40% {
    stroke-dashoffset: 0;
  }

  70% {
    stroke-dashoffset: 0;
  }

  100% {
    stroke-dashoffset: -86;
  }
}

@keyframes shieldSparkle {
  0%,
  100% {
    opacity: 0.25;
    transform: scale(0.9);
    transform-origin: center;
  }

  50% {
    opacity: 1;
    transform: scale(1.25);
    transform-origin: center;
  }
}

@keyframes shimmerSkeleton {
  0% {
    background-position: 0% 50%;
  }

  50% {
    background-position: 100% 50%;
  }

  100% {
    background-position: 0% 50%;
  }
}

@keyframes previewSweep {
  0% {
    opacity: 0;
    transform: translateX(-35%);
  }

  25% {
    opacity: 1;
  }

  80% {
    opacity: 0.1;
    transform: translateX(35%);
  }

  100% {
    opacity: 0;
    transform: translateX(40%);
  }
}

@keyframes previewChipIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes previewFloat {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-5px);
  }
}

@keyframes howDashFlow {
  from {
    stroke-dashoffset: 0;
  }

  to {
    stroke-dashoffset: -56;
  }
}

@keyframes ambientDriftA {
  0% {
    transform: translate3d(0, 0, 0) scale(1);
  }

  50% {
    transform: translate3d(24px, -16px, 0) scale(1.08);
  }

  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
}

@keyframes ambientDriftB {
  0% {
    transform: translate3d(0, 0, 0) scale(1);
  }

  50% {
    transform: translate3d(-28px, 18px, 0) scale(1.05);
  }

  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
}

.reveal-on-scroll {
  --reveal-duration: 0.4s;
  --reveal-ease: ease-out;
  --reveal-x: 0px;
  --reveal-y: 20px;
  opacity: 0;
  transform: translate3d(var(--reveal-x), var(--reveal-y), 0);
  transition:
    opacity var(--reveal-duration) var(--reveal-ease),
    transform var(--reveal-duration) var(--reveal-ease);
  transition-delay: var(--reveal-delay, 0ms);
}

.reveal-on-scroll.is-visible {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.reveal-slide-left {
  --reveal-duration: 0.5s;
  --reveal-x: -40px;
  --reveal-y: 0;
}

.reveal-slide-right {
  --reveal-duration: 0.4s;
  --reveal-x: 30px;
  --reveal-y: 0;
}

.reveal-fade-up {
  --reveal-duration: 0.4s;
  --reveal-y: 20px;
}

.result-section-enter {
  animation: resultFadeIn 260ms ease both;
}

@media (max-width: 980px) {
  .container-shell {
    padding: 0 24px;
  }

  .section-title {
    font-size: 32px;
  }

  .top-strip {
    padding: 8px 14px;
  }

  .top-strip__inner {
    border-radius: 20px;
    max-width: 100%;
    min-height: 43px;
    padding: 7px 16px;
    width: calc(100% - 48px);
  }

  .top-nav-desktop {
    display: none;
  }

  .top-hamburger {
    display: inline-block;
  }

  .top-menu {
    display: block;
    inset: calc(100% + 4px) 24px auto;
  }

  .hero-band__inner,
  .info-grid__inner,
  .feature-preview-grid {
    grid-template-columns: 1fr;
  }

  .preview-band__inner {
    grid-template-columns: 1fr;
  }

  .preview-band__visual {
    justify-self: start;
  }

  .snap-stage {
    min-height: auto;
    scroll-snap-stop: normal;
  }

  .snap-stage::before {
    opacity: 0;
  }

  .snap-stage::after {
    opacity: 0;
  }

  .snap-stage .container-shell {
    filter: none;
    transform: none;
  }

  .resource-row {
    grid-template-columns: 3px minmax(0, 1fr);
    padding: 16px 8px;
  }

  .resource-media {
    grid-column: 2;
    height: 92px;
    margin-top: 8px;
    width: min(180px, 100%);
  }

  .stats-strip__inner,
  .how-grid,
  .preview-placeholder__grid {
    grid-template-columns: 1fr;
  }

  .stats-strip__source {
    padding: 0 24px;
  }

  .how-grid__connector {
    display: none;
  }

  .stat-tile {
    border-right: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.32);
    padding-bottom: 12px;
    padding-right: 0;
  }

  .stat-tile:last-child {
    border-bottom: 0;
    padding-bottom: 0;
  }
}

@media (max-width: 760px) {
  :global(html),
  :global(body) {
    scroll-snap-type: none;
  }

  .top-strip {
    padding: 8px 10px;
  }

  .top-strip__inner {
    min-height: 43px;
    padding: 7px 12px;
    width: calc(100% - 20px);
  }

  .top-menu {
    inset: calc(100% + 4px) 16px auto;
  }

  .stats-strip__source {
    font-size: 0.74rem;
    padding: 0 16px;
  }

  .menu-link,
  .menu-sublink {
    padding: 10px 26px;
  }

  .menu-sublink {
    padding-left: 40px;
  }

  h1 {
    font-size: clamp(2.2rem, 10vw, 3rem);
  }

  .section-title {
    font-size: 28px;
  }

  .hero-band,
  .info-grid,
  .how-it-works,
  .flow-section--check,
  .preview-band,
  .panel,
  .site-footer {
    padding: 42px 0;
  }

  .site-footer__links {
    grid-template-columns: 1fr;
  }

  .site-footer__team {
    justify-content: flex-start;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
  }

  .hero-particles {
    display: none;
  }

  .hero-lottie {
    display: none;
  }

  .hero-lottie-fallback {
    display: block;
  }

  .reveal-on-scroll,
  .reveal-on-scroll.is-visible {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
