# Chat AI Assistant progress


## Current Facturation contracts checked; training progressing - 21 October 2026

IMPLEMENTED and independently reviewed: all 632 frozen TRAIN targets and 133 validation targets pass the current local Facturation registry schemas and business-shape checks without database access. All 40 pinned assistant source files match. Exact current shortlist schema sets match 626 TRAIN rows and all 133 validation rows. The six legacy TRAIN differences contain additional tools; every intended action remains supported in an eligible profile. No training input, label or scoring gate changed.

The 301 explicitly annotated TRAIN profiles pass current permitted-tool checks. The other 331 TRAIN and 133 validation rows lack profile annotations; this audit does not invent roles or establish actual authorization. Separately, 66 ORM query-construction checks across five stock/logistics resources pass. No SQL, business operation, card rendering or runtime authorization is exercised.

PARTIALLY IMPLEMENTED: at the verified 17:47 UTC observation the original 4B server trainer has completed 20/632 optimizer updates after initial validation, using 14 threads. Protected model services remain healthy. Fine-tuned accuracy and latency improvement are unmeasured; zero of six apps qualify on this replacement model. [Actual checks and limitations](../training/reports/qwen35-4b-current-native-contract-audit-v1.json).

## 4B comparison controls prepared; latency investigation - 21 October 2026

IMPLEMENTED and verified as preparation: the new selector requires the actual cached untrained baseline and every saved checkpoint, 158/316/474/632, on all 133 unchanged primary cases. It uses the original frozen scorer and unchanged 95% full-action/tool/argument, 99% structure and complete critical/clarification gates. Ten checks pass, including actual-baseline replay, missing candidates, changed labels, scorer mutation and module-shadow rejection. The single reviewer cleared the five source/reference files. Public references contain only synthetic scenarios, actual untrained responses and the original pre-training policy.

The actual replay still fails at 77/133 full actions and 71/111 eligible arguments. Synthetic passing-candidate fixtures are control tests, not model predictions. Training, its snapshots and the live models are untouched. Numerical comparison still requires successful training completion, checked adapters/exports and separate admission.

PARTIALLY IMPLEMENTED: latency is now an explicit improvement requirement. Correct baseline actions still average 35.268 seconds with about 66 output tokens. The original native phase split was not captured; no cause or improvement is established. Colibri profiling/prefix diagnostics and the local native greeting path are identified for separate measurements after training releases the CPU. [Latency findings](AI_LATENCY.md). [Prepared controls and evidence](../training/reports/qwen35-4b-comparison-preparation-v1.json).

## Replacement pilot running - 21 October 2026, 16:17 UTC

PARTIALLY IMPLEMENTED: the original Qwen3.5-4B server trainer is running and in initial preparation/validation. At the verified 16:17 UTC observation, zero optimizer updates are logged; 632 are scheduled. The fresh rank-16 adapter uses all 32 text layers, 14 CPU threads, BF16, SDPA, checkpointing, uniform assistant-only loss and learning rate 0.00005. One epoch covers every selected TRAIN row once; checkpoints are 158/316/474/632. Initial and final validation use the unchanged 133 cases.

IMPLEMENTED and verified: both longest-row capacity updates passed, taking 625.123 and 674.269 seconds with 14.824 GiB peak RSS. All 32 layers had finite gradients and changed adapter weights. The disposable probe saved no adapter. All 765 pilot metadata checks, 14 source-preparation tests and 47 launch-guard fixtures pass. The single reviewer cleared the exact numerical recipe, sources, data and actual capacity evidence. Fresh memory, idle-job, artifact and protected-service checks passed before the original trainer started.

Training completion, checkpoint export and all declared Colibri comparisons remain pending. The only measured 4B primary full-action score remains its untrained baseline, 77/133 (57.89%); no fine-tuned score or 95% guarantee exists. Zero of six apps are accepted. KAT coding, translation, grammar correction and live assistant remain unchanged. Reviewed preparation commit 4446a0c is verified on all three remotes and all 15 deployed source files.

[Actual capacity and launch evidence](../training/reports/qwen35-4b-pilot-launch-v1.json).

## Replacement baseline complete and training preparation - 21 October 2026

IMPLEMENTED and verified: the untrained Qwen3.5-4B Colibri baseline completed all 133 frozen Facturation primary cases. Correct full actions are 77/133 (57.89%), correct tools 114/133 (85.71%), eligible exact arguments 71/111 (63.96%) and valid structures 125/133 (93.98%). Clarification actions are 0/16 and critical actions 6/24. Every acceptance gate fails. Labels, parser, provider and scoring remain unchanged. The isolated worker stopped cleanly and its port is free.

IMPLEMENTED and verified as preparation: two ambiguous TRAIN requests now explicitly distinguish customer and product; 16 bilingual product-first role examples are added. All other 1,485 source rows and all 133 validation bytes are preserved. The 18 corrected/added rows pass Facturation's actual metadata registry with database access blocked. The single reviewer cleared source/data preparation; eight tests pass, including changed dependency and exclusion-input rejection. All 1,503 TRAIN and 133 validation examples pass fresh server tokenizer/template, parser, schema, loss-boundary and output-budget checks.

PARTIALLY IMPLEMENTED: the CPU capacity probe is running two disposable longest-row LoRA updates with 14 threads and all 32 text layers. It does not save an adapter or establish completed fine-tuning. A separate 632-row TRAIN-only pilot is prepared under a 640-row ceiling, preserving all 18 tools and all 1,551 declared projected features. It copies source rows unchanged, with 299 confirmed English, 301 French and 32 unresolved legacy language annotations. Six pilot checks pass. Projected coverage is not every feature interaction or predicted accuracy; numerical admission remains pending.

The replacement has not been fine-tuned or accepted. Zero of six apps are accepted. Facturation remains first; other apps follow sequentially with the same shared model. KAT coding, translation, grammar correction and live assistant remain unchanged.

[Baseline, preparation and resources](../training/reports/qwen35-4b-baseline-and-preparation-v1.json).

## Approved replacement model - 21 October 2026

IMPLEMENTED and verified: the official post-trained Qwen/Qwen3.5-4B model is downloaded on the server at revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` (Apache 2.0). All 13 source files were size-checked and their SHA256 hashes recorded; three LFS checksums were additionally verified against official metadata. Colibri conversion produced 42 artifacts across 32 text layers. KAT coding, translation, grammar correction and the live assistant remain unchanged.

The preceding Qwen3.5-0.8B correction was stopped at 82/256 updates for this approved replacement. It did not complete and its prepared comparison is retired. Obsolete experimental weights were removed, freeing 549.62 GiB; datasets, logs, measurements and source were retained. Historical running snapshots below are superseded by this entry.

PARTIALLY IMPLEMENTED: the new model's six-case native-tool smoke passed 4/6 full actions and structures. Both failures were rejected as invalid model output. A separate operator-observed diagnostic saw plain-text replies with no clarification function. The provider correctly rejected them; these failures remain in the score. Mean smoke latency was 35.938 seconds, observed P95 was 41.183 seconds. Completion tokens divided by request wall time averaged 2.242 tokens/second; this is not raw decoder speed.

The reviewed 133-case Facturation baseline is running under Colibri CPU with 7 threads, 8192 context tokens, 512 maximum output tokens, thinking disabled and temperature 0. Labels, parser and scoring are unchanged. Both initial admission failures occurred before generation and are preserved; the complete read-only server admission subsequently passed. This is evaluation, not replacement-model fine-tuning. No final 4B accuracy is available.

PLANNED: finish the baseline, validate the existing EN/FR training material against the 4B tokenizer/template, measure server LoRA capacity and fine-tune against verified failures. Facturation remains first; the same shared model will qualify on later applications sequentially. Zero of six apps are fully accepted. No model activation or business operation occurred.

[Verified replacement and progress snapshot](../training/reports/qwen35-4b-transition-v1.json).

## Facturation correction progress and comparison preparation - 21 October 2026, 13:10 UTC

PARTIALLY IMPLEMENTED: the original server training invocation is running at 13/256 contiguous updates after completing its initial 275-row teacher-forced validation. It still uses the reviewed recipe and 14 CPU threads. The latest three updates took 85.305, 16.314 and 19.906 seconds, demonstrating that update duration varies with the example. Available host memory was 43.66 GiB; production inference remains healthy and unchanged. Initial Facturation loss is 0.023521, Management Projet 0.024735 and Design Workflow 0.014350. These are teacher-forced losses, not accuracy percentages.

IMPLEMENTED and verified as source preparation: the single reviewer found no issues in the prospective Colibri coordinator, completion guard, worker controls, read-only terminal identity capture and two offline test modules. Both static dry-runs and all 15 offline tests pass. The synthetic simulations cover complete candidate ordering, rejection before unnecessary broader testing, missing final-case refusal and eligible control flow through all 275/438/48 broader cases. They do not predict model accuracy.

PARTIALLY IMPLEMENTED: actual training completion, its terminal collection and independent review, numerical comparison admission and Colibri evaluation remain pending. The comparison still requires all logical candidates 0/64/128/192/256, the unchanged scoring and critical gates, and the original checkpoint-600 retention reference. Best previous primary full-action accuracy remains 123/133 (92.48%) and exact arguments 101/111 (90.99%). Zero of six applications are fully accepted. No next-application training or production activation started.

[Recorded progress and source-only review](../training/reports/facturation-argument-coverage-v2-training-progress.json).

## Facturation correction training started - 21 October 2026, 12:39 UTC

PARTIALLY IMPLEMENTED: the fresh 256-update server epoch is running after the corrected metadata, all 531 tokenizer/template preflight cases and both longest-row capacity updates passed review. Capacity updates took 190.09 and 182.55 seconds; peak process RSS was 5.74 GiB, with finite nonzero gradients and changed adapter weights across all 24 layers.

The original trainer and exact reviewed command were observed running at 12:39:45 UTC, with zero optimizer updates logged and initial baseline validation not yet logged. The recipe uses the same already merged checkpoint-32 parent, a fresh adapter/optimizer, uniform token weights, learning rate 0.000002 and 14 CPU threads. It schedules saves at 64/128/192/256 and teacher-forced validation at 0/128/256. The source preparation commit was verified on all three remotes and all 14 deployed source files; production inference remains healthy.

Training completion and the unchanged Colibri functional/critical/retention gates remain pending. No new accuracy is established. The best previous primary result remains 123/133 full actions (92.48%) and 101/111 exact arguments (90.99%); zero of six applications are fully accepted.

[Actual preflight, capacity and initial launch evidence](../training/reports/facturation-argument-coverage-v2-preflight-and-launch.json).

## Facturation argument correction prepared - 21 October 2026

IMPLEMENTED and verified as preparation: the next correction preserves the previous 176 TRAIN rows and all 275 validation rows byte for byte, adding 80 synthetic examples, 40 English and 40 French. The resulting 256 rows comprise 224 Facturation and 16 retained examples each from Management Projet and Design Workflow. The additions cover complete multi-field text edits, unpaid filter presence, inclusive/exclusive calendar boundaries and permission-filtered payment searches. The single reviewer reproduced all additions and 894 input-only exclusions with no detected new exact or near-duplicate overlap. This is a development-informed correction, not a new blind holdout.

All 52 correction tests pass, including regressions that execute the actual frozen capacity and trainer startup guards without model imports. All 54 corrected-namespace stage-guard cases pass and were independently rerun by the single reviewer. Separately, 18 controlled local native-contract tests pass: narrow article single-filter aliases are equivalent in the tested cases, while combined filters, payment searches, revocation, tenant restrictions and user-list/detail routes keep their distinct contracts. All 1,651 tracked native source hashes remain unchanged. The model scoring rules remain unchanged.

PLANNED: a fresh server-only 256-update run from the same verified checkpoint-32 merged parent, with unchanged uniform token weights and learning rate 0.000002. Using the same parent isolates this dataset change from a new starting-weight change. The original server metadata preflight passes all 256 TRAIN and 275 validation examples; maximum lengths are 7,706 and 7,496 tokens, and its saved evidence is reviewed. The subsequent capacity attempt failed before framework import because the manifest omitted its application list. It ran zero optimizer updates and produced no capacity measurement. The corrected manifest declares all three replay applications and passes both actual consumer startup guards locally. TRAIN, validation and addition bytes are unchanged, and the failed attempt is preserved. The fresh corrected bindings and all 531 server preflight cases passed review. The separate capacity test started at 12:25 UTC; its original worker was verified active at 12:27 UTC with about 5.24 GiB RSS and 41.12 GiB available host memory. No optimizer updates were logged at that snapshot. Capacity completion and full-training admission remain pending. The unchanged functional comparison requires logical zero and checkpoints 64/128/192/256, plus applicable broader, critical and retention gates. No new accuracy or activation is established; best measured full-action accuracy remains 123/133 (92.48%), exact arguments 101/111 (90.99%), and zero of six apps are fully accepted.

[Preparation and verification](../training/reports/facturation-argument-coverage-v2-preparation.json).

## Facturation coverage comparison complete, model rejected - 21 October 2026

IMPLEMENTED and verified: The 176-update server training and all five declared Colibri primary candidates completed. Four checkpoints produced 532 fresh responses across 12 shards; logical zero reuses 133 reviewed actual checkpoint 32 responses. The original coordinator exited successfully. Fresh artifact, adapter, export, stopped-worker and free-port checks passed, and the single reviewer reproduced the completed audit and all 544 evidence hashes. Production inference remains unchanged.

| Logical candidate | Correct actions / 133 | Exact arguments / 111 | Critical / 24 |
| --- | --- | --- | --- |
| 0, cached actual checkpoint 32 | 122 (91.73%) | 100 (90.09%) | 22 |
| 44 | 121 (90.98%) | 99 (89.19%) | 21 |
| 88 | 119 (89.47%) | 97 (87.39%) | 22 |
| 132 | 123 (92.48%) | 101 (90.99%) | 21 |
| 176 | 120 (90.23%) | 98 (88.29%) | 22 |

PARTIALLY IMPLEMENTED: no candidate passes the unchanged primary gates. Diagnostic selection is checkpoint 132: 123/133 full actions (92.48%), 101/111 exact arguments (90.99%), 132/133 correct tools, 133/133 parsed structures, 16/16 clarifications and 21/24 critical cases. Relative to the cached parent, actions and arguments improve by one case but critical cases decline by one. The final checkpoint 176 scores lower at 120/133 actions. Training loss selected logical zero separately and did not rank functional candidates.

The broader 275/438/48 phases were not executed after necessary primary rejection. No new Management Projet, Design Workflow, per-language or native-security acceptance score follows this run. These correlated development cases are not fresh blind certification. Zero of six applications are fully accepted; no new model activation or next-application training occurred.

PLANNED: verify the reviewed article-filter alias equivalence using controlled native fixtures before deciding any new contract version. Current scores remain unchanged. Genuine selected failures include false unsupported denial, date bounds, missing unpaid filtering and incomplete multi-field text. The small TRAIN set has two English article examples with mixed equivalent-field conventions. This is a source-grounded diagnosis, not proven model causation or a promised accuracy gain; prepare the next TRAIN-only correction after review, without automatically repeating this recipe.

[Completed comparison and evidence](../training/reports/facturation-factor-coverage-v1-functional-comparison.json).

## Earlier coverage training completion, 21 October 2026

IMPLEMENTED and verified: the original server run completed all 176 scheduled updates, one complete epoch and final validation. All updates are finite and contiguous. The dataset was consumed once: 144 Facturation, 16 Management Projet and 16 Design Workflow examples. Runtime was 7,534.06 seconds (about 2 hours 6 minutes) on 14 CPU threads, with peak RSS 6.87 GiB.

The advanced collector verifies 26 raw evidence files, 216 external source pins, the original successful execution, an empty training cgroup and unchanged healthy production inference. The single reviewer reproduced the saved transport, terminal identity and pinned terminal verification locally. The final adapter equals checkpoint 176; all four scheduled checkpoint inventories are present.

| Teacher-forced loss, lower is better | Baseline | Update 88 | Update 176 |
| --- | --- | --- | --- |
| Micro | 0.021731 | 0.021940 | 0.022198 |
| Application macro | 0.020869 | 0.020959 | 0.021020 |
| Facturation | 0.023521 | 0.024112 | 0.025074 |
| Management Projet | 0.024735 | 0.024684 | 0.024181 |
| Design Workflow | 0.014350 | 0.014080 | 0.013805 |

The diagnostic loss selector retains logical zero, the preceding experimental checkpoint 32. Final macro, micro and Facturation losses rise; Management Projet and Design Workflow losses fall. Weighted and unweighted losses agree. These measurements do not establish functional accuracy or select the functional model.

PARTIALLY IMPLEMENTED: the Colibri comparison source is prepared and reviewed, and its actual read-only completion, artifact, resource and free-port preflight passed. The single reviewer cleared actual completion and comparison admission. The original comparison started at 10:03 UTC; checkpoint44 exported successfully and its 133-case primary evaluation is running on three four-thread Colibri workers. All four fresh checkpoints 44/88/132/176 and the reviewed actual32 baseline as logical zero remain mandatory on the unchanged 133-case primary set. Applicable 275/438/48, critical and original checkpoint-600 retention gates remain unchanged.

The best verified Facturation primary score remains 122/133 full actions (91.73%). Zero of six applications are fully accepted. No new accuracy, production activation or next-application training is established.

[Completed training evidence](../training/reports/facturation-factor-coverage-v1-training-completion.json).

## Earlier Facturation coverage launch, 21 October 2026

PARTIALLY IMPLEMENTED: launched a separate 176-example EN/FR correction after the completed ordinary-SFT run failed its unchanged primary gates. It preserves all 128 prior TRAIN rows byte for byte and adds 16 quoted/unquoted complete-text examples, 12 existing navigation examples and 20 existing date-boundary examples. Application exposure is 144 Facturation, 16 Management Projet and 16 Design Workflow. No evaluation answers were added to TRAIN; 894 evaluation-input envelopes were checked for exclusions.

The single reviewer independently reproduced the actual prepared bytes, coverage, schemas, unchanged context and validation. The server also reproduced all 473 persisted FP32 tensors exactly from the preceding merged parent plus its checkpoint-32 adapter. The reviewer checked the saved proof and transport, without independently rerunning the server calculation. The next run must create a fresh adapter and optimizer and must not apply that adapter a second time.

The admitted numerical recipe uses one 176-update epoch, learning rate 0.000002, equal assistant-token weights, checkpoints 44/88/132/176 and teacher-forced validation at 0/88/176. Functional selection compares those four candidates with actual preceding checkpoint 32 as logical zero. Frozen scoring, the 133-case primary gates, original checkpoint-600 retention reference and applicable 275/438/48 broader gates remain unchanged.

IMPLEMENTED and verified: all 176 TRAIN and 275 validation examples passed the actual server tokenizer/parser preflight, including Colibri prefix parity, supervised-token boundaries and the 512-token output allowance. Maximum lengths were 7,706 and 7,496 tokens. The single reviewer checked the original successful invocation, raw transport and all ten collected files.

IMPLEMENTED and verified: both 7,706-token capacity updates passed with finite gradients and changed weights in all 24 adapter layers. Peak RSS was 6,251,960 KiB (5.96 GiB); update times were 183.21 and 195.24 seconds. The original successful invocation and thirteen collected files were reviewed. Fresh resource and concurrency checks passed before launch.

PARTIALLY IMPLEMENTED: the one fresh 176-update run started at 07:41 UTC on the server. The first verified observation at 07:41:51 UTC shows the original controller and correct trainer command running, with zero optimizer updates observed and initial validation not yet logged. The reviewed terminal verifier requires raw baseline, optimizer updates and validation events in execution order. Functional Colibri evaluation remains pending, so no new model accuracy or activation is established. The best verified primary full-action score remains 122/133 (91.73%); zero of six applications are fully accepted. [Preflight, capacity and initial launch evidence](../training/reports/facturation-factor-coverage-v1-preflight-and-capacity.json).

## Balanced correction: comparison complete, model rejected - 21 October 2026

IMPLEMENTED and verified: the clean Colibri recovery completed all four fresh checkpoint candidates, 532 requests across 12 shards, plus the attested parent checkpoint 125 as cached logical candidate 0. The original 128-update training did not restart. The actual coordinator exited successfully. A fresh server collector rechecked every fresh model, adapter, export and before/after proof, with workers stopped, evaluation ports free and production inference unchanged. The single reviewer independently reproduced the completed audit and all 392 evidence hashes.

| Logical candidate | Correct actions / 133 | Exact arguments / 111 | Critical / 24 |
| --- | --- | --- | --- |
| 0, actual parent 125, cached | 122 (91.73%) | 102 (91.89%) | 20 |
| 32 | 122 (91.73%) | 100 (90.09%) | 22 |
| 64 | 117 (87.97%) | 95 (85.59%) | 21 |
| 96 | 118 (88.72%) | 96 (86.49%) | 21 |
| 128 | 120 (90.23%) | 98 (88.29%) | 21 |

PARTIALLY IMPLEMENTED: Facturation model quality still fails acceptance. The unchanged selector picks checkpoint 32 after the action tie because its parsed structure score is higher. It has 133/133 correct tools and parsed structures and 16/16 correct clarifications, but fails exact arguments, full actions and critical cases. Parsed structure does not establish fully executable arguments or native authorization.

The 275/438/48 broader phases did not execute because every candidate failed necessary primary gates. No new Management Projet or Design Workflow accuracy, native-security clearance or model activation is established. Zero of six applications are fully accepted, and no next-application training started.

Measured checkpoint-32 request latency averages 19.658 seconds, P95 61.936 seconds, under three concurrent four-thread workers. Mean completion tokens per request wall second is 3.471, including prompt processing and serving overhead; it is not isolated decoder speed. The one-second checkpoint-64 resource observation measured 75.8% host CPU with 40.324 GiB available memory; it is not a peak-resource benchmark.

PLANNED: prepare a separately versioned TRAIN-only coverage correction after this failure review. The small set lacks English detail/French collection user-navigation combinations and all unquoted remark-update examples, although the approved larger TRAIN source has them. These are verified coverage gaps, not proven causes or promised accuracy gains. Require source grounding, paired factor/language checks, schema validation, one review and fresh server preflight before another training run. The eight reviewed Logistics sources and bilingual central knowledge remain unchanged.

[Completed comparison and evidence hashes](../training/reports/facturation-uniform-correction-v1-functional-comparison.json).

## Clean comparison recovery started - 21 October 2026

PARTIALLY IMPLEMENTED: the reviewed recovery started at 05:22 UTC. Fresh server admission passed and checkpoint 32 export started. The completed 128-update training is reused without restarting optimization. The original failed comparison and its raw outputs remain separate.

The recovery runs checkpoints 32, 64, 96 and 128 afresh, using only the attested parent checkpoint 125 as cached logical candidate 0. Repeating checkpoint 32 preserves the existing orchestration and checks the corrected terminal-identity guard through the full path. All five logical candidates remain mandatory on the unchanged 133-case primary set; selection and applicable 275/438/48, critical and retention gates are unchanged.

IMPLEMENTED and verified as controls: all 29 offline recovery tests and 13 terminal-helper tests pass. Read-only server preflight verified completed-training identity, pinned sources, artifacts and dependencies, idle evaluation ports and unchanged healthy production inference. The single reviewer cleared the exact recovery sources and evidence before launch.

No recovery functional score is available yet. Zero of six applications are fully accepted, no model was activated and no next-application training started. The separate original refinement completed 3,103 updates; 1,587 was an incorrect conversational count.

[Recovery launch and evidence hashes](../training/reports/facturation-comparison-recovery-launch.json).

## Facturation comparison halted; identity helper verified - 21 October 2026

IMPLEMENTED and verified: checkpoint 32 completed all 133 primary cases, with equal before/after artifact and worker proofs and three workers stopped. It scores 122/133 full actions (91.73%), 100/111 exact arguments (90.09%), 100% tool selection, 100% structured output and 22/24 critical cases. It does not pass acceptance.

PARTIALLY IMPLEMENTED: checkpoint 64 collected all 133 cases and three shard summaries, then the comparison halted during its post-run proof. The guard compared the complete rendered systemd unit record; historical execution-status fields inside ExecStart had cleared. The configured command and actual invocation, main PID, start/exit timestamps, successful result and resource limits remain unchanged, with no restarts. The cause of the presentation reset is not proven. The abort stopped three owned workers. Checkpoint 64 has no after-proof and is excluded pending a fresh run; no checkpoint-64 accuracy is accepted.

IMPLEMENTED as a helper only: the corrected verifier enforces exact configuration plus the actual original execution, accepts only cleared or equivalent populated status presentation, and rejects contradictory identity. All 13 tests pass; the single reviewer also replayed actual captured evidence and rejected six additional mutations. Recovery integration and admission are pending.

The recovery must preserve the original failed invocation and raw outputs, verify/reuse the fully attested baseline and checkpoint 32, repeat checkpoint 64 in a new namespace, then complete 96/128 and unchanged selection and applicable broader gates. The original 128-update training remains complete; it must not restart. Zero of six apps are fully accepted, production inference is unchanged and no next-application training has started.

[Failure evidence and verified helper scope](../training/reports/facturation-comparison-identity-check-fix.json).

## Balanced correction: training complete - 21 October 2026

IMPLEMENTED and verified: the original server job completed all 128 scheduled optimizer updates and final validation successfully in 6,742.7 seconds (about 1 hour 52 minutes). All updates are contiguous and finite. Strict collection verifies 27 evidence files, the original successful invocation, an empty training cgroup, 206 external source pins and unchanged healthy production inference. Reported peak RSS is 6.413 GiB. The dataset was consumed once: 96 Facturation, 16 Management Projet and 16 Design Workflow examples.

| Teacher-forced loss, lower is better | Baseline | Update 64 | Update 128 |
| --- | --- | --- | --- |
| Micro | 0.022434 | 0.022095 | 0.023120 |
| Application macro | 0.022471 | 0.020997 | 0.021602 |
| Facturation | 0.020905 | 0.024714 | 0.027199 |
| Management Projet | 0.029470 | 0.024252 | 0.023834 |
| Design Workflow | 0.017037 | 0.014024 | 0.013774 |

The loss selector retains update 64. Overall macro loss falls while Facturation loss rises, and final micro loss also rises. These teacher-forced measurements do not establish functional accuracy or select the functional model. All four saved checkpoints, the final alias and the loss-selected alias are present and hash-verified.

IMPLEMENTED: the single reviewer cleared the actual completed-training evidence and comparison admission. PARTIALLY IMPLEMENTED: the Colibri comparison started at 04:21 UTC; its first checkpoint export is running. All five declared Colibri candidates, 0 (actual parent 125), 32, 64, 96 and 128, remain mandatory on the unchanged 133-case primary set. Applicable broader 275/438/48, critical and retained-application gates remain unchanged.

The best verified primary result remains 122/133 (91.73%), with exact arguments 102/111 (91.89%) and critical cases 20/24. Zero of six apps are fully accepted. No model was activated and no next-application optimization started. This completed 128-update correction is separate from the original completed 3,103-update refinement.

[Completed training evidence](../training/reports/facturation-uniform-correction-v1-training-completion.json).

## Balanced correction: midpoint validation complete - 21 October 2026

IMPLEMENTED and verified: the original job completed its scheduled 275-example validation at update 64. The raw log, validation history and saved loss selection agree under replay of the pinned selector; equal-token weighted and unweighted values match.

| Teacher-forced loss, lower is better | Baseline | Update 64 |
| --- | --- | --- |
| Micro | 0.022434 | 0.022095 |
| Application macro | 0.022471 | 0.020997 |
| Facturation | 0.020905 | 0.024714 |
| Management Projet | 0.029470 | 0.024252 |
| Design Workflow | 0.017037 | 0.014024 |

The results are mixed: overall macro loss falls while Facturation loss rises. These are training measurements, not functional accuracy. The loss selector currently retains 64; all five declared Colibri candidates remain required for functional selection.

PARTIALLY IMPLEMENTED: optimization resumed. At 03:29 UTC, 71 of 128 contiguous, finite updates were recorded with the original controller and worker live. The final updates and update-128 validation remain pending. Actual checkpoint-32 integrity was checked and reviewed: 192 finite FP32 tensors, 24 nonzero LoRA-B layers and stable files. This does not establish per-step layer updates or model acceptance. The eight reviewed Logistics sources and bilingual knowledge still match at the midpoint refresh.

Production inference remains healthy and unchanged at capture. The full primary best is still 122/133 (91.73%), with zero of six applications fully accepted. No new functional score, production activation or next-application training is established. Completed-training verification and review still precede the unchanged Colibri and broader acceptance gates.

[Actual midpoint records and verification](../training/reports/facturation-uniform-correction-v1-midpoint.json).

## Balanced correction: initial validation complete - 21 October 2026

IMPLEMENTED and verified: the original server invocation completed its unchanged 275-example initial teacher-forced validation. Micro loss 0.022434 and macro loss 0.022471 exactly reproduce the previous balanced run's unweighted reference, including all three application values. Parent artifacts and validation bytes match. This confirms the expected starting point and does not establish model accuracy.

PARTIALLY IMPLEMENTED: at 02:44 UTC the original controller and worker were live, with the first two of 128 scheduled optimizer updates complete. Both losses are finite and updates are contiguous. The recipe remains unchanged: equal assistant-token weighting, one balanced epoch and 14 CPU threads.

The single reviewer cleared the prepared five-candidate Colibri comparison, which passes 26 offline control tests. A prospective read-only artifact/cleanup collector is also reviewed. Completed-training verification and actual-evidence review remain required before comparison execution. Every declared candidate and applicable primary, broader, critical and retention gate remains mandatory.

The primary best is still 122/133 (91.73%), with zero of six applications fully accepted. Production inference is unchanged, and no next-application optimization has started.

[Initial validation and actual update evidence](../training/reports/facturation-uniform-correction-v1-initial-validation.json).

## Balanced ordinary-SFT correction running - 21 October 2026

IMPLEMENTED and verified: all 128 TRAIN and 275 unchanged validation examples passed server metadata checks, including the full 512-token output reserve. Both capacity-test updates passed across all 24 layers, with 5.555 GiB reported peak RSS. The first unweighted loss exactly reproduces the prior capacity reference. All 31 verifier tests and 46 stage-control cases pass. The single reviewer checked actual preflight/capacity evidence and cleared one fresh training run.

PARTIALLY IMPLEMENTED: the server started the 128-update correction at 02:18 UTC. It uses the existing experimental checkpoint 125 with 96 Facturation, 16 Management Projet and 16 Design Workflow examples, each once. Equal assistant-token weighting is the only numerical change from the earlier balanced correction. Learning rate 0.00001, seed, data, schedule, LoRA and the 14 CPU threads remain unchanged. The current logistics source hashes still match the reviewed metadata.

At 02:24 UTC, the original controller and worker were live, with no optimizer updates or baseline-validation result recorded yet, during initial preparation or baseline validation. This timestamped observation does not distinguish those phases or establish completion.

PLANNED: after completed-training verification and review, compare all declared Colibri candidates 0 (actual 125), 32, 64, 96 and 128 on the unchanged 133-case primary set. Applicable broader 275/438/48 and critical/retention gates remain unchanged. No accuracy improvement is predicted. The primary best remains 122/133 (91.73%), exact arguments 102/111 (91.89%) and critical cases 20/24. Zero of six applications are fully accepted. Production inference has not been replaced, and no next-application training started.

[Launch, prerequisites and timestamped observation](../training/reports/facturation-uniform-correction-v1-launch.json).

## Ordinary-SFT learning test completed; application targets unmet - 21 October 2026

IMPLEMENTED and verified: the server completed 32 optimizer updates over four epochs of the same eight TRAIN examples in 2,830.52 seconds (about 47 minutes), using 14 CPU threads. Equal assistant-token weighting was the only recipe change from the earlier weighted fit. Validation loss worsened from 0.020905 to 0.105029.

The fresh Colibri comparison completed 30 baseline and 30 candidate requests with unchanged cases, labels and scoring. The single reviewer verified actual saved evidence and reproduced every captured response through the frozen provider.

| TRAIN diagnostic | Baseline checkpoint 125 | Ordinary-SFT final 32 |
| --- | --- | --- |
| Exact actions | 23/30 | 24/30 |
| Structured output | 25/30 | 27/30 |
| Eight optimized examples | 6/8 | 8/8 |
| Other TRAIN controls | 17/22 | 16/22 |
| Transport failures | 0 | 0 |

PARTIALLY IMPLEMENTED: the eight-row fit target passes, but other TRAIN controls decline. Two update calls omit a nested closing tag and stop after 97 tokens; these are not output-budget failures. Other errors add an unsupported parameter, invent an unpaid-only filter or use November 31. The parser correctly rejects malformed calls. No business operation executed.

These results do not establish application accuracy or justify promotion. The primary best remains 122/133 (91.73%), exact arguments 102/111 (91.89%) and critical cases 20/24. Zero of six applications are fully accepted. The diagnostic's original workers are stopped, its test ports are free, and production inference remains healthy and unchanged.

PLANNED ONLY: review ordinary-token weighting on the existing balanced 128-row corrective corpus, which includes explicit/omitted unpaid-filter pairs and valid month-end targets. No next numerical recipe is admitted or running. Fresh source/data review and server preflight/resource checks are required. Full primary and broader acceptance gates remain unchanged; no next-application training started.

[Completed ordinary-SFT diagnostic](../training/reports/facturation-uniform-token-fit-v1-completion.json).

## Tool-call closure diagnosis and controlled SFT test - 21 October 2026

IMPLEMENTED and verified: a 30-case Colibri raw-trace replay preserves the earlier final-32 actions, validity, transport outcomes, completion-token counts and finish reasons. Two French update outputs repeat parameters until their output budget; an English update adds forbidden parameters. The trace is decoded text before provider parsing, not pristine token IDs. No business operation executed.

A separate teacher-only diagnostic completed 16 forward passes with zero optimizer updates. All eight final-32 variants favor the opening-angle token over the first function-closing token, despite low average loss. Moving operation last further reduces closure probability. These probabilities use gold prefixes and a BF16 training representation, so they do not predict every exported Colibri output or establish a sole cause. The single reviewer verified the actual evidence. No tokenizer, parser or EOS-token defect is established.

PARTIALLY IMPLEMENTED: a controlled 32-update server test started at 00:24 UTC after all 8 TRAIN and 133 validation examples passed metadata preflight. Its only recipe change is semantic loss weight 4 to 1, giving all assistant target tokens equal weight. Parent checkpoint 125, data, learning rate 0.0001, four epochs, seed, LoRA and evaluation controls remain unchanged. At 00:25 UTC, the original controller and worker were live with zero optimizer updates recorded, during initial preparation or baseline validation. This is a timestamped observation, not a completed run.

No new application accuracy is established. The primary best remains 122/133 (91.73%); zero of six applications are fully accepted. Diagnostic weights cannot be promoted. Production inference remains healthy and unchanged, and no next-application training started.

[Completed diagnosis and new-run observation](../training/reports/facturation-tool-call-closure-diagnostic.json).

## Disposable learning test completed; fit target missed - 20 October 2026

IMPLEMENTED and verified: all 32 optimizer updates completed on the server in 2,869.76 seconds (approximately 48 minutes), including validation. Eight approved Facturation TRAIN examples were used over four complete epochs. Weighted validation loss worsened from 0.038714 to 0.230300; unweighted loss worsened from 0.020905 to 0.131682.

The original comparison completed the fresh baseline and export, then failed a port preflight before final-checkpoint inference. A reviewed continuation reused that evidence and ran only the 30 pending final-checkpoint requests. Training, export and baseline inference were not repeated.

| TRAIN diagnostic | Baseline checkpoint 125 | Final 32 updates |
| --- | --- | --- |
| Exact actions | 23/30 | 26/30 |
| Structured output | 25/30 | 27/30 |
| Eight optimized examples | 6/8 | 7/8 |
| Other TRAIN controls | 17/22 | 19/22 |
| Transport failures | 0 | 0 |

PARTIALLY IMPLEMENTED: the 8/8 fit target failed. Two French update responses exhausted their 512-token output budget; another update added forbidden arguments. One previously correct clarification regressed. These are TRAIN diagnostics, not new application accuracy. The weights remain quarantined and cannot be promoted. The primary best remains 122/133 (91.73%), with zero of six applications fully accepted in this campaign.

The single reviewer verified 113 comparison records and replayed all 60 raw responses through the frozen provider. Completed-training provenance, artifact equality, stopped workers, free test ports and unchanged healthy production were also checked. A separate metadata-only tokenizer check found identical tokenizer files, rendered prompts and token IDs across all 30 requests; it applied no regex patch and did not explain or fix the generation failures.

PLANNED: investigate update generation termination, forbidden arguments and the clarification regression before another full training recipe. No numerical training is currently running, and no next-application training or production activation occurred.

[Completed diagnostic evidence](../training/reports/facturation-train-fit-sanity-v1-completion.json).

## Disposable Facturation learning test started - 20 October 2026

PARTIALLY IMPLEMENTED: a separate 32-update server learning test started at 22:14 UTC after review of its actual preflight. It uses eight byte-preserved approved TRAIN rows, one per semantic family, with four English and four French examples. Four complete epochs use the existing merged experimental checkpoint 125 with a fresh adapter/AdamW optimizer, learning rate 0.0001, rank 16/alpha 32 across 24 layers, BF16 SDPA, checkpointing and 14 CPU threads. The 40 GiB ceiling, zero swap and ten-percent host-RAM reserve remain enforced.

Actual tokenizer/template/Colibri-parser checks pass all eight TRAIN and 133 unchanged Facturation validation examples, with the full 512-token output reserve. At the 22:15 UTC observation, the original controller and worker were live during initial preparation or validation, with zero optimizer updates recorded. The observation does not distinguish those initial phases. This is a timestamped observation.

The purpose is to check whether the existing model can learn exact TRAIN actions before another full recipe. After completed-training review, fresh baseline/final Colibri comparison is planned on the 30 established TRAIN probes: eight fit rows and 22 other TRAIN controls. Neither subset is claimed unseen by the experimental parent. Diagnostic weights cannot be promoted, and no new application accuracy is established. The latest completed primary best remains 91.73%; zero of six applications are fully accepted by this campaign.

[Launch and preflight evidence](../training/reports/facturation-train-fit-sanity-v1-launch.json).

## Facturation correction completed; primary targets missed - 20 October 2026

IMPLEMENTED and verified: the server completed all 128 scheduled optimizer updates, one epoch and validation at 0/64/128 in 6,767.41 seconds (approximately 1 hour 53 minutes). Exposure was 96 Facturation, 16 Management Projet and 16 Design Workflow examples, each once. The same shared Qwen3.5-0.8B and reviewed BF16/LoRA recipe were used. The earlier launch snapshot is superseded by this completion.

All five declared Colibri primary candidates completed: 532 new generated cases and 133 cached baseline cases. The frozen scorer and labels are unchanged.

| Candidate | Correct actions | Exact arguments | Structured output | Critical cases |
| --- | --- | --- | --- | --- |
| 0 (actual 125, reused) | 122/133 (91.73%) | 102/111 (91.89%) | 132/133 | 20/24 |
| 32 | 119/133 (89.47%) | 98/111 (88.29%) | 132/133 | 21/24 |
| 64 | 118/133 (88.72%) | 96/111 (86.49%) | 133/133 | 21/24 |
| 96 | 117/133 (87.97%) | 95/111 (85.59%) | 133/133 | 21/24 |
| 128 | 118/133 (88.72%) | 96/111 (86.49%) | 133/133 | 21/24 |

The selector retains logical step 0, meaning the cached experimental checkpoint 125. Every candidate fails necessary primary targets. The 275 shared development, 438 regression and 48 additional controls are explicitly NOT EXECUTED under the frozen rejection policy. Lower teacher-forced macro loss and valid JSON did not establish correct arguments or 95% accuracy.

The completion audit reproduces all 12 raw shards and binds 345 evidence/source files. Fresh server checks verify stopped evaluation worker units, free evaluation ports and healthy production inference with its original start time. No production model activation or next-application training occurred. This campaign still has zero of six fully accepted applications; no new Management Projet or Design Workflow acceptance score is established.

The original separate search-refinement run completed 3,103 updates, not 1,587. That count is distinct from this 128-update correction. The queued previous-result selection schema fix remains local and undeployed, with its earlier 937 native backend tests passing.

PLANNED: investigate the remaining argument errors using approved TRAIN diagnostics before another reviewed server experiment. Keep Facturation first and retain the unchanged acceptance gates.

[Completed correction results](../training/reports/facturation-semantic-correction-v2-functional-comparison.json).

## Semantic pilot completed; primary targets missed - 20 October 2026

IMPLEMENTED and verified: all 500 scheduled optimizer updates completed in 16,874.54 seconds (approximately 4.69 hours). The single reviewer verified actual completion, all seven saved adapter directories and the unchanged recipe. The epoch used 316 Facturation, 112 Management Projet and 72 Design Workflow examples, each once. Earlier progress sections below are historical observations, superseded by this completion.

All five declared Colibri primary candidates completed, including the cached experimental parent. The comparison took 3,873 seconds and produced 532 new cases plus 133 cached baseline cases.

| Candidate | Correct actions | Exact arguments | Structured output | Critical cases |
| --- | --- | --- | --- | --- |
| 0 (actual 2048, reused) | 121/133 (90.98%) | 100/111 (90.09%) | 132/133 | 21/24 |
| 125 | 122/133 (91.73%) | 102/111 (91.89%) | 132/133 | 20/24 |
| 250 | 122/133 (91.73%) | 101/111 (90.99%) | 132/133 | 21/24 |
| 375 | 118/133 (88.72%) | 97/111 (87.39%) | 132/133 | 21/24 |
| 500 | 115/133 (86.47%) | 93/111 (83.78%) | 133/133 | 22/24 |

The unchanged selector chooses 125, but every candidate fails necessary primary targets. The 275 shared development, 438 regression and 48 additional controls are explicitly NOT EXECUTED. This run gives no new Management Projet or Design Workflow acceptance score. Zero of six applications are fully accepted; production inference remains unchanged.

IMPLEMENTED as diagnosis only: final checkpoint 500 completed 30 fixed exact TRAIN rows, with 27 exact actions, 28 schema-valid responses, zero transport failures and 30 matching prompt-token counts. Raw outputs contain one shortened literal and two unrequested end-date strings. These are generation errors, not evidence of a parser or label defect. The latter two preserve unpaid correctly. The single reviewer reproduced the saved raw evidence; workers stopped and production remained unchanged.

PLANNED: a paired generic-instruction check across all 30 rows, preserving successful controls and explicit nullable edits. No new numerical run or application activation has started. Separately, the previous-result selection schema correction is committed in an isolated local branch, with 937 native backend tests passing; it is not integrated, pushed or deployed.

[Completed primary comparison](../training/reports/facturation-semantic-pilot-v1-functional-comparison.json) and [TRAIN diagnostic](../training/reports/facturation-semantic-pilot-v1-train-diagnostic.json).

## Checkpoint 125 and native backend checks - 20 October 2026

IMPLEMENTED and verified: the first scheduled Facturation checkpoint was saved correctly. All 192 saved adapter tensors are finite FP32, with nonzero LoRA_B weights across all 24 trained layers. Rank 16 and alpha 32 match the recipe; stable file hashes and all 26 bound source files were checked. The single reviewer found no issues in the captured integrity evidence.

The current native Facturation assistant suite passed 896 tests across 20 modules, with zero failures, errors or skips, including 14 logistics knowledge cases. It used isolated synthetic local fixtures and the exact application-pinned 0.2.3 package. The stale local 0.1.0 installation was then corrected offline; its installed files match the tested wheel. Application source and production were unchanged. These backend checks are separate from model accuracy and complete production-security acceptance.

PARTIALLY IMPLEMENTED: the original 500-update run remains active. Checkpoint integrity does not establish functional accuracy. Actual successful completion and its evidence review are still required before the prepared Colibri comparison. No new accuracy score, model acceptance, production activation or next-application training is established; zero of six applications are fully accepted.

[Checkpoint and backend regression evidence](../training/reports/facturation-semantic-pilot-v1-checkpoint125-backend-checks.json).

## Initial validation complete; optimization active - 20 October 2026

IMPLEMENTED and verified at capture: the original 500-update Facturation invocation completed its unchanged 275-example initial teacher-forced validation and then its first finite optimizer update. The initial loss result exactly reproduces the previous experiment on the same merged checkpoint-2048 parent and validation bytes. This is a reproducibility check, not an accuracy improvement.

The separate completion observer and prospective Colibri comparison controls are prepared and cleared by the single reviewer. All 24 offline guards pass in the main thread. The reviewer independently reran 19 read-only tests and inspected five filesystem tests. All five functional candidates remain mandatory: logical 0 (actual 2048), 125, 250, 375 and 500. Frozen cases, scoring, thresholds, original-reference retention and applicable 275/438/48 gates stay unchanged.

PARTIALLY IMPLEMENTED: 1 of 500 optimizer updates is recorded at this observation; the epoch remains running. Actual successful completion, saved-adapter verification and completed-training review are required before export or inference. No new functional accuracy or model acceptance is established. Zero of six applications are fully accepted; production remains healthy and unchanged, and no next-application training started.

[Initial validation and prepared comparison checks](../training/reports/facturation-semantic-pilot-v1-initial-validation.json).

## Short semantic numerical pilot started - 20 October 2026

IMPLEMENTED and verified: the 500-row Facturation pilot preserves 384 earlier TRAIN rows byte-for-byte and adds all 116 reviewed English/French semantic contrasts. It contains 316 Facturation, 112 Management Projet and 72 Design Workflow rows. The retained native replay covers 18 tools, 174 measured features, 51 priority conjunctions and 58 offered-tool bundles; it covers 119 of 418 full conjunctions. These are structural inventory counts, not model accuracy.

All 16 new assembly/recipe tests pass. Actual server preflight passes every 500 TRAIN and 275 unchanged validation example. Both capacity updates pass on the 7,745-token longest row, with finite gradients and real weight changes in all 24 layers. Peak job memory is 5.90 GiB. The single reviewer cleared the exact source/data, saved actual preflight/capacity evidence and numerical admission; review did not independently contact the server.

PARTIALLY IMPLEMENTED: the distinct server training job is running, with 0 of 500 optimizer updates recorded at this launch capture. It uses the existing merged experimental checkpoint 2048, a fresh adapter/optimizer, learning rate 0.000002, 14 CPU threads, BF16 SDPA, rank 16/alpha 32 across 24 layers, semantic weight 4 and nonreentrant checkpointing. Saved candidates are 125, 250, 375 and 500; teacher-forced validation is 0, 250 and 500. A ten-percent host-RAM floor and zero job swap remain enforced.

No new functional score is established. Every declared candidate still needs unchanged Colibri evaluation. Existing best primary results remain 121/133 full actions and 100/111 exact arguments, below target. Zero of six applications are fully accepted. Production inference remains unchanged and no next-application training started.

[Actual launch and prerequisite evidence](../training/reports/facturation-semantic-pilot-v1-training-launch.json).

## Raw TRAIN diagnostic and wording correction - 20 October 2026

IMPLEMENTED and verified: the existing experimental checkpoint 2048 completed 30 fixed English/French TRAIN analogues through three isolated Colibri workers. The unchanged native provider reproduces 19 exact actions, 25 schema-valid responses and zero transport failures; all 30 prompt-token counts match. This targeted diagnostic is not a new held-out or primary application score. The exact invocation completed successfully; all workers stopped, six original processes are gone and production is healthy and unchanged. The single reviewer independently reproduced the saved evidence and scoring.

The raw update outputs omit the required operation and flatten change fields instead of using the supported changes object; at least one also truncates the requested text. Quote failures include the wrong month and an unsupported period argument. Review also found two TRAIN wording ambiguities: bounded payments lost the parent’s latest-payment cue, and current-month quotes did not distinguish the full calendar month from month-to-date. The original 19/30 result is preserved, including one native-equivalent payment call that remains a strict mismatch.

IMPLEMENTED as corrected preparation only: v2 keeps the original generator and evidence unchanged, clarifies 20 latest-payment requests and 12 calendar/month-to-date requests, and changes only two explicitly month-to-date target end dates. All 704 replay rows and 275 validation rows remain byte-identical. The new corpus still contains 116 additions and 820 total rows. All 37 affected tests pass; the single reviewer cleared the source and exact corpus. Actual server preflight passes all 820/275 examples, with maximum full lengths 7,745/7,496.

PARTIALLY IMPLEMENTED: no new numerical training, model acceptance, activation or next-application training has started. A smaller corrective numerical pilot and its resource admission remain to be selected and reviewed. The existing primary best remains 121/133 complete actions and 100/111 exact arguments. Zero of six applications are fully accepted.

[Raw diagnostic](../training/reports/facturation-semantic-contrasts-v1-diagnostic.json) and [corrected preparation](../training/reports/facturation-semantic-contrasts-v2-preparation.json).

## TRAIN semantic contrasts and server preflight prepared - 20 October 2026

IMPLEMENTED and verified as preparation only: a reproducible generator adds 116 focused Facturation TRAIN examples, balanced at 58 English and 58 French. All 704 existing replay rows remain byte-for-byte unchanged; the prepared corpus contains 820 rows (636 Facturation, 112 Management Projet, 72 Design Workflow). All 275 shared development rows and frozen scoring remain unchanged.

The eight families cover inclusive/exclusive date boundaries, user list/detail navigation, logistics roles, complete multiword remarks, unpaid-filter omission pairs, ambiguous/explicit previous-result selection, relative quote months and current-language unsupported clarifications. New records retain source permission schemas, trusted context and history. Parent annotations are replaced with metadata describing the new example.

All 26 preparation tests pass. Actual server tokenizer/template preflight passes all 820 TRAIN and 275 validation examples, including native parser round-trip, Colibri generation-prefix parity, loss/semantic alignment and output budgets. Maximum full lengths are 7,745 and 7,496 tokens. This check loads no model weights, generates no model response and performs zero optimizer updates. Production remains healthy and unchanged.

The single reviewer cleared the source, exact corpus, saved preflight evidence and publication. The main thread performed the server check; review did not independently contact the server.

PARTIALLY IMPLEMENTED: a bounded Colibri TRAIN-analogue raw-output diagnostic remains pending. No new numerical recipe or training run has started. There is no new measured functional accuracy. The previous best remains 121/133 complete actions (90.98 percent) and 100/111 exact arguments (90.09 percent), below target. Zero of six applications are fully accepted. Remaining stock, staff and payment search distinctions are retained and tracked rather than claimed newly corrected.

[Preparation and tokenizer evidence](../training/reports/facturation-semantic-contrasts-v1-preparation.json).

## Corrective epoch and primary comparison completed - 20 October 2026

IMPLEMENTED and verified by the main evidence audit: all 704 scheduled updates completed successfully, followed by every declared Colibri primary candidate. The epoch used 520 Facturation, 112 Management Projet and 72 Design Workflow examples, with 14 CPU threads. Trainer execution took 22,985.47 seconds (approximately 6.38 hours); the comparison took 3,881 seconds. These are completed work records, not acceptance.

| Candidate | Correct actions | Exact arguments | Structured output | Critical cases |
| --- | --- | --- | --- | --- |
| 0 (actual 2048, reused) | 121/133 (90.98%) | 100/111 (90.09%) | 132/133 | 21/24 |
| 176 | 119/133 (89.47%) | 98/111 (88.29%) | 132/133 | 21/24 |
| 352 | 117/133 (87.97%) | 96/111 (86.49%) | 132/133 | 21/24 |
| 528 | 117/133 (87.97%) | 96/111 (86.49%) | 133/133 | 21/24 |
| 704 | 117/133 (87.97%) | 97/111 (87.39%) | 132/133 | 20/24 |

The unchanged selector retains logical 0, the previously measured actual 2048 experimental parent. It is still unaccepted. All candidates fail necessary primary targets, so the 275 shared development, 438 regression and 48 additional controls are explicitly NOT EXECUTED. This attempt provides no new Management Projet or Design Workflow acceptance score. Zero of six applications are fully accepted by the training gates.

The audit reproduces 532 new cases plus 133 cached baseline cases, exact frozen shard bytes, summaries, all 201 reviewed controls and before/after artifacts. A separate live read-only check verifies all four completed exports, all 12 evaluation workers stopped, all 24 original processes gone and test ports free. Production is healthy and unchanged. The single reviewer independently reproduced the saved evidence and cleared this result report. The live server check was performed separately. No native business operation or new backend security test ran in this comparison.

PARTIALLY IMPLEMENTED: Facturation remains below 95 percent. A TRAIN-only contrast design is being corrected for date boundaries, list/detail navigation, entity roles, complete text values, unpaid-filter omission and ambiguous/explicit selection pairs. Remaining quote, stock and search-field mechanisms are tracked. The design has not generated a new corpus or started another training run. No next-application training or model activation has started.

[Completed primary model results](../training/reports/facturation-entity-pilot-v2-functional-comparison.json).

## Historical corrective launch observation - 20 October 2026

This launch snapshot is superseded by the completed comparison above.

IMPLEMENTED and verified at launch: one server-only 704-update epoch is running from the attested experimental checkpoint-2048 merged FP32 parent, with a fresh adapter and optimizer. The original checkpoint 600 remains the separate retention reference. The actual trainer command, model/data identities, source/configuration and original service invocation are captured in 31 immutable launch records. At that observation, initial preparation/validation is incomplete and zero of 704 optimizer updates have completed.

The run uses 520 Facturation, 112 Management Projet and 72 Design Workflow examples, 14 CPU threads, BF16 SDPA, rank 16/alpha 32 across all 24 layers, semantic loss weight 4 and a learning rate of 0.00001. Nonreentrant gradient checkpointing is enabled. Saved checkpoints are 176, 352, 528 and 704; teacher-forced validations are 0, 352 and 704. The child timeout is 12 hours and the service limit is 14 hours. The 40 GiB hard limit and zero job swap are guarded by a ten-percent host-memory reserve at admission.

Both two-update capacity measurements passed on the same longest 7,745-token TRAIN example. Without checkpointing, cgroup peak was 39.5336 GiB; with checkpointing, it was 8.0296 GiB. The checkpointed two-update total took 11.0286 percent longer, with identical recorded losses and gradient norms. This supports the lower-memory choice; it does not establish whole-epoch equivalence, completion or generated-action accuracy. Preflight passed all 704 TRAIN and 275 validation rows.

PARTIALLY IMPLEMENTED: the epoch and subsequent model evaluation remain incomplete. The prospective comparison coordinator and its six offline orchestration guards are prepared and reviewed. They require actual successful training completion and an independent evidence review before any new Colibri export or inference. All five declared development candidates must complete; an eligible selection still needs the unchanged shared development, regression and additional controls. Zero of six applications are fully accepted. Production inference is healthy and unchanged; no next-application training or model activation has started.

## Pilot comparison completed - 20 October 2026

IMPLEMENTED and verified: all declared candidate comparisons and the selected checkpoint's 275 shared development, 438 regression and 48 additional cases finished. The single reviewer independently reproduced every score and gate, checked all 18 ordered shards and 141 unchanged frozen controls, and verified the recorded model/runtime/worker evidence and cleanup.

Facturation remains below target: 111/133 full actions (83.46 percent) and 89/111 exact arguments (80.18 percent) on development; 97/108 full actions (89.81 percent) on regression; 10/16 full actions (62.5 percent) on additional controls. The additional controls selected the correct tool in all 16 cases, with eight of 14 eligible exact arguments matching. Management Projet fails the original-reference retention check. Design Workflow retains development behavior but fails broader model gates. All three final model gates fail; zero of six applications are fully accepted. No model was activated.

PARTIALLY IMPLEMENTED: at the subsequent recorded preflight observation, all 704 corrective TRAIN and 275 unchanged validation rows passed tokenizer/template, runtime-prefix, loss/semantic alignment and output-budget checks. Maximum lengths were 7,745 and 7,496 tokens. This is not optimizer training or measured successor accuracy. Actual capacity evidence, numerical admission, successful training and the complete prospective functional comparison remain required.

[Completed model results](../training/reports/facturation-entity-pilot-v1-functional-comparison.json).

## Corrective numerical recipe prepared - 19 October 2026

IMPLEMENTED as admission code: the 704-update recipe checks all 520 Facturation, 112 Management Projet and 72 Design Workflow examples are trained exactly once. It checks the unchanged tokenizer/Colibri preflight, measured capacity recipe, finite update history, source and environment identities, and validation at steps 0, 352 and 704. Saved checkpoints are 176, 352, 528 and 704. Twelve new public recipe tests pass.

The distinct private controller and launcher are prepared with a 12-hour child budget and 14-hour service budget. Nine local private guard tests pass. They include the actual frozen concurrency guard, complete input-inventory requirements, owned terminal service identity, FP32 header checks and duplicate-dispatch rejection. The single reviewer identified and the implementation fixed the service naming and incomplete evidence-inventory guards before any dispatch.

A read-only server observation independently verified the actual experimental checkpoint-2048 merged FP32 files and original checkpoint-600 reference. Each has 473 unique FP32 tensors; their identities differ. The experimental export uses the original checkpoint 600 plus its already merged checkpoint-2048 adapter. The adapter, completed training report and Colibri serving/runtime bytes match the earlier evidence. No model weights were loaded and no numerical job was started for this observation.

PARTIALLY IMPLEMENTED: the actual next run remains unbound. The current comparison must finish and receive evidence review. Fresh 704/275 preflight, the chosen mode's capacity measurement and reviewed numerical admission are still required. The proposed capacity ceiling is 40 GiB only when it preserves at least ten percent of host RAM; the CPU quota remains 14 of 16 logical CPUs. No speedup, new accuracy, accepted application or model activation is established.

## Corrective checkpoint selection prepared - 19 October 2026

IMPLEMENTED and verified as selection code only: a separately versioned selector supports saved checkpoints 176, 352, 528 and 704 without inventing validation losses for checkpoints 176 or 528. Every declared 133-case development candidate, including the actual experimental checkpoint-2048 parent as step 0, must complete. The original checkpoint-600 regression reference stays separate.

Candidates meeting every unchanged primary development target take priority, followed by full-action accuracy, structured validity and the earliest step. Tool, full-action and exact-argument targets remain 95 percent; valid structure remains 99 percent, and every existing critical planner and clarification case must match. If no candidate meets these necessary targets, the future comparison reports a primary rejection and leaves later checks explicitly unexecuted. An eligible selection still requires all 275 shared development, 438 regression and 48 additional cases, with no acceptance reranking.

The single review caught a loader mismatch before numerical execution: direct imports used current application clarification wording. The fixed loader executes the pinned historical clarification and scoring implementations in isolated globals. All three completed pilot candidates now reproduce their entire frozen score reports and published assessments exactly. All 27 local selection tests pass, including the actual saved checkpoint-72 evidence and historical English/French replies. No new inference or accuracy improvement is established by these checks.

PARTIALLY IMPLEMENTED: the prospective policy deliberately leaves actual FP32 identities and resource choices unbound and is rejected by the selector in that state. A distinct numerical controller/launcher, fresh parent/reference attestation, actual preflight and capacity evidence, and execution review remain required. The current comparison, all 141 frozen controls, production inference and the next-application queue remain unchanged.

[Prospective policy and incomplete admission](../training/reports/facturation-entity-pilot-v2-evaluation-policy.json).

## Pilot development comparison and full replay preparation - 19 October 2026

IMPLEMENTED and verified: all three successor checkpoints completed the unchanged 133-case Facturation development evaluation. Correct full actions were 111/133 (83.46 percent) at step 72, 107/133 (80.45 percent) at step 144 and 103/133 (77.44 percent) at step 216. The unchanged selector chose step 72. Its exact arguments were 89/111 (80.18 percent), with 22/24 critical planner cases. The single reviewer independently verified the scores, all candidate evidence, selection and frozen controls.

PARTIALLY IMPLEMENTED: this pilot misses the primary development targets. At this recorded observation, its planned shared development and remaining regression comparisons are still running. Selection is not acceptance. Zero of six applications are fully accepted, and production inference remains unchanged.

IMPLEMENTED and verified as data preparation only: a larger conditional replay contains 704 rows, with 520 Facturation, 112 Management Projet and 72 Design Workflow examples. It preserves every row from the preceding 384-row candidate. Its 448-row Facturation replay covers all 418 recorded structural argument conjunctions, all 174 measured marginals, all 51 designated critical/exact-lookup conjunctions, all 25 edit/delete combinations and all 58 offered-tool schema bundles. All 275 development bytes and 141 frozen controls remain unchanged. The recorded structural sampling omissions are closed; complete semantic, language, context and value coverage is not established.

All 49 affected synthetic tests pass, including the sufficient-budget coverage check. This preparation neither trains nor accepts a model. The intended experimental parent remains the prior unaccepted checkpoint 2048, subject to fresh FP32 attestation, completion of the current comparison and new numerical/evaluation review. The current comparison and next-application queue remain unchanged.

[Actual development results](../training/reports/facturation-entity-pilot-v1-development-comparison.json) and [complete recorded TRAIN inventory preparation](../training/reports/facturation-entity-pilot-v2-full-inventory-preparation.json).

## Optional Facturation replay prepared - 19 October 2026

IMPLEMENTED and verified as local data preparation only: an optional 128-row Facturation replay extends the conditional corpus to 384 rows, consisting of 200 Facturation, 112 Management Projet and 72 Design Workflow examples. All 216 original pilot rows remain byte-preserved. The default 256-row corpus still produces identical train, validation and retained-plan bytes. The 275 development rows and frozen comparison controls remain unchanged.

TRAIN-only selection covers all 18 Facturation tools, 174 measured marginal features, all 25 edit/delete resource and field-shape combinations, all 51 designated critical or exact-lookup conjunctions, and all 58 distinct offered-tool schema bundles. It covers 119 of 418 full argument conjunctions; the remaining 299 are explicitly listed in the private retained plan. The broader feature definition includes five resource codes from schemas that use plain strings. These inventory counts are not model accuracy or semantic/security coverage.

Forty-nine affected synthetic tests pass. Source/data changes, duplicate/development inputs, missing mandatory coverage and output reuse are rejected. Model identity and failure evidence remain unbound. No further numerical work, model acceptance, production activation or next-application training is authorized by this preparation. The current Colibri comparison continues unchanged.

[Optional replay preparation and limitations](../training/reports/facturation-entity-pilot-v2-facturation-replay-preparation.json).

## Entity pilot training completed - 19 October 2026

IMPLEMENTED and verified: the server-only pilot completed all 216 scheduled updates and the final 275-case validation. Each of Facturation, Management Projet and Design Workflow received 72 unique TRAIN examples. All updates are contiguous and finite. The final adapter equals saved checkpoint 216, and checkpoints 72, 144 and 216 match the earlier finite-tensor inspections. The trainer recorded approximately 2.49 hours of execution.

Final weighted semantic losses are 0.07235212742 for Facturation, 0.05521192138 for Management Projet and 0.04884412790 for Design Workflow. Each remains above its original checkpoint-600 baseline; the diagnostic loss selector therefore keeps baseline step 0. These are teacher-forced losses, not accuracy percentages. Every saved successor still requires its declared Colibri functional comparison.

PARTIALLY IMPLEMENTED: the single reviewer cleared the completed evidence, and the sequential Colibri comparison started with checkpoint 72. Generated-action accuracy and acceptance remain pending. No new generated-action accuracy, accepted application, next-application training or production activation is claimed. Production inference is healthy and unchanged.

[Actual training completion](../training/reports/facturation-entity-pilot-v1-training-completion.json).

## Conditional corrective corpus prepared - 19 October 2026

IMPLEMENTED and verified as data preparation only: a separate 256-row corpus preserves every row from the current 216-row pilot and adds 40 approved Management Projet TRAIN rows. All 72 Facturation and 72 Design Workflow rows remain byte-identical. The 112-row Management Projet sample covers all 106 measured shape/enum features; Design Workflow retains all 61. Each retained application covers nine native tools. All 275 development rows and 141 frozen control files remain unchanged.

Thirty-five synthetic data tests pass, including twelve tests for the new preparer. The preparer rejects source changes, duplicate/development inputs, missing measured coverage and invalid output locations. Missing retained language metadata remains missing. The approved original reference and helper sources are pinned; changes are rejected before preparing the candidate. Shape coverage does not establish semantic retention or model accuracy.

PLANNED and conditional: a later experiment may use the prior unaccepted checkpoint 2048 as an experimental parent, with original checkpoint 600 retained as a regression reference. No model is bound, trained or accepted by this preparation. The current pilot must first complete its unchanged comparison unsuccessfully; a separate numerical protocol, actual model attestation and review remain required. The current pilot, production model and next-application queue are unchanged.

[Conditional preparation and limitations](../training/reports/facturation-entity-pilot-v2-corrective-preparation.json).

## Focused-app reporting correction - 19 October 2026

IMPLEMENTED and verified as reporting only: `report_focused_stage_v1.py` separates the focused application's recorded model gate, retained development results, all evaluated applications and six-app model coverage. It does not reuse the legacy focused flag that can be suppressed by another application's failure. The frozen pilot driver, checkpoint selection, model scores and acceptance thresholds remain unchanged.

Eight synthetic regression tests pass, including mixed application results, retention failure, incomplete or inconsistent evidence, and the distinction between six model gates and native security. A read-only run against the completed 3,103-update comparison still reports Facturation and global model gates as failed. Native security is unassessed by this reporter; training and activation are never authorized by its output.

PARTIALLY IMPLEMENTED: the entity pilot and its generated-action comparison remain incomplete. No new accuracy, focused-model acceptance or next-application training is claimed.

## Entity pilot initial validation completed - 19 October 2026

IMPLEMENTED and verified: the 275-case initial validation finished and optimization began. The captured observation contains six of 216 planned updates. Initial losses match the original checkpoint-600 baseline exactly for Facturation, Management Projet and Design Workflow, with unchanged model artifacts, validation bytes and declared precision/configuration.

The separate Colibri comparison preparation passed 39 offline tests and independent review of its 141-file closure, including all 118 historical controls. Actual successful training completion and an independently reviewed completion packet are required before export or inference.

PARTIALLY IMPLEMENTED: no new generated-action accuracy has been measured, no successor checkpoint is available in this observation and zero of six applications are fully accepted. Production inference remains healthy and unchanged.

[Initial validation observation](../training/reports/facturation-entity-pilot-v1-initial-validation.json).

## Entity pilot started - 19 October 2026

IMPLEMENTED and verified: the server-only 216-update pilot has an actual training process and original checkpoint-600 model provenance. The captured launch observation has zero optimizer updates; initial validation is not yet complete. The shared model is unchanged in production.

Tokenizer/Colibri preflight passed all 216 TRAIN and 275 unchanged validation rows, including schema round-trip, runtime-prefix parity, loss/semantic alignment and serving output budgets. Maximum lengths were 3,320 and 7,496 tokens. All 54 preparation tests and 11 offline launch guard tests passed. The sole reviewer cleared the actual preflight evidence before numerical dispatch.

PARTIALLY IMPLEMENTED: training completion and every functional acceptance gate remain pending. All three planned successor checkpoints must be compared; the separate comparison executor still needs adaptation and review. Zero of six apps are fully accepted. No next-application training or automatic model activation started.

[Actual pilot launch](../training/reports/facturation-entity-pilot-v1-launch.json).

## Small entity pilot prepared - 19 October 2026

IMPLEMENTED and verified: prepared 72 TRAIN-only Facturation entity-copying examples from 18 distinct source rows, with 36 English and 36 French requests. Client names, article terms/references and payment search literals vary together with their target arguments. Native schemas, argument keys, filters, trusted context and history remain unchanged.

The isolated pilot corpus contains 216 rows: those 72 examples plus 72 byte-preserved TRAIN rows from each of Management Projet and Design Workflow. Each retained sample covers all nine native tools. Selection uses TRAIN-only tool and shape/enum coverage with stable hash ties. Nine MP features remain uncovered; missing source language metadata stays missing. The original 275-row validation split is byte-identical.

All 54 generator regression tests and seven offline preflight guard tests passed. The single reviewer independently reproduced both prepared corpora. PARTIALLY IMPLEMENTED: server tokenizer preflight, numerical training, Colibri evaluation and acceptance remain pending. Planned training is one 216-update epoch from the original checkpoint 600, with checkpoint comparisons at 72, 144 and 216. Preparation does not predict 95 percent accuracy. Zero of six applications are fully accepted.

[Preparation results](../training/reports/facturation-entity-pilot-v1-preparation.json) and [separate evaluation policy](../training/reports/facturation-entity-pilot-v1-evaluation-policy.json).

## Full refinement evaluation rejected - 19 October 2026

IMPLEMENTED and verified: all eight frozen candidates completed the Colibri development comparison. Checkpoint 2048 was selected, then completed 275 shared development cases, 438 held-out cases and 48 additional controls. The evaluation process exited successfully; the model failed overall acceptance.

| Application | Development full actions | Held-out full actions | Held-out exact arguments | Additional controls |
|---|---:|---:|---:|---:|
| Facturation | 121/133 (90.98%) | 100/108 (92.59%) | 78/86 (90.70%) | 9/16 (56.25%) |
| Management Projet | 75/78 (96.15%) | 191/200 (95.50%) | 144/148 (97.30%) | 16/16 (100.00%) |
| Design Workflow | 64/64 (100.00%) | 122/130 (93.85%) | 92/100 (92.00%) | 12/16 (75.00%) |

PARTIALLY IMPLEMENTED: zero of six applications are fully accepted. Management Projet regressed against the original development baseline and also failed held-out critical and clarification checks. Contracts, Gestion Magasin and Reservation were not trained by this refinement. All comparison workers stopped cleanly and production inference remained healthy and unchanged.

PLANNED: diagnose generalization using TRAIN and development evidence, review the correction, then run further server-only training and unchanged acceptance gates. No next-application training or model activation has started.

[Complete functional comparison](../training/reports/facturation-search-refinement-functional-comparison.json).

## Refinement training completed - 19 October 2026

IMPLEMENTED and verified: the original Facturation-focused run completed all 3,103 updates, one full scheduled epoch and all eight development-validation checkpoints. The terminal result is successful. The single reviewer verified the original launch and input hashes, report provenance, finite contiguous updates, all candidate adapters, the final adapter's saved-weight identity and the unchanged evaluation controls. Runtime was approximately 27.03 hours on 14 CPU threads.

The schedule contained 2,069 Facturation examples plus 709 Management Projet and 325 Design Workflow replay examples. This is one shared-model refinement run. Contracts, Gestion Magasin and Reservation were not trained by this run.

Final weighted semantic loss was 0.05059110220 for Facturation, 0.07276691810 for Management Projet and 0.05326378849 for Design Workflow. These are teacher-forced losses, not accuracy percentages. Checkpoint 512 remains selected by application-macro loss as a diagnostic only. The Colibri functional comparison must include the original checkpoint 600 baseline and every saved successor at steps 512, 1024, 1536, 2048, 2560, 3072 and 3103.

PARTIALLY IMPLEMENTED: functional accuracy, exact arguments, structured output, retained-app regression and held-out acceptance remain unverified for this run at the completion observation. Zero of six applications are fully accepted. No production model was activated and no later-application training started.

[Training completion and remaining acceptance gates](../training/reports/facturation-search-refinement-training-completion.json).

## Sixth refinement validation completed - 19 October 2026

IMPLEMENTED and verified: checkpoint 3072 completed the unchanged 275-case development validation. The captured observation contains 3,077 contiguous finite updates after optimization resumed. All earlier validation history remains unchanged. The adapter matches its initial saved-weight hash and contains 7,127,040 finite values across 192 tensors and 24 layers, with a complete payload and no all-zero tensors. The single reviewer verified the captured evidence, all ten bound inputs and the unchanged evaluation controls.

Facturation weighted semantic validation loss decreased by 5.65% from checkpoint 2560. Management Projet and Design Workflow losses increased by 7.78% and 24.61%, respectively. Relative to initial validation, changes are -17.65%, +36.93% and +24.08%, respectively. These are teacher-forced loss changes, not accuracy scores. The application-macro loss is 0.05860072274; checkpoint 512 remains selected by loss. All three weighted losses remain above checkpoint 512. Every scheduled candidate, including 3072, remains mandatory in the pending functional comparison.

The checkpoint-save to history-record span was 1,136.47 seconds and includes validation and bookkeeping. No selected-adapter save occurred at this checkpoint.

PARTIALLY IMPLEMENTED: the original 3,103-update run was incomplete at the captured observation, with the final periodic validation at 3103 still pending. Candidate export, Colibri generation, functional accuracy and retained-app regression acceptance remain pending. Zero of six applications are fully accepted. Production inference and the original evaluation inputs, scorer and provider remain unchanged; no later-application training started.

[Sixth validation and checkpoint integrity evidence](../training/reports/facturation-search-refinement-sixth-validation.json).

## Fifth refinement validation completed - 19 October 2026

IMPLEMENTED and verified: checkpoint 2560 completed the unchanged 275-case development validation. The captured observation contains 2,565 contiguous finite updates after optimization resumed. All earlier validation history remains unchanged. The adapter matches its initial saved-weight hash and contains 7,127,040 finite values across 192 tensors and 24 layers, with a complete payload and no all-zero tensors. The single reviewer verified the captured evidence, all ten bound inputs and the unchanged evaluation controls.

Facturation weighted semantic validation loss increased by 32.06% from checkpoint 2048. Management Projet and Design Workflow losses decreased by 8.26% and 3.55%, respectively. Relative to initial validation, changes are -12.71%, +27.04% and -0.43%, respectively. These are teacher-forced loss changes, not accuracy scores. The application-macro loss is 0.05440315349; checkpoint 512 remains selected by loss. All three weighted losses remain above checkpoint 512. Every scheduled candidate, including 2560, remains mandatory in the pending functional comparison.

The checkpoint-save to history-record span was 1,131.73 seconds and includes validation and bookkeeping. No selected-adapter save occurred at this checkpoint.

PARTIALLY IMPLEMENTED: the original 3,103-update run remains incomplete, with the next periodic validation at 3072. Candidate export, Colibri generation, functional accuracy and retained-app regression acceptance remain pending. Zero of six applications are fully accepted. Production inference and the original evaluation inputs, scorer and provider remain unchanged; no later-application training started.

[Fifth validation and checkpoint integrity evidence](../training/reports/facturation-search-refinement-fifth-validation.json).

## Fourth refinement validation completed - 19 October 2026

IMPLEMENTED and verified: checkpoint 2048 completed the unchanged 275-case development validation. The captured observation contains 2,405 contiguous finite updates after optimization resumed. All earlier validation history remains unchanged. The adapter contains 7,127,040 finite values across 192 tensors and 24 layers, with a complete payload and no all-zero tensors. The single reviewer verified the captured evidence, all ten bound inputs and the unchanged evaluation controls.

Facturation weighted semantic validation loss decreased by 33.90% from initial validation and by 24.99% from checkpoint 1536. Management Projet loss increased by 38.48% from initial validation and by 28.26% from checkpoint 1536. Design Workflow loss increased by 3.24% and 40.10%, respectively. These are teacher-forced loss changes, not accuracy scores. The application-macro loss is 0.05254460849; checkpoint 512 remains selected by loss. Every scheduled candidate, including 2048, remains mandatory in the pending functional comparison.

The checkpoint-save to history-record span was 1,126.05 seconds and includes validation and bookkeeping. No selected-adapter save occurred at this checkpoint.

PARTIALLY IMPLEMENTED: the original 3,103-update run remains incomplete, with the next periodic validation at 2560. Candidate export, Colibri generation, functional accuracy and retained-app regression acceptance remain pending. Zero of six applications are fully accepted. Production inference and the original evaluation inputs, scorer and provider remain unchanged; no later-application training started.

[Fourth validation and checkpoint integrity evidence](../training/reports/facturation-search-refinement-fourth-validation.json).

## Third refinement validation completed - 19 October 2026

IMPLEMENTED and verified: checkpoint 1536 completed the unchanged 275-case development validation. The recorded observation contains 1,539 contiguous finite updates after optimization resumed. The baseline, checkpoint 512 and checkpoint 1024 history remain unchanged. The adapter contains 7,127,040 finite values across 192 tensors and 24 layers, with a complete payload. The single reviewer verified the captured evidence and all ten bound input hashes.

Weighted semantic validation loss decreased from checkpoint 1024 by 8.50% for Facturation, 8.26% for Management Projet and 18.47% for Design Workflow. Relative to initial validation, changes are -11.89%, +7.97% and -26.31%, respectively. These are teacher-forced loss changes, not accuracy scores. Facturation and Management Projet loss remain above checkpoint 512, while Design Workflow loss is lower. Checkpoint 512 remains selected by application-macro loss; every scheduled candidate, including 1536, remains required in the pending functional comparison.

The checkpoint-save to history-record span was 1,123.96 seconds and includes validation and bookkeeping. No selected-adapter save occurred at this checkpoint. A private observer's memory-unit reporting error was corrected in a fresh record while preserving the original; the training job and finite-value scan were unaffected.

PARTIALLY IMPLEMENTED: the original 3,103-update run remains incomplete, with the next periodic validation at 2048. Candidate export, Colibri generation and functional acceptance remain pending. Zero of six applications are fully accepted. Production inference and the original evaluation inputs, scorer and provider remain unchanged; no later-application training started.

[Third validation and checkpoint integrity evidence](../training/reports/facturation-search-refinement-third-validation.json).

## Second refinement validation completed - 18 October 2026

IMPLEMENTED and verified: checkpoint 1024 completed the unchanged 275-case development validation. Its saved adapter contains 7,127,040 finite values across 192 tensors and 24 layers, with a complete payload. The original baseline and checkpoint-512 history remain unchanged, and the recorded observation contains 1,029 contiguous finite updates. The single reviewer confirmed the figures and storage evidence.

Weighted semantic validation loss increased from checkpoint 512 by 18.94% for Facturation, 13.26% for Management Projet and 18.18% for Design Workflow. Relative to initial validation, changes are -3.70%, +17.68% and -9.62%, respectively. These are teacher-forced loss changes, not accuracy scores. Checkpoint 512 remains selected by application-macro loss; the pending functional comparison must still include checkpoint 1024.

The checkpoint-save to history-record span was 1,121.74 seconds and includes validation and bookkeeping. No selected-adapter save occurred at this checkpoint because loss did not improve. Raw evidence is preserved with a separate reporting correction.

PARTIALLY IMPLEMENTED: optimization resumed and the original 3,103-update run remains incomplete. Candidate export, Colibri generation and functional acceptance remain pending. Zero of six applications are fully accepted. Production inference and the original evaluation inputs, scorer and provider remain unchanged; no later-application training started.

[Second validation and checkpoint integrity evidence](../training/reports/facturation-search-refinement-second-validation.json).

## Natural-timeout contingency declared - 18 October 2026

PREPARED as policy only: a separate interrupted-run protocol can preserve fully saved and validated scheduled checkpoints if the original supervisor naturally reaches its pinned child timeout. The original successful-completion policy and running job remain unchanged. Operator stops, numerical corruption, changed provenance and unexplained failures are not admitted.

The policy was declared after checkpoint-512 loss and integrity observations, while training was still active and before candidate export or generation. All eligible checkpoints must be frozen before generation and complete the same development ranking and downstream accuracy, regression, critical-case and native security gates. Interrupted training must remain recorded as incomplete.

PLANNED: separate terminal collection, actual artifact bindings, implementation, negative tests and review are still required before this contingency can execute. This is neither a new accuracy result nor authorization to stop training, activate a model or start the next application.

[Separate natural-timeout policy and limitations](../training/reports/facturation-search-refinement-natural-timeout-policy.json).

## First refinement validation completed - 18 October 2026

IMPLEMENTED and verified: checkpoint 512 was saved and its first periodic 275-case development validation completed. A read-only integrity scan verified all 7,127,040 stored float32 values across 192 tensors and 24 layers: every value is finite, the payload is complete, and the adapter hash matches the saved checkpoint. The single reviewer cleared both evidence checks. These checks do not establish the optimizer trajectory or model accuracy.

Weighted semantic validation loss changed by -19.04% for Facturation, +3.90% for Management Projet and -23.52% for Design Workflow relative to the initial validation. These are relative teacher-forced loss changes, not accuracy scores. The Management Projet increase is not a measured action-accuracy regression.

PARTIALLY IMPLEMENTED: optimization resumed after validation; the 3,103-update run remains incomplete. Candidate export, Colibri generation and functional acceptance remain pending under the unchanged comparison policy. Zero of six applications are fully accepted. Production inference and the original evaluation inputs, scorer and provider remain unchanged; no later-application training started.

[First validation and checkpoint integrity evidence](../training/reports/facturation-search-refinement-first-validation.json).

## Checkpoint handoff controls verified - 18 October 2026

IMPLEMENTED and verified as preparation: the read-only completion collector and sequential Colibri checkpoint comparison controls are cleared by one reviewer. All 23 offline handoff checks pass, and the original checkpoint-600 report recomputes unchanged. A live read-only check rejected the active training run before creating an export or comparison directory.

PARTIALLY IMPLEMENTED: initial validation has finished and optimization is active, but training, checkpoint generation and acceptance are not complete. Actual completion, a bound export and runtime evidence remain required. No new model score, production activation or later-application training is claimed; zero of six apps are fully accepted.

[Handoff preparation evidence and limits](../training/reports/facturation-search-refinement-handoff-preparation.json).

## Functional checkpoint comparison prepared - 18 October 2026

IMPLEMENTED as policy preparation only, while training is active and before any new candidate Colibri generation: compare original checkpoint 600 as baseline against the seven scheduled checkpoint/final adapters on the unchanged 133 Facturation development cases. Ranking reuses the frozen full-action and valid-structure fractions, then recorded Facturation semantic validation loss and lowest step. The trainer's separate minimum application-macro-loss adapter is a diagnostic, not functional acceptance.

PLANNED: actual export and inference require the successful completed training invocation, complete artifact and provenance checks, and a separately reviewed launch. After development selection, the chosen candidate must pass all unchanged 275 shared development cases, 438 regressions and 48 additional controls with existing application, subset, critical and retained-application regression gates. Acceptance outcomes cannot rerank checkpoints. No production activation or later-application training follows this policy.

The new policy records the new candidate steps without changing original inputs, source policies or scores. It does not predict accuracy. [Bound comparison policy](../training/reports/facturation-search-refinement-evaluation-policy.json).

## Facturation refinement launched - 18 October 2026

PARTIALLY IMPLEMENTED: the reviewed server run started at 12:34 UTC from original checkpoint 600, using the existing Transformers/PEFT pipeline. The 3,103 planned updates include 2,069 Facturation examples and retained replay for Management Projet (709) and Design Workflow (325). This is one Facturation-focused refinement, not completion of training or acceptance for any application.

The actual child process, interpreter, cgroup, dataset, sources and model provenance were verified. Settings are 14 CPU threads, a 32 GiB memory ceiling, zero swap, a 10% spare-memory floor, 24 LoRA layers and checkpointing enabled. The run is preparing inputs and performing initial validation; zero optimization updates were observed at the recorded launch check. Checkpoint and validation intervals are 512 updates.

All 3,103 training and 275 unchanged development examples passed server tokenizer/template/Colibri-parser parity, supervised-token alignment and output-budget checks. The largest training example is 7,745 tokens. All 56 preparation tests and 11 offline launch guards pass. The single reviewer cleared the exact evidence and one-shot launch.

Both checkpointing-enabled capacity updates passed on the longest training row, with finite gradients and real updates in all 24 layers and about 5.8 GiB peak process RSS. The comparison supervisor then stopped on its post-arm reserve-admission guard. A separate checkpointing-disabled probe exceeded its isolated 32 GiB limit before producing an update result. Checkpointing stays enabled; no speedup or numerical-equivalence claim is made.

No new model-accuracy score exists. Zero of six applications have passed full acceptance. The original scores, frozen evaluation inputs, scorer and provider remain unchanged. Production inference is healthy and unchanged; no candidate was activated.

[Verified launch, preflight and resource findings](../training/reports/facturation-search-refinement-launch.json).

## Natural search training candidate - 18 October 2026

IMPLEMENTED and verified as preparation: 112 natural stock questions cover English and French evenly, with product-first and location-first phrasing. All retain reviewed TRAIN arguments, tool schemas and trusted context. Native stock dates use the actual creation or update event and inclusive bounds. Four genuine or unrecognized histories remain intact; 108 questions are plain requests.

The candidate contains 3,103 examples: the exact 2,283 previously optimized TRAIN rows, plus 268 native stock-profile, 112 natural-question and 440 name-role contrasts. This retains all earlier optimized inputs and targets, including their verified language, nested edit fields and permission-profile distinctions. The other 692 original TRAIN rows remain outside this schedule. Fifty inherited neutral-wrapper duplicate groups are retained deliberately; there are zero exact-input duplicates.

All 56 preparation tests pass. The single reviewer independently checked every ordered row, schema, source hash and canonical development-input exclusion. The original 275 development rows remain byte-identical. Original evaluation targets, scoring and provider behavior are unchanged.

PARTIALLY IMPLEMENTED: server preflight and numerical admission remain pending. The required parent is original checkpoint 600; the rejected V3 adapter cannot seed training. No new model-accuracy result or production activation is claimed, and zero of six applications have passed the full acceptance gate. Two authored natural-language families and role-name variations cannot predict a 95% result or prove the cause of earlier errors.

[Candidate preparation and limitations](../training/reports/facturation-search-refinement-preparation.json).

## Search-generalization checks and stock-profile data - 18 October 2026

IMPLEMENTED and verified as data preparation: the new helpers prepare 440 name-role variants from 220 source questions and 268 native stock-only profile variants. Review excluded ambiguous role assignments and duplicate neutral greetings before model work. All 34 preparation tests pass together. Stock-profile variants preserve every question, target and argument; native schema and source-hash checks pass. Neither dataset has been trained.

Four isolated Colibri diagnostics completed. Original/rotated/opaque names each matched 4/4 targets; original/product-first/location-first wording each matched 4/4; original/native-stock-only tool bundles each matched 4/4. These reuse selected TRAIN families and do not estimate general accuracy. A separate check on two actual English development failures matched 0/2 targets with both original and Hello-wrapped prompts. The wrapper made one response schema-valid but still swapped product and location, so it is not a correctness fix.

The training audit found that stock-only examples omit combined product, location, date and limit filters present under broader access. The prepared data fills that coverage gap, but the passing profile probe does not establish it as the failure cause. All workers stopped and production inference remained unchanged. Original cases, labels, provider, scores and acceptance gates remain unchanged.

PARTIALLY IMPLEMENTED: no numerical successor or model activation started; zero of six apps are fully accepted. Next, prepare and review natural compound-search variants from TRAIN labels, bind original checkpoint 600, and run server tokenizer/template preflight before another candidate. Do not reuse the rejected adapter as a training parent.

[Verified preparations, diagnostic scope and actual results](../training/reports/facturation-search-generalization-diagnostics.json).

Earlier entries below retain their original observation state.

## Failed-generation diagnostics completed - 18 October 2026

IMPLEMENTED and verified as diagnostics: four failed Colibri requests ended normally but generated invalid arguments. Thirteen captures using the saved training-runtime adapter matched six targets and eleven schemas; seven of ten selected original failures persisted before export. This includes one native-equivalent article-search alias that remains a strict-scoring failure. These observations do not isolate quantization as the cause.

The paired shortlist probe completed all 26 requests. Full tool lists matched 3/13 targets; previously model-chosen tool plus clarification matched 5/13. It gained 2 matches and lost 0. Only offered tool lists changed, with fresh sequential workers and unchanged selected schemas, messages and settings. The first four selected tool names came from the fresh raw diagnostic. This is a failure-heavy conditional diagnostic, not an end-to-end planner score or acceptance result.

A fresh two-stage planning probe also finished: exact targets moved from 3/13 first proposals to 4/13 final proposals, gaining two and losing one. A correct financial retrieval became unsupported clarification; stock roles, missing filters and literal-copy errors persisted. The approach is rejected, and the public provider was not changed. These selected cases do not estimate general accuracy.

The training-only check used 16 original examples actually optimized in the completed run. Free generation matched 16/16 targets with 16/16 valid schemas; current teacher-forced greedy predictions matched every target token on 16/16 rows. 0 free-generation failures had both exact teacher greedy tokens and unchanged prompt prefixes. All selected training examples generate correctly while development remains below target. This is consistent with a generalization gap on these selected cases, not proof of a sole cause. Parameters remained unchanged and no optimizer was created. Current eval-mode arithmetic is distinct from historical training-mode loss.

All diagnostic workers stopped; model parameters and production inference remained unchanged. Nineteen shortlist, 23 focused-planner and 20 training-only offline guards passed. A pre-run review corrected the diagnostic unit name and removed stale unused provenance. The current logistics form, bilingual knowledge and all 40 native pins remain compatible; no removed selector is presented as a required step.

PARTIALLY IMPLEMENTED: original development and acceptance scores remain unchanged. Zero of six applications are fully accepted. No numerical successor, acceptance run, model activation or later-application training started. Select and verify a concrete planning/training improvement before another long numerical run.

[Verified diagnostic scope, results and evidence](../training/reports/facturation-replay-v3-failure-diagnostics.json).

Earlier entries below retain their original observation state.

## Complete-shape replay failed the development gate - 18 October 2026

IMPLEMENTED and independently verified as an experiment: all 2,283 server updates, real Colibri export and 275 unchanged development cases completed. All 24 intended layers received finite gradients and updates; frozen parameters stayed unchanged and the saved adapter matched the live model. Fourteen Colibri diagnostic targets passed, while the training-runtime diagnostic matched 13 of 14. These small diagnostics did not predict the broad result.

| Application | Complete actions | Exact arguments | Structured output |
| --- | --- | --- | --- |
| facturation | 110/133 (82.71%) | 89/111 (80.18%) | 131/133 (98.50%) |
| management_projet | 74/78 (94.87%) | 51/54 (94.44%) | 76/78 (97.44%) |
| design_workflow | 63/64 (98.44%) | 45/46 (97.83%) | 64/64 (100%) |

PARTIALLY IMPLEMENTED: Facturation and Management Projet fail development targets. Design Workflow passes only this development gate and declined from its baseline. The candidate is rejected for activation and extension. No acceptance run followed, no later application training started, and zero of six applications are fully accepted. All three workers and the controller stopped; production inference remained healthy and unchanged.

The single reviewer checked the current supplier form, removed selectors, visible labels, both identical bilingual knowledge copies and all 40 native pins. No logistics contract correction is justified. Three article-search failures are native-equivalent aliases under strict exact scoring; original scores remain unchanged. Other failures include dropped/swapped filters, literal-copy errors and invalid outputs.

PLANNED: inspect raw failed outputs and training/serving behavior before selecting another numerical experiment. Preserve original cases, scoring and rejected artifacts.

[Actual completion, unchanged development scores and measured performance](../training/reports/facturation-replay-v3-en-fr-development.json).

Earlier entries below retain their original observation state.

## Future queue retains the complete Facturation replay curriculum - 17 October 2026

IMPLEMENTED as data preparation: versioned conditional successors retain all 2,975 replay V3 training rows, including the 556 Facturation examples absent from the older R11 queue. Unchanged reviewed new-app examples produce Contracts 3,128 training / 319 validation rows, Gestion Magasin 3,326 / 362 and Reservation 3,506 / 402. Validation, held-out cases and fresh controls remain unchanged. A read-only check found all 29 pinned native source files for these applications still matched their prepared datasets.

Nine checks pass, including complete metadata/schema preflight for every queued stage, exact retained prefixes, rejected stale/skipped predecessors, altered evaluation inputs and overwrite prevention. The single reviewer cleared the exact source and tests. Tests reproduce the pinned base from tracked sources without depending on private prepared files.

PARTIALLY IMPLEMENTED: the current Facturation numerical job continues. These private local dataset artifacts are unbound preparations, not accepted models or new accuracy scores. The original R11 launcher does not admit this lineage; a separately reviewed actual accepted predecessor binding and server rehearsal/export/resource checks remain required. No additional training or production activation started; zero of six applications are fully accepted.

[Preparation checks and artifact identities](../training/reports/facturation-replay-v3-future-serial-preparation.json).

Earlier entries below retain their original observation state.

## Current Facturation backend verified - 17 October 2026

IMPLEMENTED and verified: the released Facturation backend and current shared assistant source passed all 2,657 backend tests and 41 subtests with isolated synthetic records. All 1,660 snapshot hashes remained unchanged, and an explicit post-run query confirmed removal of the temporary local test database. The single reviewer verified the harness, actual results and cleanup.

PARTIALLY IMPLEMENTED: model training continues separately. This backend run does not provide a new accuracy score or production end-to-end acceptance; zero of six applications are fully accepted.

[Current backend regression results and scope](../training/reports/facturation-current-backend-regressions.json).

Earlier entries below retain their original observation state.

## Evaluation safeguards prepared while training continues - 17 October 2026

IMPLEMENTED as preparation: the single reviewer cleared versioned export admission, one-shot export, Colibri development and independent completion-verification helpers. Fifty-four offline tests pass, including twelve new admission checks that reject live, failed, incomplete or substituted training, changed bindings, resource pressure and overlapping jobs. The frozen 275-case development inputs, original checkpoint-600 baseline, provider and scoring remain unchanged.

The actual export and development bindings are not yet available and are not treated as verified. Execution stays gated on the original training invocation finishing successfully, complete numerical invariants and reviewed actual artifact/evidence bindings. No export, evaluation, activation or later-application training started.

At 2026-10-17T15:18:30Z, the original training process had completed 23 of 2,283 updates and remained healthy. A separate three-second sample measured about 12.7 effective CPU cores under the fourteen-thread configuration, with no cumulative memory-pressure or OOM events recorded at that point. This sample is not a whole-run performance benchmark.

No new accuracy score exists; zero of six applications are fully accepted.

[Reviewed evaluation preparation and actual observations](../training/reports/facturation-replay-v3-evaluation-preparation.json).

Earlier entries below retain their original observation state.

## Complete-shape replay running on the server - 17 October 2026

PARTIALLY IMPLEMENTED: the reviewed 26-source/nine-data snapshot passed isolated server admission. All 2,975 training and 275 original development rows passed tokenizer, Colibri-template, parser, loss-boundary and output-budget checks. Actual original checkpoint-600 weights and the frozen Colibri runtime were rehashed before the one-shot launch; rejected trial adapters were not reused.

At 2026-10-17T15:09:32Z, the original invocation had completed all 14 baseline diagnostics and 3 of 2,283 selected updates. Recorded update losses and gradients are finite. Fourteen CPU threads and a 32 GiB limit are configured, swap is disabled, and 43.75 GiB RAM was available. The observed service peak was 4.10 GiB.

The single reviewer cleared preparation, numerical/export source, exact preflight/staging/launch payloads and actual launch evidence. Sixty-one implementation checks and seventeen private handoff simulations passed before execution. These checks and early updates do not forecast 95 percent accuracy.

PLANNED: monitor this original invocation, verify completed numerical invariants, export through Colibri, then run the unchanged development and acceptance gates. No new accuracy or activation exists; zero of six applications are fully accepted. Production inference remains healthy and unchanged.

[Actual launch and timestamped progress](../training/reports/facturation-replay-v3-server-launch.json).

Earlier entries below retain their original observation state.

## Generation failures diagnosed; complete-shape replay prepared - 17 October 2026

IMPLEMENTED: four bounded requests through the actual Colibri candidate completed with terminal HTTP/SSE responses. Three generated quote changes used a business number as the internal identifier and were correctly rejected. One stock search generated an unsupported field and misplaced a product filter; schema validation correctly rejected it. The owned worker stopped, all 13 collected files were verified, and production inference remained healthy and unchanged. These fresh diagnostics do not replace the original failed development scores.

IMPLEMENTED as preparation: a new versioned sampler preserves all 2,975 training and 275 development rows, labels and existing scoring controls. It now covers complete nested argument shapes jointly with resource, intent, context and language for both new and retained training. Scenario provenance matches complete messages, schemas and targets, allowing only the four pinned neutral greeting augmentations. The independent preflight tests caught and resolved additional omitted combinations before training.

The selected 2,283 updates contain 438 new Facturation contrasts, 811 retained Facturation rows, 709 Management Projet rows and 325 Design Workflow rows. Twenty-five preparation, seven runner and twenty-nine export tests pass. Numerical, capture, resource and cleanup functions retain their previous implementation.

PLANNED: review the exact successor source and server handoff, verify the current checkpoint-600 model and tokenizer/template admission, then run one isolated server experiment. No V3 numerical update or accuracy result exists. No rejected adapter is reused; zero of six applications are fully accepted.

[Verified raw-output diagnostic](../training/reports/facturation-replay-v2-invalid-output-diagnostic.json) and [successor preparation](../training/reports/facturation-replay-v3-preparation.json).

Earlier entries below retain their original observation state.

## Joint-context replay remains below acceptance targets - 17 October 2026

PARTIALLY IMPLEMENTED: this Facturation experiment completed its server training, real Colibri export and all 275 unchanged development cases. Independent verification recomputed the frozen scores and confirmed artifact identities, exact case/target/shard matching, event-log prefix integrity and explicit cleanup of all three workers and the controller.

Facturation full actions improved from 110/133 (82.71%) to 113/133 (84.96%); exact arguments improved from 88/111 (79.28%) to 92/111 (82.88%). Management Projet declined from 77/78 (98.72%) to 75/78 (96.15%) full actions and from 53/54 (98.15%) to 51/54 (94.44%) arguments. Design Workflow retained 64/64 actions and 46/46 arguments.

This rejects activation or extension of the experiment. Its fourteen successful export diagnostics did not establish general accuracy. No new acceptance score exists, zero of six applications are fully accepted, and the disposable adapter cannot seed a longer run. The production inference model remains healthy and unchanged.

PLANNED: review the concrete model failures and native contracts before another numerical run. Scores, frozen development/acceptance inputs and historical reports remain unchanged.

[Independently verified development results and measured latency](../training/reports/facturation-replay-v2-en-fr-development.json).

Earlier entries below retain their original observation state.

## Joint-context replay optimization and export completed - 17 October 2026

IMPLEMENTED and verified as a bounded experiment: all 1,171 selected server updates completed with finite losses and gradients, all 24 intended layers updated, unchanged frozen parameters and matching saved/live adapter. The numerical service peaked at 7.32 GiB within its 32 GiB limit. Fourteen baseline and fourteen trained diagnostic captures matched their targets.

Actual merging, conversion and Colibri replay completed. All 14 paired actions matched the training runtime and their diagnostic targets; before/after artifact proofs match and the owned export worker stopped. These diagnostics do not establish general accuracy.

PARTIALLY IMPLEMENTED: the original 275-case development comparison is now running against checkpoint 600 with unchanged cases, provider, settings and scorer. Its timestamped processed-case count is recorded separately from accuracy. Full acceptance and additional-control gates remain incomplete; zero of six applications are fully accepted. The production inference model is healthy and unchanged.

The single reviewer cleared the actual export and development handoffs. It also checked the current logistics supplier form, removed customer selectors, visible field labels, historical routes and tool scope against both identical bilingual knowledge copies; no mismatch was found.

[Executed numerical/export evidence and development observation](../training/reports/facturation-replay-v2-pilot-completion.json).

Earlier entries below retain their original observation state.

## Joint-context replay training started on server - 17 October 2026

PARTIALLY IMPLEMENTED: one isolated 1,171-update experiment started from the rehashed original checkpoint 600. The server verified all 22 source files and nine prepared data files, including pinned synthetic language provenance. Full tokenizer/template/loss-boundary checks passed all 2,975 training and 275 unchanged development rows without truncation. No failed trial adapter was reused.

At 2026-10-17T04:40:27Z, the original invocation was running with all 14 baseline captures and one update complete. Fourteen CPU threads and a 32 GiB limit are configured, swap is disabled, and 43.73 GiB RAM was available. The first update used an inherited Facturation row previously excluded by V1. Its finite loss/gradient confirms execution, not accuracy improvement.

The single reviewer cleared source, staging, resource/model admission, one-shot launch and read-only observation. Fifty-three successor implementation tests and 51 private server-handoff simulations pass. These checks do not predict 95 percent accuracy.

PLANNED: finish this original invocation, verify numerical/adapter invariants, export through Colibri and run all unchanged development and acceptance checks. No new model score, activation or later-app numerical job exists. Production inference remains healthy and unchanged; zero of six applications are fully accepted.

[Actual launch and timestamped progress](../training/reports/facturation-replay-v2-server-launch.json).

Earlier entries below retain their original observation state.

## Joint-context bilingual replay correction prepared - 17 October 2026

IMPLEMENTED and reviewed: the successor sampler preserves the frozen V1 recipe, all 2,975 training rows, all 275 development rows and existing control/scoring policies. All 116 inherited focused examples are replay-eligible. The selected 1,171 updates contain 126 new Facturation contrasts, 514 retained Facturation rows, 357 Management Projet rows and 174 Design Workflow rows. Ninety inherited focused rows are selected; all their available semantic projections are covered.

Request language comes from explicit row metadata or exact matches in three pinned synthetic training annotation sources. Of 2,975 rows, 1,362 are labelled English, 1,345 French and 268 remain unknown. Interface language is kept separately; it is never substituted for request language. Joint intent, current-page and previous-result context now preserve combinations missed by marginal coverage.

Seventeen successor preparation, seven runner and twenty-nine export checks pass. Twenty-seven earlier export checks and twelve original preparation checks also pass. The actual isolated-directory admission test passes. The single reviewer cleared the source. Numerical, resource and cleanup functions remain unchanged.

PLANNED: verify source-only server release, stage the exact source/data closure and admit one isolated server experiment from the original selected checkpoint 600. No numerical update, new accuracy result or activation has occurred for this successor. The rejected adapter will not be reused. Zero of six applications are fully accepted.

[Source, selection and actual checks](../training/reports/facturation-replay-v2-preparation.json).

Earlier entries below retain their original observation state.

## Replay trial did not meet development targets - 17 October 2026

IMPLEMENTED and independently verified: all 275 unchanged Colibri development cases finished at 04:14:06 UTC. Raw event booleans and the frozen scorer reproduce every reported metric and target gate. All bound artifacts and the explicitly scoped event-log prefix match; before/after serving proofs are byte-identical, stderr is empty, and the controller plus all three workers stopped.

| Application | Exact actions, baseline to trial | Exact arguments, baseline to trial | Trial structure |
| --- | ---: | ---: | ---: |
| facturation | 110/133 (82.71%) to 110/133 (82.71%) | 88/111 (79.28%) to 89/111 (80.18%) | 133/133 (100.00%) |
| management_projet | 77/78 (98.72%) to 72/78 (92.31%) | 53/54 (98.15%) to 49/54 (90.74%) | 76/78 (97.44%) |
| design_workflow | 64/64 (100.00%) to 64/64 (100.00%) | 46/46 (100.00%) to 46/46 (100.00%) | 64/64 (100.00%) |

PARTIALLY IMPLEMENTED: the 306-update replay experiment did not improve Facturation action accuracy and regressed Management Projet. The candidate is rejected for activation and extension. Design Workflow passes only this development set. No new acceptance run occurred; the last completed Facturation regression remains 96/108 (88.89%). Zero of six applications are fully accepted.

PLANNED: review training/development errors, replay effectiveness and prompt/tool contracts before another numerical experiment. Do not extend or reuse the disposable adapter. Acceptance/additional-control cases and scoring remain unchanged, and production inference is healthy and unchanged.

[Verified completed comparison](../training/reports/facturation-replay-v1-en-fr-development.json).

Earlier entries below retain their original observation state.

## Contrast/replay trial and Colibri diagnostics complete - 17 October 2026

IMPLEMENTED and verified: the original 306-update numerical invocation finished successfully, including all 14 baseline and 14 trained-model captures. All 24 intended layers received nonzero gradients and updates; frozen parameters stayed unchanged, and saved/live adapter equality passed. The trial timer was 8,474.95 seconds, covering updates through final verification and excluding baseline capture/loading. Service cgroup peak was 6.621 GiB.

The real FP32 merge, Colibri conversion and all 14 streamed paired requests completed; the worker stopped. Thirteen actions matched validly across runtimes. Training-runtime target matches were 13/14 and Colibri target matches 14/14, with zero correct-to-incorrect export changes. These are small training/development diagnostics, not general accuracy.

PARTIALLY IMPLEMENTED: the original 275-case Colibri development comparison is running against the unchanged checkpoint-600 baseline. At 2026-10-17T03:46:39.114630+00:00, six cases were complete, all three owned workers were running and controller stderr was empty. No new full development or acceptance score exists. The last completed Facturation regression remains 96/108 (88.89%).

Production inference is healthy and unchanged. No longer epoch, later-application numerical job or activation has started. Zero of six applications are fully accepted; this disposable adapter must not seed a longer run.

[Verified trial/export and timestamped comparison status](../training/reports/facturation-replay-v1-pilot-completion.json).

Earlier entries below retain their original observation state.

## Replay-preserving server trial running - 17 October 2026

PARTIALLY IMPLEMENTED: the exact 21-file source closure and three prepared data files were staged. Actual checkpoint-600 FP32 model weights and the frozen Colibri runtime were rehashed and matched the original selection. One isolated 306-update trial started after resource admission; the failed V2 pilot adapter was not reused.

At 2026-10-17T01:18:19Z, all 14 baseline captures and two contiguous selected updates were complete under the original invocation. Fourteen CPU threads and a 32 GiB limit are configured, with swap disabled. Available RAM was 40.63 GiB. Completion, all-layer/frozen-weight verification, trained captures, export and new accuracy remain pending.

The reviewed selection mixes 126 new Facturation contrasts, 90 retained Facturation rows, 57 Management Projet rows and 33 Design Workflow rows. Production inference is healthy and unchanged. No later-application numerical job or full epoch has started; zero of six applications are fully accepted.

[Actual launch and timestamped progress](../training/reports/facturation-replay-v1-server-launch.json).

Earlier entries below retain their original observation state.

## Server metadata preflight passed; numerical handoff prepared - 17 October 2026

IMPLEMENTED and verified on the server: all 2,975 training and 275 original development rows pass exact tokenizer/Colibri-template parity, tool-argument parsing, loss-boundary/alignment and output-budget checks. Maximum sequences are 7,745 and 7,496 tokens within the 8,192-token context; no truncation is permitted. This loaded tokenizer metadata only, not model weights.

IMPLEMENTED as preparation: numerical/capture/resource functions retain the reviewed runner implementation. Export admission now also enforces the dataset's required checkpoint 600 and predecessor report hash. Thirty-six runner/export tests, seven staging tests and nine one-shot launch tests pass, in addition to the twelve preparation checks. These are 64 offline checks, not model-accuracy tests.

The single reviewer cleared the private staging and launch handoff. PLANNED: stage the exact 21-file source closure and three prepared data files, rehash the actual selected FP32 model, check resources and admit one 306-update server experiment. No numerical trial or new model score exists yet. Production inference remains healthy and unchanged; zero of six applications are fully accepted.

[Actual server preflight and handoff checks](../training/reports/facturation-replay-v1-execution-preparation.json).

Earlier entries below retain their original observation state.

## Coherent Facturation contrasts and explicit replay prepared - 17 October 2026

IMPLEMENTED as preparation only: a source-verified recipe preserves all 2,419 cumulative training rows and appends 556 existing focused inputs, yielding 2,975 training rows and the original 275 development rows. No labels were created or changed. The single reviewer found one missing inherited control-policy record; it was preserved, tested and re-reviewed with no remaining issues.

The bounded selection contains 306 updates: 126 new Facturation contrasts, 90 retained Facturation examples, 57 Management Projet replay examples and 33 Design Workflow replay examples. Twenty complete four-state matrix groups replace isolated variants. All 154 existing contrast axes and 424 marginal replay features are covered. Every scheduled window, including the tail, contains all four source groups.

Twelve metadata/schema tests pass, covering source-byte/target preservation, complete contrast groups, older searches, scheduling, control-policy inheritance, conflict/tamper rejection and separate pinned admission. These tests load no model weights and estimate no accuracy.

PLANNED: bind the unchanged checkpoint-600 predecessor and run server tokenizer/template/context checks, then review numerical admission before one isolated experiment. No new numerical training, full epoch, model activation or later-app training has started. Existing acceptance sets/scoring remain unchanged. Zero of six applications are fully accepted.

[Reviewed preparation and actual checks](../training/reports/facturation-replay-v1-preparation.json).

Earlier entries below retain their original observation state.

## V2 pilot development regressed; candidate rejected - 17 October 2026

IMPLEMENTED and verified: the unchanged 275-case development comparison finished at 00:35:37 UTC. All metrics were independently recomputed; bound artifact hashes match, before/after serving proofs are identical, stderr is empty and all three owned workers stopped.

| Application | Exact actions, baseline to pilot | Exact arguments, baseline to pilot | Structured output, pilot |
| --- | ---: | ---: | ---: |
| facturation | 110/133 (82.71%) to 107/133 (80.45%) | 88/111 (79.28%) to 85/111 (76.58%) | 133/133 (100.00%) |
| management_projet | 77/78 (98.72%) to 72/78 (92.31%) | 53/54 (98.15%) to 48/54 (88.89%) | 76/78 (97.44%) |
| design_workflow | 64/64 (100.00%) to 64/64 (100.00%) | 46/46 (100.00%) to 46/46 (100.00%) | 64/64 (100.00%) |

PARTIALLY IMPLEMENTED: the pilot failed to improve Facturation and regressed Management Projet. It is rejected for activation and must not seed a longer run. Design Workflow passes only this development comparison, not overall acceptance. The last completed Facturation regression remains 96/108 (88.89%); no new acceptance run was executed. Zero of six applications are fully accepted.

PLANNED: review training/development error patterns and the training mix before another isolated experiment from the unchanged predecessor. All 92 updates were Facturation-only, without other-application replay. Existing acceptance contents/scoring remain unchanged. Production inference is unchanged; no later-application training or full V2 epoch has started.

[Verified full development comparison](../training/reports/facturation-focus-v2-en-fr-development.json).

Earlier entries below retain their original observation state.

## Facturation bounded trial and Colibri export complete - 17 October 2026

IMPLEMENTED and verified: the original 92-update trial completed successfully, including all 14 baseline and 14 trained-model captures. All 24 intended LoRA layers received nonzero gradients and updates; frozen parameters stayed unchanged, and the saved adapter matched the live trained model. The recorded trial timer was 2561.42 seconds, covering updates, adapter persistence, trained captures and verification, excluding baseline capture/loading. The service cgroup peak was 7.170 GiB, which is not process RSS.

The real merge, Colibri conversion and all 14 streamed replay requests completed successfully; the replay worker stopped. Training-runtime and Colibri actions matched validly on 12/14 captures. Each matched 11/14 targets, but one development capture changed from correct to incorrect in Colibri. These small paired diagnostics do not establish acceptance accuracy.

PARTIALLY IMPLEMENTED: the unchanged 275-row shared development comparison is running against checkpoint 600. At 2026-10-17T00:15:26.968748+00:00, 71/275 cases had completed, with the original controller live and no errors. Three attested workers use the original four-thread, 8192-context, 512-output-token, no-thinking settings. The new score is pending; the last completed Facturation regression remains 96/108 (88.89%).

This is a completed bounded trial, not a full 1487-row V2 epoch or an accepted model. Zero of six applications are fully accepted. Production inference remains healthy and unchanged; no longer epoch, later-app training or activation has started. The disposable adapter must not seed a full run.

[Verified trial, export and timestamped development status](../training/reports/facturation-focus-v2-pilot-completion.json).

Earlier entries below retain their original observation state.

## Facturation pilot running; development handoff prepared - 16 October 2026

PARTIALLY IMPLEMENTED: at 2026-10-16T23:37:30.599726+00:00, the original server pilot was live at 39/92 updates. Production inference was healthy and unchanged. The trial has not completed, and no new pilot accuracy result exists.

IMPLEMENTED as preparation only: the reviewed export dispatcher and development adapter/controller are ready for the completed trial. Nine export-dispatch checks, eleven worker-adapter checks and fourteen controller checks pass. The single reviewer found no remaining issues. The frozen evaluator changes only its model identifier; scoring and all 275 shared development cases remain unchanged.

The completed export must preserve the admitted binding's ordered content across its pretty launch representation and compact completed representation, with both exact byte hashes checked. A stale export-service status mapping was also fixed. No export or development workers have started, and no longer epoch or candidate activation is authorized by these helpers. Seventeen current and 79 historical evaluation controls remain unchanged.

[Timestamped progress and preparation evidence](../training/reports/facturation-focus-v2-development-preparation.json).

Earlier entries below retain their original observation state.

## Completed Facturation-focused evaluation - 16 October 2026

IMPLEMENTED and verified: the original evaluation completed all five 133-case development candidates, the selected checkpoint's 275 shared development cases, 438 frozen regressions and 48 additional controls. The original controller stopped cleanly at 23:12:37 UTC. Checkpoint 600 remains selected by the unchanged development policy; acceptance did not rerank candidates.

| Application | Full regression actions | Exact regression arguments | Additional-control actions | Acceptance |
| --- | ---: | ---: | ---: | --- |
| facturation | 96/108 (88.89%) | 74/86 (86.05%) | 9/16 (56.25%) | Failed |
| management_projet | 192/200 (96.00%) | 141/148 (95.27%) | 16/16 (100.00%) | Failed |
| design_workflow | 121/130 (93.08%) | 91/100 (91.00%) | 14/16 (87.50%) | Failed |

PARTIALLY IMPLEMENTED: the 95% accuracy target is not met. Facturation's development actions rose from 108/133 (81.20%) to 110/133 (82.71%), while its main regression actions fell from the previous 97/108 (89.81%) to 96/108 (88.89%). The changed model has not demonstrated an overall improvement and is not approved for activation. Management Projet's averages exceed 95%, but its critical/subset gates still fail. There are zero fully accepted applications in this six-app campaign.

PLANNED: verify the actual selected model files, run the reviewed 92-update refinement pilot, export and replay through Colibri, and compare all 275 shared development cases against this same starting model. The 48 additional controls are small, repeatedly evaluated team-authored scenarios, not independent population certification. Existing acceptance cases and scoring remain unchanged. No production activation or later-application training occurred.

[Verified complete evaluation](../training/reports/facturation-focus-v1-en-fr-evaluation.json).

SUBSEQUENT OBSERVATION, 23:14 UTC: actual selected FP32 files, tokenizer/configuration, export metadata and serving artifacts were verified against the completed report. A metadata-only preview passed before the isolated 92-update server pilot started with 14 CPU threads and a 32 GiB memory ceiling. The pilot is running; no pilot accuracy improvement, longer-epoch admission or activation is claimed. Its adapter must not seed a subsequent full run.

Earlier entries below retain their original observation state.

## Facturation V2 export/replay guards prepared - 16 October 2026

IMPLEMENTED as preparation only: the V2 export/replay supervisor requires the completed focused predecessor report, matching terminal/application gates, exact pilot selection, selected serving proofs and a separate observation of actual selected FP32 files. The frozen report binds the serving export; it does not itself attest FP32 weight bytes. The future observation must bind those files, dtype/layout and export metadata to the same report before launch.

All 27 synthetic supervisor tests pass. Export execution, resource admission, process ownership and cleanup functions retain the reviewed V1 implementation. The single reviewer found no remaining issues. Seventeen current and 79 historical evaluation controls remain unchanged.

PLANNED: finish the running regression/additional-control evaluation, derive and verify the selected-model observation, admit the bounded server pilot, then perform real export/Colibri replay and all 275 shared development comparisons. No numerical pilot, pilot export, new accuracy result, longer epoch, model activation or later-app training has occurred. [Verified supervisor preparation](../training/reports/facturation-focus-v2-replay-preparation.json).

Earlier entries below retain their original observation state.

## Facturation V2 pilot admission and token checks verified - 16 October 2026

IMPLEMENTED as preparation only: a deterministic pilot selects 92 unique training inputs: 78 new contrasts and 14 retained tool sentinels. It covers 154 declared marginal/pairwise axes, all ten added categories in English and French, and all existing tool/operation/clarification-reason groups. This does not cover every Cartesian combination or all 440 additions.

All 12 admission tests pass. Numerical, capture and resource-control functions remain identical to the reviewed V1 runner. Other training/evaluation workloads block numerical launch. The single reviewer found no remaining issues. A missing tokenizer model-configuration pin was fixed and re-reviewed before the server metadata check ran.

The server tokenizer, Colibri-template/parser, semantic-loss boundary and output-budget checks pass all 1,487 training and 133 validation rows. The longest sequences are 7,745 and 7,496 tokens respectively, within the 8,192-token context; no truncation is permitted. These checks loaded no model weights and executed no numerical training.

PLANNED: finish the current frozen regression evaluation, bind the actual selected FP32 predecessor, verify resources, run the bounded server pilot, then compare Colibri development results against the same starting model. No longer epoch, production activation or later-application training is admitted. [Verified pilot preparation](../training/reports/facturation-focus-v2-pilot-preparation.json).

Earlier entries below retain their original observation state.

## Facturation extraction contrasts prepared; current regressions running - 16 October 2026

IMPLEMENTED as preparation only: the next Facturation curriculum contains 1,487 training rows and the same 133 validation rows. All 1,047 parent training rows and every validation byte are retained. The 440 new synthetic rows comprise 220 English and 220 French examples, including 320 date/optional-filter matrix rows and 120 mixed-filter, unpaid-balance, calendar-boundary, literal-copy, navigation, selection and payment contrasts.

Thirteen tests pass. Native metadata checks validate all 440 new labels with database connections prohibited. The single reviewer found no incorrect targets; the parent-generator hash guard and 42 French agreement errors were fixed and re-reviewed. The supplier-workflow read-scoping change is bound by an exact old/new source transition. Native tool shortlists are recomputed normally and can differ across variants, so complete model inputs are not claimed identical.

The existing focused run completed its five-checkpoint development comparison. Checkpoint 600 was selected with 110/133 full actions (82.71%) and 88/111 eligible exact arguments (79.28%). Its 275-case shared development regression is running before 438 regressions and 48 additional controls. These are development measurements, not 95% acceptance. No production model activation or later-application training occurred.

PLANNED: complete token/template/parser preflight, bind the actual measured starting model, implement explicitly balanced pilot admission, and run a bounded server pilot followed by same-base development/regression comparison. The new curriculum has not been trained, and no longer epoch is admitted. Current and historical evaluation controls remain unchanged. [Preparation evidence](../training/reports/facturation-focus-v2-preparation.json).

Earlier entries below retain their original observation state.

## Facturation epoch complete; Colibri comparison running - 16 October 2026

IMPLEMENTED and verified: one server-only Facturation epoch completed all 1,047 updates and final validation, retaining the original R11 step-2400 FP32 starting model. The recorded training timer covers 34,166.99 seconds (about 9 hours 29 minutes), excluding initial model loading and dataset encoding. Peak process RSS was 7.714 GiB. Training used the same shared Qwen3.5-0.8B, 14 CPU threads and the reviewed checkpointing configuration.

| Checkpoint | Weighted validation loss | Unweighted validation loss |
| --- | ---: | ---: |
| 0 | 0.04873197 | 0.02600715 |
| 300 | 0.06851523 | 0.03435935 |
| 600 | 0.06091881 | 0.03038344 |
| 900 | 0.04969220 | 0.02470716 |
| 1047 | 0.06773017 | 0.03382859 |

Lower loss is better. None of the new checkpoints improved weighted validation loss over step 0, which denotes the original starting model. The final checkpoint therefore has not demonstrated a validation-loss improvement. Loss selection is separate from functional checkpoint selection and is not an accuracy score.

PARTIALLY IMPLEMENTED: Colibri is comparing checkpoints 300, 600, 900 and 1,047 on the unchanged 133-row Facturation development split. A changed selected model still requires the separate three-app development regression, 438 frozen regressions and 48 additional controls. No new 95% result or model acceptance is established.

The final adapter has 192 F32 tensors with matching layout and LoRA configuration; its file size and checksum were verified without loading model tensors. The single reviewer found no new invalid labels in all 133 development rows and 116 added examples, including 90 added date-bound rows. Six development rows retain a known equivalent-argument limitation under exact scoring; scoring remains unchanged.

Seventeen current and 79 historical evaluation controls remain unchanged. The completed report collector verified all 22 bound training inputs. Production inference remains unchanged, and this workflow has not activated a new model or started later-application training. [Verified training completion](../training/reports/facturation-focus-v1-training-completion.json).

Earlier entries below retain their original observation state.

## Facturation checkpoints verified - 16 October 2026, 19:41 UTC

PARTIALLY IMPLEMENTED: the server-only Facturation run reached 923/1,047 updates in this timestamped observation. Checkpoints 300, 600 and 900 are saved. Their 192 F32 adapter tensors have matching names, shapes, byte layout and LoRA configuration; file sizes and checksums were recorded without loading model tensors or running inference. The original training process remains live.

| Checkpoint | Weighted validation loss |
| --- | ---: |
| Baseline | 0.04873197 |
| 300 | 0.06851523 |
| 600 | 0.06091881 |
| 900 | 0.04969220 |

Lower loss is better. Checkpoint 900 improves on 300 and 600, but remains above the baseline, so the loss selector still retains step 0. These are teacher-forced loss measurements, not tool-calling accuracy or acceptance scores.

PLANNED: finish update 1,047 and final validation, then follow the frozen Colibri checkpoint comparison and acceptance policy. A changed selected model still requires the separate development/regression checks and additional controls. Seventeen current evaluation controls, 79 historical pipeline controls and all bound local training inputs remain unchanged. No production model activation or later-application training was performed by this workflow; production inference is healthy and its container has not restarted.

[Verified checkpoint observations](../training/reports/facturation-focus-v1-checkpoint-observation.json). Earlier entries below retain their original observation state.


## Facturation logistics knowledge synchronized - 16 October 2026

IMPLEMENTED and verified: English/French logistics knowledge now reflects supplier-purchase dossiers, retained historical client/proforma links, the registered supplier selector and separate brand selection. Guidance uses current form captions and distinguishes the date fields. Purchase conditions, advance proof, matching import-title amount/currency, payment triggers, receipts and closing requirements come from the existing business guards. Operational AI write permissions remain unchanged.

All 442 selected regressions passed in 49.45 seconds, including native AI permissions, supplier-only dossiers, supplier-directory access and bilingual knowledge retrieval. All 1,180 frozen training/validation targets remain valid against current capability-scoped tool contracts, including 54 logistics targets. Only the 358 rows with explicit profile metadata were checked against a profile; no role was inferred for the 822 legacy rows. Runtime authorization is covered separately by backend tests.

The reviewed source reached company, personal and production remotes. Production source hashes and the stored English/French knowledge version match. The web service is healthy, workers are running, and the production model and active training process are unchanged. The primary checkout already contains the released commit through concurrent work; the other agent's changes were preserved.

PARTIALLY IMPLEMENTED: focused model training and accuracy acceptance remain incomplete. These checks are not a model score, full backend suite or production E2E security certification. The current logistics adapter searches, reads and opens dossiers and receipts; no supplier-directory CRUD or payment action was added. [Verified compatibility and release report](../training/reports/facturation-logistics-knowledge-v1.json).


## Facturation focused native regressions - 16 October 2026

IMPLEMENTED and verified: 310 existing authorization, operation, history, confirmation and document-action regressions passed in 45.73 seconds. They used controlled fixtures in a unique local PostgreSQL test database, which was removed after the run. The application and shared-source snapshots were unchanged throughout testing; no production data or server numerical workload was involved.

The working tree includes concurrent purchase/logistics work owned by another agent. It was tested without editing it. The current shared source was selected explicitly because the installed local package was stale. Two earlier harness failures occurred before test execution and remain preserved in private evidence.

This is a selected native regression run, not a full backend suite, model-accuracy measurement, real-model E2E test or production security certification. Facturation model training continues separately. [Verified native regression report](../training/reports/facturation-focus-v1-native-regressions.json).


## Facturation full epoch running - 16 October 2026, 11:17 UTC

PARTIALLY IMPLEMENTED: the reviewed Facturation-only full run is live on the server, starting from the original R11 step-2400 FP32 model. Its actual operator binding exactly matches the final reviewed preview. The published diagnostics, selection policy, source checkout and all three remote heads were verified before launch.

The run plans one epoch of 1,047 updates using 14 CPU threads, checkpointing and a 32 GiB service ceiling with no swap. The first live observation was baseline validation with 0/1,047 updates, about 12.7 busy CPU cores and 2.323 GiB process RSS. Baseline validation occurs before optimization; these numbers are not completed training or accuracy results.

Model acceptance remains incomplete. The latest completed larger-suite scores remain the failed R11 results below. No production model activation or later-application training occurred. [Verified launch](../training/reports/facturation-focus-v1-launch.json).

Earlier entries below retain their original observation state.


## Facturation rehearsal and Colibri export verified - 16 October 2026

IMPLEMENTED and verified: the isolated server rehearsal completed 35 finite updates across all 24 intended layers, with 14 captures before and after. Frozen base parameters remained unchanged, and the saved disposable adapter exactly matched the live model used for captures. Elapsed time from optimizer-loop start through final captures/integrity checks was 1,320.02 seconds; initial baseline captures are excluded.

IMPLEMENTED and verified: all 14 export/replay responses were schema-valid. No framework-correct action became Colibri-incorrect. Colibri matched 11/12 training targets and 1/2 development targets; the framework matched 10/12 and 1/2 respectively. These are bounded mechanics samples, not held-out acceptance accuracy. The independent checker reconstructs original prompts, targets and references, preserves schema key order, and binds the completed service invocation. The temporary worker stopped and production inference remains unchanged.

PLANNED: a single full Facturation epoch of 1,047 updates, using the original R11 step-2400 FP32 model. The disposable rehearsal adapter must never seed full training. The frozen policy compares steps 0, 300, 600, 900 and 1,047 on the unchanged 133-row Facturation development split, representing 104 underlying scenario groups. Lower loss alone does not establish an accuracy gain. Three-app validation, all 438 regressions and 48 additional controls remain required after selection. No new full epoch has started yet.

The planned service uses 14 CPU threads, checkpointing and a 32 GiB ceiling with no swap and the existing 10% host-memory reserve. The prior successful two-update 7,745-token capacity probe has the same configuration and all 473 tensor shapes/dtypes as the selected base; its original service invocation and finite updates were rechecked. No second capacity workload was run.

[Verified bounded diagnostics](../training/reports/facturation-focus-v1-rehearsal-diagnostics.json), [frozen focused selection policy](../training/reports/facturation-focus-v1-checkpoint-selection-policy.json).

Earlier entries below retain their original observation state.


## Current status: R11 evaluated, Facturation refinement next - 16 October 2026

IMPLEMENTED and verified: all 2,419 R11 training updates, five saved-checkpoint development comparisons, 438 regressions and 48 additional English/French controls completed. The frozen development rule selected step 2400. Independent verification binds every scored event to its original worker log and selected artifact proofs. The selected FP32 base still has the same 473 F32 tensors. All temporary workers stopped and production inference remains unchanged.

| Application | Fully correct regression actions | Exact regression arguments | Additional controls: full actions |
| --- | ---: | ---: | ---: |
| Facturation | 97/108 (89.81%) | 75/86 (87.21%) | 7/16 (43.75%) |
| Management Projet | 193/200 (96.50%) | 143/148 (96.62%) | 15/16 (93.75%) |
| Design Workflow | 118/130 (90.77%) | 88/100 (88.00%) | 14/16 (87.50%) |

Acceptance FAILED. No application passes all required model gates. Management Projet's larger-suite averages exceed 95%, but its critical/subset checks and additional controls still fail. Only 3/15 regression sets pass all gates. These are planner measurements, not authorization or production-readiness certification. The 16 additional cases per application are small team-authored bilingual controls and are reported separately; they are not a population-accuracy estimate.

The model is still the same shared Qwen3.5-0.8B, served by Colibri. The next run focuses only on Facturation with 1,047 training rows and 133 unchanged validation rows. The 35-update focused server rehearsal and bounded Colibri export comparison are verified. The full 1,047-update epoch has not started; its final operator binding is next. Management Projet and Design Workflow regression checks remain mandatory. Contracts, Gestion Magasin and Reservation are prepared but untrained. There are zero accepted applications from the six-app training campaign.

[Completed R11 evaluation](../training/reports/shared-v5r11-en-fr-evaluation.json), [development comparison](../training/reports/shared-v5r11-functional-validation.json), [focused preparation](../training/reports/facturation-focus-v1-preparation.json).

## R11 checkpoint comparison complete - 16 October 2026

IMPLEMENTED and verified: all five saved checkpoints completed the same 275 development cases. Artifact identities, original result shards and stopped temporary workers were verified. The frozen application-macro selection rule chose step 2400, independently recomputed from every candidate. The final step 2419 was not the most accurate candidate.

| Application | Fully correct development actions | Exact arguments | Tool selection | Structured output |
|---|---:|---:|---:|---:|
| facturation | 108/133 (81.20%) | 87/111 (78.38%) | 130/133 (97.74%) | 132/133 (99.25%) |
| management_projet | 77/78 (98.72%) | 53/54 (98.15%) | 77/78 (98.72%) | 78/78 (100%) |
| design_workflow | 64/64 (100%) | 46/46 (100%) | 64/64 (100%) | 64/64 (100%) |

PARTIALLY IMPLEMENTED: the selected candidate is running the separate 438-case regression evaluation, followed by 48 additional controls. These development scores do not establish acceptance or live application accuracy. Facturation remains below its development targets and is the next focused refinement priority. No focused optimizer run has started. Other applications remain queued.

[Verified checkpoint comparison](../training/reports/shared-v5r11-functional-validation.json). The 275 rows include neutral-history variants of 222 underlying scenarios. The matching R8 baseline was reused only for the identical frozen inputs, provider, model and inference settings. No model activation occurred.


## Facturation-only focus prepared - 16 October 2026

IMPLEMENTED as preparation only: the next refinement focuses on Facturation, following the request to work on one application at a time. The model remains shared. The current R11 evaluation finishes first; no additional numerical workload has started.

The versioned curriculum contains 1,047 training rows: all 931 existing Facturation rows, byte-identical, plus 116 English/French contrasts. All 133 existing Facturation validation rows remain byte-identical. The additions vary date digits, inclusive/exclusive bounds, optional customer/product/location filters, users-list versus user-detail navigation, complete remarks and unselected-record clarification. Other applications and all acceptance inputs remain unchanged.

Nine dataset tests pass. The actual native schema and permission-profile check accepts all 116 additions with database access prohibited. Tokenizer, Colibri-template/parser, loss-boundary and output-budget checks pass all 1,180 training/validation rows. One reviewer checked every new label; two provenance findings were fixed and re-reviewed. These are preparation checks, not model accuracy results.

PLANNED: bind the measured starting model after the current evaluation, run a bounded server rehearsal and functional comparison, then train Facturation if those checks support proceeding. Recheck Management Projet and Design Workflow because updates to one shared model can degrade other applications. After Facturation meets the required gates, continue one application at a time. Contracts, Gestion Magasin and Reservation remain untrained.

[Preparation evidence](../training/reports/facturation-focus-v1-preparation.json), [dataset manifest](../training/datasets/facturation-focus-v1-en-fr/manifest.json).

PARTIALLY IMPLEMENTED: a dedicated Facturation-only rehearsal admission path is prepared. It admits only the published focused manifest, rejects other stages and retained-data substitutions, and always covers all six new categories in both languages. The static audit proposes 35 updates, 12 training captures and two validation captures. Seven admission tests pass. The single reviewer found no remaining issues after fixing concurrent-job detection and default category recording. Numerical, capture, source-integrity and service-admission functions retain the existing implementation; the process denylist additionally recognizes the existing V3 rehearsal and selective capacity probe.

No numerical rehearsal, export comparison or full focused run has executed. [Rehearsal preparation](../training/reports/facturation-focus-v1-rehearsal-preparation.json).

PARTIALLY IMPLEMENTED: the focused export/replay supervisor is prepared with unchanged export, service isolation and cleanup mechanics. It requires a completed, independently verified R11 report covering all 438 regressions and 48 additional controls, plus the actual selected FP32 fingerprint and original serving proofs. An unaccepted candidate may be examined only for further Facturation refinement; this does not admit a later application or activate a model. All 24 synthetic supervisor tests pass. Category-order compatibility and remote/controller proof-serialization findings were fixed and re-reviewed. The proof-content hash remains exact; the remote writer adds one newline that the controller omits. The actual terminal report, FP32 binding, numerical rehearsal and Colibri replay remain pending. [Replay preparation](../training/reports/facturation-focus-v1-replay-preparation.json).

## R11 training completed; accuracy evaluation running - 16 October 2026

IMPLEMENTED and verified: the server training service exited successfully after all 2,419 contiguous updates and final validation. The complete epoch covered 931 Facturation, 1,012 Management Projet and 476 Design Workflow examples. Reported training duration was 19 hours 16 minutes, with 7.734 GiB peak RSS. Dataset, trainer and exposure checks passed.

PARTIALLY IMPLEMENTED: the Colibri comparison is evaluating the five saved checkpoints on the same 275 development cases. The matching baseline measurements are retained. Step 1200 has the lowest recorded validation loss; functional selection and new acceptance scores are not yet available. Only the selected changed candidate will advance to 438 regression cases and 48 additional controls.

The controller and three evaluation workers were verified live. All 79 frozen control files still match. Production inference remains healthy and unchanged. Contracts, Gestion Magasin and Reservation remain prepared but untrained. Training completion does not establish 95% accuracy or authorize activation.

[Training completion evidence](../training/reports/shared-v5r11-training-completion.json). The sections below retain their historical observation dates.

## Selective checkpoint diagnostic preparation - 16 October 2026

PARTIALLY IMPLEMENTED: the separate [two-step server probe](../training/scripts/probe_cpu_selective.py), [paired comparator](../training/scripts/compare_selective_checkpointing.py), and [text checkpoint-mask helper](../training/scripts/selective_checkpointing.py) are prepared. They do not modify the active trainer. The probe requires a terminal, accepted R11 predecessor, its selected FP32 model, and the actual Contracts curriculum. It reuses the serial trainer's encoding and loss functions, with explicit full or alternating text-layer masks.

The probe requires its reviewed interpreter and exact startup command, a dedicated 14-thread / 32 GiB / zero-swap service, no overlapping numerical work, and 10% spare host memory. It observes checkpoint API calls and verifies finite gradients and genuine updates across all 24 intended layers. Frozen weights remain checked. It saves initial adapters, raw gradients, and updated adapters for two updates on the longest training example. These disposable tensors must never seed full training.

All 25 synthetic tests pass; the single reviewer found no remaining issues after three corrections. The comparator now requires independently pinned original-binding and completion hashes, verifies helper source before import, and checks the stopped service invocation and command. It reports exact numerical equality with matching shapes/dtypes and finite values; signed zeros compare equal. Both runs must preserve the existing 1.4 memory-capacity margin. Measured compute time excludes serialization/checks and does not predict a full training run.

No numerical diagnostic, paired tensor comparison, capacity measurement, or speed measurement has executed. Actual accepted-model bindings and server execution remain incomplete. A successful diagnostic would still require subsequent rehearsal, export/Colibri checks, and full model acceptance. Current R11 training, its 79 frozen controls, production inference, and later-app training remain unchanged. [Preparation evidence](../training/reports/selective-checkpoint-diagnostic-preparation.json).

## Contracts replay admission prepared for R11 - 15 October 2026

IMPLEMENTED as preparation only: replay_contracts_after_r11.py admits the forthcoming Contracts rehearsal against an actually accepted R11 model and its exact retained curriculum. The earlier supervisor expects 2,339 R8 updates; this separate version requires all 2,419 R11 updates and one of its five declared changed checkpoints. The original supervisor and the 79 frozen active R11 files remain unchanged.

The checker preserves model identity, source, cleanup and rehearsal guards. It requires all 15 regression sets (438 cases), 48 fresh controls and complete per-application counts. Each application must reach at least 95% tool selection, exact arguments and full actions, plus 99% valid structure, in both phases. Existing critical-case gates also remain mandatory.

All 45 synthetic tests pass: eight R11 admission tests, 15 existing behavior tests run against the new supervisor, and 22 original supervisor tests. These tests check the supervisor, not model accuracy. Actual R11 acceptance, selected-model binding, Contracts numerical rehearsal and server export/replay remain incomplete. No Contracts training or production activation occurred. [Preparation evidence](../training/reports/contracts-r11-replay-preparation.json).

## Later-app curriculum retention verified - 15 October 2026

IMPLEMENTED as preparation only: the queued Contracts V6r11, Gestion Magasin V7r11 and Reservation V8r12 curricula retain the complete R11 training prefix, including all 80 coverage examples and the six clarified English requests. Existing new-application rows, validation and evaluation inputs remain unchanged. Each stage uses strict byte-for-byte retention without a correction exception.

Eight integrity and bounded startup tests pass. Metadata checks pass all 3,352 cumulative training/validation examples and 738 evaluation cases, including tokenizer/template agreement, Colibri parsing, schemas, loss alignment and output budgets. The single reviewer found no issues. These checks do not measure model accuracy.

R11 remains the only server training job. No later application has started training or received an accepted model. Each future stage still requires its actual accepted predecessor, current native-source verification, a frozen baseline, numerical/export rehearsal and resource checks. [Preparation results](../training/reports/serial-after-r11-preparation.json), [metadata checks](../training/reports/shared-v8r12-en-fr-metadata-preflight.json).

## Corrected serving checks verified - 15 October 2026

IMPLEMENTED and verified: the corrected Colibri replay completed all 26 requests with schema-valid exact target actions and zero framework-correct to Colibri-incorrect changes. Twenty-five actions match the framework captures; the remaining action corrects the existing development literal-copy error. The independent verifier and single reviewer confirmed the paired results, unchanged artifacts and stopped worker. This is a bounded training/development diagnostic, not a full accuracy result.

IMPLEMENTED and verified: all six clarified R11 financial-summary requests returned the exact expected actions through the same temporary Colibri model. Separately, all 275 validation prompts remain identical after serialization through the frozen native provider, with no HTTP requests or model inference. The full server metadata preflight passes all 2,419 training and 275 validation examples.

PARTIALLY IMPLEMENTED: full R11 training started on 15 October 2026 at 12:00 UTC with 14 CPU threads, a 32 GiB service ceiling and no swap. It schedules all 2,419 updates from the original R8 selected checkpoint, not the disposable rehearsal weights. Checkpointing-on passed both capacity updates across all 24 intended layers, with 6.508 GiB peak RSS. The isolated checkpointing-off probe exceeded the 32 GiB memory cgroup before completing an update; its original failure is preserved. The reviewed fallback retains checkpointing-on and does not claim a speedup. Production remains unchanged.

IMPLEMENTED and verified: the automatic controller is running and waits for successful full-epoch completion. It compares the baseline and steps 600, 1200, 1800, 2400 and 2419 on the unchanged 275 validation rows. Only the selected changed candidate advances to 438 regressions and 48 fresh controls, reported separately. Seventeen handoff tests and eight fallback admission tests pass; the single reviewer found no issues. Training completion, new accuracy measurements and acceptance remain incomplete. [Launch evidence](../training/reports/shared-v5r11-launch.json), [checkpoint selection policy](../training/reports/shared-v5r11-checkpoint-selection-policy.json).

[Corrected replay evidence](../training/reports/shared-v5r10-rehearsal-diagnostics.json), [six wording checks](../training/reports/shared-v5r11-wording-preparation.json).

## Earlier records



## Shared refinement wording preparation - 15 October 2026

IMPLEMENTED and verified as dataset preparation: V5r11 clarifies exactly six English requests from "collected payments" to "total amount collected". All expected targets, 2,413 other training rows, validation and evaluation inputs remain unchanged. Four focused tests and all six changed-row tokenizer/template/schema/loss/output-budget checks pass; the single reviewer found no issues. Parent helper hashes are verified before generation.

PARTIALLY IMPLEMENTED: the R10 numerical rehearsal completed, and its corrected Colibri replay is pending. V5r11 has not been trained; targeted wording checks and verified export parity are still required before full refinement. No new accuracy result or production activation is claimed. [Wording preparation](../training/reports/shared-v5r11-wording-preparation.json).

## Shared rehearsal complete; corrected Colibri replay pending - 15 October 2026

IMPLEMENTED and verified: all 63 numerical updates completed, all 24 intended layers received finite gradients and actual updates, the saved adapter matches the live model and frozen base parameters remain unchanged. Independent action checks and the single reviewer confirm training captures improved from 16/20 to 20/20; development captures stayed 5/6, with no correct-to-incorrect changes. This demonstrates learning on the rehearsed examples, not acceptance or development improvement.

PARTIALLY IMPLEMENTED: merge and Colibri conversion completed, but the first replay was invalid for prompt parity. Its client alphabetically reordered tool-schema keys during JSON serialization, changing all 26 prompts. Reproducing that ordering explains all 26 server-reported token counts. Original evidence is preserved and the temporary worker stopped.

IMPLEMENTED and tested: request bytes, hashes and saved artifacts now preserve nested schema order. The 82 affected tests pass, including three regressions that failed before the fix and coverage of nested properties and both supervisors. Tokenizer-only checks preserve all 26 original prompt strings and token counts. The single reviewer found no remaining issue. Prompt/token validation and exact-action scoring were not weakened.

Corrected Colibri replay, six R11 wording checks, full refinement and acceptance remain incomplete. The disposable adapter must not seed full training. Production is unchanged. [Rehearsal diagnosis and fix](../training/reports/shared-v5r10-rehearsal-diagnostics.json).

## Earlier results and preparations


## Latest completed acceptance, 15 October 2026

PARTIALLY IMPLEMENTED: R8 completed all 2,339 training updates and eight development checkpoint comparisons. The selected final checkpoint failed acceptance: 409/438 fully correct regression actions (93.38%), 309/334 exact arguments (92.51%) and 438/438 valid structures. Four of 15 regression sets pass every frozen gate.

| Application | Regression full actions | Regression exact arguments | Fresh full actions | Fresh exact arguments |
|---|---:|---:|---:|---:|
| facturation | 98/108 (90.74%) | 77/86 (89.53%) | 6/16 (37.50%) | 4/14 (28.57%) |
| management_projet | 187/200 (93.50%) | 138/148 (93.24%) | 16/16 (100%) | 10/10 (100%) |
| design_workflow | 124/130 (95.38%) | 94/100 (94%) | 13/16 (81.25%) | 9/12 (75%) |

The separate 48 fresh controls score 35/48 full actions (72.92%), 23/36 exact arguments (63.89%), and 48/48 correct tools and structures. These are 24 bilingual scenarios, not external certification. Frozen scoring, original inputs and checkpoint selection are unchanged. Independent recomputation matches every saved assessment. Temporary evaluation workers stopped; the production model remains unchanged. No app is fully accepted on this shared candidate. Contracts, Gestion Magasin and Reservation training have not started.

[Completed evaluation](../training/reports/shared-v5r8-en-fr-evaluation.json). Earlier development scores below are checkpoint-selection measurements, not the final acceptance results.

IMPLEMENTED as preparation: shared V5r10 retains all 2,339 corrected V5r9 training rows, appends the 80 reviewed development-coverage examples, and preserves all 275 validation rows plus 438 regression and 48 fresh controls. Tokenizer/template/parser/loss and output-budget checks pass all 2,694 training/validation rows. The category-aware rehearsal retains all 48 original mechanics examples and adds bilingual coverage for all eight new categories: 63 updates, 20 training captures and six development captures, before and after. Only training rows receive updates.

The single reviewer found and verified a fix for concurrent older-rehearsal detection. Numerical execution, Colibri export replay and the full refinement remain pending. The existing Contracts supervisor still requires an actually accepted predecessor; it is unchanged. Later-app preparations will need the full accepted refinement curriculum before use. [Preparation evidence](../training/reports/shared-v5r10-rehearsal-preparation.json).

## Earlier reports

## Reviewed coverage supplement - 2026-10-15

IMPLEMENTED as preparation only: 80 synthetic English/French examples address reviewed development coverage gaps: 68 Facturation, four Management Projet and eight Design Workflow. They cover custom-period currency summaries, natural product/location filters, inclusive date bounds, unpaid balances, literal remarks, unchosen results, dated receipts and resource-specific completion statuses. All 80 pass actual native metadata checks with database access forbidden, tokenizer/Colibri template/parser round trips, semantic loss boundaries and output budgets. Seven focused tests pass. Maximum complete example length is 4,775 tokens; maximum expected output is 103 tokens within the 512-token limit.

The single reviewer found no new incorrect targets and no copied frozen requests. The missing helper provenance inventory was corrected; a fresh native generation produced identical training bytes. The supplement remains separate: no cumulative continuation is assembled, no new numerical rehearsal or training has run, and no accuracy improvement is claimed. R8 evaluations, scoring and production are unchanged. [Supplement](../training/datasets/coverage-contrasts-v1-en-fr/manifest.json), [checks](../training/reports/coverage-contrasts-v1-preflight.json).


## Current checkpoint results, 15 October 2026

PARTIALLY IMPLEMENTED: R8 training completed all 2,339 updates. All eight saved checkpoints completed the same 275 development cases, with unchanged artifacts and stopped temporary workers verified. The frozen selection rule chose the final checkpoint, step 2339. This completes checkpoint comparison; it does not establish model acceptance.

| Application | Fully correct development actions | Exact arguments | Tool selection | Structured output |
|---|---:|---:|---:|---:|
| facturation | 107/133 (80.45%) | 88/111 (79.28%) | 127/133 (95.49%) | 132/133 (99.25%) |
| management_projet | 77/78 (98.72%) | 53/54 (98.15%) | 77/78 (98.72%) | 78/78 (100%) |
| design_workflow | 63/64 (98.44%) | 45/46 (97.83%) | 64/64 (100%) | 64/64 (100%) |

Facturation remains below target. Management Projet and Design Workflow meet the development thresholds on this checkpoint, but final acceptance is still pending. The selected candidate has entered the separate 438-case regression evaluation; 48 fresh controls follow. Production uses its existing model. Contracts, Gestion Magasin and Reservation have prepared datasets but their training has not started.

[Verified checkpoint comparison](../training/reports/shared-v5r8-functional-validation.json). The 275 rows include neutral-history variants of 222 underlying scenarios. These are development scores, not blind acceptance scores or measured live application accuracy.

IMPLEMENTED: the expected-reply budget safeguard is reviewed and published. All 308 training integrity tests and all 4,010 prepared six-application metadata examples pass. The guard does not establish numerical learning, export parity or model accuracy. [Pretraining budget verification](../training/reports/pretraining-output-budget-20261015.json).

## Earlier implementation and training records

PARTIALLY IMPLEMENTED: the server export/replay supervisor is prepared for Contracts after actual R8 acceptance. All 302 training-integrity tests pass, including 22 supervisor tests, and two Linux subprocess checks verify cleanup without model loading or service changes. One reviewer found two provenance issues; both were fixed and re-reviewed. The supervisor requires accepted predecessor evidence, independently pinned numerical output, exact service invocation, sequential export/serving and before/after worker verification. It never grants model acceptance or starts full training. Actual bindings, numerical rehearsal, model export and replay remain pending. [Supervisor preparation](../training/reports/rehearsal-supervisor-preparation-20261014.json).

IMPLEMENTED and verified as preparation: the review caught a rehearsal mismatch where a tool call after a Qwen role boundary could be credited although Colibri would stop before it. The runner now uses the pinned native stop filter before thinking/tool parsing and retains raw plus filtered evidence. Replay rejects older unfiltered captures. All 280 training-integrity tests pass, including 26 focused synthetic capture/replay tests; the single reviewer found no remaining issue in this fix. Rechecking all four corrected preparations changed no dataset hash or rehearsal selection. Numerical execution, real export comparison and accuracy measurement remain pending. The active R8 run and frozen controller are unchanged. [Stop-handling evidence](../training/reports/rehearsal-stop-preflight-20261014.json).

IMPLEMENTED and verified as preparation: corrected cumulative datasets cover Contracts V6r10 (2,492 training / 319 validation), Gestion Magasin V7r10 (2,690 / 362) and Reservation V8r11 (2,870 / 402). Exactly six retained target labels change from each prior preparation; all other rows, application additions, validation and evaluation inputs remain unchanged. All 269 training-integrity tests pass, including 24 Contracts mutation/startup checks and nine final-stage tests. The latter reject skipped predecessors and altered retained rows before model import. A separate subprocess test verifies the isolated scripts/data/control layout. The single reviewer found no remaining issues.

Final metadata checks pass all 3,272 training/validation examples and 738 evaluation cases, including the exact retained Contracts and Gestion Magasin prefixes. Full static audits select 59, 72 and 84 training-only rehearsal rows respectively. These checks do not establish semantic independence, numerical learning, export parity or model accuracy. No later-stage model has been trained or accepted. [Contracts metadata](../training/reports/shared-v6r10-en-fr-metadata-preflight.json), [Contracts audit and artifact inventory](../training/reports/shared-v6r10-en-fr-pretraining-audit.json), [final cumulative metadata](../training/reports/shared-v8r11-en-fr-metadata-preflight.json), [later-stage audits](../training/reports/later-name-corrections-preflight-20261014.json).

IMPLEMENTED and deployed: bounded source-based target review covered all 2,339 R8 training rows and identified six incorrect name-search labels plus three native defects. The native fixes recognize complete proforma invoice targets, validate card/carte targets, and match customer names across first/last-name fields. Final Facturation and Design Workflow assistant suites pass 875 and 97 tests respectively. Design Workflow retains an existing threaded-test database teardown warning. One reviewer checked the final fixes. All three remotes, deployed source, health and migration state were verified; business counts and database volumes were preserved. Training, the production model, feature flags and deployment hooks were unchanged. [Review and release evidence](../training/reports/target-label-review-20261014.json).

This is source and controlled-fixture verification, not a model score or a claim that every training phrase is perfect. The active R8 run still contains the six known labels; its frozen inputs are not changed midway. The corrected replacements and launch checks below apply to the next run.

IMPLEMENTED and verified as preparation: the source review found six Management Projet name-only searches labelled with the broader multi-field query. The separate management-name-errata-v2-en-fr artifact replaces those six targets with client_name, supplier_name or project_name, preserving every request, tool schema, history and trusted context. All 227 training integrity tests pass, including eleven correction tests; all six exact tokenizer/template/Colibri-parser/loss-boundary checks pass. [Correction evidence](../training/reports/management-name-errata-v2-en-fr-preflight.json).

IMPLEMENTED as preparation: shared-v5r9-en-fr applies the six replacements to the three-app curriculum. Its other 2,333 training rows and all validation/evaluation inputs are unchanged. All 236 training integrity tests pass, including nine new retention tests; metadata checks pass 2,614 training/validation examples and 486 evaluation cases. The known-label and full static audits pass, selecting 48 training-only rehearsal rows. No model is bound and numerical rehearsal has not run. [Metadata checks](../training/reports/shared-v5r9-en-fr-metadata-preflight.json), [static audit](../training/reports/shared-v5r9-en-fr-pretraining-audit.json).

PARTIALLY IMPLEMENTED: actual accepted-model bindings and server numerical rehearsal remain pending. The corrected Contracts preparation is shared-v6r10-en-fr, conditional on R8 passing. It retains the original R8 dataset identity and applies exactly six pinned target replacements without treating untrained V5r9 as an accepted predecessor. The old V6r9/V7r9/V8r10 preparations fail the known-label gate. Gestion Magasin V7r10 and Reservation V8r11 retain their corrected predecessors exactly, without a correction exception. Each still needs the actual accepted predecessor model and run binding. If R8 fails, V5r9 is available for a justified three-app refinement after rehearsal. No additional epoch is required solely for dataset naming, and no later-stage training is authorized by this preparation.

IMPLEMENTED and verified as preparation: a review of all 180 Reservation training rows found four requests with misleading date wording. They now explicitly refer to reservation arrival dates or rental years and current returned/paid status. All action labels, histories, validation and held-out bytes remain unchanged. All 216 training integrity tests pass; final metadata checks pass 3,272 training/validation rows and 738 evaluation cases. The corrected final-stage preparation is shared-v8r10-en-fr, retaining the complete shared-v7r9-en-fr prefix. Native date filters and financial calculation sources are pinned. [Correction evidence](../training/reports/reservation-temporal-corrections-20261014.json).

PARTIALLY IMPLEMENTED: the server-only exact replay collector is implemented and synthetic transport tests pass. It preserves issued payloads, bounded raw response bytes, parsed events and failures; rejects truncated or malformed streams; and never authorizes training. Real numerical rehearsal, export and live-worker replay remain pending until the active R8 controller completes. [Collector evidence](../training/reports/cpu-rehearsal-collector-preparation-20261014.json). Those earlier preparations remain preserved; corrected successors and accepted model bindings are required. No later-stage optimizer has started.

IMPLEMENTED and verified as preparation: the single semantic review found one confirmed financial-definition mismatch in Gestion Magasin and four ambiguous Contracts requests. The corrected native wording states that the metric sums paid amounts on confirmed sales created today and currently marked paid, across payment modes; it does not filter payment dates. Four Contracts requests now explicitly identify the customer. Versioned source datasets retain all targets, contexts, histories and split order, including the affected French history duplicate.

All 193 training tests and 58 PostgreSQL assistant tests plus 6 subtests pass. The native six-sale fixture covers creation date, current payment status, store isolation and payment modes. Metadata checks pass all 3,272 cumulative training/validation rows and 738 evaluation cases without weights or inference. One historical-input hash check found by review was fixed and mutation-tested. [Correction evidence](../training/reports/native-semantic-corrections-20261014.json), [metadata evidence](../training/reports/shared-v8r9-en-fr-metadata-preflight.json).

Earlier preparation: Contracts V6r9, Gestion Magasin V7r9 and Reservation V8r10 preserved the then-current retained curriculum. These names identify future dataset revisions, not a new running training job. The active R8 run and all original inputs/results remain unchanged. Do not start the superseded V6r8/V7r8/V8r8 or Reservation V8r9 preparations. Fresh accepted-predecessor bindings, native-source verification, numerical rehearsal and real Colibri export comparison remain required before the next full run. All 90 GM evaluation envelopes have refreshed native metadata, including two revised questions, so they require fresh baseline/candidate predictions. Historical scores must not be relabelled as measurements on the corrected inputs.

Earlier preparation: exact rehearsal replay helpers were prepared and reviewed. All 187 training integrity tests pass, including 15 new comparison tests. The helpers bind the exact sent payload, preserve structured clarification arguments and failed responses, validate token usage and compare actions without normalizing defaults. At that preparation stage, numerical rehearsal, real export, network collection and live worker attestation were pending. The collector implementation is now prepared; execution remains pending. Current R8 training and its frozen controller are unchanged. [Comparison preparation](../training/reports/cpu-rehearsal-comparison-preparation-20261014.json).

PARTIALLY IMPLEMENTED: the disposable server rehearsal runner is prepared and reviewed. All 172 training integrity tests pass, including 13 synthetic rehearsal tests; metadata selection passes all four curricula. It reuses pinned trainer functions, checks real updates and unchanged base parameters, and binds saved adapter weights to before/after captures. Numerical execution and export/Colibri comparison remain pending until the current controller finishes training and evaluation. No second optimizer or later application has started. [Procedure and remaining launch gates](AI_PRETRAINING_CHECKS.md), [preparation evidence](../training/reports/cpu-rehearsal-preparation-20261014.json).

IMPLEMENTED and verified: the reusable read-only `audit_training_inputs.py` checks manifest hashes, application coverage, trusted-context consistency, explicit English/French language scope, target schemas, duplicate tool definitions, contradictory labels for identical full model inputs, exact training/validation overlap and complete schedule coverage. R8 and all three queued cumulative stages pass. All 159 training integrity tests pass, including 11 adversarial audit tests. Training-only rehearsal sets contain 48, 59, 72 and 84 varied examples respectively. Exact input checks preserve genuine history; they do not establish semantic independence or model accuracy. [Audit and preparation evidence](../training/reports/pretraining-correctness-audit-20261014.json).

PLANNED before the next full training: execute a disposable server-only numerical rehearsal and compare its decoded actions through the real merge/export and Colibri path, using a predeclared development-validation probe. Verify gradients and actual updates, investigate unexpected critical-target or export discrepancies, then discard rehearsal weights and start the full run from its original pinned base. The current capacity probe checks one long row twice; the expanded numerical rehearsal has not run. R8 continues unchanged, with no competing optimizer. No simulation or predicted 95% result is claimed.

IMPLEMENTED and verified as reporting preparation: `report_serial_candidate_v2.py` keeps original regressions and the 48 R8 fresh controls separate, checks each represented application against the existing targets plus 95% full actions, and rejects retained-app regressions within either group. It binds clarification scoring to the attested evaluation provider, avoiding false failures from later wording changes. Twenty report tests pass, and replaying the captured 48-case baseline exactly reproduces every overall and per-app assessment, including all 12 correct clarifications. This replay is not new inference or an accuracy improvement. The running R8 controls and frozen data remain unchanged. Each future stage must use this report with its frozen provider clarification source; no later training or activation has started. [Reporting evidence](../training/reports/serial-stage-report-controls-v2.json).

PARTIALLY IMPLEMENTED: R8 server training started on 2026-10-14 at 10:17 UTC with 14 CPU threads. Both capacity updates passed across all 24 intended layers; peak RSS was 5.86 GiB. The reviewed controller monitors training and continues into checkpoint evaluation. Training is incomplete and no R8 accuracy improvement is claimed. [Launch evidence](../training/reports/shared-v5r8-launch.json). The same shared Qwen3.5-0.8B candidate selected at R7 step 1200 scores 47/48 correct tools (97.92%), 18/36 eligible exact arguments (50%), 48/48 valid structures (100%) and 30/48 full actions (62.5%) on 48 new English/French controls. This exposes a generalization gap beyond the repeatedly inspected regressions. The controls comprise 24 bilingual scenarios authored by the implementation team, not independent external certification. All three temporary Colibri workers stopped and production remained unchanged. [Fresh baseline](../training/reports/shared-v5r8-baseline.json).

IMPLEMENTED and verified: the R8 curriculum retains all 2,065 R7 training rows and all 275 validation rows unchanged, appending 274 native-verified synthetic examples for date boundaries, compound filters, descriptive shortcuts, saved selections, financial limitations and priority edits. All 2,614 training/validation rows and 48 fresh control envelopes pass tokenizer/template/parser and loss-boundary checks. Thirteen R8 integrity tests pass. The FP32 training base reproduces all 474 tensors of the evaluated Colibri artifact after its documented FP16 export. These preparation checks are not accuracy improvements. [Dataset](../training/datasets/shared-v5r8-en-fr/manifest.json), [metadata checks](../training/reports/shared-v5r8-en-fr-metadata-preflight.json).

PARTIALLY IMPLEMENTED: the server-only R8 epoch is running. After completion, compare saved checkpoints using the unchanged 275-row validation set, then evaluate only the selected changed candidate against the original 438 regressions and the 48 fresh controls separately. Neither acceptance set selects checkpoints or supplies optimization examples. The selected candidate must pass all existing gates and the fresh controls for each application. No candidate activates itself, and later application training remains queued. [Frozen selection policy](../training/reports/shared-v5r8-checkpoint-selection-policy.json).

PARTIALLY IMPLEMENTED: R7 training and evaluation completed on 2026-10-14, but model acceptance FAILED. All 2,065 server training steps and seven saved-checkpoint comparisons completed; the predeclared functional rule selected step 1200. On 438 V2 regression cases: 427/438 correct tools (97.49%), 313/334 eligible exact arguments (93.71%), 435/438 valid structures (99.32%) and 413/438 fully matched actions (94.29%). Only 4/15 sets pass every gate; six critical model cases fail. All three evaluation workers stopped, artifact identities matched before/after, and production stayed unchanged. Management Projet remains disabled. Contracts, Gestion Magasin and Reservation training remain queued behind shared-model acceptance. [Measured R7 report](../training/reports/shared-v5r7-en-fr-evaluation.json).

IMPLEMENTED and verified: the queued R8 preparations retain every byte of the current shared curriculum and append the existing reviewed synthetic examples for each later application. Contracts V6r8 contains 2,492 training / 319 validation / 564 evaluation cases; Gestion Magasin V7r8 contains 2,690 / 362 / 654; Reservation V8r8 contains 2,870 / 402 / 738. Each evaluation total includes the 48 fresh controls, which remain excluded from optimization and checkpoint selection and must be reported separately from the original regressions. Thirteen retention, scope and trainer-startup tests pass. Metadata checks pass all 3,272 cumulative training/validation rows and 738 evaluation envelopes using the server-matching tokenizer and Colibri template/parser, without local model weights or inference. The sole reviewer found no source issues. These are preparations, not trained models; each stage still requires its exact accepted predecessor, a frozen baseline and server admission checks. [Metadata evidence](../training/reports/shared-v8r8-en-fr-metadata-preflight.json).

## Draggable assistant launcher - 2026-10-12

IMPLEMENTED and deployed: the six frontends use the same dependency-free launcher hook. The default bottom offset is 96px; mouse, touch and pen dragging, a 6px drag threshold, keyboard arrows and Home reset keep the button movable without changing the robot or native theme. Position is clamped to the viewport and device safe areas, including classic scrollbar gutters. Route changes and chat close/reopen preserve position while the authenticated layout remains mounted; reload resets it.

Verification: 358 assistant tests, six TypeScript checks, scoped lint and all six optimized production builds passed. One reviewer found a scrollbar coordinate issue, which was fixed and regression-tested; the final review has no remaining findings. Native dummy-login browser checks passed in all six apps; Facturation also passed authenticated live launcher checks. All six frontend releases passed normal Git pushes and remote-head verification; their live containers contain the compiled launcher and their HTTPS routes return 200. Production settings, 44 supporting containers, database volumes and the running training process were unchanged. Gestion Magasin’s tested footer still overlaps the default position; dragging clears it and restores next-page access. Training continues independently; production assistant feature flags and the shared model remain unchanged.

## Current shared-model and rollout status - updated 2026-10-13

IMPLEMENTED - training complete: V5r6 finished all 1,969 server optimization steps in 56,587.8 seconds (15 hours 43 minutes), covering 850 Management Projet, 689 Facturation and 430 Design Workflow examples. All recorded losses are finite. The original loss rule selected step 1800: validation macro loss 0.0702729237, compared with baseline 0.0709163280 and final-step loss 0.0731497569. Management Projet improves against its baseline loss; Facturation and Design Workflow remain above theirs. These are losses, not accuracy scores. [Completed training evidence](../training/reports/shared-v5r6-en-fr-training.json).

PARTIALLY IMPLEMENTED - acceptance FAILED: all 438 frozen cases and the eight-request performance probe completed. R6 scores 420/438 correct tools (95.89%), 305/334 eligible exact arguments (91.32%) and 438/438 valid structures (100%). Only 3/15 frozen sets pass all gates. Management Projet reaches 95.95% exact arguments but 93% tool selection; Facturation and Design Workflow remain below the argument target. That step-1800 checkpoint is not promoted. The subsequent eight-checkpoint functional validation comparison completed all 2,200 requests and selected step 1969. Its separate unchanged 438-case acceptance run also FAILED: 415/438 tools (94.75%), 308/334 exact arguments (92.22%) and 435/438 valid structures (99.32%). Only 3/15 sets pass; critical actions match 130/150. The eight-request probe completed and all three workers stopped. Neither checkpoint is promoted and no later-app training has started. [Selected-checkpoint results](../training/reports/shared-v5r6-selected-en-fr-evaluation.json), [selected performance](../training/reports/shared-v5r6-selected-en-fr-performance.json). [Complete accuracy results](AI_MODEL_ACCURACY.md#v5r6-measured-results--2026-10-13), [performance evidence](../training/reports/shared-v5r6-en-fr-performance.json).

IMPLEMENTED - checkpoint comparison complete: the fixed validation rule selects step 1969 with 231/275 fully matched actions and 86.65% application-macro action accuracy. The baseline scored 227/275 (85.39% macro); the loss-selected step 1800 scored 223/275 (84.11%). All eight candidates completed 275 rows representing 222 underlying scenarios. Their worker identities and artifacts matched before/after, temporary workers stopped, and production remained unchanged. Validation is not acceptance; the separate 438-case evaluation for step 1969 has completed and failed its frozen gates. [Full comparison](../training/reports/shared-v5r6-functional-validation.json).

IMPLEMENTED - precision diagnostic complete: the same 60 fixed validation scenarios score 47/60 fully matched actions with dense int8 enabled and disabled, with 58/60 valid structures in each. Two cases improve and two regress; 45 pass in both modes and 11 fail in both. All three diagnostic workers stopped and production remained unchanged. This small paired diagnostic does not establish acceptance or explain every remaining error. No overall gain supports changing the inference precision at this point. [Measured diagnostic](../training/reports/shared-v5r6-precision-diagnostic.json). The exported model contains 474 FP16 tensors, verified against the evaluated weight hashes. Disabling dense int8 uses FP32 computation from those exported values; it does not restore the original unrounded FP32 training weights. The historical report field `candidate_full_precision` refers to this int8-disabled mode. [Storage precision clarification](../training/reports/shared-v5r6-precision-storage-note.json).

IMPLEMENTED - framework reference complete: all twelve fixed development scenarios ran successfully with the same 474 FP16-rounded exported tensors and pinned configuration. The training framework and Colibri with dense int8 disabled return identical actions/errors on all twelve: eight correct and four incorrect. Normal Colibri dense-int8 mode previously matched nine of these twelve. All three modes produced twelve valid structures. This small diagnostic finds no overall framework advantage and does not establish acceptance or complete numerical equivalence. Production remains unchanged; no training or business operation ran. [Paired framework evidence](../training/reports/shared-v5r6-framework-reference.json).

IMPLEMENTED - R7 starting baseline measured: 50 changed cases were requested afresh, with 228 byte-identical validation and 435 byte-identical evaluation cases reused under the same step-1969 model, runtime, provider and settings. V2 validation matches 231/275 actions (86.83% application macro). The separately versioned V2 evaluation remains below target: 415/438 correct tools (94.75%), 306/334 exact arguments (91.62%), 435/438 valid structures (99.32%) and 394/438 fully matched actions; 2/15 sets pass. These are baseline results before R7 optimization, not training improvements. All temporary workers stopped and production remains unchanged. Original V1 scores are preserved; no combined latency claim is made. [Baseline and reuse evidence](../training/reports/shared-v5r7-baseline.json).

PARTIALLY IMPLEMENTED - next training preparation: `shared-v5r7-en-fr` contains 2,065 training and 275 validation examples for the same three applications. It replaces twelve reviewed inconsistent instructions at their original indices, retains the other 1,957 parent rows byte-for-byte and appends 96 reviewed saved-selection context contrasts. The separately versioned V2 validation clarifies 47 rows without changing their targets. Original V1 training, validation and evaluation files remain unchanged; both 438-case evaluation versions are bound by hash.

Six integrity tests pass. All 2,340 training/validation rows pass schema, tokenizer, Colibri-template/parser and loss-boundary checks; maximum lengths are 7,662 training and 7,496 validation tokens within 8,192. The sole reviewer found no remaining issues. No weights were loaded locally during dataset preparation and no accuracy gain was claimed. Server metadata and capacity checks subsequently passed; R7 training has now started as recorded above. [Prepared dataset](../training/datasets/shared-v5r7-en-fr/manifest.json), [metadata evidence](../training/reports/shared-v5r7-en-fr-metadata-preflight.json).

IMPLEMENTED and deployed: shared core 0.2.3 removes invoice-only wording and the blanket claim that profit is unavailable from its English/French clarification messages. The schemas, reason/language identifiers and permission checks are unchanged. Source and packaged-core checks each pass the same 30 tests; six native application suites pass 1,293 tests plus 174 subtests, with one inapplicable case skipped. The single reviewer found no issues. All seven source changes have been released through their existing hooks after pulling each remote. All three remote heads, deployed package files, health checks and migrations are verified in all six apps. Business-table counts, database volumes, settings, feature flags, hooks and unrelated containers are unchanged. The production model is unchanged. [Deployment evidence](../training/reports/core-0.2.3-release.json). [Package evidence](../training/reports/core-0.2.3-preparation.json).

IMPLEMENTED and verified: eight incorrect R6 Management Projet record proposals were replayed through the actual native target guard with synthetic saved context; all eight were rejected. This read-only guard check does not execute business operations and does not turn model failures into successes. The complete R6 model score remains unchanged. [Target-guard audit](../training/reports/shared-v5r6-target-guard-audit.json).

IMPLEMENTED and verified: the exact training base matches 473 previously verified FP32 tensors, all three attested tokenizer files and the full shard index. Server metadata checks passed 1,969 training and 275 validation rows. Two resumed capacity updates passed across all 24 layers; the earlier user-interrupted attempt is preserved and does not count as a completed capacity test.


PARTIALLY IMPLEMENTED: V5r5 training/export and all 438 frozen evaluations completed. Acceptance FAILED: 406/438 correct tools (92.69%), 299/334 eligible exact arguments (89.52%) and 430/438 valid structures (98.17%). Step 600 was selected by validation; production remains unchanged. See [measured results](AI_MODEL_ACCURACY.md#v5r5-measured-results--2026-10-12).

IMPLEMENTED and verified: all 825 validation requests completed across saved R5 checkpoints 600, 1200 and 1800. The fixed rule selects step 600: 227/275 action matches and 85.39% application-macro action accuracy, versus 220/275 (82.93% macro) and 219/275 (82.86% macro). These are validation scores, not acceptance. The 275 rows cover 222 underlying scenarios; grouped scores are reported separately. Step 600 is the identical candidate already evaluated on all 438 frozen regressions, so its failed acceptance remains authoritative without repeating unchanged tests. All worker artifacts/processes matched before and after; temporary workers stopped and production remained unchanged. [Measured comparison](../training/reports/shared-v5r5-functional-validation.json), [frozen policy](../training/reports/shared-v5r5-checkpoint-selection-policy.json).

IMPLEMENTED and verified: shared core 0.2.2 and all six native adapters validate saved selections and recognized explicit record targets. Native authorization, exact-target confirmation and requesting-user history remain authoritative. Assistant suites passed: Facturation 863; Management Projet 90 plus 140 subtests; Design Workflow 93; Contracts 87 plus 14 subtests; Gestion Magasin 87 plus 10 subtests; Réservation 73 plus 10 subtests, with one inapplicable tenant-move case skipped. The single reviewer found no remaining source issues. These backend checks do not count as model accuracy.

IMPLEMENTED and verified: approved existing-hook backend releases completed for contracts, gestion_magasin, reservation, management_projet. Core 0.2.2 source, migrations, health checks, all requested remote heads, database volumes and business-table counts were verified. Their assistant feature flags remain disabled; the shared production model is unchanged. The remaining Facturation and Design Workflow backend releases are also published to all three remotes: Facturation `fdffbf28403e`, Design Workflow `c6bc398fd5d6`. Fresh native suites passed 863 and 93 tests respectively. Deployed source/core hashes, migrations, health, business row counts, database volumes and unchanged training/model identities were verified. [Release evidence](../training/reports/approved-backend-release-20261012.json).

IMPLEMENTED locally and verified: new V6r6/V7r6/V8r6 preparations retain the complete current V5r6 curriculum, including all 166 added training rows. Contracts contains 2,122/319/516 training/validation/held-out cases; Gestion Magasin 2,320/362/606; Réservation 2,500/402/690. Seven integrity tests passed. All 2,902 cumulative training/validation rows passed server-matching tokenizer, Colibri template/parser and loss-boundary checks without loading weights or running local inference/training. The 690 held-out envelopes are byte-identical to the previously checked set; their metadata evidence is reused explicitly, not counted as fresh inference. [Metadata evidence](../training/reports/shared-v8r6-en-fr-metadata-preflight.json). These preparations do not establish model accuracy. Bind the actual accepted predecessor before any launch; if the accepted curriculum changes, prepare another version rather than dropping its rows. No later-stage training has started.

Historical R5 preparation: IMPLEMENTED locally: corrected sequential datasets retain exact predecessor bytes and unchanged new-app held-out envelopes. Contracts V6r5 has 1,956/319/516 training/validation/held-out cases; Gestion Magasin V7r5 has 2,154/362/606; Réservation V8r5 has 2,334/402/690. All 2,736 cumulative training/validation rows and 690 held-out rows passed local tokenizer/template/parser checks without model weights. The same 2,736 training/validation rows also passed the server metadata check at 0.25 CPU core and 2 GiB, with 573,161,472 bytes peak memory. No weights or optimization were loaded. [Local metadata evidence](../training/reports/shared-v8r5-en-fr-metadata-preflight.json), [server evidence](../training/reports/shared-v8r5-en-fr-server-preflight.json).

85 shared/training tests and 168 subtests passed. Source, dataset, tokenizer and runtime hashes are pinned. Four completed, idle benchmark services were stopped to release their approximately 10.4 GiB allocation; their model files and results were preserved. Current training, latest comparison candidates and production inference remained unchanged.

No later application training has started. Contracts → Gestion Magasin → Réservation remain sequential and require predecessor acceptance, a frozen baseline and launch-time resource/capacity checks. Management Projet remains disabled in production. Colibri PR work remains deferred.


Current step: shared V5r8 server training, model-quality evaluation and reviewed preparation for subsequent runs. All six application integrations and the named-list navigation releases are authorized; later application training remains sequential behind shared-model acceptance. The Facturation Phase 1 report and subsequent application reports remain available as historical implementation evidence. Successful basic workflows do not establish 95% broad model accuracy.

## Historical Facturation rollout - 2026-10-08 and 2026-10-09

The following results describe the earlier Facturation rollout and its model version. They remain evidence for that release; the current shared-model status and six-application releases are recorded above.

### IMPLEMENTED and verified
- Reusable Python provider/orchestrator/registry, Django integration,17 typed tools, native permissions, company/object checks, bounded read results, safe navigation and financial calculations reused from Facturation.
- Supported document/client edits and deletion require exact-target confirmation and fresh native permissions. Native history and durable AI audit identify the requesting user. Stock reversal for delivery deletion uses the shared native service.
- Authenticated root FAB, native theme/components, responsive chat, company-tab scope, history, cancellation, retries, slash help, human form labels and explicit detail-to-list navigation.
-12 reviewed bilingual knowledge documents, incremental synchronization, permission filtering before ranking, exact-version history protection. General help delivers verified procedures; specific business questions use the local model. Exact positional follow-ups use authorized saved references.
- Server-only v4 LoRA training completed410steps; validation loss0.117782→0.068355. No private business records used. Colibri CPU export and artifact hashes verified.
- Production at this checkpoint: all three Facturation/shared-core repositories released through local commits/Git; all nine remote heads verified. Backend and frontend native HTTP routes return 200; private model remains healthy with the same model identity and start time.
- Latest module-shortcut changes: 819 assistant/backend tests and 112 chat frontend tests passed; TypeScript, ESLint and the assistant-enabled production build passed.
- Full backend2,272tests+30subtests passed; final assistant765tests passed, then52 focused help/reference regressions after review. Four Docker/static-asset tests passed. Frontend75 final native/chat tests, TypeScript, ESLint and production build passed.
- Real local v4 checks passed invoice/client/product search, quote/article search, EN/FR collected-payment summaries, unpaid/ordinal follow-ups, navigation/list return and reviewed EN/FR workflow answers. Original model failures remain recorded separately.
- Public-repository audit found no actual credentials or private business artifacts in release commits. Runtime environments, keys, browser state, raw reports, weights and checkpoints are ignored. Application code is edited locally and released via Git pushes.

### Suggestion-button update - 2026-10-09
- IMPLEMENTED: complete permission-filtered English/French starter questions, immediate sending on click, active-company isolation and explicit click-to-send instructions. Slash-menu entries remain editable drafts.
- Validation: 831 assistant backend/security tests and 115 chat frontend tests passed; TypeScript, ESLint, production frontend build and source/wheel checks passed. The single reviewer found no unresolved code issues.
- Initial production UI release: each of the five questions sent exactly once in the active company. Unpaid invoices, recent quotes, stock and invoice workflow completed safely; desktop/mobile fit, native English metadata and slash drafting passed.
- Preserved failures: original logistics wording returned INVALID_MODEL_OUTPUT; its clearer French/English replacement completed successfully as separate normal chat requests. An English fresh-conversation unpaid search incorrectly selected the previous-results tool; audit confirmed CONTEXT_EXPIRED from that unavailable tool, with unchanged user authorization. The corrected catalogue omits this tool until a nonempty result set exists. A private provider probe then selected the correct unpaid-invoice search. The stock probe confirmed the native minimum-status filter; empty production cards alone were not treated as filter evidence.
- Final corrected release: 10/10 actual production button-click checks passed (five French, five English), with one exact request per click and correct company scope. Both final stock questions independently selected the native minimum-status filter in private provider probes. Source heads and installed wheel were verified, services healthy, model unchanged. Observed production stock lists were empty; no live threshold values were inferred. Evidence: [sanitized starter checks](../training/reports/production-starter-suggestions-checks.json).
- These targeted checks do not replace the held-out model evaluation, whose last recorded scores remain below target. The catalogue correction has not been rescored against that dataset.

### Measured model limits
Frozen independent80 cases: tool selection50/80 (62.5%); exact arguments24/76 (31.58%); schema73/80 (91.25%). Base: 44/80,18/76,61/80. Targets95/95/99 are UNMET. Complex filters, limits, operation choice and malformed calls remain weaknesses. The application's deterministic help/reference handlers are not credited as model accuracy.

Dedicated server8-request sample: sequential mean8.34s, p95(maximum of4)9.74s; concurrency2 mean12.29s, p95(maximum of4)17.66s. Decode56.94tokens/s excludes prefill; peak process RSS2.58GiB and about4busy CPU cores. This small sample is not a load-capacity certification.

### Production verification
- Prepared production checklist: 12/12 passed, including dashboard FAB, invoice/article search, financial equality, company/history isolation, bilingual workflows, navigation, mobile fit and public-login absence. The new module release passed nine additional production checks: permitted catalogue, English/French capability answers, stock/logistics/article reads, described article search and desktop/mobile menu fit.

### PARTIALLY IMPLEMENTED
- Overall model acceptance remains below target, despite passing the tested basic application workflows.

### Remaining limitations
- Complex model requests may omit filters or ask for clarification; inspect returned record details before selecting an action. Exact-target confirmation is mandatory for supported writes.
- Stock, logistics, account and payment adapters are read-only. Supported writes are bounded document/client actions, not all operations in every module.
- Full physical-device keyboard and assistive-technology certification remains unperformed.
- At this historical checkpoint, Management Projet integration and Design Workflow shared-model training were authorized, with the remaining application integrations still planned. The current six-application implementation and release status is recorded above; every application reuses the shared model.

Historical work log: [AI_PROGRESS_HISTORY.md](AI_PROGRESS_HISTORY.md). Detailed evidence: [AI_TESTING.md](AI_TESTING.md), [AI_FINE_TUNING.md](AI_FINE_TUNING.md), and training/reports.

## Shared UI revision - 2026-10-10

IMPLEMENTED locally: canonical Design Workflow-based MUI interface, identical Facturation and Management Projet copies, local SVG robot/icons, scoped palette, optional company row, bold author labels, meaningful immediate suggestions, accessible shortcuts, draft-safe command switching, bare-slash help and mobile input sizing. Existing business handlers and permissions remain authoritative. Management Projet production activation is still disabled.

Verified with local synthetic logins: 24 actual screenshots covering reference/Facturation/Management Projet × light/dark × empty/populated × shortcuts closed/open, eight side-by-side comparisons, mobile 390×844 and 390×420, six-line input, Escape/focus wrapping, draft preservation, company switching, AI detail-to-list navigation, native confirmation priority and cancellation. No API responses were replaced for these browser checks. Physical-device keyboard and assistive-technology certification remain unperformed.

Automated validation: Facturation 125 assistant frontend tests; Management Projet 55; Facturation 12 focused backend tests; Management Projet 3 focused backend tests (including English/French subcases); 190 existing Facturation form tests. TypeScript, assistant ESLint and both production frontend builds passed. Design Workflow’s requested bold labels passed its 26 assistant tests and production build. One reviewer completed the review with no remaining blocker after fixes.

IMPLEMENTED: reviewed source published to company, personal and production for the central repository, Facturation frontend/backend, Management Projet frontend/backend and Design Workflow frontend. All 18 remote heads matched. Three frontend production builds, deployed-source comparisons, container health and anonymous HTTPS login checks passed. No backend migration was needed. The eleven Facturation form return fixes are published. Management Projet’s effective production AI setting remains false; the shared inference process and training unit were not restarted.

PLANNED: remaining shared UI integrations. The six-app navigation follow-up is recorded below. Shared V5 server training continues; no V5 accuracy score is available yet. Colibri upstream PRs remain explicitly deferred.


## Six-app return navigation - 2026-10-10

IMPLEMENTED and verified locally: all remaining history-based return controls removed from facturation, management_projet, design_workflow, contracts, gestion_magasin and reservation. The Holding portal is excluded. Contracts has four corrected list/form destinations, Gestion Magasin 22 and Reservation ten. Six not-found pages keep their explicit Home/dashboard action instead of a history-dependent Return button.

Gestion Magasin returns preserve the applicable store for articles, stock, inventory, sales, expenses and attendance. List selection accepts the URL hint only when the store belongs to a visible active membership. Cross-store lists keep their existing destinations. Manual store changes synchronize an existing store hint without undoing the native pagination reset or discarding sorting and anchor parameters. The stock-detail destination still follows its stock/store-stock label.

Validation: 297 focused frontend tests passed across the six apps; the broader Magasin/pagination run passed 69 tests (overlapping coverage, not an additional unique count). Scoped ESLint, TypeScript and all six production builds passed. Regressions cover authorized deep links, invalid/unknown store hints, revoked membership, restricted store visibility, tab changes and pagination preservation. One reviewer completed the final review with no remaining findings. Local browser checks confirmed explicit 404-to-dashboard navigation in Facturation, Management Projet and Design Workflow. Source scans found no remaining history navigation calls. Sensitive-added-content checks passed.

Publication: IMPLEMENTED. All six reviewed frontend commits are published to company, personal and production; all 18 remote heads matched. Deployed source matches the reviewed files in each app, all six frontend containers are healthy and all six login routes return HTTP 200. Production browser verification confirmed Facturation’s 404 Home navigation; the other checked apps reached their expected sign-in pages without active browser sessions. Authenticated navigation for those apps was verified locally where available, not claimed as a complete production business-flow test. No backend, database, model, permission or training configuration changes were included. The training process retained its original process identity; the shared inference service remained healthy with its original start time.

## Serial training and Contracts preparation - 2026-10-10

PARTIALLY IMPLEMENTED: Contracts (`contrat`) native adapter and shared UI are under local validation. See [discovery](AI_CONTRACTS_DISCOVERY.md), [actual checks and remaining gates](AI_CONTRACTS_PROGRESS.md), and the [single-job training queue](AI_TRAINING_QUEUE.md). The current shared V5 run continues; no Contracts training or model accuracy is claimed.

The user's additional login-theme request is limited to Contracts and Réservation, with Facturation as the reference. Local desktop/mobile screenshots confirm matching dark canvas, transparent outlined fields, heading size and a theme toggle 16px from the top/right. Theme switching preserves typed input and persists across reload. IMPLEMENTED: the two theme fixes are published to company, personal and production; all six remote heads matched. Exact-source production builds and 26 existing auth/theme tests per app passed. Live Contracts desktop and Réservation mobile login checks confirmed the palette, outlined fields and top-right toggle; both containers are healthy. The training process retained its original PID.

## Contracts adapter preparation - 2026-10-10

PARTIALLY IMPLEMENTED: native permission/company tools, confirmed writes with actor history, EN/FR knowledge, history and canonical MUI UI are verified locally. Final checks: 576 backend tests plus 4 subtests; 60 final assistant/form frontend tests, TypeScript, ESLint and production build passed. Local dummy browser checks include scope isolation, read-only denial, actual PDF, confirmed deletion/audit, history and eight-state visual comparison. See [Contracts progress](AI_CONTRACTS_PROGRESS.md). The shared next-stage dataset passed tokenizer/Colibri preflight; Contracts model training/accuracy and activation are still incomplete. Shared V5 remains the only active training job.

Contracts source is now published disabled: backend `00503a910cda`, frontend `875524520cc0`, six remote heads verified; additive migration/knowledge sync and native health checks passed with existing business row counts unchanged. Gestion Magasin now has the locally tested adapter and prepared dataset documented below; Réservation local implementation and dataset preparation are recorded below.

## Gestion Magasin local preparation - 2026-10-10

PARTIALLY IMPLEMENTED: native store/role tools, controlled actor-attributed writes, history/RAG and canonical MUI UI are locally tested. Full backend run: 448 tests; final assistant subset: 56. Frontend: 40 focused tests; dummy browser scope, native PDF, confirmed deletion and read-only/history checks passed. Eight reference comparisons have no visual blocker. Synthetic EN/FR data is prepared, not trained; no model accuracy is claimed. See [details and remaining gates](AI_GESTION_MAGASIN_PROGRESS.md). Current shared V5 remains the only training job; its frozen inputs are unchanged.

Gestion Magasin source release: backend `a7acaefa4891`, frontend `ee6ffbaf750e`, all six remote heads verified. Additive migration and twelve knowledge documents applied with all sixty business-table counts unchanged; services healthy. Assistant remains disabled, shared production model and current training unchanged.

## Réservation local preparation - 2026-10-10

PARTIALLY IMPLEMENTED: native permissions (including independent Hilton access), seven bounded tools, actor-attributed confirmations, owner-scoped history/RAG and canonical MUI UI pass local checks. Final backend: 514 tests, including 43 assistant tests; frontend: 26 assistant tests, TypeScript, ESLint and production build pass. Native dummy-login browser checks cover search/navigation/list return, confirmed deletion/history, logout/read-only access and EN/FR responses. Eight side-by-side chat comparisons and two mobile sizes pass. See [details](AI_RESERVATION_PROGRESS.md).

Synthetic EN/FR data is prepared, not trained: 150/30/84 Réservation train/validation/held-out cases. The six-app shared-v8 preparation retains earlier curricula; current V5 frozen inputs remain unchanged. Model accuracy, server benchmarks and activation remain incomplete.

Réservation source is published disabled: backend `105cc4e24c90`, frontend `3c09a4d8a103`, six remote heads and 37 deployed backend file hashes verified. Assistant migration/knowledge sync succeeded; all 26 business-table counts are unchanged. Services and live login are healthy, anonymous assistant access returns 401, and the shared production model/current training process are unchanged.

The prepared cumulative six-app dataset passed exact server tokenizer/Colibri preflight: 2,014 rows, maximum 4,977 tokens, no truncation. This was metadata-only validation and started no new training job. That metadata check started no optimization; V5 has subsequently completed.


## Shared V5 status update - 2026-10-10

IMPLEMENTED: training, isolated export, 328 frozen evaluations, warm performance probe and artifact/process verification completed. Model acceptance remains PARTIALLY IMPLEMENTED: all eight evaluation sets miss at least one required gate. The native tokenizer check passed 328/328 prompt-ID comparisons; runtime diagnostics are now complete (see the later update). No further optimization job has started. Contracts, Gestion Magasin and Réservation source is published disabled with datasets prepared; serial model training and acceptance remain pending. Production model unchanged. See [measured scores and limitations](AI_MODEL_ACCURACY.md#shared-v5-measured-results--2026-10-10).

## Shared V5r2 preparation - 2026-10-10

IMPLEMENTED: failure diagnostics distinguish learned mistakes from export problems; all three native refinement generators pass schema validation with database access forbidden. Existing rows and frozen benchmarks are retained. The single reviewer found no native-label or permission/target issues. Fifteen training/acceptance regression tests pass.

PARTIALLY IMPLEMENTED: the 1,454/186 shared refinement dataset and 34 independent cases are prepared. The sequential server capacity comparison passed with checkpointing enabled (two finite updates across all 24 layers; peak RSS 5.39 GiB). Disabling it reached the isolated 18 GiB memory limit before completing a step. Keep checkpointing enabled; no model was saved or activated. Exact server preflight passed all 1,640 rows (maximum 5,135 tokens). All 34 new frozen baseline cases were measured before optimization; their failed acceptance is documented. Reviewer-requested validation deduplication preserved every training and held-out row. The revised exact server preflight passed all 1,640 rows again. The isolated V5r2 continuation has started (1,454 steps, 14 CPU threads, 24 text layers, rank 16, checkpointing enabled). Guarded export and all 362 frozen cases are queued automatically. Optimization completion and full acceptance remain pending. Production model unchanged.

V5r2 reviewed preparation source is published as `c7fbddfda2eba43503dbf0e803f61d881b03b313`; all three remote heads and all 35 deployed file hashes were verified. The production inference service remained healthy with unchanged start time.

## Serial runner preparation - 2026-10-10

IMPLEMENTED locally: separately versioned future-stage runner and strict cumulative application validation, with all 22 training integrity/acceptance/scope tests passing. The active V5r2 trainer, helper scripts, dataset and evaluator remain unchanged. No later-stage optimization has started. The single reviewer verified that obsolete mixtures, altered predecessor files and missing retained rows are rejected, with no remaining findings. The serial runner still requires its own server preflight and launch gates before use; model acceptance remains incomplete.

The serial runner source was published as `3ee7b7d9f242bf26e6f6be686c0303fd711967cc`; all three remote heads and six deployed file hashes matched. Its 22 tests also passed on the server without loading weights or optimizing. The revised V8r2 cumulative dataset then passed the server tokenizer/template/parser/loss-boundary preflight for all 2,168 rows, with matching metadata/script hashes and no truncation. V6r2/V7r2 remain exact validated prefixes. [Server preflight evidence](../training/reports/shared-v8r2-en-fr-server-preflight.json). The current V5r2 training continues; no later-stage optimization or production model replacement has started.

## Shared candidate and metadata follow-up - 2026-10-11

PARTIALLY IMPLEMENTED: V5r2 completed 1,454 server optimization steps and isolated Colibri export. Its 362-case frozen evaluation is complete and acceptance failed; no model activation or replacement is authorized by training completion. Follow-up local tool descriptions clarify supported filters, native status labels, budget rows versus totals, and editable form labels. Backend suites and one independent review passed; the source is not deployed and the separate description-only diagnostic is not measured. See [the serial queue](AI_TRAINING_QUEUE.md) for exact validation counts and remaining gates.

V5r2 measured totals: 344/362 correct tools (95.03%), 254/280 eligible exact arguments (90.71%), 358/362 valid structures (98.90%). The matched V5 baseline was 322/362, 226/280 and 352/362. Only one of 11 sets passes every gate; aggregate gains do not erase critical-case failures. The isolated eight-request warm probe measured 7.805 s sequential mean, 11.699 s at concurrency two, 54.73 decode tokens/s excluding prefill, 2.60 GiB peak RSS and zero errors. [Full measured results](AI_MODEL_ACCURACY.md#shared-v5r2-measured-results--2026-10-11).

## Shared model diagnostics and adapter corrections - 2026-10-11

The description-only V5r2 comparison completed all 362 cases on the same pinned candidate, provider and runtime. Tool selection increased from 344/362 to 346/362 (95.58%); exact arguments increased from 254/280 to 257/280 (91.79%); structured validity decreased from 358/362 to 356/362 (98.34%). Three of eleven sets passed all gates. Overall acceptance still FAILS; production was not changed. This is regression evidence, not an unseen certification. [Measured report](../training/reports/shared-metadata-v1-en-fr-comparison.json).

IMPLEMENTED and verified locally, not released: Management Projet now sends freshly authorized saved result IDs in display order to the planner. Expired, malformed or incomplete selections clear entirely, without shifting ordinals. Exact-target confirmation and native actor history remain unchanged. Shared calendar anchors derive from the application's trusted local date; they do not calculate business amounts or infer missing years. Facturation's search descriptions distinguish customer/product fields, native statuses, inclusive date bounds and requested result limits. Native registry checks confirmed unchanged validation and permission metadata.

Verification after these changes: Facturation 856 assistant tests passed; Management Projet 84 tests and 130 subtests passed; Design Workflow 88 tests passed. Five shared calendar tests cover leap years, year rollover, invalid dates, unchanged caller data and actual planner context. The single reviewer found no unresolved issues.

PARTIALLY IMPLEMENTED: a separate `shared-adapter-v2-en-fr` diagnostic contains the original 362 user prompts/labels bound to current native planner inputs plus 28 new English/French saved-result cases. Historical capability metadata recovery and synthetic ordinal fixtures are explicit in its manifests. All 390 cases passed exact server-matching tokenizer/template/parser/loss-boundary checks; maximum prompt 7,228 tokens plus 512 reserved output tokens fits 8,192. No local model inference or training ran. The server evaluation completed all 390 cases against the unchanged V5r2 candidate. On the matched 362 cases: 346/362 correct tools (95.58%), 255/280 exact arguments (91.07%), and 357/362 valid structures (98.62%). The separate 28 new follow-up cases scored 12/28 tools, 9/20 exact arguments, and 25/28 valid structures. Across all 390: 358/390 tools (91.79%), 264/300 exact arguments (88.00%), and 382/390 valid structures (97.95%). Only three of twelve sets passed all gates; acceptance FAILS. All temporary workers were stopped after artifact and process verification. [Measured comparison](../training/reports/shared-adapter-v2-en-fr-comparison.json). This run changes adapter instructions, tool descriptions and calendar context together and cannot isolate each contribution.

Training status: the 1,454-step V5r2 optimization is complete; the 390-case adapter evaluation is complete and failed acceptance. Failure diagnosis and adapter correction continue; no new sustained training job has started. Contracts, Gestion Magasin and Réservation training remain queued one at a time behind acceptance. The shared model and production feature activation remain unchanged.

### Saved-result target validation follow-up

IMPLEMENTED locally and reviewed: exact ordinal-target validation now exists across all six native adapters. See the V5r3 preparation section below for verified tests and publication status. This safeguard was motivated by an isolated diagnostic selecting the wrong in-set ID; no business operation was executed by that diagnostic. Model scores are unchanged by backend safeguards.

The eight malformed calls were replayed separately with the same pinned provider and candidate process: four invented an unsupported supplier filter for financial summaries, two used field names absent from Management Projet, one omitted the required operation, and one requested an unavailable previous-result deletion operation. Provider/schema validation rejected them; the diagnostic executed no business tool and did not replace benchmark results. [Failure analysis](../training/reports/shared-adapter-v2-malformed-calls.json).

## Reviewed V5r3 preparation - 2026-10-11

PARTIALLY IMPLEMENTED: `shared-v5r3-en-fr` preserves the reviewed current-metadata curriculum and adds 122 diverse English/French training examples plus 36 validation examples. Totals: 1,576 training and 222 validation rows. The existing 390 diagnostic cases remain unchanged; 48 newly authored cases are frozen separately, making 438 evaluation cases. They are authored by the implementation team, not a blind external certification. Failure categories informed training; exact normalized split overlap is rejected, while semantic-independence limitations remain explicit.

All 1,798 SFT/validation rows and the 48 new evaluation cases passed tokenizer/template/Colibri-parser/loss-boundary checks against server-matching metadata. Maximum training length is 7,648 tokens; maximum new evaluation prompt is 3,224 plus 512 output tokens. No local model weights were loaded. [Metadata preflight](../training/reports/shared-v5r3-en-fr-metadata-preflight.json). New-case baseline measurement is running on the unchanged isolated V5r2 candidate. No V5r3 optimization has started. A server capacity check at the revised longest example remains required.

The two-update precision comparison on the earlier 5,135-token example passed for both modes: BF16 averaged 104.06 seconds/update with 5.38 GiB peak RSS; FP32 averaged 113.55 seconds with 6.59 GiB. BF16 is retained based on those measured costs. This saved no adapter and measured no accuracy. [Precision report](../training/reports/cpu-training-precision-v1.json).

IMPLEMENTED and verified locally: the six native adapters use a shared safeguard for explicit EN/FR ordinal mutation targets. A recognized request for the third saved result cannot propose the first saved result, even if both are authorized or the first is the current page. Expired/malformed selections, conflicting explicit IDs and wrong resource types reject; quoted or recognized replacement values do not become targets. This is bounded syntax, not a general natural-language intent parser. Native authorization and separate exact-target confirmation still apply.

Validation: 14 shared context tests and 22 training-integrity tests pass. Final native assistant suites: Facturation 860, Management Projet 86 plus 130 subtests, Design Workflow 90, Contracts 58 plus 4 subtests, Gestion Magasin 58, Réservation 45. The single reviewer found no unresolved code or final-dataset issues. Native adapter publication and packaged-wheel synchronization remain pending; no backend/model deployment or feature activation is claimed. Contracts, Gestion Magasin and Réservation optimization remain queued, one at a time, behind shared-model acceptance.


## Conversation framing and V5r4 preparation - 2026-10-11

The 48 new frozen V5r3 baseline cases completed against the unchanged V5r2 candidate: 14/48 correct tools, 0/34 eligible exact arguments, 48/48 valid structures. Acceptance fails. [Measured baseline](../training/reports/shared-refinement-v2-en-fr-baseline.json). V5r3 remains an untrained, preserved dataset; its multi-turn failures prompted a separate input-format investigation before sustained optimization.

A nine-request server diagnostic compared original separate user turns, removal of history, and clearly labelled history inside the current user turn. Facturation article-reference search and Design Workflow person/project/status search became correct with either alternative; Management Projet's VAT edit still produced invalid arguments. This is a small diagnostic, not model acceptance or proof of a runtime defect. Original frozen results remain unchanged.

IMPLEMENTED and verified locally: the shared planner labels earlier user messages as background and preserves the current request separately for native clarification localization. It does not parse user-provided labels to recover trusted current text. System/assistant history is excluded; native authorization remains independent. Both French-to-English and English-to-French follow-ups pass in the four affected native providers. Shared/dataset tests: 23 passed, 41 subtests. Native assistant suites: Facturation 860, Management Projet 87 plus 136 subtests, Design Workflow 90, Contracts 59 plus 10 subtests, Gestion Magasin 59 plus 6 subtests, Réservation 46 plus 6 subtests. One reviewer found no remaining issues.

PARTIALLY IMPLEMENTED: `shared-dialogue-v1-en-fr` preserves all 438 logical evaluation cases and expected labels; only 78 contain reformatted history and require fresh baseline measurement. Reuse of the other 360 results requires identical input hashes and the same pinned provider/candidate. This diagnostic is running. Combined reused results are not performance measurements.

`shared-v5r4-en-fr` retains all 1,576/222 V5r3 training/validation examples in their original splits, reformats existing histories, and adds 137/53 bounded neutral greeting/thanks variants. Totals: 1,713 training and 275 validation rows. Variants are not independent examples; no held-out targets enter SFT. The generator, production framing helper and source manifests are hashed. All 1,988 training/validation rows and all 438 evaluation cases passed tokenizer/template/parser/loss-boundary checks, with 7,648 maximum training tokens and 7,235 maximum evaluation prompt tokens plus 512 reserved output. [Preflight](../training/reports/shared-v5r4-en-fr-metadata-preflight.json). No local model weights were loaded.

No V5r4 sustained optimization has started. Server preflight, capacity validation, packaged native wheel synchronization and publication remain pending. Production model and feature flags are unchanged. Contracts, Gestion Magasin and Réservation training remain sequential behind acceptance; Colibri PR work stays deferred.


## Shared V5r4 training started - 2026-10-11

IMPLEMENTED: the complete baseline comparison is measured. Across 438 unchanged logical scenarios, conversation framing changes tool selection from 372/438 (84.93%) to 386/438 (88.13%), eligible exact arguments from 264/334 (79.04%) to 277/334 (82.93%), and valid structure from 430/438 (98.17%) to 425/438 (97.03%). All acceptance gates still fail. The 78 changed histories were measured freshly; 360 identical inputs reuse prior measurements with the same pinned candidate/provider. No combined latency claim is made. [Full comparison](../training/reports/shared-dialogue-v1-en-fr-baseline.json).

IMPLEMENTED: exact server preflight passed 1,713 training and 275 validation rows. Two unsaved capacity updates on the longest 7,648-token example passed across all 24 layers; peak RSS 6.33 GiB, update times 182.43 and 172.04 seconds using ten threads while the four-thread diagnostic ran. The initial 18 GiB job allowance was rejected by the resource gate before any job started; the revised 15 GiB limit preserved the 10% reserve plus additional headroom. [Preflight](../training/reports/shared-v5r4-en-fr-server-preflight.json), [capacity](../training/reports/shared-v5r4-en-fr-capacity.json).

PARTIALLY IMPLEMENTED: the reviewed single server continuation has started from the existing V5r2 merged checkpoint. One complete epoch covers 1,713 examples (557 Facturation, 760 Management Projet, 396 Design Workflow), rank 16/alpha 32 across 24 text layers, BF16 CPU SDPA, semantic loss weight 4 and learning rate 0.00005. Limits: 14 of 16 CPU threads, 15 GiB memory, no job swap. The shared source release `f619d6714bbd` is verified on all three remotes. Existing production inference remains healthy and unchanged.

The launcher binds the exact baseline, capacity, data, scripts, base and runtime artifacts; guarded export waits for successful complete coverage. A monitor will evaluate all 438 frozen scenarios afresh after successful isolated export. Completion, accuracy and activation are not claimed. Contracts, Gestion Magasin and Réservation remain sequential future stages.

IMPLEMENTED locally: the identical shared core 0.2.1 wheel is packaged for all six backends with source-content hashes verified. Tests against that actual wheel passed: Facturation 860; Management Projet 87 plus 136 subtests; Design Workflow 90; Contracts 59 plus 10 subtests; Gestion Magasin 59 plus 6 subtests; Réservation 46 plus 6 subtests. Native source publication remains pending; this source-only central push did not deploy application code or activate a model.


## Argument-rule diagnostic prepared - 2026-10-11

PARTIALLY IMPLEMENTED: a separate four-arm comparison preserves the same twelve synthetic cases and their targets, tools and permissions. Four are observed name/date failures; eight new controls cover names across languages, missing years, leap and non-leap centuries, and native status conversion. The arms use the original instructions, a literal-name rule, a complete-month/year rule, or both. This changes no application code or active frozen evaluation and performs no training.

Preparation checks passed: four integrity tests plus eight subtests; all 48 input/target combinations passed the server-matching tokenizer, Colibri parser, template and loss-boundary checks. Maximum prompt length is 2,527 tokens with 512 reserved output tokens. One reviewer found no issues. [Metadata evidence](../training/reports/planner-rules-v1-en-fr-preflight.json).

No diagnostic inference has run. It must follow the original candidate evaluation and performance measurement. Known failures are regression cases, and these controls are not independent certification. Any useful rule still requires broader regression evaluation before application changes or activation.


## Follow-up input diagnostic prepared - 2026-10-11

PARTIALLY IMPLEMENTED: the newest 48 cases expose repeated unsupported replies despite offered supported tools. A separately versioned 12-case EN/FR diagnostic includes three actionable bilingual scenarios, a business-background control, an unsupported-operation pair and a missing-year pair. Four arms preserve the original envelope, omit history diagnostically, change exact neutral greeting wording to the existing training phrasing, or put the current request first. The greeting arm is a wording intervention and preserves language; genuine task history remains byte-identical. The business-background control does not prove history dependence because trusted context already contains the selected records. Current-only is not a proposed production memory policy.

Five invariant tests plus 11 subtests pass. All 48 envelopes pass tokenizer, Colibri parser/template, loss-boundary and semantic alignment checks without local weights or inference. Maximum prompt 2,962 tokens plus 512 output within 8,192. [Metadata evidence](../training/reports/planner-history-v1-en-fr-preflight.json). Server measurement is queued behind the original argument-rule diagnostic and malformed-call replay. This small selected diagnostic cannot replace acceptance; no held-out targets enter training.

IMPLEMENTED locally and reviewed: shared core 0.2.2 and all six native adapters bind recognized explicit resource/ID pairs before accepting an unrelated current or saved record. Quoted values and recognized replacement clauses, including bilingual field-colon/equality forms, do not supply targets. Longest overlapping resource phrases preserve French invoice labels; separate conflicting targets reject. The ordinal guard still rejects incorrect, expired or out-of-range references. This bounded syntax is not a general intent parser or authorization mechanism; native permissions and exact-target confirmation remain mandatory. No model schema-narrowing experiment or backend deployment is claimed.

Package verification: identical 0.2.2 wheel in all six backends; SHA-256 cb7683557d82a0a91c39bdc8e50a01d2708b2808c3aa54208a8234ae22b8eaa8. Shared/training suite: 68 tests plus 154 subtests. Native suites against the actual wheel: Facturation 863; Management Projet 90 plus 140 subtests; Design Workflow 93; Contracts 87 plus 14 subtests; Gestion Magasin 87 plus 10 subtests; Réservation 73 plus 10 subtests, with one inapplicable tenant-move case skipped. Single reviewer found no remaining issues.


## Argument-rule diagnostic and malformed calls - 2026-10-11

IMPLEMENTED: all 96 isolated rule-diagnostic requests completed. For V5r4, original/names/dates/both exact arguments were respectively 4/10, 5/10, 4/10 and 5/10. Neither explicit full-month regression was fixed by any arm. Name copying improved one selected search but could worsen time-report tool choice; century-date controls still produced incorrect dates/years. No runtime prompt change is justified by these limited results. V5r2 results and all unchanged acceptance evidence remain recorded separately. [Diagnostic results](../training/reports/planner-rules-v1-en-fr-results.json).

IMPLEMENTED: four schema-rejected V5r4 calls were replayed without business execution. One used an unsupported stock-movement status, one invented a stock-write field, and two quote-number requests emitted no parsed tool call. A later inspection of the unchanged isolated log correlates both original requests and their replays with rejected prepare_change calls containing an invalid integer identifier. Their expected action was record search. The exact generated identifier value was not captured, and this does not establish a Colibri defect. Original errors and scores are preserved. [Malformed-call report](../training/reports/shared-v5r4-en-fr-malformed-calls.json).

## Greeting-bias correction and V5r5 preparation - 2026-10-11

IMPLEMENTED: the 96-request history diagnostic is complete. V5r4 eligible exact arguments increased from 2/8 with the original envelope to 6/8 with current-only or longer neutral greetings, but both alternatives produced two invalid outputs. Current-first remained 2/8. No production history/prompt change is justified. The untouched full acceptance result remains 390/438 tool selections (89.04%), 284/334 exact arguments (85.03%) and 434/438 valid outputs (99.09%). [Diagnostic evidence](../training/reports/planner-history-v1-en-fr-results.json).

IMPLEMENTED locally: the curriculum audit identified all 118 original short Hello/Bonjour histories as clarification labels. V5r5 reconstructs trusted role boundaries from the pinned V5r3 sources and V5r4 augmentation manifest, then assigns neutral history using input-only hashes that exclude labels. Current questions, targets, schemas, trusted context, genuine history and split membership remain unchanged. Training now includes 282 actionable plus 56 clarification examples after Hello, and 281 actionable plus 62 clarification examples after Bonjour. Ninety training-only date variants add all months, ordinary leap/non-leap years and century controls, using verified training templates. These are correlated variants, not independent examples. Totals: 1,803 training and 275 validation; all 438 original held-out scenarios stay excluded and unchanged.

Historical preparation status (2026-10-11): optional periodic validation selects the checkpoint with the lowest application-macro semantic validation loss, retaining the base if none improves. Final checkpoint loss remains separately reported. This is checkpoint selection, not acceptance. Server preflight, trainer smoke test, new optimization, export and acceptance evaluation are pending. No new model has been activated.

IMPLEMENTED: the six native target-binding fixes were fetched/pulled and published normally to company and personal source remotes, with exact heads verified. At that preparation checkpoint, production backend deployment was pending approval; the four subsequently approved deployments are recorded at the top of this page. The generated Facturation source snapshot corresponds to central commit c012a92; later training preparation is not included in that snapshot yet.

V5r5 preparation verification: 78 shared/training tests plus 164 subtests pass. All 1,803 training and 275 validation rows pass schema validation, exact Colibri parser round-trip, template parity, loss masking and semantic weighting alignment. All 438 retained evaluation cases pass the same checks. Maximum training length is 7,662 tokens; maximum evaluation prompt is 7,235 plus 512 reserved output, within 8,192. Tokenizer metadata matches the existing server candidate; no local weights or optimization were used. [Metadata report](../training/reports/shared-v5r5-en-fr-metadata-preflight.json).

## Shared V5r5 training completed - 2026-10-12

IMPLEMENTED training, acceptance FAILED: the reviewed isolated continuation completed from the existing V5r2 base using source commit `3b976f8dd7d0`. One complete epoch covered 1,803 examples; 275 validation examples were checked initially, every 300 steps and at completion. The lowest application-macro validation loss selected step 600. All 438 frozen cases completed; the candidate failed acceptance and remains unpromoted. Learning rate 0.00002; 24 text layers; rank 16/alpha 32; semantic weight 4; 14 CPU threads; 12 GiB limit; no swap. Existing production inference remains healthy and unchanged.

IMPLEMENTED: server preflight passed 1,803/275 rows; the longest 7,662-token two-step capacity check passed at 6.43 GiB peak RSS. The real two-step trainer smoke test selected the intermediate checkpoint at step 1 after evaluating steps 0/1/2. It proves mechanics, not accuracy. [Capacity](../training/reports/shared-v5r5-en-fr-capacity.json), [smoke](../training/reports/shared-v5r5-en-fr-trainer-smoke.json).

IMPLEMENTED: guarded export of selected checkpoint 600 and all 438 unchanged acceptance cases completed. Acceptance failed; measured results are recorded at the top of this page. The export guard rejects a step-zero selection. No production model activation or next-app training follows automatically from training completion.

IMPLEMENTED locally: corrected future datasets preserve exact predecessor byte prefixes and all existing new-app held-out envelopes. Contracts: 1,956/319/516 training/validation/test cases; Gestion Magasin: 2,154/362/606; Réservation: 2,334/402/690. All 2,736 training/validation rows plus 690 held-out rows pass local tokenizer/Colibri metadata preflight. No local weights were loaded. The server metadata preflight subsequently passed all 2,736 training/validation rows; all future optimization and predecessor acceptance remain pending.

Verification of the later-stage preparation: 85 shared/training tests and 168 subtests pass. The sole reviewer found no remaining issues. The complete curated-source dry-run passed secret/private-path exclusions; generated model weights and private evaluation logs remain excluded. No future optimizer has run.

## Resource allocation and V5r6 preparation - 2026-10-12

IMPLEMENTED and verified: saved-checkpoint evaluation used three four-thread workers (12 threads total). All 825 comparisons completed. Finished R2/R4/R5 evaluation services were then stopped to release RAM; all weights/results and production inference were preserved. Training remains configured for 14 of 16 logical threads, retaining the 10% memory reserve.

Two unsaved, 7,662-token checkpointed optimizer updates passed in 188.31 and 173.61 seconds, with 6.34 GiB peak RSS and genuine updates in all 24 intended layers. Disabling gradient checkpointing failed before any successful update at both 20 GiB and 26 GiB limits. The initial 22 GiB attempt failed admission before launching; a duplicate-stop cleanup bookkeeping error was independently recovered. All probe processes are stopped and production remained healthy. Retain gradient checkpointing; no measured speed improvement from extra activation memory is claimed. [Resource evidence](../training/reports/cpu-training-resource-comparison-20261012.json).

PARTIALLY IMPLEMENTED: V5r6 retains the exact 1,803 prior training rows and all 275 validation rows, adding 166 synthetic English/French examples for date bounds, combined unpaid/customer/product filters, current-page reads and literal field values. Total: 1,969 training rows. All 438 frozen evaluation cases remain unchanged. Two native-routing/target wording issues were corrected before training and reviewed by the single reviewer.

All 69 training-integrity tests pass. Native audit passes all 166 new tool/schema selections and eight Facturation explicit targets; independent review also checked eight Management Projet explicit targets. Metadata preflight passes all 2,244 training/validation rows and 438 evaluation cases, with no local weights or training. [Metadata checks](../training/reports/shared-v5r6-en-fr-metadata-preflight.json), [native audit](../training/reports/shared-v5r6-native-curriculum-audit.json). These are data/preparation checks, not model accuracy. This preparation checkpoint was followed by the verified V5r6 launch recorded at the top of this page.

Management Projet and the next three application assistants remain disabled. No production model replacement; future application training stays sequential after acceptance.

## Named list pagination returns - 2026-10-12

IMPLEMENTED and verified locally in all six application frontends: named list buttons restore validated page, page size and ordering, scoped to the existing company/store target. Fresh list visits and direct links without saved state use the normal named list. No history-based return calls remain in application source. Browser checks caught and fixed a route-commit timing reset for non-default page sizes; pagination now reads Next's canonical query and uses the supported native-history update.

All six related test suites, type checks, scoped lint and optimized production builds pass. The sole reviewer found no remaining issues. Dummy-login browser checks passed named-list returns and reloads across all six, including non-default sizes and sorting where supported; Facturation article company scope and Gestion Magasin catalog store scope passed at page 3 with 25 rows. IMPLEMENTED in production: all six frontend releases are published to company, personal and production; all 36 frontend/backend remote references match. All frontend containers contain the compiled helper and are healthy; all six frontend HTTPS routes and backend health endpoints return 200. Production configuration, 44 supporting containers, database volumes and the training process are unchanged. Facturation also passed an authenticated production page-2/size-5/sort round trip and reload; other authenticated business-flow checks were local. [Release evidence](../training/reports/list-return-release-20261012.json).

Limitations: only pagination and existing ordering are remembered, not in-memory search/filter text. Design Workflow's project board is unpaginated and unchanged. Training remains separate and the current run has no accepted accuracy score.


## Sequential R6 preparation - 2026-10-12

IMPLEMENTED and verified: Contracts V6r6, Gestion Magasin V7r6 and Réservation V8r6 preserve every current V5r6 training/validation byte and the existing new-app splits. Training counts are 2,122, 2,320 and 2,500 respectively; held-out counts stay 516, 606 and 690. Seven focused integrity tests, the full 72-test training suite and 2,902 tokenizer/template/parser/semantic-boundary checks passed. The single reviewer found no remaining issues. Existing identical held-out metadata checks are reused by hash. The preparation adds one versioned generator, integrity tests, three synthetic dataset versions and one metadata report. No model weights or local training were used.

PARTIALLY IMPLEMENTED: the V5r6 server training run remains active. These future stages require acceptance of their exact predecessor, a frozen baseline and launch-time server/resource checks. None has started; no accuracy or production-readiness claim follows from metadata validation.


## Serial-stage capacity preparation - 2026-10-12

IMPLEMENTED and verified without loading weights: `training/scripts/probe_cpu_serial_v1.py` extends the existing two-step CPU capacity procedure to an explicitly selected Contracts, Gestion Magasin or Réservation stage. Before model import it checks both dataset hashes, exact cumulative application scope and byte-for-byte retention of the declared predecessor. It retains the Linux/server-only guard, CPU/memory protections, longest-example probe and per-layer gradient/update checks. The frozen three-application probe remains unchanged. Three startup tests passed, covering all stages, a stale predecessor, a skipped stage and the server-only restriction; the single reviewer found no issues.

PLANNED: execute this unsaved optimizer probe on the server after the preceding stage is accepted and before starting the next full training. The launcher must still bind the accepted predecessor model and perform current resource admission; preparing the probe does not establish capacity, accuracy or authorize another concurrent job.


IMPLEMENTED and verified: the exact server metadata check also passed all 2,902 cumulative training/validation rows, with maximum lengths of 7,662/7,496 tokens inside the 8,192-token context. It used 0.25 CPU core, a 2 GiB limit and 682,393,600 bytes peak memory. The completed temporary check was stopped; the active training PID and healthy production model remained unchanged. [Server metadata evidence](../training/reports/shared-v8r6-en-fr-server-preflight.json). This loaded no model weights and performed no optimization.


## Clarification failure audit - 2026-10-12

IMPLEMENTED and independently reviewed: read-only analysis of the unchanged V5r5 synthetic evaluations identified 27 failed clarifications: six invalid structures, 18 valid but incorrect tool choices and three incorrect clarification reasons. Eight incorrect edit/archive targets were replayed through existing target guards and all rejected. This is a target-guard replay, not a new end-to-end authorization test, and all eight remain failures in model accuracy. Dataset/event hashes match the original 15 evaluation sets. [Audit evidence](../training/reports/shared-v5r5-clarification-audit.json).

KNOWN EVALUATION LIMITATION: one French supplier-summary question omits the supplier noun included in its English counterpart; trusted context does not resolve the entity type. The original prompt, label and failed score remain unchanged. No favorable rescoring is claimed.

PARTIALLY IMPLEMENTED: an isolated local branch removes invoicing-only record/metric assumptions from all six shared English/French clarification messages. The single reviewer found no issues; 30 existing core tests and 12 offline provider parsing checks pass. Integration, package updates and release remain pending until the active pinned evaluations finish. Main-branch provider hashes and production remain unchanged. This is a wording correction, not a model-accuracy improvement.


## R6 validation and fallback preparation - updated 2026-10-13

PARTIALLY IMPLEMENTED: validation macro losses at steps 300/600/900/1200/1500/1800 are respectively 0.0962517421, 0.0851006019, 0.0817649788, 0.0749553844, 0.0854565879 and 0.0702729237. Step 1800 is the first checkpoint below the 0.0709163280 baseline application-macro loss and is now selected. All three application losses improved from step 1500 to step 1800. Management Projet is below its baseline loss; Facturation and Design Workflow remain above theirs. Training is now complete; final-step macro loss is 0.0731497569 and step 1800 remains selected. The selected candidate completed the unchanged frozen acceptance suite and failed acceptance. These losses are not tool-accuracy percentages; the complete R6 acceptance scores are recorded at the top of this page and no production activation occurred. [Latest measured checkpoint report](../training/reports/shared-v5r6-validation-through-1800.json), [preserved step-1500 report](../training/reports/shared-v5r6-validation-through-1500.json).

IMPLEMENTED and verified as preparation only: a separately frozen fallback compares actual validation tool predictions for the baseline, each scheduled checkpoint (300 through 1,800) and final step 1,969. It reconstructs the exact prior 275-row envelope, including its 222 scenario groups, and retains the existing scoring and tie-breaking rules. This can run only after successful complete training and the original candidate remaining unaccepted. All 79 training tests pass, including 12 checkpoint-comparison tests; the single reviewer found no issues. [Frozen policy](../training/reports/shared-v5r6-checkpoint-selection-policy.json).

PARTIALLY IMPLEMENTED: the private server export/evaluation runner is prepared and all ten offline safety tests pass. It binds published baseline provenance, exact validation batches, completed training, candidate artifacts and identical inference settings; it rejects overlapping optimization and insufficient resource reserves. One reviewer found two provenance gaps, both fixed and covered by mutation tests, then found no remaining issues. No server controller execution or fallback inference has started. The active training/evaluation controller and original loss-based selection remain unchanged. Any selected changed model still requires the existing 438-case acceptance suite; validation alone cannot accept it. [Controller checks](../training/reports/shared-v5r6-fallback-control-checks.json).


## Selected-checkpoint acceptance preparation - 2026-10-12

PARTIALLY IMPLEMENTED: the separate functional fallback now has a prepared acceptance handoff for its selected changed checkpoint. It reuses the existing 438-case, 15-set evaluator and baseline comparison, with the same model/provider settings and scoring. All eight predetermined validation candidates must finish; the selection is recomputed from their complete frozen predictions before admission. The baseline cannot advance as a new candidate. No activation or subsequent training is performed by this runner.

Eleven offline handoff tests pass, including altered selection/events, incomplete comparison, baseline selection, changed-candidate rejection and invalid performance evidence. The runner now also prepares the unchanged eight-request speed/memory probe on the same isolated candidate workers before stopping them. One reviewer found no issues; read-only server checks confirmed the pinned benchmark inputs. No candidate launch or inference has run; actual acceptance, performance and native security remain incomplete. The active R6 controller is unchanged. [Preparation evidence](../training/reports/shared-v5r6-selected-acceptance-controls.json).


## Serial-stage acceptance reporting preparation - 2026-10-12

IMPLEMENTED and verified as preparation only: `report_serial_candidate_v1.py` recomputes the full baseline and candidate assessments for the prepared Contracts (516 cases), Gestion Magasin (606) and Réservation (690) stages. It requires all frozen sets and retained applications, verifies artifact file-map hashes and completion-pinned result hashes, and keeps the existing accuracy gates. A decline in a retained application's tool, structure, action or exact-argument count blocks stage acceptance even if aggregate targets pass.

Eleven focused offline tests and all 90 training-integrity tests pass. The single reviewer found two provenance gaps; both were fixed and regression-tested, with no remaining findings. No future-stage inference or training has run. Launch-time accepted-predecessor bindings, actual measurements, native security and application verification remain incomplete. Current R6 controls and frozen evaluations are unchanged. [Preparation evidence](../training/reports/serial-stage-report-controls.json).


## Completed training and recovery handoff - 2026-10-13

IMPLEMENTED: all 1,969 optimization steps and final validation completed successfully; step 1800 remains selected. Export succeeded. The initial evaluation handoff stopped before submitting cases because systemd reports an absolute interpreter path. A separately reviewed recovery requires the exact absolute interpreter and executable realpath, retaining every model/argument/artifact check. Eleven offline checks pass; the original controls and failure evidence are preserved. The recovery completed all 438 unchanged cases and the eight-request performance probe. Acceptance failed; all three temporary workers stopped and production remained unchanged.

PARTIALLY IMPLEMENTED: versioned fallback controls can admit that recovery only after complete recomputed results show failed acceptance and all three isolated workers stop. The fixed eight-checkpoint validation policy and all scoring remain unchanged. Fifteen offline fallback tests and eleven selected-checkpoint acceptance/performance handoff tests pass; the single reviewer found no remaining issues. Neither fallback inference nor later-app training has started. [Fallback controls](../training/reports/shared-v5r6-fallback-control-checks-v2.json), [selected-checkpoint handoff](../training/reports/shared-v5r6-selected-acceptance-controls-v2.json).


## Versioned benchmark errata preparation - 2026-10-13

IMPLEMENTED and verified as preparation only: `shared-dialogue-v2-en-fr` retains all 438 scenarios and 15 sets. It corrects only the three previously documented defects: the two payment-schedule requests saying “before 2026-11-01” now expect the inclusive upper bound 2026-10-31, and the French supplier-expense question explicitly identifies the supplier, matching its English counterpart. The other 435 rows remain byte-identical. V1 inputs, historical scores, active checkpoint comparison, training data and acceptance thresholds are unchanged.

Eight generator tests pass. Fresh metadata checks pass all 438 V2 cases against the existing tokenizer, chat template and Colibri parser. The largest prompt is 7,235 tokens, with 512 output tokens reserved within 8,192. The single reviewer found no issues. No V2 model inference, training or acceptance has occurred. V2 requires separately bound baseline/candidate results, reported alongside V1; preparation cannot qualify a model or activate an application. [Dataset manifest](../training/datasets/shared-dialogue-v2-en-fr/manifest.json), [metadata checks](../training/reports/shared-dialogue-v2-en-fr-metadata-preflight.json).


## Token-ID parity diagnostic - 2026-10-13

IMPLEMENTED and verified: a tokenizer-only harness compiled the unchanged Colibri C encoder, with its default settings, and compared its token IDs with the training tokenizer. The four encoder source files and tokenizer metadata match the server; its recorded inference binary hash was also rechecked. All 4,926 corpus comparisons passed: 3,938 prompt/full-example encodings from 1,969 training rows, 550 from 275 validation rows, and 438 V2 evaluation prompts. These are encoding checks, not additional model-accuracy cases. No weights or local inference were loaded. The single reviewer found no issues. [Evidence](../training/reports/shared-v5r6-tokenizer-id-parity.json).

PARTIALLY IMPLEMENTED - Unicode edge case remains: five of six separate probes passed; a decomposed accented name differed because the default C path does not apply the tokenizer's NFC normalization. This did not affect the checked corpus and does not explain the observed validation failures. No runtime/provider change has been applied. Any correction must be separately tested without altering the active comparison. Numerical inference parity was not tested.


## Saved-result training contrasts - 2026-10-13

IMPLEMENTED and verified as preparation only: `selection-contrasts-v1-en-fr` contains 96 correlated variations of 36 existing Management Projet synthetic training requests. The variants preserve the user request and field values while changing the saved context: 36 use new valid identifiers, 36 have no saved selection, and 24 have fewer results than the requested position. Missing or out-of-range targets require clarification. The existing 1,969 training rows, 275 validation rows and frozen evaluations remain unchanged. This additional data has not been merged into a training run or used for optimization.

Six unit tests pass. The actual native target guard passed 244 synthetic request-binding checks; all 96 examples passed tokenizer, template, parser and loss-boundary validation, and all 192 prompt/full-example encodings matched the unchanged C tokenizer. Maximum prompt length is 3,250 tokens, with 512 output tokens reserved. The single reviewer found no issues and confirmed zero request overlap with validation and both frozen benchmark versions. These checks establish preparation correctness, not improved model accuracy. [Preparation evidence](../training/reports/selection-contrasts-v1-en-fr-preflight.json).

A separate audit of the original expected Management Projet edit/delete targets passed all 182 cases: 130 training, 12 validation and 40 V2 evaluation cases. This verifies request-to-record binding with synthetic context; it neither queries records nor certifies database permissions. [Expected-label audit](../training/reports/management-projet-target-label-audit.json).

## Future validation wording corrections - 2026-10-13

IMPLEMENTED and verified as preparation only: `shared-validation-v2-en-fr` keeps the same 275 rows, tools, trusted contexts and expected actions. It clarifies 39 distinct requests (47 rows including history variants); the remaining 228 rows are byte-identical. The single review of all 222 original scenarios identified two native-filter scope mismatches and several ambiguous or uncertain entity references.

The article cases now explicitly request article records using the native reference-or-designation search, rather than implying designation-only search or an unlabelled product-only filter. Budget-entry questions name the native stage/description/notes search scope. Other edits identify projects, suppliers, assignment, monetary amount or substring matching. Uncertain wording is distinguished from a confirmed incorrect assumption.

Six integrity tests pass, including unchanged targets/history and exclusion of the changed requests from training and both held-out versions. All 275 schema/template/parser/loss-boundary checks and 550 C-versus-training token sequences pass; the largest prompt is 7,468 tokens plus 512 reserved output tokens, within 8,192.

PARTIALLY IMPLEMENTED: no V2 inference or checkpoint selection has run. Clearer questions change difficulty, so future V2 scores must be reported separately. The active eight-checkpoint comparison, historical results, training data and held-out acceptance inputs remain unchanged. This preparation does not improve or certify model accuracy. [Prepared validation](../training/datasets/shared-validation-v2-en-fr/manifest.json), [metadata evidence](../training/reports/shared-validation-v2-en-fr-preflight.json).

## Training search-scope corrections - 2026-10-13

IMPLEMENTED and verified as preparation only: `training-scope-errata-v1-en-fr` supplies twelve replacement rows for the existing 1,969-row training split. Review of all 28 Facturation article-search and 46 Management Projet budget-entry-search examples found four designation-only questions labelled with the broader reference-or-designation search, and eight stage-only questions labelled with the broader stage/description/notes search.

The replacements explicitly request those supported multi-field searches. Targets, other filters, history, tools and trusted context are unchanged. A future dataset must replace the exact indexed source rows, preserving 1,957 other rows; appending conflicting alternatives is not allowed. The original dataset and completed training remain unchanged.

Four integrity tests, twelve schema/template/parser/loss-boundary checks and 24 C token-ID comparisons pass. The largest replacement prompt is 2,460 tokens. Changed requests do not overlap either validation version or either held-out version.

PARTIALLY IMPLEMENTED: these replacements are not yet assembled into a cumulative training dataset or used for optimization. No accuracy improvement is claimed. [Replacement manifest](../training/datasets/training-scope-errata-v1-en-fr/manifest.json), [metadata checks](../training/reports/training-scope-errata-v1-en-fr-preflight.json).
