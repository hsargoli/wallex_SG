# 0009. Nooaah ML Stack — LightGBM

**Status:** Accepted
**Date:** 2026-10-11
**Deciders:** Hosein, Di

## Context

ADR-0008 chose rule-based classifier for Nooaah Phase 1. Walk-forward
validation showed it underperforms in ranging regimes (W2: -7.13%,
ranging windows zero trades or losses). Root cause: rule-based gives
false `trending_up` positives in ranging markets.

An ML classifier trained on historical TP/SL outcomes should learn
to distinguish real breakouts from fake ones.

## Decision

Use **LightGBM** for Nooaah's ML classifier.

- Already used in `scripts/ml/pipeline_lgbm.py` (project precedent)
- Fast, low-memory, handles small datasets well
- Feature set: 22 features from `ml_bottom_model.build_features`
- Label: binary (TP-before-SL = 1, else 0) from `pipeline_lgbm.build_label`
- Model file: `data/models/nooaah_lgbm_v1.txt`

Alternative — sklearn RandomForest — rejected because:
- LightGBM is faster and more accurate on tabular data
- Project already had LightGBM pipelines (proven pattern)

## Consequences

- **Positive:** better regime detection, integrates with ADR-0008
  subdomain (`LGBMClassifier` implements `RegimeClassifierPort`)
- **Negative:** new dependency `lightgbm` (this ADR)
- **Neutral:** rule_based stays as fallback if model missing

## Risks

- **Overfitting:** with only ~2500 samples, need train/test split
  and cross-validation. Mitigation: 70/30 split, monitor test vs train.
- **Label leakage:** label is derived from future candles. Use strict
  walk-forward evaluation, never train on data used for test.

## References

- ADR-0008 — Nooaah DDD subdomain
- `scripts/ml/pipeline_lgbm.py` — precedent
- `app/services/ml_bottom_model.py` — feature engineering
