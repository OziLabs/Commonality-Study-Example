
import sqlite3
import pandas as pd
import scipy.stats as stats

# 1. Load the CSVs into an in-memory SQL database
conn = sqlite3.connect(':memory:')
pd.read_csv('upstream_data_posted.csv').to_sql('upstream', conn, index=False)
pd.read_csv('downstream_data_posted.csv').to_sql('downstream', conn, index=False)

query = """
SELECT d.Status, u.*
FROM downstream d
JOIN upstream u ON d."Sub-SN" = u."Sub-SN"
"""
df_joined = pd.read_sql_query(query, conn)

# --- STEP 4: ADVANCED COMMONALITY ANALYSIS ---
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
