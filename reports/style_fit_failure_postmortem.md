# Style Fit Failure Postmortem

## Incident

Phase 5.2 completed a research-only Universe V2 replay and V1 vs V2 comparison. Engineering replay succeeded, but the final generalization verdict was FAILED_GENERALIZATION.

## What Failed

- The V1 Style Fit conclusion did not survive the Universe V2 qualified research replay.
- Horizon robustness became CONFLICTING.
- Incremental value robustness became CONFLICTING.
- Phase 3 original conclusion still directionally supported = False.
- Phase 3 incremental value still directionally supported = False.

## What Did Not Fail

- Replay completed over 267 replay dates.
- V2 used exactly 16 QUALIFIED_RESEARCH ETFs.
- Only qualified research symbols were used: True.
- QDII included: False.
- Single ETF data source preserved: True.
- No execution or preview code was modified by Phase 5.2 or Phase 5.3.

## Root Cause Assessment

Primary cause: Universe-sensitive methodology. V2 changes the sample composition enough that the Style Fit categories no longer produce stable cross-horizon incremental value.

Supporting causes:

- Universe Shift: V2 replaces broad V1 exposure diversity with a smaller, more concentrated qualified research set.
- BOND Coverage Loss: V2 has no BOND qualified research ETF, so V1 bond support cannot be recovered.
- Style Instability: HIGH_BETA_THEME and COMMODITY_CYCLICAL require special treatment; SECTOR_DEFENSIVE flips direction.
- Regime Instability: NEUTRAL is the most problematic regime.
- Horizon Conflict: 1d, 3d, and 20d conflict with the expected supported-vs-conflict ordering.

## Research Interpretation

The correct interpretation is not that Style Fit is useless. The repository evidence supports a narrower statement: Style Fit is a Universe V1-specific historical finding with qualified cell-level value, but it is not yet a cross-universe generalizable framework.

## What Remains Unknown

- Whether a finer style taxonomy would recover stable behavior.
- Whether longer V2 history would reduce NEUTRAL and horizon instability.
- Whether per-ETF or per-exposure weighting would reduce ETF-day pooling dependence.
- Whether the failure is specific to the 16 qualified V2 ETFs or would persist in a broader Research Universe.

## Governance Decision

- Phase 5.3 = COMPLETE.
- Failure Attribution = COMPLETE.
- Preview Research = NOT_STARTED.
- Formal Execution = BLOCKED.
- Style Fit should be downgraded to Universe V1-specific until future research proves cross-universe robustness.

## Recommended Next Research Posture

Do not proceed to Preview Research. The next phase should be a research design decision, not optimization. Main should choose between freezing Style Fit as a V1-specific research asset or opening a new Style Framework redesign track. The evidence favors redesigning the Style Framework if Style Fit remains strategically important.

