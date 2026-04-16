import {
  CLASSIFICATION_CONFIDENCE_THRESHOLD,
  RED_FLAG_RULES,
  TAXONOMY,
  UNKNOWN_TYPE,
} from '../constants/scamRules'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const PYMUPDF_PARSE_ENDPOINT = `${API_BASE}/api/pymupdf/parse`
const ANALYZE_ENDPOINT = `${API_BASE}/api/analyze`

function clampScore(score) {
  return Math.max(0, Math.min(100, score))
}

function getRiskTier(score) {
  if (score >= 80) return 'Critical'
  if (score >= 60) return 'High'
  if (score >= 40) return 'Medium'
  return 'Low'
}

function calculateRiskScore(matches) {
  const baseScore = matches.reduce((sum, item) => sum + item.weight, 0)
  const highCount = matches.filter((item) => item.severity === 'high').length
  const multiplicativeRedFlagBonus = highCount >= 3 ? 12 : 0
  const diversityBonus = matches.length >= 4 ? 6 : 0
  return clampScore(baseScore + multiplicativeRedFlagBonus + diversityBonus)
}

function classifyScamType(matches) {
  const typeScores = Object.fromEntries(TAXONOMY.map((item) => [item, 0]))

  for (const match of matches) {
    for (const [type, vote] of Object.entries(match.typeVotes)) {
      typeScores[type] += vote * match.weight
    }
  }

  const ranking = Object.entries(typeScores).sort((a, b) => b[1] - a[1])
  const [topType, topScore] = ranking[0]
  const totalScore = ranking.reduce((sum, [, score]) => sum + score, 0)
  const confidence = totalScore === 0 ? 0 : topScore / totalScore

  if (topScore === 0 || confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD) {
    return {
      scamType: UNKNOWN_TYPE,
      confidence,
      confidenceThreshold: CLASSIFICATION_CONFIDENCE_THRESHOLD,
    }
  }

  return {
    scamType: topType,
    confidence,
    confidenceThreshold: CLASSIFICATION_CONFIDENCE_THRESHOLD,
  }
}

function buildExplanation(matches, score, scamType) {
  if (!matches.length) {
    return [
      'No strong warning signs were found in this content.',
      'You should still verify the employer through official channels before sharing private information.',
    ]
  }

  const topLabels = matches.slice(0, 3).map((item) => item.label)
  const joinedTopLabels = topLabels.join(', ')
  const signalLabel = matches.length === 1 ? 'warning sign' : 'warning signs'
  const typeLine =
    scamType === UNKNOWN_TYPE
      ? 'The scam type is still unclear because the message does not strongly match one known category.'
      : `This content most closely matches: ${scamType}.`

  return [
    `We found ${matches.length} ${signalLabel}, including ${joinedTopLabels}.`,
    `Risk score is ${score} out of 100 because these signs appeared together.`,
    typeLine,
  ]
}

function extractMatchedPhrases(input, matches) {
  if (!input) return []

  return matches
    .map((rule) => {
      try {
        const flags = rule.pattern.flags.replace(/g/g, '')
        const pattern = new RegExp(rule.pattern.source, flags)
        const found = input.match(pattern)?.[0]?.trim()
        if (!found) return null

        return {
          phrase: found.slice(0, 72),
          severity: rule.severity,
          label: rule.label,
        }
      } catch {
        return null
      }
    })
    .filter(Boolean)
}

function buildAnalysisExcerpt(input) {
  if (!input) return ''
  const normalized = input.replace(/\s+/g, ' ').trim()
  return normalized.slice(0, 340)
}

async function parsePdfByPyMuPDF(pdfFile) {
  const formData = new FormData()
  formData.append('file', pdfFile)

  const response = await fetch(PYMUPDF_PARSE_ENDPOINT, {
    method: 'POST',
    body: formData,
  })

  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    if (response.status === 502) {
      throw new Error(
        'PDF parsing service is unavailable (502). Please make sure the backend API is running on 127.0.0.1:8000.',
      )
    }

    const detail = typeof payload?.detail === 'string' ? payload.detail : ''
    throw new Error(detail || `PyMuPDF parsing failed with status ${response.status}`)
  }

  const text = typeof payload?.text === 'string' ? payload.text.trim() : ''
  if (text) {
    return text
  }

  const warning =
    Array.isArray(payload?.warnings) && payload.warnings.length ? payload.warnings[0] : ''
  const suffix = warning ? ` (${warning})` : ''
  return `[No readable text extracted from "${pdfFile.name}". The file may be image-based or OCR is not available${suffix}.]`
}

function buildPdfExtractionErrorMessage(pdfFile, error) {
  const reason = error instanceof Error ? error.message : 'Unknown parser error'
  return `PDF extraction could not be completed for "${pdfFile.name}": ${reason}.`
}

export function normalizeExtractedContent(rawText) {
  if (typeof rawText !== 'string') return ''
  return rawText.replace(/\u0000/g, '').trim()
}

export function isExtractionDiagnosticMessage(text) {
  return /^PDF extraction could not be completed|^\[No readable text extracted/i.test(text)
}

export function toAnalysisInput(content) {
  const normalized = normalizeExtractedContent(content)
  if (!normalized) return ''

  if (isExtractionDiagnosticMessage(normalized)) {
    return ''
  }

  return normalized
}

export async function extractTextFromSubmission({ inputType, text, link, pdfFile }) {
  if (inputType === 'text') {
    return text.trim()
  }

  if (inputType === 'link') {
    return link.trim()
  }

  if (inputType === 'pdf' && pdfFile) {
    try {
      return await parsePdfByPyMuPDF(pdfFile)
    } catch (error) {
      return buildPdfExtractionErrorMessage(pdfFile, error)
    }
  }

  return ''
}

export function analyzeTextContent(content) {
  const analysisInput = toAnalysisInput(content)
  const matches = RED_FLAG_RULES.filter((rule) => rule.pattern.test(analysisInput))
  const matchedPhrases = extractMatchedPhrases(analysisInput, matches)
  const riskScore = calculateRiskScore(matches)
  const riskTier = getRiskTier(riskScore)
  const typeResult = classifyScamType(matches)
  const suspicious = riskScore >= 40 || matches.length >= 2

  return {
    suspicious,
    riskScore,
    riskTier,
    scamType: typeResult.scamType,
    classificationConfidence: typeResult.confidence,
    classificationConfidenceThreshold: typeResult.confidenceThreshold,
    indicators: matches.map((item) => item.label),
    factors: matches.map((item) => ({
      label: item.label,
      weight: item.weight,
      severity: item.severity,
    })),
    matchedPhrases,
    analysisExcerpt: buildAnalysisExcerpt(analysisInput),
    explanation: buildExplanation(matches, riskScore, typeResult.scamType),
  }
}

function normalizeRiskLevel(level, score) {
  if (level === 'SEVERE') return 'Critical'
  if (level === 'HIGH') return 'High'
  if (level === 'MEDIUM') return 'Medium'
  if (level === 'LOW') return 'Low'
  return getRiskTier(score || 0)
}

function normalizeBackendResult(result) {
  const explanation = Array.isArray(result?.explanation)
    ? result.explanation
    : [result?.explanation || 'No explanation available.']

  const normalizedFactors = Array.isArray(result?.factors)
    ? result.factors.map((item) =>
        typeof item === 'string'
          ? { label: item, weight: null, severity: null }
          : item
      )
    : []

  return {
    ...result,
    riskTier: normalizeRiskLevel(result?.riskLevel, result?.riskScore),
    classificationConfidence:
      result?.classificationConfidence ?? result?.confidence ?? 0,
    classificationConfidenceThreshold:
      result?.classificationConfidenceThreshold ?? 0.33,
    explanation,
    factors: normalizedFactors,
  }
}

export async function analyzeTextContentByBackend(content, metadata = {}) {
  const analysisInput = toAnalysisInput(content)

  if (!analysisInput) {
    return normalizeBackendResult({
      suspicious: false,
      binaryLabel: 'Not suspicious',
      riskScore: 0,
      riskLevel: 'LOW',
      scamType: 'unknown or unclear',
      confidence: 0,
      indicators: [],
      factors: [],
      explanation: 'No readable content was available for analysis.',
      stages: {
        firstContact: false,
        trustBuilding: false,
        taskAssignment: false,
        paymentRequest: false,
        paymentRequestNextLikely: false,
      },
    })
  }

  const payload = {
    inputType: metadata.inputType || 'text',
    text: analysisInput,
    message_type: metadata.message_type || 'Email',
    platform: metadata.platform || 'Gmail',
    job_type: metadata.job_type || 'Remote',
  }

  const response = await fetch(ANALYZE_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  const result = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = typeof result?.detail === 'string' ? result.detail : ''
    throw new Error(detail || `Analyze request failed with status ${response.status}`)
  }

  return normalizeBackendResult(result)
}