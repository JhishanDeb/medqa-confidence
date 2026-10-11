# PILOT report: mistralai/Mistral-7B-Instruct-v0.3

Pilot uses 20 **train** questions (indices [1899, 2075, 2168, 2309, 2331, 3218, 3384, 3976, 5772, 6085, 6243, 6532, 6845, 6874, 7103, 8013, 8104, 8536, 9585, 10049]). Not part of the study.

## qid 1899 (gold B)

### Rendered CoT prompt

```
<s>[INST] The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 21-year-old man with a recent history of traumatic right femur fracture status post open reduction and internal fixation presents for follow-up. The patient says his pain is controlled with the oxycodone but he says he has been severely constipated the past 4 days. No other past medical history. Current medications are oxycodone and ibuprofen. The patient is afebrile and vital signs are within normal limits. On physical examination, surgical incision is healing well. Which of the following is correct regarding the likely role of opiates in this patient’s constipation?
A. Opiates increase the production and secretion of pancreatic digestive enzymes
B. Opiates increase fluid absorption from the lumen leading to hard stools
C. Opiates decrease the sympathetic activity of the gut wall
D. Opiates activate the excitatory neural pathways in the gut

Think through the problem step by step. Then finish with exactly these two lines:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>[/INST]
```

### Raw greedy CoT output G

```
 Answer: B. Opiates increase fluid absorption from the lumen leading to hard stools
Confidence: 100
```

finish=stop, tokens=28, sample answers=['rption from the lumen leading to hard stools\nConfidence: 100', 'rption from the lumen leading to hard stools\nConfidence: 100', 'ption from the lumen leading to hard stools\n\nConfidence: 100', 'ption from the lumen leading to hard stools\n\nConfidence: 100', 'rption from the lumen leading to hard stools\nConfidence: 100']

### Rendered Direct prompt + prefill

```
<s>[INST] The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 21-year-old man with a recent history of traumatic right femur fracture status post open reduction and internal fixation presents for follow-up. The patient says his pain is controlled with the oxycodone but he says he has been severely constipated the past 4 days. No other past medical history. Current medications are oxycodone and ibuprofen. The patient is afebrile and vital signs are within normal limits. On physical examination, surgical incision is healing well. Which of the following is correct regarding the likely role of opiates in this patient’s constipation?
A. Opiates increase the production and secretion of pancreatic digestive enzymes
B. Opiates increase fluid absorption from the lumen leading to hard stools
C. Opiates decrease the sympathetic activity of the gut wall
D. Opiates activate the excitatory neural pathways in the gut

Reply with exactly these two lines and nothing else:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>[/INST]Answer:
```

Direct p = {'A': 0.0, 'B': 1.0, 'C': 0.0, 'D': 0.0}, letter_mass 1.0000; confidence generation after `Answer: B\nConfidence:` = ' 95'

## qid 2075 (gold B)

### Rendered CoT prompt

```
<s>[INST] The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 45-year-old man comes to the clinic complaining of yellow skin and eyes, loss of appetite, and severe nausea over the last month or so. He drinks 2–3 beers everyday and about 5–6 on the weekend. He does not take any over-the-counter medications. He has smoked one pack of cigarettes every day for the last 20 years but does not use illicit drugs. Additionally, he reports no history of vomiting, abdominal pain, altered bowel habits, or unintentional weight loss. His temperature is 37°C (98.6°F), blood pressure is 135/85 mm Hg, pulse is 78/ min, respiratory rate is 14/ min, and BMI is 19 kg/m2. On physical examination his skin and sclera are icteric, and his abdomen is tender with a mildly enlarged liver. On laboratory investigations:
Complete blood count
Hemoglobin 11 g/dL
MCV 105 µm3
White blood cell 14,000/mm3
Platelets 110,000/mm3
Which of the following liver function analyses is expected in this patient?
A. Alanine aminotransferase (ALT): 1,500 / Aspartate aminotransferase (AST): 1,089 / AST/ALT: 0.73
B. Alanine aminotransferase (ALT): 120 / Aspartate aminotransferase (AST): 256 / AST/ALT: 2.1
C. Alanine aminotransferase (ALT): 83 / Aspartate aminotransferase (AST): 72 / AST/ALT: 0.87
D. Alanine aminotransferase (ALT): 2,521 / Aspartate aminotransferase (AST): 2,222 / AST/ALT: 0.88

Think through the problem step by step. Then finish with exactly these two lines:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>[/INST]
```

### Raw greedy CoT output G

```
 Answer: A
Confidence: 95
```

finish=stop, tokens=11, sample answers=[' Answer: A\n\nConfidence: 95', 'inotransferase (AST): 1,089 / AST/ALT: 0.73\n\nConfidence: 95%', ' Answer: B\n\nConfidence: 95%', "T, which is less consistent with the patient's presentation.", 'te aminotransferase (AST): 256 / AST/ALT: 2.1\nConfidence: 95']

### Rendered Direct prompt + prefill

```
<s>[INST] The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 45-year-old man comes to the clinic complaining of yellow skin and eyes, loss of appetite, and severe nausea over the last month or so. He drinks 2–3 beers everyday and about 5–6 on the weekend. He does not take any over-the-counter medications. He has smoked one pack of cigarettes every day for the last 20 years but does not use illicit drugs. Additionally, he reports no history of vomiting, abdominal pain, altered bowel habits, or unintentional weight loss. His temperature is 37°C (98.6°F), blood pressure is 135/85 mm Hg, pulse is 78/ min, respiratory rate is 14/ min, and BMI is 19 kg/m2. On physical examination his skin and sclera are icteric, and his abdomen is tender with a mildly enlarged liver. On laboratory investigations:
Complete blood count
Hemoglobin 11 g/dL
MCV 105 µm3
White blood cell 14,000/mm3
Platelets 110,000/mm3
Which of the following liver function analyses is expected in this patient?
A. Alanine aminotransferase (ALT): 1,500 / Aspartate aminotransferase (AST): 1,089 / AST/ALT: 0.73
B. Alanine aminotransferase (ALT): 120 / Aspartate aminotransferase (AST): 256 / AST/ALT: 2.1
C. Alanine aminotransferase (ALT): 83 / Aspartate aminotransferase (AST): 72 / AST/ALT: 0.87
D. Alanine aminotransferase (ALT): 2,521 / Aspartate aminotransferase (AST): 2,222 / AST/ALT: 0.88

Reply with exactly these two lines and nothing else:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>[/INST]Answer:
```

Direct p = {'A': 0.4818, 'B': 0.2385, 'C': 0.0052, 'D': 0.2745}, letter_mass 0.9997; confidence generation after `Answer: A\nConfidence:` = ' 99'

## qid 2168 (gold C)

### Rendered CoT prompt

```
<s>[INST] The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 48-year-old woman presents to the physician because of facial flushing and weakness for 3 months, abdominal discomfort and bloating for 6 months, and profuse watery diarrhea for 1 year. She reports that her diarrhea was episodic initially, but it has been continuous for the past 3 months. The frequency ranges from 10 to 12 bowel movements per day, and the diarrhea persists even if she is fasting. She describes the stools as odorless, watery in consistency, and tea-colored, without blood or mucus. She has not been diagnosed with any specific medical conditions, and there is no history of substance use. Her temperature is 36.9°C (98.4°F), heart rate is 88/min, respiratory rate is 18/min, and blood pressure is 110/74 mm Hg. Her physical exam shows decreased skin turgor, and the abdominal exam does not reveal any significant abnormality. Laboratory studies show:
Serum glucose 216 mg/dL (12.0 mmol/L)
Serum sodium 142 mEq/L (142 mmol/L)
Serum potassium 3.1 mEq/L (3.1 mmol/L)
Serum chloride 100 mEq/L (100 mmol/L)
Serum calcium 11.1 mg/dL (2.77 mmol/L)
Her 24-hour stool volume is 4 liters. Which of the following tests is most likely to yield an accurate diagnosis?
A. Urinary 5-hydroxyindoleacetic acid excretion
B. Plasma gastrin level
C. Plasma vasoactive intestinal peptide
D. Plasma glucagon level

Think through the problem step by step. Then finish with exactly these two lines:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>[/INST]
```

### Raw greedy CoT output G

```
 Answer: A. Urinary 5-hydroxyindoleacetic acid excretion

Confidence: 95%

The patient's symptoms, including chronic diarrhea, abdominal discomfort, and weight loss, along with the laboratory findings of hypokalemia, hyponatremia, and a low stool osmolality (which can be inferred from the large stool volume and watery stool consistency) suggest a diagnosis of carcinoid syndrome. This syndrome is associated with the secretion of various hormones, including serotonin, by a neuroendocrine tumor, most commonly a carcinoid tumor of the gastrointestinal tract. Urinary 5-hydroxyindoleacetic acid (5-HIAA) is a metabolite of serotonin and is elevated in carcinoid syndrome. The other options (gastrin, vasoactive intestinal peptide, and glucagon) are not typically associated with the symptoms and laboratory findings presented in this case.
```

finish=stop, tokens=229, sample answers=['ma glucagon level would be more indicative of a glucagonoma.', 'inary 5-HIAA is the most direct test for carcinoid syndrome.', 'tion is the most likely test to yield an accurate diagnosis.', 'Urinary 5-hydroxyindoleacetic acid excretion\nConfidence: 95%', 'is the most accurate diagnostic test for carcinoid syndrome.']

### Rendered Direct prompt + prefill

```
<s>[INST] The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 48-year-old woman presents to the physician because of facial flushing and weakness for 3 months, abdominal discomfort and bloating for 6 months, and profuse watery diarrhea for 1 year. She reports that her diarrhea was episodic initially, but it has been continuous for the past 3 months. The frequency ranges from 10 to 12 bowel movements per day, and the diarrhea persists even if she is fasting. She describes the stools as odorless, watery in consistency, and tea-colored, without blood or mucus. She has not been diagnosed with any specific medical conditions, and there is no history of substance use. Her temperature is 36.9°C (98.4°F), heart rate is 88/min, respiratory rate is 18/min, and blood pressure is 110/74 mm Hg. Her physical exam shows decreased skin turgor, and the abdominal exam does not reveal any significant abnormality. Laboratory studies show:
Serum glucose 216 mg/dL (12.0 mmol/L)
Serum sodium 142 mEq/L (142 mmol/L)
Serum potassium 3.1 mEq/L (3.1 mmol/L)
Serum chloride 100 mEq/L (100 mmol/L)
Serum calcium 11.1 mg/dL (2.77 mmol/L)
Her 24-hour stool volume is 4 liters. Which of the following tests is most likely to yield an accurate diagnosis?
A. Urinary 5-hydroxyindoleacetic acid excretion
B. Plasma gastrin level
C. Plasma vasoactive intestinal peptide
D. Plasma glucagon level

Reply with exactly these two lines and nothing else:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>[/INST]Answer:
```

Direct p = {'A': 0.2583, 'B': 0.7358, 'C': 0.0058, 'D': 0.0002}, letter_mass 1.0000; confidence generation after `Answer: B\nConfidence:` = ' 99'

## Rates

- Greedy answer parse rate: 100.0% (methods {'answer_line': 20})
- Greedy confidence parse rate before recovery: 100.0%; after: 100.0%
- Direct confidence parse rate: 100.0%
- forced_answer: 0.0%; parsed-vs-argmax mismatch: 0.0%
- letter_mass median: CoT 1.000 (min 0.999), Direct 1.000 (min 0.970)
- Truncation: greedy 0.0%, samples 0.0%
- Accuracy (train, 20 q — noisy): CoT 0.45, Direct 0.55
- Output health: {'min_printable_ratio': 1.0, 'max_repeated_line': 1, 'empty_outputs': 0}

## Throughput and projection

- 1.0 s per question (all 6 calls), 223 generated tokens/s
- Setup (install + download + smoke test + load): 9.1 min
- Projected full run (1,273 questions): **0.76 h** (limit 11.0 h) → OK
- The projection is conservative: the full run batches 50 questions per chunk vs 20 here.

## Warnings

- none
