import joblib
import pandas as pd

model = joblib.load("backend/ml/artifacts/label_model_v2.pkl")

sample = pd.DataFrame([{
    "text": "Earn $500/day by completing simple tasks from home. Pay onboarding fee now.",
    "message_type": "Email",
    "platform": "LinkedIn",
    "job_type": "Remote",
    "contains_link": 0,
    "contains_email": 0,
    "has_payment_request": 1,
    "asks_personal_info": 0
}])

pred = model.predict(sample)[0]
prob = model.predict_proba(sample)[0][1]

print("Prediction:", pred)
print("Scam probability:", prob)