from backend.services.domain_lookup import normalize_domain_from_url, lookup_domain
from backend.ml.link_inference import predict_link


def analyze_link_input(raw_url: str) -> dict:
    domain = normalize_domain_from_url(raw_url)
    domain_info = lookup_domain(domain)

    link_pred, link_prob = predict_link(raw_url)

    indicators = []
    explanation_parts = []

    if domain_info["found"] and domain_info["is_known_suspicious"]:
        indicators.append("Domain is listed as suspicious in the StepSafe database")
        if domain_info["risk_note"]:
            explanation_parts.append(domain_info["risk_note"])

    elif domain_info["found"] and domain_info["is_known_safe"]:
        indicators.append("Domain is recognized as a known legitimate site")
        explanation_parts.append("The submitted domain matched a known safe record.")

    else:
        indicators.append("Domain is not recognized in the StepSafe database")
        explanation_parts.append("No trusted or suspicious record was found for this domain.")

    if link_pred == 1:
        indicators.append("Link structure matches known suspicious URL patterns")
        explanation_parts.append(f"Link model suspicious probability: {link_prob:.4f}")

    return {
        "domain": domain,
        "domainInfo": domain_info,
        "linkPrediction": int(link_pred),
        "linkProbability": round(link_prob, 4),
        "linkIndicators": indicators,
        "linkExplanation": explanation_parts,
    }