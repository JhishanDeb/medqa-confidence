# PILOT report: Qwen/Qwen2.5-7B-Instruct

Pilot uses 20 **train** questions (indices [1899, 2075, 2168, 2309, 2331, 3218, 3384, 3976, 5772, 6085, 6243, 6532, 6845, 6874, 7103, 8013, 8104, 8536, 9585, 10049]). Not part of the study.

## qid 1899 (gold B)

### Rendered CoT prompt

```
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 21-year-old man with a recent history of traumatic right femur fracture status post open reduction and internal fixation presents for follow-up. The patient says his pain is controlled with the oxycodone but he says he has been severely constipated the past 4 days. No other past medical history. Current medications are oxycodone and ibuprofen. The patient is afebrile and vital signs are within normal limits. On physical examination, surgical incision is healing well. Which of the following is correct regarding the likely role of opiates in this patient’s constipation?
A. Opiates increase the production and secretion of pancreatic digestive enzymes
B. Opiates increase fluid absorption from the lumen leading to hard stools
C. Opiates decrease the sympathetic activity of the gut wall
D. Opiates activate the excitatory neural pathways in the gut

Think through the problem step by step. Then finish with exactly these two lines:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct><|im_end|>
<|im_start|>assistant

```

### Raw greedy CoT output G

```
Opiates can cause constipation by decreasing the motility of the gastrointestinal tract, which is a primary mechanism of their action. They do not increase pancreatic enzyme production, fluid absorption, or activate excitatory neural pathways in the gut.

Answer: B
Confidence: 95
```

finish=stop, tokens=58, sample answers=['anism of constipation, which is B.\n\nAnswer: B\nConfidence: 90', 'Answer: B\nConfidence: 90', 'se in GI motility and peristalsis.\n\nAnswer: B\nConfidence: 90', 'swer from the options provided is:\n\nAnswer: B\nConfidence: 70', 'sm of opiate-induced constipation.\n\nAnswer: C\nConfidence: 95']

### Rendered Direct prompt + prefill

```
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: A 21-year-old man with a recent history of traumatic right femur fracture status post open reduction and internal fixation presents for follow-up. The patient says his pain is controlled with the oxycodone but he says he has been severely constipated the past 4 days. No other past medical history. Current medications are oxycodone and ibuprofen. The patient is afebrile and vital signs are within normal limits. On physical examination, surgical incision is healing well. Which of the following is correct regarding the likely role of opiates in this patient’s constipation?
A. Opiates increase the production and secretion of pancreatic digestive enzymes
B. Opiates increase fluid absorption from the lumen leading to hard stools
C. Opiates decrease the sympathetic activity of the gut wall
D. Opiates activate the excitatory neural pathways in the gut

Reply with exactly these two lines and nothing else:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct><|im_end|>
<|im_start|>assistant
Answer:
```

Direct p = {'A': 0.0, 'B': 1.0, 'C': 0.0, 'D': 0.0}, letter_mass 1.0000; confidence generation after `Answer: B\nConfidence:` = ' 85'

## qid 2075 (gold B)

### Rendered CoT prompt

```
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

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
Confidence: <a number from 0 to 100: the probability that your answer is correct><|im_end|>
<|im_start|>assistant

```

### Raw greedy CoT output G

```
Let's analyze the patient's symptoms and history step by step:

1. **Symptoms and History**:
   - Yellow skin and eyes (jaundice)
   - Loss of appetite
   - Severe nausea
   - Alcohol consumption (2-3 beers daily, 5-6 on weekends)
   - No history of vomiting, abdominal pain, altered bowel habits, or unintentional weight loss
   - Physical examination: icteric skin and sclera, tender abdomen, mildly enlarged liver

2. **Laboratory Findings**:
   - Hemoglobin: 11 g/dL (normal range: 13.8-17.2 g/dL for men)
   - MCV: 105 µm3 (suggests macrocytic anemia, possibly due to alcohol)
   - WBC: 14,000/mm3 (normal range: 4,000-11,000/mm3)
   - Platelets: 110,000/mm3 (normal range: 150,000-450,000/mm3)

3. **Interpretation**:
   - The patient's symptoms and history suggest liver disease, likely due to alcohol abuse.
   - Elevated liver enzymes (ALT and AST) are expected in liver disease.
   - The AST/ALT ratio is often used to differentiate between hepatocellular and cholestatic liver disease. A ratio >1.5 is more indicative of hepatocellular injury, while a ratio <1.0 is more indicative of cholestatic injury.

4. **Analyzing the Options**:
   - **Option A**: ALT: 1,500, AST: 1,089, AST/ALT: 0.73
     - This suggests a cholestatic pattern, which is less likely given the patient's history and symptoms.
   - **Option B**: ALT: 120, AST: 256, AST/ALT: 2.1
     - This suggests a hepatocellular pattern, which is more consistent with the patient's history of alcohol abuse.
   - **Option C**: ALT: 83, AST: 72, AST/ALT: 0.87
     - This suggests a mild hepatocellular pattern, which is less likely given the severity of symptoms.
   - **Option D**: ALT: 2,521, AST: 2,222, AST/ALT: 0.88
     - This suggests a hepatocellular pattern but with extremely high values, which is less likely given the patient's history and symptoms.

Given the patient's history of alcohol abuse and the presence of jaundice, the most likely liver function analysis is a hepatocellular pattern with elevated ALT and AST, and a ratio that suggests hepatocellular injury.

Answer: B
Confidence: 95
```

finish=stop, tokens=619, sample answers=[' as it shows a high AST/ALT ratio.\n\nAnswer: B\nConfidence: 95', 'with alcohol-related liver injury.\n\nAnswer: B\nConfidence: 95', 'clinical presentation and history.\n\nAnswer: B\nConfidence: 95', 's, option B is the most plausible.\n\nAnswer: B\nConfidence: 95', ' they suggest severe liver damage.\n\nAnswer: D\nConfidence: 95']

### Rendered Direct prompt + prefill

```
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

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
Confidence: <a number from 0 to 100: the probability that your answer is correct><|im_end|>
<|im_start|>assistant
Answer:
```

Direct p = {'A': 0.9717, 'B': 0.0081, 'C': 0.0, 'D': 0.0202}, letter_mass 1.0000; confidence generation after `Answer: A\nConfidence:` = ' 85'

## qid 2168 (gold C)

### Rendered CoT prompt

```
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

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
Confidence: <a number from 0 to 100: the probability that your answer is correct><|im_end|>
<|im_start|>assistant

```

### Raw greedy CoT output G

```
The patient's symptoms and laboratory findings suggest a diagnosis of carcinoid syndrome, which is often associated with a neuroendocrine tumor. The key features include facial flushing, diarrhea, and hypokalemia. The 24-hour stool volume of 4 liters is also consistent with significant fluid loss, which can be seen in carcinoid syndrome due to increased vasoactive intestinal peptide (VIP) secretion from the tumor.

1. **Urinary 5-hydroxyindoleacetic acid excretion (A)**: This test is used to diagnose carcinoid syndrome by measuring the excretion of 5-HIAA, a metabolite of serotonin. However, it is not the most direct test for identifying the cause of the symptoms.
2. **Plasma gastrin level (B)**: Elevated gastrin levels can indicate Zollinger-Ellison syndrome, which is characterized by peptic ulcers and hypersecretion of gastric acid. This does not fit the patient's symptoms.
3. **Plasma vasoactive intestinal peptide (VIP) (C)**: This test is highly specific for diagnosing VIP-secreting tumors, which can cause watery diarrhea, hypokalemia, and hypochloremic metabolic alkalosis. The patient's hypokalemia and hypochloremia are consistent with this diagnosis.
4. **Plasma glucagon level (D)**: Elevated glucagon levels can indicate glucagonoma, which can cause weight loss, diabetes, and diarrhea. However, the hypokalemia and hypochloremia are more indicative of VIP-secreting tumors.

Given the patient's symptoms and laboratory findings, the most likely diagnosis is a VIP-secreting tumor, and the test that is most likely to yield an accurate diagnosis is the plasma vasoactive intestinal peptide level.

Answer: C
Confidence: 95
```

finish=stop, tokens=382, sample answers=['asma vasoactive intestinal peptide\n\nAnswer: C\nConfidence: 95', 'is a key feature of this syndrome.\n\nAnswer: B\nConfidence: 95', ' can cause the symptoms described.\n\nAnswer: C\nConfidence: 95', 'soactive intestinal peptide (VIP).\n\nAnswer: C\nConfidence: 95', 'oactive intestinal peptide (VIP).\n\nAnswer: C\nConfidence: 100']

### Rendered Direct prompt + prefill

```
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

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
Confidence: <a number from 0 to 100: the probability that your answer is correct><|im_end|>
<|im_start|>assistant
Answer:
```

Direct p = {'A': 0.0, 'B': 0.0, 'C': 1.0, 'D': 0.0}, letter_mass 1.0000; confidence generation after `Answer: C\nConfidence:` = ' 85'

## Rates

- Greedy answer parse rate: 100.0% (methods {'answer_line': 20})
- Greedy confidence parse rate before recovery: 100.0%; after: 100.0%
- Direct confidence parse rate: 100.0%
- forced_answer: 0.0%; parsed-vs-argmax mismatch: 0.0%
- letter_mass median: CoT 1.000 (min 1.000), Direct 1.000 (min 1.000)
- Truncation: greedy 0.0%, samples 0.0%
- Accuracy (train, 20 q — noisy): CoT 0.60, Direct 0.65
- Output health: {'min_printable_ratio': 1.0, 'max_repeated_line': 1, 'empty_outputs': 0}

## Throughput and projection

- 2.1 s per question (all 6 calls), 539 generated tokens/s
- Setup (install + download + smoke test + load): 10.5 min
- Projected full run (1,273 questions): **1.18 h** (limit 11.0 h) → OK
- The projection is conservative: the full run batches 50 questions per chunk vs 20 here.

## Warnings

- none
