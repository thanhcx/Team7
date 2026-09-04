# I&O Operations Support Agent — Synthetic Dataset

All data is synthetic. No MSB production data is included.

## Use Case 1 — Application Performance Degradation
Time: 2026-08-25 14:00–14:20
Question: "Internet Banking đang chậm từ khoảng 14:00. Kiểm tra giúp tôi nguyên nhân có thể nằm ở đâu?"
Expected RCA Hypothesis: Application DB connection pool exhaustion / application saturation.

## Use Case 2 — Infrastructure Performance Degradation
Time: 2026-08-26 10:00–10:20
Question: "Internet Banking đang chậm từ khoảng 10:00. Kiểm tra giúp tôi nguyên nhân có thể nằm ở đâu?"
Expected RCA Hypothesis: Storage performance degradation affecting application response time.

## Agent flow
Understand Request → Resolve System/Time → Read Data → Correlate → Retrieve Knowledge → Findings & Evidence → RCA Hypothesis → Recommendation → References → Confidence/Insufficient Evidence
