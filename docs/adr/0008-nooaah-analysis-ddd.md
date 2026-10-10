# 0008. Nooaah Analysis Engine — DDD Subdomain

**Status:** Accepted
**Date:** 2026-10-10
**Deciders:** Hosein, Di

## Context

Project is on branch `refactor/full-ddd` (ADR-0002). `domain/` and
`application/` are alive: entities (`Candle`, `Market`, `Order`), ports
(`ExchangePort`), and use cases (`GetCandlesUseCase`, `ScanMarketsUseCase`)
already follow the dependency rule documented in `AI_PROJECT_GUIDE.md`.

We are adding **Nooaah** (6 letters: two `o`, two `a`) — an analysis
engine that classifies market regimes and builds per-symbol personality
stats (volatility, RSI, trend, volume-z).

Two constraints:

1. Existing bots live in `services/bots/{name}/` with no DDD layering.
   This is acknowledged technical debt. Nooaah is the first bot whose
   core is *analysis* (features, regimes, personality), not *execution*
   (signal in, order out).
2. `domain/analysis/` does not exist (confirmed by `ls` on 2026-10-10).

Naming note: **Nooaah the bot** is distinct from **Nooa the AI
colleague** (team member, per `AI_PRIMER.md`). Similar names, different
things. Recorded here to prevent future confusion.

## Decision

We build Nooaah as a **4-layer DDD subdomain**, not inside `services/`.

Layers (Phase 1 — MVP, no KMeans):

    backend/app/
    ├── domain/analysis/
    │   ├── entities/       ← Regime, PersonalityStats
    │   ├── value_objects/  ← FeatureVector, ClusterLabel
    │   ├── ports/          ← FeatureExtractorPort, RegimeClassifierPort
    │   └── models/         ← feature_math.py (pure: RSI, volatility)
    ├── application/use_cases/
    │   └── analyze_symbol.py  ← AnalyzeSymbolUseCase
    ├── infrastructure/analysis/
    │   └── ta_features.py     ← implements FeatureExtractorPort
    └── presentation/api/v1/
        └── analysis.py        ← GET /v1/analysis/{symbol}

Dependency direction (unchanged, per AI_PROJECT_GUIDE):

    presentation → application → domain
                        ↑
                  infrastructure

Phase 1 (MVP) delivers:
- feature extraction (volatility, RSI, trend, volume-z)
- raw descriptive stats (mean, std, min/max over window)
- simple chart endpoint
- **no classification, no KMeans**

Phase 2 (separate ADR or update to this one) adds KMeans on the same
pipeline.

Rejected:

- `services/analysis/` — doubles the existing debt.
- `app/analysis/` standalone module — simpler, but abandons the DDD
  pattern this branch is explicitly built around.

## Consequences

- Positive:
  - Domain stays pure (no sklearn/numpy/pandas imports).
  - UseCase testable with mocked ports.
  - Swappable classifier (KMeans today, HMM later) — only infra changes.
  - Sets the pattern for future analytical bots.
- Negative:
  - 4 files instead of 1. More upfront work than `services/`.
  - First bot to break the `services/bots/` convention — this ADR is
    the justification.
- Neutral:
  - KMeans deferred; Phase 1 ships earlier with less risk.
  - `services/bots/` debt remains for other bots — out of scope.

## Alternatives

1. **Standalone `app/analysis/` module.** Simpler, still isolated from
   `services/`, but not DDD. Rejected: branch is `refactor/full-ddd`;
   consistency matters more than 1–2 hours saved.
2. **`services/analysis/`.** Fastest. Rejected: doubles debt, and
   Nooaah's logic is the project's analytical core.
3. **Full DDD including KMeans in Phase 1.** Rejected: KMeans tuning
   (K?, scaling?) risks blocking MVP; pipeline first, classifier second.

## Risks

- **Over-engineering for MVP.** Mitigation: Phase 1 deliberately narrow
  (features + stats). If friction appears, fall back to standalone module.
- **Ports premature.** If no second implementation is foreseen,
  `FeatureExtractorPort` may be ceremony. Mitigation: keep the port but
  do not extract a second adapter until HMM is real.
- **Naming collision (Nooaah/Nooa).** Mitigation: this ADR; code
  comments use the full name.
- **Other bots left behind.** Migration of `services/bots/` not done
  here. Risk accepted; tracked in ROADMAP.

## Future Work

1. **Phase 2 — KMeans.** Add `infrastructure/analysis/kmeans_classifier.py`,
   implement `RegimeClassifierPort`, human-label clusters.
2. **Bot wrapper.** If Nooaah needs to trade, add `services/bots/nooaah/`
   that *consumes* the analysis engine. Analysis stays in the subdomain;
   the bot is orchestration only.
3. **Migrate `services/` debt.** Out of scope; separate ADR.

## Update — 2026-10-10: Port-based classifier (two implementations)

After writing this ADR, we discovered `services/regime_detector.py`
already exists — a rule-based classifier using ADX, ATR%, EMA
alignment, and cumulative return, calibrated for 1h crypto.

It is well-written and in active use (see `test_regime_filter.py`).
Rejected the "Phase 1 without classifier" plan. Revised:

- Phase 1 ships TWO classifiers behind `RegimeClassifierPort`:
  - `infrastructure/analysis/rule_based_classifier.py`
    — migrated from `services/regime_detector.py`
  - `infrastructure/analysis/kmeans_classifier.py`
    — new, data-driven, K chosen via silhouette
- Selector via env: `ANALYSIS_CLASSIFIER=rule_based|kmeans`
- Enables A/B comparison on real data (see "Future Work" #2)

Why the revision:

1. Throwing away a working rule-based classifier is wasteful.
2. `RegimeClassifierPort` was flagged as "premature" in Risks — with
   two implementations it becomes justified, not ceremony.
3. The user's goal is "personality of each symbol"; comparing two
   classifiers strengthens the analysis, not weakens it.

All other decisions unchanged. Phase 1 ships both classifiers.

Status: Proposed -> Accepted

## Rollback

No code written yet. If Phase 1 is rejected before merge:

    git reset --hard 024bfd6

(HEAD of `refactor/full-ddd` at time of writing.)

## References

- docs/AI_PROJECT_GUIDE.md — dependency rule
- docs/adr/0002-branch-strategy.md
- docs/adr/0007-websocket-realtime.md — ADR style precedent
- ~/Documents/AI_PRIMER.md — M11 (ADR for every major decision)
- Branch: refactor/full-ddd
