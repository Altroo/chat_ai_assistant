# Shared model accuracy work

## Latest verified comparison: coverage correction - 21 October 2026

The 176-update server training and all five declared Colibri primary candidates completed. Four checkpoints produced 532 fresh responses across 12 shards; logical zero reuses 133 reviewed actual checkpoint 32 responses. The original coordinator exited successfully. Fresh artifact, adapter, export, stopped-worker and free-port checks passed, and the single reviewer reproduced the completed audit and all 544 evidence hashes. Production inference remains unchanged.

| Logical candidate | Correct actions / 133 | Exact arguments / 111 | Critical / 24 |
| --- | --- | --- | --- |
| 0, cached actual checkpoint 32 | 122 (91.73%) | 100 (90.09%) | 22 |
| 44 | 121 (90.98%) | 99 (89.19%) | 21 |
| 88 | 119 (89.47%) | 97 (87.39%) | 22 |
| 132 | 123 (92.48%) | 101 (90.99%) | 21 |
| 176 | 120 (90.23%) | 98 (88.29%) | 22 |

PARTIALLY IMPLEMENTED: no candidate passes the unchanged primary gates. Diagnostic selection is checkpoint 132: 123/133 full actions (92.48%), 101/111 exact arguments (90.99%), 132/133 correct tools, 133/133 parsed structures, 16/16 clarifications and 21/24 critical cases. Relative to the cached parent, actions and arguments improve by one case but critical cases decline by one. The final checkpoint 176 scores lower at 120/133 actions. Training loss selected logical zero separately and did not rank functional candidates.

The broader 275/438/48 phases were not executed after necessary primary rejection. No new Management Projet, Design Workflow, per-language or native-security acceptance score follows this run. These correlated development cases are not fresh blind certification. Zero of six applications are fully accepted; no new model activation or next-application training occurred.

[Completed comparison and evidence](../training/reports/facturation-factor-coverage-v1-functional-comparison.json).

## Previous verified ordinary-SFT comparison - 21 October 2026

PARTIALLY IMPLEMENTED: the ordinary-SFT correction completed training and all five logical primary candidates, but no candidate passed. Four checkpoints ran 532 fresh Colibri requests; the existing parent 125 supplied 133 explicitly cached cases.

| Candidate | Full actions / 133 | Exact arguments / 111 | Critical / 24 |
| --- | --- | --- | --- |
| Parent 125, cached as 0 | 122 (91.73%) | 102 (91.89%) | 20 |
| 32 | 122 (91.73%) | 100 (90.09%) | 22 |
| 64 | 117 (87.97%) | 95 (85.59%) | 21 |
| 96 | 118 (88.72%) | 96 (86.49%) | 21 |
| 128 | 120 (90.23%) | 98 (88.29%) | 21 |

Checkpoint 32 is the diagnostic functional selection, with 100% tool/parsed-structure accuracy and 16/16 clarifications. Full actions, exact arguments and critical cases still fail. All thresholds, inputs, labels and scoring remain unchanged. Training loss selected 64 separately; loss did not rank the functional candidates.

The single reviewer reproduced raw shards, summaries, results, selection and 392 evidence hashes. Fresh server checks confirm model/adapter integrity, stopped workers, free evaluation ports and unchanged production. Broader 275/438/48 evaluations were not run after primary rejection. These correlated development cases are not fresh blind certification, and parsed structure is not native tool executability.

Zero of six apps are fully accepted. No new per-language, retained-app or native-security acceptance score is claimed, and production inference remains unchanged.

[Detailed measurements, latency and evidence](../training/reports/facturation-uniform-correction-v1-functional-comparison.json).

## Current result: Facturation correction rejected - 20 October 2026

All 128 server training updates and every declared Colibri primary comparison completed. None reaches the required full-action, exact-argument and critical-case gates.

| Candidate | Correct actions | Exact arguments | Structured output | Critical cases |
| --- | --- | --- | --- | --- |
| 0 (actual 125, reused) | 122/133 (91.73%) | 102/111 (91.89%) | 132/133 | 20/24 |
| 32 | 119/133 (89.47%) | 98/111 (88.29%) | 132/133 | 21/24 |
| 64 | 118/133 (88.72%) | 96/111 (86.49%) | 133/133 | 21/24 |
| 96 | 117/133 (87.97%) | 95/111 (85.59%) | 133/133 | 21/24 |
| 128 | 118/133 (88.72%) | 96/111 (86.49%) | 133/133 | 21/24 |

Logical 0 reuses the unaccepted experimental checkpoint 125; it is not the production model. All four new checkpoints regress against it. The 275 shared development, 438 regression and 48 additional-control cases were not executed after primary rejection. This run establishes no new Management Projet or Design Workflow acceptance result.

Zero of six applications are fully accepted by the current campaign. Production inference remains healthy and unchanged. Facturation stays the focus; remaining apps train sequentially after acceptance. These inspected, correlated primary cases are not fresh blind certification. The original 3,103-update refinement and this separate 128-update correction must not be conflated.

[Completed correction results](../training/reports/facturation-semantic-correction-v2-functional-comparison.json).

## Historical R11 evaluation - 16 October 2026

IMPLEMENTED and verified: all 2,419 R11 training updates, five saved-checkpoint development comparisons, 438 regressions and 48 additional English/French controls completed. The frozen development rule selected step 2400. Independent verification binds every scored event to its original worker log and selected artifact proofs. The selected FP32 base still has the same 473 F32 tensors. All temporary workers stopped and production inference remains unchanged.

| Application | Fully correct regression actions | Exact regression arguments | Additional controls: full actions |
| --- | ---: | ---: | ---: |
| Facturation | 97/108 (89.81%) | 75/86 (87.21%) | 7/16 (43.75%) |
| Management Projet | 193/200 (96.50%) | 143/148 (96.62%) | 15/16 (93.75%) |
| Design Workflow | 118/130 (90.77%) | 88/100 (88.00%) | 14/16 (87.50%) |

Acceptance FAILED. No application passes all required model gates. Management Projet's larger-suite averages exceed 95%, but its critical/subset checks and additional controls still fail. Only 3/15 regression sets pass all gates. These are planner measurements, not authorization or production-readiness certification. The 16 additional cases per application are small team-authored bilingual controls and are reported separately; they are not a population-accuracy estimate.

The model is still the same shared Qwen3.5-0.8B, served by Colibri. The next run focuses only on Facturation with 1,047 training rows and 133 unchanged validation rows. The 35-update focused server rehearsal and bounded Colibri export comparison are verified. The full 1,047-update Facturation epoch is now running from the original selected model. No new acceptance score is available. Management Projet and Design Workflow regression checks remain mandatory. Contracts, Gestion Magasin and Reservation are prepared but untrained. There are zero accepted applications from the six-app training campaign.

[Completed R11 evaluation](../training/reports/shared-v5r11-en-fr-evaluation.json), [development comparison](../training/reports/shared-v5r11-functional-validation.json), [focused preparation](../training/reports/facturation-focus-v1-preparation.json).

The following sections are historical observations, not the current job state.

## R8 preparation and fresh baseline: 2026-10-14

Server training started at 10:17 UTC with 14 CPU threads after metadata and capacity checks passed. The automatic checkpoint/evaluation controller is running. Training and post-training acceptance remain incomplete. [Launch evidence](../training/reports/shared-v5r8-launch.json).

R8 means revision eight of the shared training experiment, not a new foundation model. It continues from the R7 step-1200 Qwen3.5-0.8B candidate. The curriculum retains every R7 training/validation row and adds 274 native-verified English/French examples, for 2,339 training rows and 275 validation rows.

Before R8 optimization, the unchanged candidate completed 48 newly authored controls using the same frozen Colibri runtime, provider and inference settings. These are 24 bilingual scenarios, eight per application. They expose a generalization gap beyond the repeatedly inspected 438-case regression suite:

| Application | Correct tools | Eligible exact arguments | Valid structure | Fully matched actions |
| --- | ---: | ---: | ---: | ---: |
| facturation | 16/16 (100%) | 2/14 (14.29%) | 16/16 (100%) | 4/16 (25%) |
| management_projet | 16/16 (100%) | 8/10 (80%) | 16/16 (100%) | 14/16 (87.5%) |
| design_workflow | 15/16 (93.75%) | 8/12 (66.67%) | 16/16 (100%) | 12/16 (75%) |
| Combined | 47/48 (97.92%) | 18/36 (50%) | 48/48 (100%) | 30/48 (62.5%) |

These small, correlated samples are implementation-team controls, not blind external certification or population accuracy estimates. They remain excluded from optimization and checkpoint selection. The curriculum was frozen before these baseline results; it was not adjusted to match their failures. The original regression scores below remain unchanged.

All temporary baseline workers stopped. Model/runtime identities matched before and after, and production remained unchanged. No business tools executed. R8 accuracy has not been measured after optimization. Only the fixed 275-row validation set selects a checkpoint; the selected changed candidate must then pass both the original regressions and these fresh controls, reported separately.

[Fresh baseline and evidence hashes](../training/reports/shared-v5r8-baseline.json), [curriculum](../training/datasets/shared-v5r8-en-fr/manifest.json), [selection policy](../training/reports/shared-v5r8-checkpoint-selection-policy.json).

## Prior completed round

PARTIALLY IMPLEMENTED: R7 training and evaluation completed on 2026-10-14, but model acceptance FAILED. All 2,065 server training steps and seven saved-checkpoint comparisons completed; the predeclared functional rule selected step 1200. On 438 V2 regression cases: 427/438 correct tools (97.49%), 313/334 eligible exact arguments (93.71%), 435/438 valid structures (99.32%) and 413/438 fully matched actions (94.29%). Only 4/15 sets pass every gate; six critical model cases fail. All three evaluation workers stopped, artifact identities matched before/after, and production stayed unchanged. Management Projet remains disabled. Contracts, Gestion Magasin and Reservation training remain queued behind shared-model acceptance. [Measured R7 report](../training/reports/shared-v5r7-en-fr-evaluation.json).

IMPLEMENTED and verified: the queued R8 preparations retain every byte of the current shared curriculum and append the existing reviewed synthetic examples for each later application. Contracts V6r8 contains 2,492 training / 319 validation / 564 evaluation cases; Gestion Magasin V7r8 contains 2,690 / 362 / 654; Reservation V8r8 contains 2,870 / 402 / 738. Each evaluation total includes the 48 fresh controls, which remain excluded from optimization and checkpoint selection and must be reported separately from the original regressions. Thirteen retention, scope and trainer-startup tests pass. Metadata checks pass all 3,272 cumulative training/validation rows and 738 evaluation envelopes using the server-matching tokenizer and Colibri template/parser, without local model weights or inference. The sole reviewer found no source issues. These are preparations, not trained models; each stage still requires its exact accepted predecessor, a frozen baseline and server admission checks. [Metadata evidence](../training/reports/shared-v8r8-en-fr-metadata-preflight.json).

Management Projet remains disabled in production by explicit user instruction. This work uses the existing shared Qwen3.5-0.8B checkpoint and Colibri CPU runtime; no new foundation model or application-specific model is downloaded. Production weights, permissions and financial calculations remain unchanged.


## R7 completed results: 2026-10-14

Training completed all 2,065 steps on the server. The seven saved checkpoints each completed the same 275-case validation evaluation; the prior baseline predictions were reused with matching bindings. Step 1200 was selected by the predeclared application-macro action rule, with 242/275 validation actions correct. The loss-only checkpoint was step 600; loss and action accuracy are different measurements.

The selected checkpoint then completed 438 English/French V2 regression cases. Relative to the matching R7 baseline, correct tools improved from 415 to 427, exact arguments from 306/334 to 313/334, and fully matched actions from 394 to 413. Valid structures remained 435/438. The baseline reused 435 identical results and freshly measured three corrected cases; all 438 candidate results are fresh, so no combined baseline latency claim is made.

| Application | Correct tools | Exact arguments | Valid structure | Fully matched actions | Critical model failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| facturation | 105/108 (97.22%) | 74/86 (86.05%) | 108/108 (100%) | 96/108 (88.89%) | 0 |
| management_projet | 193/200 (96.50%) | 142/148 (95.95%) | 197/200 (98.50%) | 190/200 (95.00%) | 5 |
| design_workflow | 129/130 (99.23%) | 97/100 (97.00%) | 130/130 (100%) | 127/130 (97.69%) | 1 |

**Acceptance FAILED.** Only four of fifteen frozen sets pass every gate. Management Projet's remaining critical cases include unsupported supplier-specific financial requests and choosing the wrong saved client for an edit. Design Workflow's remaining critical case returns a translated priority label instead of the required tool value. Facturation still misses combined filters, strict-before dates, operational statuses and financial intent. These are model-planning failures; this evaluator executes no business operations and does not establish an authorization bypass.

Before/after model, provider and runtime proofs match; all three temporary workers stopped and their ports closed. The original production assistant remained healthy with unchanged start time. No later-app training or model activation occurred. No separate R7 performance benchmark was run. Original benchmark results and labels remain preserved.

[Recomputed results, per-set gates and evidence hashes](../training/reports/shared-v5r7-en-fr-evaluation.json).

## V5r6 measured results — 2026-10-13

Server training completed all 1,969 steps in 15 hours 43 minutes, using 14 CPU threads and 7.65 GiB peak RSS. Step 1800 was selected by application-macro validation loss; the final-step loss did not improve it. Export succeeded. An exact interpreter-path check stopped the first evaluation handoff before any requests; separately reviewed recovery preserved that evidence and completed the unchanged suite without retraining.

**Acceptance FAILED: 420/438 correct tools (95.89%), 305/334 eligible exact arguments (91.32%) and 438/438 valid structures (100%).** R5 scored 92.69%, 89.52% and 98.17% respectively. Fully matched actions improved from 376/438 to 397/438, but only 3/15 sets pass all gates. Critical model cases match 135/150 and clarification reason/language matches 78/90. No business tools execute in this evaluator; these are planner failures, not measured authorization bypasses.

| Application | Correct tools | Eligible exact arguments | Valid structure |
| --- | ---: | ---: | ---: |
| design_workflow | 129/130 (99.23%) | 90/100 (90.0%) | 130/130 (100.0%) |
| facturation | 105/108 (97.22%) | 73/86 (84.88%) | 108/108 (100.0%) |
| management_projet | 186/200 (93.0%) | 142/148 (95.95%) | 200/200 (100.0%) |

Management Projet's argument score improved, while its tool score remains below target. Design Workflow's exact-argument result regressed from 94/100 in R5 to 90/100 in R6. Better aggregate scores do not establish acceptance or allow a production replacement.

The unchanged eight-request warm probe measured 7.756s sequential mean (7.919s observed P95), 11.639s concurrency-two mean (15.845s observed P95), 55.71 decode tokens/s excluding prefill and 2.73 GiB peak process RSS. Four requests per group are a small measurement, not production capacity certification. Two other identical workers remained loaded and idle during the probe. All eight requests completed without errors; all three workers then stopped. Production remained unchanged.

The exact report publisher checks published recovery-control hashes, frozen inputs, reconstructed scores, stopped-worker evidence and the original performance payload/input/script hashes. Three offline mutation tests pass and the single reviewer found no remaining issues after two evidence checks were strengthened.

The eight-checkpoint comparison below is complete and selects step 1969. Its separate unchanged 438-case acceptance evaluation also failed, as recorded below; the scores above belong to the original step-1800 candidate. Contracts, Gestion Magasin and Réservation training remain pending.

Evidence: [accuracy](../training/reports/shared-v5r6-en-fr-evaluation.json), [training and selection](../training/reports/shared-v5r6-en-fr-training.json), [isolated performance](../training/reports/shared-v5r6-en-fr-performance.json).

## V5r6 completed checkpoint comparison — 2026-10-13

All 2,200 Colibri requests completed: the unchanged 275-row validation split for eight predetermined checkpoints. It contains 222 underlying scenarios, including 53 correlated history variants. The frozen rule selects **step 1969**, primarily by application-macro action accuracy; the grouped score is a separate diagnostic and does not change that rule.

| Step | Fully matched actions | Application-macro accuracy | Scenario-grouped macro accuracy |
| --- | ---: | ---: | ---: |
| Baseline (0) | 227/275 | 85.39% | 85.41% |
| 300 | 228/275 | 85.29% | 85.77% |
| 600 | 229/275 | 85.54% | 85.52% |
| 900 | 229/275 | 86.34% | 86.94% |
| 1200 | 225/275 | 85.87% | 85.84% |
| 1500 | 218/275 | 82.50% | 82.45% |
| 1800 | 223/275 | 84.11% | 84.01% |
| **1969** | **231/275** | **86.65%** | **86.74%** |

At step 1969, action matches are Facturation 100/133, Management Projet 71/78 and Design Workflow 60/64. Valid structures are respectively 131/133, 75/78 and 64/64. These are validation results, not the held-out tool/exact-argument scores or authorization tests.

All candidate artifacts/process identities matched before and after; all temporary comparison workers stopped and production remained unchanged. The publisher recomputed all 24 result shards, fixed selection and worker-stop evidence. Three publisher tests passed, including changed-control and invalid-control-list subcases; one reviewer found no issues.

The selected candidate completed its separate unchanged acceptance and performance suite below. The previously inspected frozen suite remains a regression benchmark, not a fresh blind certification.

Evidence: [complete comparison](../training/reports/shared-v5r6-functional-validation.json), [frozen policy](../training/reports/shared-v5r6-checkpoint-selection-policy.json).

## V5r6 selected-checkpoint acceptance — 2026-10-13

**Acceptance FAILED:** step 1969 completed all 438 cases and eight performance requests. Tool selection is 415/438 (94.75%), eligible exact arguments 308/334 (92.22%), structured validity 435/438 (99.32%) and fully matched actions 396/438 (90.41%). Only 3/15 frozen sets pass all gates. Critical actions match 130/150; clarification reason/language matches 74/90. Compared with step 1800, three more eligible argument cases pass, but five fewer tool choices and five fewer critical actions match. No promotion follows this result.

| Application | Correct tools | Eligible exact arguments | Valid structure |
| --- | ---: | ---: | ---: |
| design_workflow | 127/130 (97.69%) | 92/100 (92.0%) | 129/130 (99.23%) |
| facturation | 105/108 (97.22%) | 73/86 (84.88%) | 108/108 (100.0%) |
| management_projet | 183/200 (91.5%) | 143/148 (96.62%) | 198/200 (99.0%) |

The unchanged four-thread probe measured 7.870s sequential mean (8.028s observed P95), 11.838s concurrency-two mean (16.069s observed P95), 55.57 decode tokens/s excluding prefill and 2.74 GiB peak RSS. All eight requests completed without errors. Four requests per group are a small warm sample, not capacity certification; native tool-call buffering prevents treating first-visible-event latency as raw time to first token. Two other workers remained loaded and idle during this probe.

Artifact and process identities matched before/after; all three acceptance workers stopped. The publisher reconstructed frozen scores and checked transitive control hashes, performance provenance and stop evidence. Five preparatory publisher tests passed; one reviewer found no remaining issues after provenance checks were strengthened. Original step-1800 results are preserved. Production weights and application feature flags remain unchanged.

The separate precision diagnostic completed all 60 outcome-independently selected validation scenarios, 20 per application. With the same step-1969 weights, dense int8 enabled and disabled each match 47/60 actions and produce 58/60 valid structures. Facturation changes from 12/20 to 11/20 action matches; Management Projet from 18/20 to 19/20; Design Workflow stays 17/20. Paired outcomes: 45 correct in both, two correct only with int8, two correct only with dense int8 disabled and 11 incorrect in both. Eight outputs differ. This validation sample is separate from the 438-case acceptance suite.

The loader with dense int8 disabled initially left its OpenMP pool at one thread. The initial attempt stopped before any scored request; reviewed recovery used three unscored one-token warmups and retained all exact four-thread and artifact checks. All 60 cases then completed; all three workers stopped. Four report mutation tests passed and the sole reviewer found no remaining issues. No controlled throughput probe with dense int8 disabled was run. This small diagnostic shows no overall accuracy gain from changing precision; it neither proves equivalence nor establishes model acceptance. Production remains unchanged. [Paired precision evidence](../training/reports/shared-v5r6-precision-diagnostic.json). The exported model contains 474 FP16 tensors, verified against the evaluated weight hashes. Disabling dense int8 uses FP32 computation from those exported values; it does not restore the original unrounded FP32 training weights. The historical report field `candidate_full_precision` refers to this int8-disabled mode. [Storage precision clarification](../training/reports/shared-v5r6-precision-storage-note.json).

Evidence: [selected accuracy](../training/reports/shared-v5r6-selected-en-fr-evaluation.json), [selected performance](../training/reports/shared-v5r6-selected-en-fr-performance.json).

IMPLEMENTED — framework reference complete: all twelve fixed development scenarios ran successfully with the same 474 FP16-rounded exported tensors and pinned configuration. The training framework and Colibri with dense int8 disabled return identical actions/errors on all twelve: eight correct and four incorrect. Normal Colibri dense-int8 mode previously matched nine of these twelve. All three modes produced twelve valid structures. This small diagnostic finds no overall framework advantage and does not establish acceptance or complete numerical equivalence. Production remains unchanged; no training or business operation ran. [Paired framework evidence](../training/reports/shared-v5r6-framework-reference.json).

## Shared core 0.2.3 deployment — 2026-10-13

Application-neutral English/French clarification wording is deployed and verified in all six apps. Package files, health, migrations and all three remote heads match; business-table counts, volumes, settings and the production model remain unchanged. This wording update makes no model-accuracy claim and does not change the frozen evaluation renderer. [Deployment evidence](../training/reports/core-0.2.3-release.json).

IMPLEMENTED — R7 starting baseline measured: 50 changed cases were requested afresh, with 228 byte-identical validation and 435 byte-identical evaluation cases reused under the same step-1969 model, runtime, provider and settings. V2 validation matches 231/275 actions (86.83% application macro). The separately versioned V2 evaluation remains below target: 415/438 correct tools (94.75%), 306/334 exact arguments (91.62%), 435/438 valid structures (99.32%) and 394/438 fully matched actions; 2/15 sets pass. These are baseline results before R7 optimization, not training improvements. All temporary workers stopped and production remains unchanged. Original V1 scores are preserved; no combined latency claim is made. [Baseline and reuse evidence](../training/reports/shared-v5r7-baseline.json).

## R7 reviewed dataset preparation — 2026-10-13

PARTIALLY IMPLEMENTED — next training preparation: `shared-v5r7-en-fr` contains 2,065 training and 275 validation examples for the same three applications. It replaces twelve reviewed inconsistent instructions at their original indices, retains the other 1,957 parent rows byte-for-byte and appends 96 reviewed saved-selection context contrasts. The separately versioned V2 validation clarifies 47 rows without changing their targets. Original V1 training, validation and evaluation files remain unchanged; both 438-case evaluation versions are bound by hash.

Six integrity tests pass. All 2,340 training/validation rows pass schema, tokenizer, Colibri-template/parser and loss-boundary checks; maximum lengths are 7,662 training and 7,496 validation tokens within 8,192. The sole reviewer found no remaining issues. No weights were loaded locally during dataset preparation and no accuracy gain was claimed. Server metadata and capacity checks subsequently passed; R7 training has now started as recorded above. [Prepared dataset](../training/datasets/shared-v5r7-en-fr/manifest.json), [metadata evidence](../training/reports/shared-v5r7-en-fr-metadata-preflight.json).

## V5r5 measured results — 2026-10-12

Server-only training and export completed: 1,803 optimizer steps and 275 validation examples in English/French. The selected adapter is step 600, with application-macro validation loss 0.070752 (baseline 0.130523). Final step 1,803 had 0.077062 and was not exported. Training took 14.73 hours, using 14 CPU threads and 7.70 GiB peak RSS.

All 438 frozen accuracy cases completed. **Acceptance FAILED: 406/438 correct tools (92.69%), 299/334 eligible exact arguments (89.52%) and 430/438 valid structures (98.17%).** The 95% tool/argument and 99% structure targets, clarification checks, critical cases and per-set gates are unchanged. The model remains unpromoted. Backend authorization tests are separate from planner scores.

| Application | Correct tools | Eligible exact arguments | Valid structure |
| --- | ---: | ---: | ---: |
| design_workflow | 127/130 (97.69%) | 94/100 (94.0%) | 130/130 (100.0%) |
| facturation | 99/108 (91.67%) | 70/86 (81.4%) | 105/108 (97.22%) |
| management_projet | 180/200 (90.0%) | 135/148 (91.22%) | 195/200 (97.5%) |

At the user's request, the remaining accuracy groups used three temporary four-thread Colibri workers sharing identical model artifacts, for 12 CPU threads total. Previously completed results were preserved; every worker's identity/artifacts and output hashes were verified. Parallel-suite latency is not a matched speedup result. No new model was downloaded. Sidecars were stopped before the final four-thread performance probe.

The separate eight-request warm sample measured 7.631s sequential mean, 11.462s at concurrency two, 56.11 decode tokens/s excluding prefill, and 2.65 GiB peak process RSS. Four requests per group do not establish production load capacity.

Evidence: [accuracy](../training/reports/shared-v5r5-en-fr-evaluation.json), [training and selection](../training/reports/shared-v5r5-en-fr-training.json), [isolated performance](../training/reports/shared-v5r5-en-fr-performance.json). Further model improvement remains required before Contracts → Gestion Magasin → Réservation training; no later job has started.

## Saved-checkpoint functional comparison — 2026-10-12

All 825 requests completed using three four-thread Colibri workers. The unchanged 275-row validation split was evaluated for each saved adapter. Selection rules and input hashes were frozen before inference.

| Saved step | Fully matched actions | Application-macro action accuracy | Scenario-grouped application-macro accuracy |
| --- | ---: | ---: | ---: |
| **600** | **227/275** | **85.39%** | **85.41%** |
| 1200 | 220/275 | 82.93% | 83.25% |
| 1800 | 219/275 | 82.86% | 83.44% |

Step 600 remains selected. The later saved checkpoints did not improve validation action accuracy. Its 48 unmatched rows comprise 35 Facturation, ten Management Projet and three Design Workflow rows; these counts include correlated history variants. Validation is not an independent acceptance score. The same step-600 model, tokenizer, runtime and inference settings already completed the 438-case failed acceptance evaluation above; repeating that unchanged suite is unnecessary.

All three pre/post process identities and artifact digests matched. The two temporary workers stopped successfully, production inference remained healthy and unchanged, and no business tool executed. No infrastructure timeout, service-unavailable or context-limit error occurred in the 825 requests. Some outputs were invalid model actions; runtime health must not be read as perfect accuracy. The 275 rows represent 222 underlying scenarios, and the source has no per-language labels. No per-language or matched speedup claim is made.

The reviewed publisher requires all candidate steps, all 19 chunks per candidate, events and summary hashes, the frozen scoring dependencies, matching model/dataset/configuration evidence and successful worker cleanup. It recomputes selection before publishing the sanitized report. [Results](../training/reports/shared-v5r5-functional-validation.json), [policy](../training/reports/shared-v5r5-checkpoint-selection-policy.json).

The dated work below preserves earlier diagnoses and measurements; it is not the current rollout status.

## Diagnosis and verified corrections

The shared v2 benchmark remains the recorded baseline. Genuine failures include dropped AND filters, wrong resources, record searches in place of totals, confused follow-up operations and inappropriate clarification. A current-page ID explicitly supplied by the planner can be equivalent to omitting it and using trusted context; this strict-scoring limitation is recorded without changing benchmark scores. Generic name search and name-only filters are not automatically considered equivalent because the backend searches different fields.

The previous balanced run exposed only 122 of 410 Facturation examples, including none of its four get_invoice targets. Complete epochs now cover every source row once, distribute applications throughout the epoch and independently reshuffle later epochs. File hashes, declared application scope and nonempty splits are checked before weights load. Validation loss is reported separately for each application and as micro/macro averages; loss is not tool accuracy.

Colibri's Qwen parser previously recovered types only from top-level properties. Facturation search_operations declares compound oneOf schemas; ten validation labels with correct numeric limits became strings and failed validation. The parser now recovers unambiguous types through oneOf, anyOf and allOf, preserving known types across untyped conjunctive constraints. Ambiguous types remain strings; backend schema validation and authorization still apply. The correction is confined to the isolated evaluation runtime until an approved release. A separate control reran all 80 frozen Facturation cases with the same v2 weights and corrected parser: all parsed outcomes were identical (55/80 tools, 29/66 exact arguments, 76/80 valid structures). No held-out accuracy gain is credited to the parser correction. Control latency was measured during training and is not used as a deployment performance comparison. The Colibri server suite ran 436 tests, with zero failures and one existing skip; six targeted integrity tests passed.

## Versioned data

Shared v3 contains 798 synthetic training examples and 124 validation examples: Facturation 410/86, Management Projet 266/22 and Design Workflow 122/16. New Management Projet examples cover supported combinations of customer/project/supplier/date/status filters, financial periods and metrics, current-page records, ordinals, approved form labels, denied permissions, missing years, unsupported requests and English/French language switching. History matches the actual user-only planner history. No business database queries or real records are used.

A new 20-case bilingual companion hold-out was authored and frozen before this training. Original application acceptance files and evaluator are unchanged. The original acceptance failures informed new curriculum categories; the original tests therefore are retained regression tests, not an unseen final certification. The companion set is small and does not certify broad reliability. Exact normalized prompt overlap is rejected across training, validation and both held-out sets; exhaustive semantic near-duplicate exclusion is not claimed.

Server preflight verified all 922 targets round-trip through the tokenizer template and corrected parser. Largest training example: 4,744 tokens; largest validation example: 4,977 tokens. No truncation is used with the 8K budget. The single reviewer found no remaining training blockers after native-label and history corrections. A server-only forward/backward probe on the same 4,744-token example recorded 37.162 seconds with eager attention and 26.054 seconds with CPU SDPA; loss changed from 0.029573 to 0.030182 and both gradients were finite. SDPA is selected for this run. This single-step probe is not end-to-end training throughput; its process peak RSS is cumulative across both modes. [PyTorch documents CPU SDPA training support](https://dev-discuss.pytorch.org/t/torchinductor-update-6-cpu-backend-performance-update-and-new-features-in-pytorch-2-1/1514).

## Execution status

IMPLEMENTED: v3 server training and isolated export completed. All 798 examples were optimized exactly once: Facturation 410, Management Projet 266, Design Workflow 122. Duration was 6,527.5 seconds; peak RSS 16.55 GiB. Unweighted validation CE changed from 0.080327 to 0.069862; that is not an accuracy result.

All original v3 application regression runs completed: Management Projet 43/60 correct tools, 28/50 exact arguments, 60/60 valid structures; Design Workflow 46/60, 25/48, 60/60; Facturation 59/80, 30/66, 78/80. The shared v2 comparison was 44/60, 27/50, 60/60; 41/60, 23/48, 60/60; and 55/80, 29/66, 76/80 respectively. None of these candidates meets the acceptance targets. The companion measured 10/20 correct tools, 4/14 exact arguments and 19/20 valid structures. The isolated eight-request warm inference probe recorded 7.754 s sequential mean, 11.672 s at concurrency two, 55.75 decode tokens/s excluding prefill, 2.60 GiB peak RSS and zero errors; this small sample is not production capacity certification. The production feature remains disabled.

## Next accuracy round

IMPLEMENTED: shared v4 server-only training and isolated Colibri export completed from the existing shared v3 checkpoint, selected because aggregate three-application regressions improved while retaining all original inputs. This is a continuation decision, not production approval. The new shared v4 curriculum contains 1,060 train and 142 validation examples: Facturation 410/86, Management Projet 446/32, Design Workflow 204/24. It includes contrastive totals versus record lists, exact known-record edits versus descriptive search, narrowed capabilities, native bilingual statuses, complete AND filters, open-ended dates, workloads, unchanged quoted text, and application-specific unsupported operations.

Fresh 32-case Management Projet and 24-case Design Workflow sets were frozen before this round. The earlier originals and companion are unchanged. Original sources remain preserved; inherited Design Workflow training envelopes were rebuilt with the current native permission context and actual offered schemas. Canonical clarification metadata matches the real provider, checked by a source parity test. Nine integrity tests passed. Server preflight passed all 1,202 examples, including exact tokenizer IDs for weighted-token offsets, schema validity, parser round-trip and runtime prompt parity. No business database was accessed.

The isolated two-step capacity probe passed at 24 text layers, rank 16, alpha 32 and nonreentrant gradient checkpointing. All intended layers had finite, nonzero gradients and actual adapter updates at both steps; optimizer state remained finite. On the longest 4,744-token training example, step times were 93.26 and 86.21 seconds, with 5.34 GiB cumulative peak RSS. This is capacity evidence on the previous v2 checkpoint, not measured v4 accuracy or representative throughput.

The completed run used one complete epoch, 8K context, CPU SDPA and no truncation. Semantic action names, parameter names and values receive weight 4; XML syntax and EOS retain weight 1. Unweighted validation loss is also reported so weighted and ordinary losses are not confused. The recorded memory floor leaves at least 10% of host RAM available; Fourteen of sixteen measured logical CPU threads are allocated, reserving capacity for existing services. The run is capped at 25 GiB with no new swap; measured peak training RSS was 6.22 GiB. Critical backend permissions remain authoritative. No production activation is authorized or inferred from training success.

## Reusing the checks

Before any future optimization, run `training/scripts/preflight_training.py` with the reviewed data directory, existing checkpoint and intended Colibri runtime snapshot. It checks file hashes, offered/schema-valid targets, tokenizer/Colibri generation-prefix parity, token loss boundaries, parser round-trips and context limits without loading weights or executing business tools. A passing preflight is format compatibility, not model acceptance. The trainer independently checks hashes, approved application scope and nonempty splits.

```sh
python training/scripts/preflight_training.py --data /path/to/versioned-data --model /path/to/existing-checkpoint --runtime /path/to/colibri --output /path/to/new-preflight-report.json
```

The exact completed v3 trainer is retained as `training/scripts/archive/train_cpu_shared_v3.py`, matching its recorded SHA256. Its matching `training_schedule.py` is retained beside it, matching the recorded helper SHA256 and the trainer’s sibling-file check. Current training uses `training/scripts/train_cpu.py`; the archive is not used by the active continuation. Safe v3 measurements and provenance are in `training/reports/shared-v3-*`; private logs, operator paths and model artifacts remain excluded.

## Additional acceptance gates

The frozen evaluator excludes clarification cases from exact-argument percentages. Its per-case `arguments_correct` still checks the backend-rendered reason and language, but a perfect tool/exact-argument aggregate could conceal those errors. `training/scripts/model_acceptance.py` separately recomputes expected-action matches from the frozen events, requires every clarification and proposed change to match (including unrequested change proposals during read requests), and reports denied-access, unsupported destructive requests, ambiguous metrics and missing periods separately. It rejects missing, duplicate or relabeled cases and binds the report to dataset, event and unchanged evaluator hashes. Original benchmark scores are preserved.

The fresh Management Projet and Design Workflow sets contain 32 and 24 bilingual cases, representing 16 and 12 shared scenarios. This is a small evaluation sample, not broad reliability certification. Passing model gates never replaces native backend permission, tenant, confirmation and audit checks or authorizes production activation. The additional gates were specified before the v4 evaluation results. Fifteen training-integrity and acceptance tests passed; the single reviewer found no remaining blockers after the unexpected-change counterexample was fixed.

## Current verification — 2026-10-10

All 1,060 v4 training steps completed in 18,230.7 seconds. Unweighted validation CE changed from 0.074493 to 0.061744; weighted CE changed from 0.131969 to 0.119650. Per-application unweighted final CE was Facturation 0.064030, Management Projet 0.064588, Design Workflow 0.049757. These values measure teacher-forced loss, not successful tool calls. The original application regressions are complete: Management Projet 50/60 correct tools, 41/50 eligible exact arguments and 56/60 valid structures; Design Workflow 54/60, 41/48 and 59/60; Facturation 70/80, 48/66 and 75/80. All three fail the frozen acceptance gates. Additional critical-action checks found 5, 6 and 11 failures respectively. The companion measured 19/20 tools, 14/14 eligible exact arguments and 19/20 valid structures, but four critical clarification/unsupported-operation cases still failed. The fresh Management Projet set measured 26/32, 20/26 and 30/32; fresh Design Workflow measured 19/24, 12/18 and 21/24. All 276 cases completed with the frozen inputs unchanged; no production activation follows this run.

The fresh v3 baseline completed: Management Projet 17/32 tools, 10/26 eligible exact arguments, 32/32 valid structures; Design Workflow 15/24, 5/18, 23/24. All original inputs remain unchanged.

A native Management Projet safeguard now rejects model-guessed edit/delete targets unless the target matches the current page, fresh saved authorized results, or a complete explicit resource ID in the current instruction. Quote business numbers are not treated as internal IDs. Current native authorization and separate confirmation still apply. This addresses wrong-target proposals, not an authorization bypass or an automatic deletion. The local backend passed 618 tests and 111 subtests, including 78 assistant tests and 111 subtests; nine pure target checks are included. The single reviewer found no remaining issues. This safeguard is included in published backend `d453a9c4145a`; company, personal and production heads were verified. The assistant remains disabled pending model acceptance.


## Shared v5 preparation

IMPLEMENTED: a reviewed English/French continuation curriculum and server preflight. Shared v5 contains 1,318 training examples and 168 validation examples: Facturation 410/86, Management Projet 616/48, Design Workflow 292/34. Sources are the separately versioned Management Projet v4 and Design Workflow v3 curricula plus unchanged Facturation replay. Only synthetic entities and verified application capabilities are used. No application permissions, financial calculations or production data were changed for this training.

The added examples contrast record lists with financial totals, preserve literal search text, distinguish supported from unsupported filters and date limits, ask for missing context, and require verified target discovery for descriptive change requests. Quote business numbers are searched instead of being treated as internal IDs. The generator validates proposed Management Projet changes against the same native target-provenance helper used by the backend. The reviewed Design Workflow examples distinguish its actual broad `mine` scope from strictly assigned tasks and its title-or-description search from unsupported title-only search.

New 32-case Management Projet and 20-case Design Workflow sets were frozen before v5 training. Their completed v4 baselines measured Management Projet 18/32 tools, 9/20 eligible exact arguments and 26/32 valid structures; Design Workflow 13/20, 9/14 and 17/20. These harder fresh cases are recorded separately from earlier scores. Prior held-out files remain unchanged; exact normalized prompt overlap is checked, while exhaustive semantic independence is not claimed. The server preflight passed all 1,486 rows for schema/parser round-trip, runtime prompt parity, loss boundary and weighted-token alignment. Largest training/validation examples remain 4,744/4,977 tokens, within the unchanged 8K context.

IMPLEMENTED: server-only V5 continuation and isolated export completed from the shared v4 checkpoint, one complete epoch, rank 16/alpha 32 across 24 text layers, CPU SDPA, semantic weight 4 and learning rate 0.00005. Training was launched after all baseline and artifact checks passed. Actual V5 evaluation results are recorded below; acceptance remains incomplete. The launcher requires completed v4 measurements and new baselines, pins data/scripts/base/runtime hashes, and permits export only after successful trainer termination and complete coverage. Training remains PyTorch, Hugging Face Transformers and PEFT/LoRA; Colibri serves the resulting isolated candidate. Acceptance still requires actual frozen test results.


The completed v4 eight-request warm CPU probe measured 7.909 s sequential mean, 11.884 s at concurrency two, 56.18 decode tokens/s excluding prefill, 2.60 GiB peak RSS and zero errors. It used the same prompts and four-thread configuration as v3. This small warm sample is not sustained production capacity certification. Full public-safe measurements are in [the comparison](../training/reports/shared-v4-en-fr-comparison.json), [training report](../training/reports/shared-v4-en-fr-training.json) and [performance report](../training/reports/shared-v4-en-fr-performance.json); six separate acceptance reports retain the stricter critical-action results.


## Shared V5 measured results — 2026-10-10

All 1,318 optimization steps completed in 22,710.3 seconds. Every example was used once: Management Projet 616, Facturation 410 and Design Workflow 292. Peak training RSS was 6.97 GiB. Unweighted validation CE changed from 0.065782 to 0.036077; this is not tool accuracy.

All 328 frozen cases completed with unchanged evaluator, data, model artifacts and candidate process identity. None of the eight sets passes all acceptance gates.

| Set | Correct tools | Exact arguments | Valid structure |
| --- | --- | --- | --- |
| Management Projet original | 58/60 | 46/50 | 59/60 |
| Design Workflow original | 56/60 | 43/48 | 58/60 |
| Facturation original | 73/80 | 51/66 | 78/80 |
| Management Projet companion | 19/20 | 11/14 | 20/20 |
| Management Projet fresh | 28/32 | 23/26 | 32/32 |
| Design Workflow fresh | 21/24 | 16/18 | 23/24 |
| Management Projet newest hold-out | 25/32 | 15/20 | 30/32 |
| Design Workflow newest hold-out | 18/20 | 11/14 | 20/20 |

The unchanged four-thread Colibri CPU profile measured 7.777 s sequential mean, 11.676 s mean at concurrency two, 55.44 decode tokens/s excluding prefill, and 2.64 GiB peak RSS. This eight-request warm probe had zero transport errors and is not sustained production capacity certification.

The metadata-only native C tokenizer diagnostic matched all 328 prompt token sequences against the training tokenizer. Separate free-generation, stopping and numerical-path diagnostics are in progress; they do not alter these frozen scores. No additional application training or production activation follows automatically. The existing production model remains unchanged.

[Full comparisons and acceptance gates](../training/reports/shared-v5-en-fr-comparison.json), [training evidence](../training/reports/shared-v5-en-fr-training.json), [performance evidence](../training/reports/shared-v5-en-fr-performance.json).

## Shared V5 diagnosis and refinement preparation

The tokenizer is aligned: native Colibri and training token IDs match on all 328 frozen prompts. A selected ten-case diagnostic compared the original BF16 adapter, its merged FP32 export, Colibri integer inference enabled, and Colibri integer inference disabled. The original adapter, merged export and integer-disabled runtime produced identical parsed actions/errors. Both archive repetition loops already exist in the trained adapter. Disabling integer inference recovered one assignee-filter case but did not fix the main errors. These deliberately failure-heavy cases are **not an overall accuracy estimate**. [Recorded diagnostic evidence](../training/reports/shared-v5-en-fr-diagnostics.json).

The separately versioned `shared-v5r2-en-fr` preparation retains all 1,318 previous training rows and adds 136 synthetic English/French examples. It covers archive/name combinations, assignment versus text filters, record versus financial-summary intent, all requested filter values, missing versus explicit years, known edits versus descriptive searches, and previous-result references. There are 1,454 training rows, 186 validation rows and 34 new independent cases, excluded from both training and validation. Earlier 328 cases remain unchanged regression evidence; their failure categories informed the curriculum. This is preparation, not a successful training or accuracy result.

The 34 new independent cases were measured **before** refinement optimization, with the same V5 Colibri process and frozen evaluator. They deliberately cover harder combinations; this small set is not a production-wide success-rate estimate.

| New set | Tools | Exact eligible arguments | Valid structure |
| --- | --- | --- | --- |
| Management Projet | 8/12 | 5/8 | 12/12 |
| Design Workflow | 6/10 | 0/8 | 8/10 |
| Facturation | 10/12 | 5/8 | 12/12 |

A review replaced one **unmeasured validation pair** that reused a training sentence template with a distinct two-field contact-edit composition. All training rows and all independent/frozen test rows stayed byte-identical, and the untrained draft was retained privately. No test labels or test prompts changed. Raw baselines: [Management Projet](../training/reports/shared-v5r2-baseline-management-projet.json), [Design Workflow](../training/reports/shared-v5r2-baseline-design-workflow.json), [Facturation](../training/reports/shared-v5r2-baseline-facturation.json).


## Shared V5r2 measured results — 2026-10-11

IMPLEMENTED: server-only LoRA continuation completed all 1,454 steps in 24,467.4 seconds (about 6 h 48 min), followed by isolated Colibri export. Each training example was used once: Management Projet 664, Facturation 458, Design Workflow 332. Peak training RSS was 6.37 GiB. Ordinary validation CE improved from 0.042611 to 0.039598, while semantically weighted CE worsened from 0.066865 to 0.077601. Loss is not tool accuracy.

All 362 frozen cases completed on the same pinned candidate process and artifacts, with the unchanged evaluator and labels. Aggregate tool selection is 344/362 (95.03%), eligible exact arguments 254/280 (90.71%), and valid structure 358/362 (98.90%). The matched V5 baseline was 322/362 (88.95%), 226/280 (80.71%), and 352/362 (97.24%). These aggregate gains do not satisfy all acceptance gates: only the Design Workflow newest 20-case set passes every gate. Production remains unchanged; later application training is not started.

| Set | Correct tools | Exact arguments | Valid structure |
| --- | --- | --- | --- |
| management projet candidate | 57/60 | 47/50 | 60/60 |
| design workflow candidate | 60/60 | 45/48 | 60/60 |
| facturation candidate | 79/80 | 54/66 | 79/80 |
| management projet companion | 20/20 | 14/14 | 20/20 |
| management projet fresh | 30/32 | 24/26 | 32/32 |
| design workflow fresh | 24/24 | 16/18 | 24/24 |
| management projet new holdout | 27/32 | 20/20 | 30/32 |
| design workflow new holdout | 20/20 | 14/14 | 20/20 |
| management projet refinement | 9/12 | 8/8 | 11/12 |
| design workflow refinement | 8/10 | 6/8 | 10/10 |
| facturation refinement | 10/12 | 6/8 | 12/12 |

Remaining failures include dropped search filters, incorrect relative dates, confusion between person/project text, known edits classified as searches, and wrong clarification reasons/languages. These planner tests execute no financial reads or writes. Critical model-case failures must not be misreported as successful business operations or backend authorization bypasses. Native authorization and exact-target confirmation remain separately tested.

The unchanged four-thread Colibri CPU profile measured 7.805 s sequential mean (p95/max of four: 7.980 s), 11.699 s at concurrency two (p95/max of four: 15.929 s), 54.73 decode tokens/s excluding prefill, 2.60 GiB peak RSS, about four busy CPU cores, and zero errors. This is an eight-request warm sample, not sustained production capacity certification.

The original 328 regressions informed curriculum work; the additional 34 cases were frozen and baseline-measured before V5r2 optimization. Paired translations are not independent statistical samples. A separate description-only diagnostic is prepared, preserving every original prompt/context/expected action/schema constraint; it is not yet measured and cannot replace these scores.

[Full comparison and acceptance gates](../training/reports/shared-v5r2-en-fr-comparison.json), [training evidence](../training/reports/shared-v5r2-en-fr-training.json), [performance evidence](../training/reports/shared-v5r2-en-fr-performance.json).

## Shared model diagnostics and adapter corrections — 2026-10-11

The description-only V5r2 comparison completed all 362 cases on the same pinned candidate, provider and runtime. Tool selection increased from 344/362 to 346/362 (95.58%); exact arguments increased from 254/280 to 257/280 (91.79%); structured validity decreased from 358/362 to 356/362 (98.34%). Three of eleven sets passed all gates. Overall acceptance still FAILS; production was not changed. This is regression evidence, not an unseen certification. [Measured report](../training/reports/shared-metadata-v1-en-fr-comparison.json).

IMPLEMENTED and verified locally, not released: Management Projet now sends freshly authorized saved result IDs in display order to the planner. Expired, malformed or incomplete selections clear entirely, without shifting ordinals. Exact-target confirmation and native actor history remain unchanged. Shared calendar anchors derive from the application's trusted local date; they do not calculate business amounts or infer missing years. Facturation's search descriptions distinguish customer/product fields, native statuses, inclusive date bounds and requested result limits. Native registry checks confirmed unchanged validation and permission metadata.

Verification after these changes: Facturation 856 assistant tests passed; Management Projet 84 tests and 130 subtests passed; Design Workflow 88 tests passed. Five shared calendar tests cover leap years, year rollover, invalid dates, unchanged caller data and actual planner context. The single reviewer found no unresolved issues.

PARTIALLY IMPLEMENTED: a separate `shared-adapter-v2-en-fr` diagnostic contains the original 362 user prompts/labels bound to current native planner inputs plus 28 new English/French saved-result cases. Historical capability metadata recovery and synthetic ordinal fixtures are explicit in its manifests. All 390 cases passed exact server-matching tokenizer/template/parser/loss-boundary checks; maximum prompt 7,228 tokens plus 512 reserved output tokens fits 8,192. No local model inference or training ran. The server evaluation completed all 390 cases against the unchanged V5r2 candidate. On the matched 362 cases: 346/362 correct tools (95.58%), 255/280 exact arguments (91.07%), and 357/362 valid structures (98.62%). The separate 28 new follow-up cases scored 12/28 tools, 9/20 exact arguments, and 25/28 valid structures. Across all 390: 358/390 tools (91.79%), 264/300 exact arguments (88.00%), and 382/390 valid structures (97.95%). Only three of twelve sets passed all gates; acceptance FAILS. All temporary workers were stopped after artifact and process verification. [Measured comparison](../training/reports/shared-adapter-v2-en-fr-comparison.json). This run changes adapter instructions, tool descriptions and calendar context together and cannot isolate each contribution.

Training status: the 1,454-step V5r2 optimization is complete; the 390-case adapter evaluation is complete and failed acceptance. Failure diagnosis and adapter correction continue; no new sustained training job has started. Contracts, Gestion Magasin and Réservation training remain queued one at a time behind acceptance. The shared model and production feature activation remain unchanged.

The eight malformed calls were replayed separately with the same pinned provider and candidate process: four invented an unsupported supplier filter for financial summaries, two used field names absent from Management Projet, one omitted the required operation, and one requested an unavailable previous-result deletion operation. Provider/schema validation rejected them; the diagnostic executed no business tool and did not replace benchmark results. [Failure analysis](../training/reports/shared-adapter-v2-malformed-calls.json).

## Reviewed V5r3 preparation — 2026-10-11

PARTIALLY IMPLEMENTED: `shared-v5r3-en-fr` preserves the reviewed current-metadata curriculum and adds 122 diverse English/French training examples plus 36 validation examples. Totals: 1,576 training and 222 validation rows. The existing 390 diagnostic cases remain unchanged; 48 newly authored cases are frozen separately, making 438 evaluation cases. They are authored by the implementation team, not a blind external certification. Failure categories informed training; exact normalized split overlap is rejected, while semantic-independence limitations remain explicit.

All 1,798 SFT/validation rows and the 48 new evaluation cases passed tokenizer/template/Colibri-parser/loss-boundary checks against server-matching metadata. Maximum training length is 7,648 tokens; maximum new evaluation prompt is 3,224 plus 512 output tokens. No local model weights were loaded. [Metadata preflight](../training/reports/shared-v5r3-en-fr-metadata-preflight.json). New-case baseline measurement is running on the unchanged isolated V5r2 candidate. No V5r3 optimization has started. A server capacity check at the revised longest example remains required.

The two-update precision comparison on the earlier 5,135-token example passed for both modes: BF16 averaged 104.06 seconds/update with 5.38 GiB peak RSS; FP32 averaged 113.55 seconds with 6.59 GiB. BF16 is retained based on those measured costs. This saved no adapter and measured no accuracy. [Precision report](../training/reports/cpu-training-precision-v1.json).

IMPLEMENTED and verified locally: the six native adapters use a shared safeguard for explicit EN/FR ordinal mutation targets. A recognized request for the third saved result cannot propose the first saved result, even if both are authorized or the first is the current page. Expired/malformed selections, conflicting explicit IDs and wrong resource types reject; quoted or recognized replacement values do not become targets. This is bounded syntax, not a general natural-language intent parser. Native authorization and separate exact-target confirmation still apply.

Validation: 14 shared context tests and 22 training-integrity tests pass. Final native assistant suites: Facturation 860, Management Projet 86 plus 130 subtests, Design Workflow 90, Contracts 58 plus 4 subtests, Gestion Magasin 58, Réservation 45. The single reviewer found no unresolved code or final-dataset issues. Native adapter publication and packaged-wheel synchronization remain pending; no backend/model deployment or feature activation is claimed. Contracts, Gestion Magasin and Réservation optimization remain queued, one at a time, behind shared-model acceptance.


## Shared V5r4 training started — 2026-10-11

IMPLEMENTED: the complete baseline comparison is measured. Across 438 unchanged logical scenarios, conversation framing changes tool selection from 372/438 (84.93%) to 386/438 (88.13%), eligible exact arguments from 264/334 (79.04%) to 277/334 (82.93%), and valid structure from 430/438 (98.17%) to 425/438 (97.03%). All acceptance gates still fail. The 78 changed histories were measured freshly; 360 identical inputs reuse prior measurements with the same pinned candidate/provider. No combined latency claim is made. [Full comparison](../training/reports/shared-dialogue-v1-en-fr-baseline.json).

IMPLEMENTED: exact server preflight passed 1,713 training and 275 validation rows. Two unsaved capacity updates on the longest 7,648-token example passed across all 24 layers; peak RSS 6.33 GiB, update times 182.43 and 172.04 seconds using ten threads while the four-thread diagnostic ran. The initial 18 GiB job allowance was rejected by the resource gate before any job started; the revised 15 GiB limit preserved the 10% reserve plus additional headroom. [Preflight](../training/reports/shared-v5r4-en-fr-server-preflight.json), [capacity](../training/reports/shared-v5r4-en-fr-capacity.json).

PARTIALLY IMPLEMENTED: the reviewed single server continuation has started from the existing V5r2 merged checkpoint. One complete epoch covers 1,713 examples (557 Facturation, 760 Management Projet, 396 Design Workflow), rank 16/alpha 32 across 24 text layers, BF16 CPU SDPA, semantic loss weight 4 and learning rate 0.00005. Limits: 14 of 16 CPU threads, 15 GiB memory, no job swap. The shared source release `f619d6714bbd` is verified on all three remotes. Existing production inference remains healthy and unchanged.

The launcher binds the exact baseline, capacity, data, scripts, base and runtime artifacts; guarded export waits for successful complete coverage. A monitor will evaluate all 438 frozen scenarios afresh after successful isolated export. Completion, accuracy and activation are not claimed. Contracts, Gestion Magasin and Réservation remain sequential future stages.

IMPLEMENTED locally: the identical shared core 0.2.1 wheel is packaged for all six backends with source-content hashes verified. Tests against that actual wheel passed: Facturation 860; Management Projet 87 plus 136 subtests; Design Workflow 90; Contracts 59 plus 10 subtests; Gestion Magasin 59 plus 6 subtests; Réservation 46 plus 6 subtests. Native source publication remains pending; this source-only central push did not deploy application code or activate a model.

## Date-label errata discovered during R6 review — 2026-10-13

Two original Management Projet cases, `search-schedule-fr/en`, use “avant/before 2026-11-01” but expect the inclusive end date `2026-11-01`. The actual backend applies `due_date__lte`; strict-before semantics require `2026-10-31`. The independent reviewer confirmed the mismatch. The original results and running checkpoint comparison remain unchanged; this is a benchmark limitation, not an accuracy improvement. A corrected future evaluation must be separately versioned and measured. [Errata evidence](../training/reports/shared-v5r6-date-label-errata.json).


## Versioned benchmark errata preparation — 2026-10-13

IMPLEMENTED and verified as preparation only: `shared-dialogue-v2-en-fr` retains all 438 scenarios and 15 sets. It corrects only the three previously documented defects: the two payment-schedule requests saying “before 2026-11-01” now expect the inclusive upper bound 2026-10-31, and the French supplier-expense question explicitly identifies the supplier, matching its English counterpart. The other 435 rows remain byte-identical. V1 inputs, historical scores, active checkpoint comparison, training data and acceptance thresholds are unchanged.

Eight generator tests pass. Fresh metadata checks pass all 438 V2 cases against the existing tokenizer, chat template and Colibri parser. The largest prompt is 7,235 tokens, with 512 output tokens reserved within 8,192. The single reviewer found no issues. No V2 model inference, training or acceptance has occurred. V2 requires separately bound baseline/candidate results, reported alongside V1; preparation cannot qualify a model or activate an application. [Dataset manifest](../training/datasets/shared-dialogue-v2-en-fr/manifest.json), [metadata checks](../training/reports/shared-dialogue-v2-en-fr-metadata-preflight.json).
