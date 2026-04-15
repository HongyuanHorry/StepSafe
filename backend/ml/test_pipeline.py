from inference import predict_message
from rules import build_analysis_response

sample_payload = {
    "text": "Congratulations! You are selected. Earn $500/day by completing simple tasks from home. Pay onboarding fee to start immediately.",
    "message_type": "Email",
    "platform": "LinkedIn",
    "job_type": "Remote"
}

row, scam_pred, scam_prob, type_pred = predict_message(sample_payload)
result = build_analysis_response(row, scam_pred, scam_prob, type_pred)

print("Normalized row:")
print(row)

print("\nFinal StepSafe-aligned result:")
for k, v in result.items():
    print(f"{k}: {v}")