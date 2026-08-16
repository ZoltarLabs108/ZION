"""
audit7.py — the machine truncation-checker (recipe §7.2, standing protocol).

A weekly book is "final" ONLY when every mandated §6 stage returns RAN in the SAME driver that
wrote the ledger, with: (a) the stage executed and wrote a non-empty artifact; (b) NO parameter the
recipe says to SWEEP was hardcoded; (c) the mandated gate for that stage was the one applied.
Any TRUNCATED or MISSING on a mandated stage BLOCKS the "final" label — mirrors the monthly AUDITOR.

This file is intentionally dumb and strict: it judges the STAGE RECORDS the orchestrator hands it.
It cannot be fooled by a sibling script — a stage counts only if it ran in the driver's own walk.
"""
import os

# The mandated §6 pipeline. `swept` = params that MUST be swept (grid length >= 2, else hardcoded).
# `gate` = the exact gate the stage must apply (None = no gate to check).
SPEC = [
    dict(key='preproc',     name='Preproc (PIT-lag + dollar splice)',  tier='mandated', swept=[],    gate=None),
    dict(key='audit0',      name='Stage 0 — data-audit gate',          tier='mandated', swept=[],    gate=None),
    dict(key='hsweep',      name='Stage 0.5 — HORIZON SWEEP',          tier='mandated', swept=['H'], gate=None),
    dict(key='cascade',     name='Stage 1 — grammar27 cascade',        tier='mandated', swept=[],    gate='train-floor+val-winner'),
    dict(key='wf',          name='Stage 2 — expanding WF (train<=t-H)', tier='mandated', swept=[],    gate=None),
    dict(key='convergence', name='Stage 4 — 3-lens RD/ODY/SANC',        tier='mandated', swept=[],    gate='3-lens-unanimous'),
    dict(key='decision',    name='Stage 5 — DECISION',                 tier='mandated', swept=[],    gate='edge-over-drift'),
    dict(key='ledger',      name='Stage 6 — net-of-cost ledger',       tier='mandated', swept=[],    gate=None),
]


def _artifact_ok(path):
    return bool(path) and os.path.exists(path) and os.path.getsize(path) > 0


def audit7(records, driver):
    """records: {key: dict(ran, artifact, swept_grids{param:[...]}, gate_applied, note)}.
       Returns (rows, blocked). rows = list of (name, verdict, detail)."""
    rows = []; blocked = False
    for st in SPEC:
        r = records.get(st['key'])
        verdict, detail = 'RAN', ''
        if r is None or not r.get('ran'):
            verdict, detail = 'MISSING', 'stage did not run in this driver'
        elif not _artifact_ok(r.get('artifact')):
            verdict, detail = 'MISSING', f"no/empty artifact ({r.get('artifact')})"
        else:
            # (b) swept params must not be hardcoded
            for pnm in st['swept']:
                grid = r.get('swept_grids', {}).get(pnm, [])
                if len(grid) < 2:
                    verdict, detail = 'TRUNCATED', f"{pnm} hardcoded to {grid} (must sweep)"
                    break
            # (c) mandated gate must match
            if verdict == 'RAN' and st['gate'] and r.get('gate_applied') != st['gate']:
                verdict, detail = 'TRUNCATED', f"gate '{r.get('gate_applied')}' != mandated '{st['gate']}'"
        if verdict in ('TRUNCATED', 'MISSING') and st['tier'] == 'mandated':
            blocked = True
        rows.append((st['name'], verdict, detail))
    return rows, blocked


def render(rows, blocked, driver, asset):
    w = max(len(n) for n, _, _ in rows)
    out = [f"§7 AUDIT — driver={driver}  asset={asset}", "-"*(w+34)]
    for name, verdict, detail in rows:
        mark = {'RAN': 'ok ', 'SUBSET': '~  ', 'TRUNCATED': 'XX ', 'MISSING': 'XX '}[verdict]
        out.append(f"  [{mark}] {name:<{w}}  {verdict:<9} {detail}")
    out.append("-"*(w+34))
    out.append(f"  RESULT: {'BLOCKED — not final (fix the XX stages)' if blocked else 'ALL CLEAR — eligible for final label'}")
    return "\n".join(out)
