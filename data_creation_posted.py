import pandas as pd
import numpy as np
import random

# --- SETTINGS ---
num_records = 1000  # Number of modules
num_sub_parts = num_records * 3

# --- STEP 1: GENERATE UPSTREAM DATA (The Factory Floor) ---
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

# --- STEP 2: GENERATE DOWNSTREAM DATA (Test Result) ---
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
