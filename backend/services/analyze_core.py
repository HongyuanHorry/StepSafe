from backend.ml.inference import predict_message
from backend.ml.rules import build_analysis_response
from backend.services.link_analysis import analyze_link_input


def analyze_payload(payload: dict) -> dict[str, object]:
    row, scam_pred, scam_prob, type_pred = predict_message(payload)
    result = build_analysis_response(row, scam_pred, scam_prob, type_pred)

    if payload.get("inputType") == "link":
        link_result = analyze_link_input(payload.get("text", ""))

        result["domain"] = link_result["domain"]
        result["domainInfo"] = link_result["domainInfo"]
        result["linkPrediction"] = link_result["linkPrediction"]
        result["linkProbability"] = link_result["linkProbability"]

        result["indicators"] = result.get("indicators", []) + link_result["linkIndicators"]
        result["factors"] = result.get("factors", []) + link_result["linkIndicators"]

        extra_explanation = " ".join(link_result["linkExplanation"]).strip()
        if extra_explanation:
            result["explanation"] = f"{result['explanation']} {extra_explanation}".strip()

    return result