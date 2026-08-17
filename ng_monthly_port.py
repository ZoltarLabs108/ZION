"""
ng_monthly_port.py — run ONLY the new NatGas config through the ZION monthly clean-OOS machinery
(multiasset_pipeline.run_asset), with the same audit-loop semantics as main(): re-run until clean
(max 3 passes). Writes the standard NatGas_* report files. The port's honest prior: the validated
ASSET_PIPELINE 60.3% came from the older driver (single-split, optimistic by construction — the
whole reason ZION exists); expect the clean number LOWER, possibly ABSTAIN. A null is a result.
"""
import importlib.util, os
import pandas as pd

spec = importlib.util.spec_from_file_location('mp', '/Users/castaglia/Desktop/ZION/multiasset_pipeline.py')
mp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mp)

df = pd.read_csv(mp.PANEL)
df['Date'] = pd.to_datetime(df['Date'])
for c, lag in mp.PUB_LAG.items():
    if c in df.columns: df[c] = df[c].shift(lag)
df['TermSpread_p10'] = df['Term_Spread_10Y_2Y'] + 10.0

os.makedirs(mp.REPORTS, exist_ok=True)
for pass_no in range(1, 4):
    lines, tier_rows, summary, findings, artifacts = mp.run_asset('NatGas', df)
    print(f'--- pass {pass_no}: {len(findings)} audit findings ---')
    for f in findings: print('   ', f)
    if not findings:
        break
mp.write_asset_files('NatGas', lines, artifacts)
print('\n'.join(lines[-40:]))
print('\nsummary:', summary)
