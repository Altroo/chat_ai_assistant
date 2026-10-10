# Shared model training queue

Only one server training process may run at a time. All applications use the same Qwen3.5-0.8B family through Colibri CPU inference. No per-application model download is authorized. Training data is approved synthetic EN/FR metadata, never private records or conversations.

| Order | Scope | Status | Exit gate |
| --- | --- | --- | --- |
| Current | Shared V5: Facturation, Management Projet, Design Workflow | TRAINING; 1,318-step complete epoch | Export, artifact attestation, all 328 frozen cases, performance probe, acceptance report |
| Next | Contracts (`contrat`) | Adapter/UI published disabled; synthetic dataset prepared | Frozen baseline, exact tokenizer preflight, tested adapter, prior training complete; retain existing curricula and regression sets |
| Following | Gestion Magasin (`gestion_magasin`) | Adapter/UI published disabled; synthetic dataset prepared | Reviewed frozen baseline, server preflight, preceding serial stage validated |
| Following | Réservation (`reservation`) | Adapter/UI published disabled; synthetic dataset prepared | Frozen baseline, server preflight and preceding stage validation |

Training progress and loss are not accuracy. Failed acceptance requires investigation and a separately versioned improvement round; it does not justify changing frozen test labels or activating an unaccepted model. Model selection follows measured scores, not automatic preference for the newest checkpoint. Earlier applications must not regress.

The active V5 scripts, datasets and evaluator are pinned by hash. Do not edit them while the run/evaluation is active. Contracts requires extending the runner's declared application allowlist after the active run finishes (or using a separately reviewed version); the current runner intentionally accepts only the original three applications. No Contracts job has been launched.

Management Projet remains disabled. Training/export alone does not authorize replacing the shared production inference process. Colibri upstream PRs remain deferred until the user explicitly resumes them.

The prepared `shared-v6-en-fr` mix has 1,440 training and 198 validation rows, retaining all V5 source rows and adding the 122/30 Contracts rows. Its 78 Contracts held-out cases join the existing 328 frozen cases for 406 total cases. This is preparation only; Exact server tokenizer/Colibri preflight passed all 1,638 rows with maximum 4,977 tokens. Runner scope extension and frozen baseline evaluation remain required.

Application discovery: [Gestion Magasin discovery](AI_GESTION_MAGASIN_DISCOVERY.md) and [Réservation discovery](AI_RESERVATION_DISCOVERY.md). These discovery documents identify native boundaries; companion progress reports distinguish tested adapters from incomplete model acceptance.

Gestion Magasin preparation: 166 training, 30 validation and 90 held-out cases. The proposed `shared-v7-en-fr` mix has 1,606/228 train/validation rows and 496 held-out cases, retaining all earlier curricula. No new training process has been started. See [actual local checks and limitations](AI_GESTION_MAGASIN_PROGRESS.md).

Réservation preparation: 150 training, 30 validation and 84 held-out cases. The proposed `shared-v8-en-fr` mix has 1,756/258 train/validation rows and 580 held-out cases, retaining all prior rows. It is prepared only; no additional training process has started. See [verified local scope and remaining gates](AI_RESERVATION_PROGRESS.md).

The cumulative shared-v8 server tokenizer/Colibri preflight passed all 2,014 rows, covering the unchanged shared-v7 prefix as well. Maximum lengths: 4,744 training/4,977 validation tokens within 8,192. This validates metadata formatting, not model accuracy or successful training. The prepared baselines and serial acceptance gates remain required. [Report](../training/reports/shared-v8-en-fr-preflight.json).
