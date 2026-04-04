import {
  CLASSIFICATION_CONFIDENCE_THRESHOLD,
  RED_FLAG_RULES,
  TAXONOMY,
  UNKNOWN_TYPE,
} from '../constants/scamRules'

const PYMUPDF_PARSE_ENDPOINT = '/api/pymupdf/parse'

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
  const typeScores = TAXONOMY.reduce((map, item) => ({ ...map, [item]: 0 }), {})

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
      'No strong warning sign was found in this content.',
      'Still verify the employer through official channels before sharing private information.',
    ]
  }

  return [
    `This content triggered ${matches.length} warning sign(s), so the risk score is ${score}.`,
    `Most likely scam type: ${scamType}.`,
    'Do not pay fees and do not share identity or bank details until the employer is verified.',
  ]
}

async function parsePdfByPyMuPDF(pdfFile) {
  const formData = new FormData()
  formData.append('file', pdfFile)

  const response = await fetch(PYMUPDF_PARSE_ENDPOINT, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`PyMuPDF parsing failed with status ${response.status}`)
  }

  const payload = await response.json()
  const text = typeof payload?.text === 'string' ? payload.text.trim() : ''

  if (!text) {
    throw new Error('PyMuPDF returned empty text content')
  }

  return text
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
    } catch {
      const raw = await pdfFile.text()
      return `${pdfFile.name} ${raw}`.trim()
    }
  }

  return ''
}

export function analyzeTextContent(content) {
  const matches = RED_FLAG_RULES.filter((rule) => rule.pattern.test(content))
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
    explanation: buildExplanation(matches, riskScore, typeResult.scamType),
  }
}
