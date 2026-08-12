# PHASE: SANCTUARY — RECIPE STEP 2s · 3 (analogue "voice")
Tier:    EXAM
Worktree: ZION_SANCTUARY   Branch: sanctuary-dev
Owns:    ZION calc-14 (magnitude) + a secondary direction voice; feeds CASSANDRA

## CONTRACT (the handoff)
IN   ← RED DAWN:  certified signal + the asset return panel + fold split (train/test).
OUT  → DECISION:  analogue voice = {analogue_dir, analogue_sim, n_matches, perm_p} + the swept
                  window winner; and → CASSANDRA the direction-conditional analogue LIST for
                  magnitude/range. Frozen as `sanctuary_voice.csv` + `SANCTUARY_ALL_MATCHES.csv`.
GATE :  secondary voice only. Direction admitted at k=2 convergence (RED DAWN ∩ SANCTUARY agree)
        with permutation p ≤ .10; magnitude/range admitted only if it beats drift/zero (VETO else).
        Analogue-class certification floor = 0.40 (macro class = 0.45).

## ACTIONS  (in order)
1. **Window sweep (2s)** — score windows w ∈ {3,4,5,6} by validation-LB (Wilson LB on the VA
   slice); freeze the winner. (CYCLOPS already does this; X used a fixed [3,4,5] blend.)
2. **Similarity kernel** — `(|corr| + cosine)/2` over the window's return vector. (Byte-identical
   in X and CYCLOPS.) `|corr|` = de-meaned shape; cosine = magnitude+sign.
3. **[NEW — broaden the catch, per operator]** make the secondary catch MORE GENERAL than X or
   CYCLOPS, in ranked order of effect:
   a. lower `min_sim` floor 0.55 → 0.40 (single biggest catch-widener);
   b. **scale-invariant kernel** — z-score/normalize each window before cosine, or Spearman rank
      corr, so level/vol differences stop suppressing matches across regimes;
   c. **admit inverted analogues** — use sign-flipped forward returns for high-|corr| mirror
      windows (kernel already half-does this via `abs(corr)`);
   d. relax structural caps — ≥5-match minimum, X's 1–2-mo continuity rule, non-overlap mask;
   e. keep the bin-prefilter OFF (CYCLOPS already dropped it) and drop X's time-decay + VIX/CAPE
      regime shrink multipliers.
4. **[NEW — general waveform quality]** add coarse shape descriptors as *secondary* match
   features (NOT gates): # of periods / dominant period length of the window, average-waveform
   distance (shared with ODYSSEY ACTION 4), amplitude. Purpose: broader catch as a secondary
   signal, not a precise caller.
5. **Verdict** — direction = similarity-weighted mean of forward returns; magnitude → CASSANDRA
   (top-N by similarity, direction-conditional, similarity-weighted forward return → RANGE).

## DIAGNOSTICS
- pass criterion: permutation p ≤ .10 on the fired set AND conditional-lift ≥ 0 as a voice.
- magnitude: CASSANDRA range must beat drift/zero baseline MAE, else VETO (publish tier-
  conditioned RANGE only — never a point target).
- emitted: `sanctuary_voice.csv`, `SANCTUARY_ALL_MATCHES.csv`, per-window validation-LB table,
  permutation p, grade (A–F), forward_dir_pct, best-match window.
- failure mode → most assets are permutation-INSIGNIFICANT (sample grade F, perm_p 1.0). If so:
  contribute nothing to direction; keep only the magnitude/range role where it earns it.

## CADENCE  (analogue × frequency)
- MONTHLY : F — full analogue voice + swept window + CASSANDRA range (primary home).
- WEEKLY  : s — re-rank analogues on the weekly panel; report only.
- DAILY   : N/A — analogue forward horizon is ≥ monthly; no meaningful daily analogue.

## PROVENANCE / PRIOR ART  (verified in code, 2026-08-12)
- **Kernel identical** in X (`HYACINTH_5_SANCTUARY.py:455`) and CYCLOPS (`deps/lib_spy.py:103`,
  `forecast.py:39`): `(|corr|+cosine)/2` on return vectors.
- **X is the NARROW one:** hard SD-bin exact-pattern prefilter (60-mo rolling-SD z, 6 bins, hash
  must match) + 1–2-mo continuity + 0.55 floor + `exp(-0.05·yrs)` time-decay + VIX/CAPE regime
  shrink (×1/×0.8/×0.5). Horizon 3-mo. Ensemble lookback [3,4,5].
- **CYCLOPS is ALREADY more general:** dropped the bin prefilter + shrinkers; just 0.55 floor +
  ≥5 matches; adds the validation-LB window sweep (3–6mo); horizon 1-mo; top-N for magnitude.
- **Waveform qualities:** essentially ABSENT in both (no avg-waveform, no #periods, no per-period
  length, no amplitude/momentum feature). Only "shape" is `|corr|`. ACTION 4 adds them, secondary.
- **Standing verdict (honest):** analogue is permutation-insignificant on most assets — it won
  only Silver's last-10y cell. Its durable value is on **magnitude** via CASSANDRA, not direction
  ([[monthly-price-target-verdict]]: SANCTUARY/CASSANDRA match beats stats for magnitude, p<1e-4).
  Broadening trades precision for coverage → stays a SECONDARY voice, gated by perm/lift.
