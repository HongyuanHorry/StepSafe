from inference import predict_message

sample_payload = {
    "text": "Congratulations! You are selected. Earn $500/day by completing simple tasks from home. Pay onboarding fee to start immediately."
}

row, scam_pred, scam_prob, type_pred = predict_message(sample_payload)

print("Normalized row:")
print(row)

print("\nPrediction:")
print("Scam label:", scam_pred)
print("Scam probability:", scam_prob)
print("Scam type:", type_pred)