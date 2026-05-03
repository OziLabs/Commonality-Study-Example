# --- Introduction ---
This is an example of a root cause analysis script across multiple areas/ buildings/ companies. I will be showing how I created the data, prepared the data, and conducted the analysis below. In the real world I would follow the 8D proccess, so before this step, a team would already be formed of the stakeholders in a RACI matrix. After, the problem would be defined such as a failure spike, yield drop, or scrap spike. Then containment would be completed of this area and material.

Below, potentially after a 5 Why Analysis, the root cause investigation really begins in the form of a commonality study: 

# --- Synthetic Dataset Modeling Real World ---
## Importing Packages
```python
# --- STEP 1: IMPORTING PACKAGES ---
import pandas as pd
import numpy as np
import random

# --- SETTINGS ---
# For every module there are 3 sub-components
num_records = 1000  # Number of modules
num_sub_parts = num_records * 3  # Number of sub-parts per module

```

## Generating Upstream Source's Data Synthetically
```python
# --- STEP 2: GENERATE UPSTREAM DATA (The Factory Floor) ---
upstream_list = []
for i in range(num_sub_parts):
    sub_sn = f"SBN{str(i).zfill(8)}"
    pn = random.choice(['PCB0001', 'PCB0002', 'PCB0003'])
    row = {"Sub-SN": sub_sn, "Part Number": pn}
    
    for s in range(1, 11):
        # Baseline measurement is 10.0
        val = np.random.normal(10.0, 0.5)
        
        # INJECT ROOT CAUSE: Station 4 drift
        if s == 4 and random.random() < 0.10:
            val = np.random.normal(15.0, 0.5)
            
        row[f"Station{s} Measurement"] = round(val, 3)
    upstream_list.append(row)

df_u = pd.DataFrame(upstream_list)
df_u.to_csv('upstream_data_posted.csv', index=False)

```


## Generating Downstream Source's Data Synthetically
```python
# --- STEP 3: GENERATE DOWNSTREAM DATA (Test Result) ---
downstream_list = []
for i in range(num_records):
    msn = f"MSN{str(i).zfill(8)}"
    subs = df_u.iloc[i*3 : (i*3)+3]
    
    # Logic: Module fails if any sub-part Station 4 > 13.5
    status = "Pass"
    if (subs["Station4 Measurement"] > 13.5).any():
        status = "Fail"
        
    for sub_sn in subs["Sub-SN"]:
        downstream_list.append({"SN": msn, "Sub-SN": sub_sn, "Status": status})

df_d = pd.DataFrame(downstream_list)
df_d.to_csv('downstream_data_posted.csv', index=False)

```

# --- Data Preparation ---
## Importing Packages
```python
# --- STEP 4: IMPORTING 2ND PACKAGES (NEW FILE) ---
import sqlite3
import pandas as pd
import scipy.stats as stats

# Load the CSVs into an in-memory SQL database
conn = sqlite3.connect(':memory:')
pd.read_csv('upstream_data_posted.csv').to_sql('upstream', conn, index=False)
pd.read_csv('downstream_data_posted.csv').to_sql('downstream', conn, index=False)

```

## Running SQL query 
```python
# --- STEP 4: RUNNING SQL QUERY ---
query = """
SELECT d.Status, u.*
FROM downstream d
JOIN upstream u ON d."Sub-SN" = u."Sub-SN"
"""
df_joined = pd.read_sql_query(query, conn)

```

# --- Commonality Analysis ---
## Running the full analysis

Delta: 
Measures the raw shift in averages between "Fail" and "Pass" groups
$$
\Delta = \bar{x}_{fail} - \bar{x}_{pass}
$$

Sample Z Score (Standard Differnce): 
Measures how many standard deviations the "Fail" average is away from the "Pass" norm 
$$
z_{sample} = \frac{\bar{x}_{fail} - \bar{x}_{pass}}{s_{pass}}
$$

T-Statistic (t):
Determines if the difference is statistically significant (certainty)
$$
t = \frac{\bar{x}_{fail} - \bar{x}_{pass}}{\sqrt{\frac{s_{fail}^2}{n_{fail}} + \frac{s_{pass}^2}{n_{pass}}}}
$$

Sample Correlation Coefficient (r):
Measures the strength of the linear relationship between a measurement and the failure status
$$
r = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n} (x_i - \bar{x})^2 \sum_{i=1}^{n} (y_i - \bar{y})^2}}
$$

```python
# --- STEP 5: RUNNING FULL COMMONALITY ANALYSIS ---
def run_full_analysis(df):
    # Prepare numeric status for correlation (Fail=1, Pass=0)
    df['Status_Numeric'] = df['Status'].map({'Fail': 1, 'Pass': 0})
    meas_cols = [c for c in df.columns if 'Measurement' in c]
    
    results = []

    for col in meas_cols:
        # Split groups
        fail_group = df[df['Status'] == 'Fail'][col]
        pass_group = df[df['Status'] == 'Pass'][col]
        
        # 1. Delta (Size of shift)
        delta = fail_group.mean() - pass_group.mean()
        
        # 2. Z-Score (Weirdness compared to Pass group)
        z_score = delta / pass_group.std() if pass_group.std() != 0 else 0
        
        # 3. P-Value (Certainty)
        t_stat, p_val = stats.ttest_ind(fail_group, pass_group)
        
        # 4. Correlation (Connection strength)
        corr, _ = stats.pearsonr(df[col], df['Status_Numeric'])
        
        results.append({
            "Station": col,
            "Delta": round(delta, 3),
            "Z-Score": round(z_score, 2),
            "P-Value": round(p_val, 5),
            "Correlation": round(corr, 3)
        })

    # Sort by Correlation to float the root cause to the top
    report = pd.DataFrame(results).sort_values(by='Correlation', ascending=False)
    
    print("\n" + "="*70)
    print("ROOT CAUSE COMMONALITY REPORT")
    print("="*70)
    print(report.to_string(index=False))
    
    # Print the Smoking Gun
    top_cause = report.iloc[0]
    print("\n" + "-"*70)
    print(f"CONCLUSION: {top_cause['Station']} is the identified Root Cause.")
    print(f"It shows a Z-Score of {top_cause['Z-Score']} and Correlation of {top_cause['Correlation']}.")
    print("-"*70)

run_full_analysis(df_joined)

```

# --- Conclusion ---
This analysis has now confidently identified Station 4 as the root cause source. Its Z score was 3.66 and P-Value 0.0000. 

Next steps would be designing a systemic solution for this root cause. After validating the design with SMEs, I would begin implementation into the system. 

Post Tasks: Adding controls and poke-yokes to allow this solution to be robust in the long term. Then hosting a final meeting summarizing results and impact, and thanking everyone who helped along the way. 

