# Retrieval evaluation

Embedding model: `sentence-transformers/all-MiniLM-L6-v2` · Documents: 30 · Chunks: 180 · RAG_MIN_SCORE: 0.35

| # | Question | Expected document | Top result | Top score | Rank of expected |
|---|---|---|---|---|---|
| 1 | what is hb | haemoglobin | haemoglobin | 0.649 | 1 |
| 2 | bad cholesterol | ldl-cholesterol | ldl-cholesterol | 0.616 | 1 |
| 3 | sugar test 3 months average | hba1c | hba1c | 0.537 | 1 |
| 4 | what does MCV mean | mcv-mch-mchc | mcv-mch-mchc | 0.536 | 1 |
| 5 | what is the good cholesterol | hdl-cholesterol | hdl-cholesterol | 0.595 | 1 |
| 6 | what does a reference range mean | reference-ranges-explained | reference-ranges-explained | 0.752 | 1 |
| 7 | why do I need to fast before a blood test | fasting-before-tests | fasting-before-tests | 0.761 | 1 |
| 8 | what is PCV in my blood report | hematocrit | hematocrit | 0.641 | 1 |
| 9 | low platelets meaning | platelets | platelets | 0.572 | 1 |
| 10 | what is TSH | thyroid-panel | thyroid-panel | 0.510 | 1 |
| 11 | kidney function eGFR | creatinine-and-egfr | creatinine-and-egfr | 0.660 | 1 |
| 12 | what are triglycerides | triglycerides | triglycerides | 0.651 | 1 |
| 13 | high potassium level | electrolytes | electrolytes | 0.620 | 1 |
| 14 | SGPT SGOT liver enzymes | liver-function-tests-overview | liver-function-tests-overview | 0.557 | 1 |
| 15 | what does ferritin show | iron-studies-ferritin | iron-studies-ferritin | 0.580 | 1 |
| 16 | neutrophils and lymphocytes percentage | wbc-differential | wbc-differential | 0.667 | 1 |
| 17 | what does a CBC test check | complete-blood-count-overview | complete-blood-count-overview | 0.640 | 1 |
| 18 | what do H and L mean on my report | common-report-abbreviations | how-to-read-a-lab-report | 0.578 | 2 |
| 19 | what is mg/dL | units-of-measurement | units-of-measurement | 0.540 | 1 |
| 20 | sunshine vitamin deficiency test | vitamin-d | vitamin-d | 0.640 | 1 |

**hit@1 = 0.95** · **hit@3 = 1.00** (target ≥ 0.80) · questions = 20

Score distribution (best chunk per question):

- On-topic: min 0.510, median 0.618, max 0.761
- Off-topic: min 0.037, median 0.087, max 0.137

RAG_MIN_SCORE should sit between the highest off-topic score and the lowest on-topic score.
