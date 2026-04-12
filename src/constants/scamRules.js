export const TAXONOMY = ['task-based scam', 'job scam', 'payment scam']
export const UNKNOWN_TYPE = 'unknown or unclear'
export const CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.5

export const RED_FLAG_RULES = [
  {
    id: 'payment-request',
    label: 'Asked for payment or deposit',
    pattern: /(deposit|registration fee|upfront|pay now|transfer|release payment|processing fee)/i,
    severity: 'high',
    weight: 34,
    typeVotes: { 'payment scam': 1.0 },
  },
  {
    id: 'sensitive-information',
    label: 'Requested personal identity or bank details',
    pattern: /(passport|id card|driver license|bank details|account number|tax file|otp)/i,
    severity: 'high',
    weight: 34,
    typeVotes: { 'job scam': 0.8, 'payment scam': 0.2 },
  },
  {
    id: 'urgency-language',
    label: 'Used urgent pressure language',
    pattern: /(urgent|immediately|asap|today only|act now|deadline today)/i,
    severity: 'medium',
    weight: 22,
    typeVotes: { 'job scam': 0.7, 'task-based scam': 0.3 },
  },
  {
    id: 'task-based-pattern',
    label: 'Matched task-based earning pattern',
    pattern: /(simple task|rating task|telegram task|commission per task|like and subscribe)/i,
    severity: 'high',
    weight: 30,
    typeVotes: { 'task-based scam': 1.0 },
  },
  {
    id: 'unrealistic-income',
    label: 'Promised unrealistic easy income',
    pattern:
      /(easy money|guaranteed income|earn\s+\$?\d+\s+(per day|daily|weekly)|no experience needed high income)/i,
    severity: 'medium',
    weight: 20,
    typeVotes: { 'job scam': 0.5, 'task-based scam': 0.5 },
  },
]
