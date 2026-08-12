# PHASE: ODYSSEY — RECIPE STEP 2 (waveform "voice")
Tier:    EXAM
Worktree: ZION_ODYSSEY   Branch: odyssey-dev
Owns:    ZION calc-9 (convergence), voice-role lift on the certified RED DAWN signal

## CONTRACT (the handoff)
IN   ← RED DAWN:  certified 27-type cascade signal (direction per month) + the asset price
                  series (for the waveform) + the fold split (train/test) from Stage-2 WF.
OUT  → DECISION:  a **voice verdict** per month = {odyssey_dir, odyssey_conf, waveform_quality,
                  lift_vs_base}. NOT a standalone call. Frozen as `odyssey_voice.csv`.
GATE :  voice-lift is only *reported*; it is admitted to DECISION as one convergence vote only
        where conditional-lift `a1−a0 > 0` at permutation p ≤ .10 (exam_asset.py `voice()` bar).
        Its main value is AT DECISION, not alone.

## ACTIONS  (in order — no step skippable)
1. **Rolling-SD z-score** of N-period returns over SDLB (monthly 36 mo, per CYCLOPS `lib_spy`;
   X used 756/520/252 daily/weekly/monthly). SD is PIT — trailing only, never full-sample.
2. **Fixed 6-bin encode** (`_zbin_fixed`, constant thresholds) → signed bin sequence = the
   waveform "shape". (X's full-sample equiprobable binning was look-ahead — deliberately NOT
   reproduced; keep fixed thresholds.)
3. **Shape match**: last LB=4 bins matched to history via per-position exact/±1/±2 product
   similarity (`_sim_bins`). Forward returns of matches → up-prob → dir + conf.
4. **[NEW] Period/waveform-quality layer** (this is the phase's new work — primitives already
   exist in `HYACINTH_3_RED_DAWN_X.py`, lift them in, PIT-safe):
   a. **# of periods / cycle length** — port `find_optimal_cycle_length` (peak/trough counting,
      min-decline/recovery guards) and/or `_est_natural_cycle` (autocorrelation-peak). Compute
      on TRAIN only; label each test window with its dominant period.
   b. **Composite/average waveform IN TRAIN → applied to TEST** — for each detected period,
      build the train-average waveform (shape + amplitude + momentum), *dynamic* to the training
      window. Score the test window's distance to the current-phase composite.
   c. **Change-of-extremes** — how much each waveform period's extremes (amplitude, momentum)
      change vs the prior period; large regime-shift in the waveform = low quality/low weight.
   d. **[OPTIONAL] Markov** — transition matrix over the 6 bins (or over {rising/falling/extreme}
      states) estimated on TRAIN; next-state direction as an extra vote. Absent everywhere today.
5. **Per-pattern accuracy** — enumerate the distinct waveform patterns (cf. X
   `catalog_all_patterns`) and report OOS hit-rate PER PATTERN. **Goal: isolate the FEW months
   whose waveform quality is genuinely high** — not a blanket signal. Everything else abstains.

## DIAGNOSTICS  (how it proves itself)
- pass criterion (voice): conditional lift `a1(agree) − a0(base) > 0` at perm-p ≤ .10 on fired set.
- [NEW] waveform-quality gate: a month is "strong-waveform" only if (composite-distance below
  train percentile) AND (extremes-change below threshold) AND (per-pattern OOS LB > 0.50).
- emitted: `odyssey_voice.csv`, `waveform_patterns_oos.csv` (per-pattern acc + n), a composite-
  waveform plot per detected period, sign-flip permutation p, Cohen's-d effect size.
- failure mode → if no month clears the quality gate: emit ABSTAIN for the voice (report the near
  misses); do NOT lower the bar. A weak/absent waveform is the honest answer.

## CADENCE  (waveform × frequency)
- MONTHLY : F — full waveform voice + composite-quality score (the primary home).
- WEEKLY  : s — re-read the bin state on weekly bars; report only (weekly waveform is noisier).
- DAILY   : shadow — record the daily bin-state (board condition) beside the monthly read; never
            drives. Consistent with the RECAL shadow→promote rule.

## PROVENANCE / PRIOR ART  (verified in code, 2026-08-12)
- **Shared core, X & CYCLOPS:** rolling-SD → z-score → 6 fixed signed bins → bin-sequence shape
  → fuzzy analogue match. IDENTICAL primitive in both.
- **X (`HYACINTH_4_ODYSSEY.py` TrendaEngine):** runs it STANDALONE — own direction + sign-flip
  permutation p + Cohen's-d + `catalog_all_patterns` (per-pattern up_pct/accuracy). Has amplitude
  as MIN/MED/HIGH z-magnitude; velocity/accel z-cols (`_Z6_vel/_acc`) live in the macro path, NOT
  the bin engine.
- **CYCLOPS (`exam_asset.py voice()`, `deps/lib_spy.py odyssey_signal`):** SAME engine DEMOTED to
  a conditional-lift voice on the certified RED DAWN signal (`lift = a1 − a0`). Dropped X's
  look-ahead equiprobable binning.
- **Already exists but NOT in ODYSSEY / NOT in CYCLOPS** (only in `RED_DAWN_X`): true peak/trough
  extrema + cycle-length counting (`find_optimal_cycle_length:5521`), autocorrelation natural-
  period (`_est_natural_cycle:8965`). These are the primitives ACTION 4 lifts in.
- **Absent everywhere:** composite/average waveform built in train & applied to test; Markov /
  transition matrix; FFT/spectral/phase. ACTION 4 is genuinely new build.
- **Standing cautions (honest):** [[waveform-intraday-hypothesis]] — intraday shape did NOT
  persist (only vol did); [[oracle-tron-detcyc-verdicts]] — DETCYC deterministic-cycle detector was
  REJECTED per prereg. Monthly waveform is different, largely unexplored territory — but the prior
  says treat shape as fragile: **secondary voice only, quality-gated to the few strong months.**
