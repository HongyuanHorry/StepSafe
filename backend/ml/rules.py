from typing import Dict, List


# -------------------------------------------------
# StepSafe-aligned taxonomy mapping
# Handover taxonomy:
# - task-based scam
# - job scam
# - payment scam
# - unknown or unclear
# -------------------------------------------------
TYPE_MAPPING = {
    "Task-Based Scam": "task-based scam",
    "Fake Job": "job scam",
    "Advance Fee": "payment scam",
    "Phishing": "unknown or unclear",
    "Legitimate": "unknown or unclear",
}


# -------------------------------------------------
# StepSafe-style rule definitions
# Mirrors the handover concepts:
# - id
# - label
# - regex pattern equivalent logic
# - severity
# - weight
# - typeVotes
# For simplicity, we use keyword checks first.
# -------------------------------------------------
RULES = [
    {
        "id": "high_income_simple_task",
        "label": "Unrealistic earnings for simple tasks",
        "severity": "high",
        "weight": 34,
        "typeVotes": {"task-based scam": 3, "payment scam": 1},
        "keywords": [
            "earn $", "easy money", "simple tasks", "daily payout",
            "fast cash", "watching videos", "reviewing products",
            "reviewing apps", "like posts"
        ],
    },
    {
        "id": "advance_payment",
        "label": "Message contains or implies a payment request",
        "severity": "high",
        "weight": 34,
        "typeVotes": {"payment scam": 3, "task-based scam": 1},
        "keywords": [
            "pay", "payment", "fee", "deposit", "transfer",
            "refundable", "unlock premium", "onboarding fee"
        ],
    },
    {
        "id": "sensitive_info",
        "label": "Requests sensitive personal information",
        "severity": "high",
        "weight": 30,
        "typeVotes": {"unknown or unclear": 2, "job scam": 1},
        "keywords": [
            "bank details", "paypal details", "account number",
            "passport", "id", "salary setup"
        ],
    },
    {
        "id": "trust_building",
        "label": "Gradual trust-building language",
        "severity": "medium",
        "weight": 22,
        "typeVotes": {"job scam": 2, "task-based scam": 1},
        "keywords": [
            "congratulations", "selected", "shortlisted",
            "dear applicant", "exclusive opportunity", "limited slots"
        ],
    },
    {
        "id": "unverified_link",
        "label": "Includes a link that may redirect to an unverified site",
        "severity": "medium",
        "weight": 20,
        "typeVotes": {"payment scam": 1, "task-based scam": 1, "job scam": 1},
        "keywords": [
            "http://", "https://", "www."
        ],
    },
    {
        "id": "unverified_recruiter",
        "label": "Recruiter identity not fully verifiable",
        "severity": "medium",
        "weight": 18,
        "typeVotes": {"job scam": 2},
        "keywords": [
            "@"
        ],
    },
]


def map_model_type_to_stepsafe(model_type: str) -> str:
    return TYPE_MAPPING.get(model_type, "unknown or unclear")


def match_rules(row: Dict) -> List[Dict]:
    """
    Match StepSafe-style warning signs against the normalized row.
    """
    text = str(row.get("text", "")).lower()
    matches = []

    for rule in RULES:
        matched = any(keyword in text for keyword in rule["keywords"])

        # Also use structured features for stronger alignment
        if rule["id"] == "advance_payment" and row.get("has_payment_request", 0) == 1:
            matched = True
        if rule["id"] == "sensitive_info" and row.get("asks_personal_info", 0) == 1:
            matched = True
        if rule["id"] == "unverified_link" and row.get("contains_link", 0) == 1:
            matched = True
        if rule["id"] == "unverified_recruiter" and row.get("contains_email", 0) == 1:
            matched = True

        if matched:
            matches.append(rule)

    return matches


def compute_risk_score(matched_rules: List[Dict]) -> int:
    """
    StepSafe handover logic:
    1. Sum matched warning-sign weights
    2. If high-severity matches >= 3, add 12
    3. If total matches >= 4, add 6
    4. Clamp to 0..100
    """
    base_score = sum(rule["weight"] for rule in matched_rules)
    high_count = sum(1 for rule in matched_rules if rule["severity"] == "high")
    total_count = len(matched_rules)

    if high_count >= 3:
        base_score += 12
    if total_count >= 4:
        base_score += 6

    base_score = max(0, min(100, base_score))
    return base_score


def classify_stepsafe_type(matched_rules: List[Dict], ml_type: str) -> str:
    """
    StepSafe-aligned classification:
    - aggregate weighted typeVotes from matched rules
    - optionally nudge with ML prediction
    """
    vote_totals = {
        "task-based scam": 0,
        "job scam": 0,
        "payment scam": 0,
        "unknown or unclear": 0,
    }

    for rule in matched_rules:
        for scam_type, votes in rule["typeVotes"].items():
            vote_totals[scam_type] += votes

    ml_bucket = map_model_type_to_stepsafe(ml_type)
    if ml_bucket != "unknown or unclear":
        vote_totals[ml_bucket] += 2

    total_votes = sum(vote_totals.values())
    if total_votes == 0:
        return "unknown or unclear"

    top_type = max(vote_totals, key=vote_totals.get)
    confidence = vote_totals[top_type] / total_votes

    if confidence < 0.5:
        return "unknown or unclear"

    return top_type


def detect_stage(row: Dict, predicted_type: str) -> Dict:
    """
    Optional extension beyond the handover.
    Keep it as extra output, not core contract.
    """
    text = str(row.get("text", "")).lower()

    stage1 = any(w in text for w in [
        "job offer", "opportunity", "application", "position",
        "recruiter", "hiring", "shortlisted", "selected"
    ])

    stage2 = any(w in text for w in [
        "congratulations", "selected", "dear", "welcome",
        "official", "limited slots", "exclusive"
    ])

    stage3 = (
        predicted_type == "task-based scam" or
        any(w in text for w in [
            "task", "complete tasks", "training task",
            "reviewing apps", "like posts", "watching videos", "reviewing products"
        ])
    )

    stage4 = (
        row.get("has_payment_request", 0) == 1 or
        any(w in text for w in ["fee", "deposit", "payment", "transfer", "unlock"])
    )

    return {
        "firstContact": stage1,
        "trustBuilding": stage2,
        "taskAssignment": stage3,
        "paymentRequest": stage4,
        "paymentRequestNextLikely": (
            not stage4 and predicted_type in ["task-based scam", "payment scam"]
        )
    }


def build_explanation(binary_label: str, risk_score: int, scam_type: str, matched_rules: List[Dict]) -> str:
    """
    Plain-language explanation field requested by the handover.
    """
    if binary_label == "Not suspicious":
        return "The submitted content does not currently show enough warning signs to be classified as suspicious."

    if matched_rules:
        top_labels = ", ".join(rule["label"].lower() for rule in matched_rules[:3])
        return (
            f"The content was marked as suspicious because it matched several warning signs, "
            f"including {top_labels}. The current risk score is {risk_score}/100 and the most likely category is {scam_type}."
        )

    return (
        f"The content was marked as suspicious based on the model prediction and supporting indicators. "
        f"The current risk score is {risk_score}/100 and the most likely category is {scam_type}."
    )


def build_analysis_response(row: Dict, scam_pred: int, scam_prob: float, type_pred: str) -> Dict:
    """
    Final StepSafe-aligned response for /api/analyze.
    Required by handover direction:
    - suspicious
    - binaryLabel
    - riskScore
    - scamType
    - indicators
    - factors
    - explanation
    """
    matched_rules = match_rules(row)
    risk_score = compute_risk_score(matched_rules)

    # StepSafe suspicious rule from handover, blended with ML prediction:
    # suspicious = ML prediction OR (riskScore >= 40) OR (matched indicators >= 2)
    suspicious = bool(scam_pred) or (risk_score >= 40) or (len(matched_rules) >= 2)

    # Blend ML + StepSafe taxonomy
    stepsafe_type = classify_stepsafe_type(
        matched_rules=matched_rules,
        ml_type=type_pred
    )

    binary_label = "Suspicious" if suspicious else "Not suspicious"

    indicators = [rule["label"] for rule in matched_rules]
    factors = indicators.copy()

    explanation = build_explanation(
        binary_label=binary_label,
        risk_score=risk_score,
        scam_type=stepsafe_type,
        matched_rules=matched_rules
    )

    response = {
        "suspicious": suspicious,
        "binaryLabel": binary_label,
        "riskScore": risk_score,
        "scamType": stepsafe_type,
        "confidence": round(float(scam_prob), 4),
        "indicators": indicators,
        "factors": factors,
        "explanation": explanation,
        # optional extension
        "stages": detect_stage(row, stepsafe_type),
        # useful debug fields while developing
        "matchedRuleCount": len(matched_rules),
        "modelScamProbability": round(float(scam_prob), 4),
        "modelTypeRaw": type_pred,
    }

    return response