# Pre-training correctness checks

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



## Shared rehearsal complete; corrected Colibri replay pending - 15 October 2026

IMPLEMENTED and verified: all 63 numerical updates completed, all 24 intended layers received finite gradients and actual updates, the saved adapter matches the live model and frozen base parameters remain unchanged. Independent action checks and the single reviewer confirm training captures improved from 16/20 to 20/20; development captures stayed 5/6, with no correct-to-incorrect changes. This demonstrates learning on the rehearsed examples, not acceptance or development improvement.

PARTIALLY IMPLEMENTED: merge and Colibri conversion completed, but the first replay was invalid for prompt parity. Its client alphabetically reordered tool-schema keys during JSON serialization, changing all 26 prompts. Reproducing that ordering explains all 26 server-reported token counts. Original evidence is preserved and the temporary worker stopped.

IMPLEMENTED and tested: request bytes, hashes and saved artifacts now preserve nested schema order. The 82 affected tests pass, including three regressions that failed before the fix and coverage of nested properties and both supervisors. Tokenizer-only checks preserve all 26 original prompt strings and token counts. The single reviewer found no remaining issue. Prompt/token validation and exact-action scoring were not weakened.

Corrected Colibri replay, six R11 wording checks, full refinement and acceptance remain incomplete. The disposable adapter must not seed full training. Production is unchanged. [Rehearsal diagnosis and fix](../training/reports/shared-v5r10-rehearsal-diagnostics.json).

## Earlier results and preparations


## Current refinement rehearsal preparation - 2026-10-15

The R8 pipeline has finished and failed its regression and fresh gates. Shared V5r10 is prepared with 2,419 training and 275 unchanged validation examples. It retains the six reviewed name-label corrections and appends the 80 coverage contrasts without modifying either acceptance set.

Use the versioned category-aware audit and runner, audit_training_inputs_v2.py and rehearse_cpu_v3.py, for this refinement rehearsal. The default selection remains compatible with V2. Explicitly selecting the eight added categories gives 63 training updates, 20 training captures and six development captures before and after updates. Selection is deterministic and outcome-independent. Each added category has an English and French capture. All original 48 mechanics rows remain selected.

Numerical rehearsal, serialized-adapter export and actual Colibri replay remain pending. This preparation does not predict 95% accuracy. The rehearsal adapter must be discarded for any full run; start the full run from its original pinned base. The old Contracts replay supervisor remains conditional on actual predecessor acceptance and cannot be used to bypass that gate.

[Prepared counts, selected rows, source identities and metadata results](../training/reports/shared-v5r10-rehearsal-preparation.json).

## Earlier preparation records

## Reviewed coverage supplement - 2026-10-15

IMPLEMENTED as preparation only: 80 synthetic English/French examples address reviewed development coverage gaps: 68 Facturation, four Management Projet and eight Design Workflow. They cover custom-period currency summaries, natural product/location filters, inclusive date bounds, unpaid balances, literal remarks, unchosen results, dated receipts and resource-specific completion statuses. All 80 pass actual native metadata checks with database access forbidden, tokenizer/Colibri template/parser round trips, semantic loss boundaries and output budgets. Seven focused tests pass. Maximum complete example length is 4,775 tokens; maximum expected output is 103 tokens within the 512-token limit.

The single reviewer found no new incorrect targets and no copied frozen requests. The missing helper provenance inventory was corrected; a fresh native generation produced identical training bytes. The supplement remains separate: no cumulative continuation is assembled, no new numerical rehearsal or training has run, and no accuracy improvement is claimed. R8 evaluations, scoring and production are unchanged. [Supplement](../training/datasets/coverage-contrasts-v1-en-fr/manifest.json), [checks](../training/reports/coverage-contrasts-v1-preflight.json).

IMPLEMENTED and verified as preparation: corrected cumulative datasets cover Contracts V6r10 (2,492 training / 319 validation), Gestion Magasin V7r10 (2,690 / 362) and Reservation V8r11 (2,870 / 402). Exactly six retained target labels change from each prior preparation; all other rows, application additions, validation and evaluation inputs remain unchanged. All 269 training-integrity tests pass, including 24 Contracts mutation/startup checks and nine final-stage tests. The latter reject skipped predecessors and altered retained rows before model import. A separate subprocess test verifies the isolated scripts/data/control layout. The single reviewer found no remaining issues.

Final metadata checks pass all 3,272 training/validation examples and 738 evaluation cases, including the exact retained Contracts and Gestion Magasin prefixes. Full static audits select 59, 72 and 84 training-only rehearsal rows respectively. These checks do not establish semantic independence, numerical learning, export parity or model accuracy. No later-stage model has been trained or accepted. [Contracts metadata](../training/reports/shared-v6r10-en-fr-metadata-preflight.json), [Contracts audit and artifact inventory](../training/reports/shared-v6r10-en-fr-pretraining-audit.json), [final cumulative metadata](../training/reports/shared-v8r11-en-fr-metadata-preflight.json), [later-stage audits](../training/reports/later-name-corrections-preflight-20261014.json).

IMPLEMENTED and verified as preparation: a review of all 180 Reservation training rows found four requests with misleading date wording. They now explicitly refer to reservation arrival dates or rental years and current returned/paid status. All action labels, histories, validation and held-out bytes remain unchanged. All 216 training integrity tests pass; final metadata checks pass 3,272 training/validation rows and 738 evaluation cases. The corrected final-stage preparation is shared-v8r10-en-fr, retaining the complete shared-v7r9-en-fr prefix. Native date filters and financial calculation sources are pinned. [Correction evidence](../training/reports/reservation-temporal-corrections-20261014.json).

PARTIALLY IMPLEMENTED: the server-only exact replay collector is implemented and synthetic transport tests pass. It preserves issued payloads, bounded raw response bytes, parsed events and failures; rejects truncated or malformed streams; and never authorizes training. Real numerical rehearsal, export and live-worker replay remain pending until the active R8 controller completes. [Collector evidence](../training/reports/cpu-rehearsal-collector-preparation-20261014.json). Those earlier preparations remain preserved; corrected successors and accepted model bindings are required. No later-stage optimizer has started.

IMPLEMENTED and verified as preparation: the single semantic review found one confirmed financial-definition mismatch in Gestion Magasin and four ambiguous Contracts requests. The corrected native wording states that the metric sums paid amounts on confirmed sales created today and currently marked paid, across payment modes; it does not filter payment dates. Four Contracts requests now explicitly identify the customer. Versioned source datasets retain all targets, contexts, histories and split order, including the affected French history duplicate.

All 193 training tests and 58 PostgreSQL assistant tests plus 6 subtests pass. The native six-sale fixture covers creation date, current payment status, store isolation and payment modes. Metadata checks pass all 3,272 cumulative training/validation rows and 738 evaluation cases without weights or inference. One historical-input hash check found by review was fixed and mutation-tested. [Correction evidence](../training/reports/native-semantic-corrections-20261014.json), [metadata evidence](../training/reports/shared-v8r9-en-fr-metadata-preflight.json).

Earlier preparation: Contracts V6r9, Gestion Magasin V7r9 and Reservation V8r10 preserved the then-current retained curriculum. These names identify future dataset revisions, not a new running training job. The active R8 run and all original inputs/results remain unchanged. Do not start the superseded V6r8/V7r8/V8r8 or Reservation V8r9 preparations. Fresh accepted-predecessor bindings, native-source verification, numerical rehearsal and real Colibri export comparison remain required before the next full run. All 90 GM evaluation envelopes have refreshed native metadata, including two revised questions, so they require fresh baseline/candidate predictions. Historical scores must not be relabelled as measurements on the corrected inputs.

Earlier preparation: exact rehearsal replay helpers were prepared and reviewed. All 187 training integrity tests pass, including 15 new comparison tests. The helpers bind the exact sent payload, preserve structured clarification arguments and failed responses, validate token usage and compare actions without normalizing defaults. At that preparation stage, numerical rehearsal, real export, network collection and live worker attestation were pending. The collector implementation is now prepared; execution remains pending. Current R8 training and its frozen controller are unchanged. [Comparison preparation](../training/reports/cpu-rehearsal-comparison-preparation-20261014.json).

PARTIALLY IMPLEMENTED: the static audit and server rehearsal runner are prepared. All 172 training integrity tests pass, including 13 rehearsal contract tests with synthetic fixtures. Metadata preparation passes the current R8 curriculum and all three queued stages. The numerical rehearsal has not run; adapter export and Colibri comparison have not run. [Preparation evidence](../training/reports/cpu-rehearsal-preparation-20261014.json).

The purpose is to detect mistakes before another full training run. This does not predict 95% accuracy or replace per-application acceptance testing.

## Before launching

The completed [source review](../training/reports/target-label-review-20261014.json) traced all 2,339 current training targets in bounded groups and led to three tested native fixes. This coverage does not prove model behavior; use it alongside the numerical and export checks below.

The semantic review found six incorrect retained Management Projet name-search labels. Their corrections are versioned in management-name-errata-v2-en-fr and assembled into shared-v5r9-en-fr. That three-app preparation changes exactly those six targets; every other training row and every validation/evaluation input remain unchanged. Its 236 integrity tests, static audit and exact metadata checks pass. It is untrained and has no model binding. The current R8 and queued V6r9/V7r9/V8r10 files remain immutable historical preparations and fail the known-label check.

Do not require a new epoch solely to make dataset names align. The reviewed serial_scope_v3.py implements only the pinned six-target R8-to-Contracts correction; serial_scope_v2.py remains unchanged. The new train_cpu_serial_v4.py, probe_cpu_serial_v2.py and rehearse_cpu_v2.py apply the same check before model import. All other retained-byte changes reject, and later stages require exact corrected predecessors without the exception. This validates dataset lineage only. The launcher must still bind the actual accepted R8 model and completed run, frozen baseline and current resources. If R8 fails, evaluate whether a corrected three-app refinement is justified; neither preparation authorizes training.

~~~sh
python -B training/scripts/prepare_management_name_errata_v2.py --check-data "$REHEARSAL_DATA"
~~~

This mandatory operator check rejects the known broad-search labels, incorrect replacement fields and append-only corrections. It covers six reviewed requests, not arbitrary semantic errors. Run the complete static audit, native semantic review and numerical/export rehearsal as separate checks. Passing this command alone never authorizes training. No later-stage automatic launcher is enabled.

The operator must verify that the preceding controller has completed training, checkpoint comparison and acceptance evaluation. Idle services between controller phases are insufficient. Bind the selected base model, exact dataset, retained curriculum, trainer source and full-run configuration before starting. A later application also requires its predecessor to pass the existing acceptance gates.

Only one training, rehearsal, export or evaluation workload runs at a time. The runner rejects active competing training processes and relevant running, starting or stopping services. Production inference is allowed to remain running. The existing server launcher must retain the resource budget and at least 10% available system memory; no additional model is downloaded.

Run the static audit first:

~~~sh
python -B training/scripts/audit_training_inputs.py --data "$REHEARSAL_DATA" --output "$REHEARSAL_AUDIT"
~~~

This validates full dataset hashes, declared application scope, trusted-context labels, explicit English/French metadata, tool schemas, exact conflicting labels, exact split overlap and schedule coverage. Exact comparisons do not prove semantic independence or every business label.

## Server rehearsal

The rehearse_cpu_v2.py runner validates the full cumulative curriculum and predecessor before selecting optimization rows. It extracts only five named functions from the hash-pinned trainer, without running that file's top-level CLI. Its encoding and loss functions match the shared and serial trainers. The trainer's adjacent semantic-loss, LoRA, retention and correction helpers must match the rehearsal helpers before use, plan creation and completion.

The metadata preparations select the rows below. All corrected curricula listed below pass the known-label check. Every stage still needs its actual accepted predecessor model and completed run bindings before execution. These counts are preparation evidence, not launch approval:

| Curriculum | Optimization rows | Trained-row captures | Development-validation captures |
| --- | ---: | ---: | ---: |
| Shared V5r9 | 48 | 6 | 6 |
| Contracts V6r10 | 59 | 8 | 8 |
| Gestion Magasin V7r10 | 72 | 10 | 10 |
| Reservation V8r11 | 84 | 12 | 12 |

Captures are selected before inference, without outcome-based selection. Every trained-row capture belongs to the selected optimization rows. Only training rows receive updates. No acceptance case is used for optimization or checkpoint selection.

The following illustrates the conditional Contracts V6r10 rehearsal inside the approved server execution environment. The model, runtime, output and reviewed source checksum are operator bindings. REHEARSAL_RETAINED_DATA must contain the actual accepted R8 run's original dataset. If that predecessor is not accepted, do not use this example.

REHEARSAL_CORRECTION_ROOT is explicit, independent of the script directory. Stage exactly the 36 relative files and hashes listed under correction_artifacts in the [audit](../training/reports/shared-v6r10-en-fr-pretraining-audit.json): corrected V5r9 manifest/train/valid, the V2 errata manifest/replacements, and frozen evaluation files. Evaluation files are integrity-checked only and never passed to the optimizer. There is no repository-path fallback. Include the trainer's validation_selection.py dependency as well as all rehearsal, retention and correction helpers when staging isolated scripts. The isolated startup test verifies this layout without weights. Omit --correction-root for future strict-retention stages with no correction declaration.

~~~sh
CHAT_AI_TRAINING_SERVER=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B training/scripts/rehearse_cpu_v2.py \
  --stage contrat \
  --data "$REHEARSAL_DATA" \
  --retained-data "$REHEARSAL_RETAINED_DATA" \
  --correction-root "$REHEARSAL_CORRECTION_ROOT" \
  --model "$REHEARSAL_BASE_MODEL" \
  --runtime "$REHEARSAL_RUNTIME" \
  --trainer training/scripts/train_cpu_serial_v4.py \
  --trainer-sha256 "$REHEARSAL_TRAINER_SHA256" \
  --output "$REHEARSAL_OUTPUT" \
  --threads 14 --max-seq-length 8192 \
  --learning-rate 0.00001 --semantic-loss-weight 4 \
  --lora-layers 24 --lora-rank 16 --lora-alpha 32
~~~

These explicit settings match the current reviewed training configuration. The next run must use its own reviewed full-training settings. Rehearsals retain seed 17, BF16, SDPA, nonreentrant gradient checkpointing, batch size one, AdamW with zero weight decay and gradient clipping at one. Installed library versions and actual optimizer defaults are recorded.

The runner checks finite losses, gradients, parameters and optimizer state. All intended layers must participate and must receive nonzero gradients and actual adapter updates over the selected examples. It also verifies that frozen base parameters remain unchanged.

Before/after captures preserve independently rendered prompts through hashes, raw generated token IDs, unfiltered replies, filtered serving replies, matched text stops, parsed actions, schema validity, termination state and errors. After native terminal EOS removal, the runner applies the pinned Qwen chat StopFilter before the native thinking splitter, tool parser and schema validation. The role boundaries im_end and im_start stop parsing even when leading; a tool call after a boundary is not credited. Complete calls before the boundary remain valid without requiring final EOS. Training and validation results remain separate.

Captures and plans carry the qwen36-stop-filter-v1 contract. Replay loading rejects older unfiltered evidence. Raw HF generation can continue beyond a textual stop, so its token count is diagnostic and must not be presented as served-token parity. The no-thinking splitter preserves the pinned runtime behavior rather than assuming unexpected opening think markers create a new reasoning block.

All four corrected preparations were rechecked with this runner: dataset hashes and selected rehearsal rows are unchanged. Earlier metadata/static reports remain historical evidence. The [stop-handling report](../training/reports/rehearsal-stop-preflight-20261014.json) supersedes their rehearsal-source identity and records the current parser and test hashes. No numerical rehearsal or live export comparison is claimed.

The disposable adapter is fingerprinted, and its saved tensors must equal the live adapter used for the final captures. Completion binds the plan, captures and metrics by hash. These records belong in ignored private evaluation output, not a public source commit.

## Export comparison and full training

Numerical completion is explicitly reported as EXPORT COMPARISON PENDING. It does not authorize the next full run.

1. Confirm the rehearsal process exited successfully and its evidence and adapter hashes still match.
2. Use the real export_adapter.py FP32-base merge, followed by the same pinned Colibri conversion and serving settings intended for the full candidate.
3. Run exactly the frozen capture prompts through the exported candidate. Preserve raw outputs, parsed actions, tokenizer/runtime hashes and termination details. Do not substitute acceptance cases.
4. Investigate discrepancies and failed critical targets before the full run. BF16 training, FP32 merging and serving quantization differ, so a changed output alone does not prove serialization corruption.
5. Discard rehearsal optimizer/model state. Start full training from the original selected base, using the full validated curriculum. Do not resume from the disposable adapter.
6. Evaluate the resulting candidate against unchanged per-application acceptance gates. Production activation remains separate.

The active R8 trainer, controller, frozen inputs and production model are unchanged by this preparation.

## Exact replay helpers

The `rehearsal_comparison.py` module supplies evidence loading, exact request construction, streamed-event parsing and paired diagnostics. Its 15 synthetic tests pass; no actual model replay has run. It does not start services, export weights, make network requests, attest a live worker or authorize full training.

Do not use the standard evaluator summary for this comparison. It normalizes optional default arguments and converts clarification arguments into display text. Calling the provider's `choose()` with a complete rehearsal tool inventory also appends a second clarification definition. The replay payload must use the original messages and tools directly.

The bound server controller must:

1. Call `load_captures(rehearsal, data)` to check the completed rehearsal, all capture evidence, complete adapter inventory and exact dataset hashes.
2. Verify the pinned base, tokenizer and runtime identities. Call `replay_requests(evidence, renderer, tokenizer, model_id)` with those same template/tokenizer implementations. This verifies each prompt hash and token count and derives its output budget as the lesser of 512 and the available 8192-token context.
3. Preserve the issued requests before inference. Send each payload directly to the isolated worker's streaming chat endpoint, without rebuilding schemas or calling `choose()`. The existing exporter and worker verification patterns can be reused; their historical full-run entry points cannot.
4. Preserve every raw streamed JSON object, transport failure class, terminal finish reason, usage and whether the DONE marker arrived. For each response, record the split, row index, input hash and prompt hash in `identity`, plus `request_sha256` computed from the exact payload actually sent. Use the module's canonical JSON encoding for that digest. Keep this evidence in ignored private evaluation output.
5. Call `compare_pairs(requests, responses)`. Changed or missing requests fail admission. Malformed responses, invalid tool calls, mismatched prompt usage and exceeded output budgets remain failures. A clean EOF after a valid terminal finish reason matches the native provider's behavior; an absent DONE marker alone is not a model failure.
6. Recheck the exported model, runtime, worker executable, command, environment and process identity after replay, then stop the isolated worker. These checks belong to the server controller and remain required regardless of the helper result.

The report separates training captures from development captures. It records exact valid-action agreement and correct-to-incorrect changes. Two failed calls never count as agreement. Type distinctions and explicit default arguments are preserved for diagnosis, so semantic equivalence must be investigated before treating a difference as an export defect. Streamed tool-call objects do not establish generated-token parity.

All helper reports leave model acceptance and full-training authorization false. The numerical rehearsal and real export/controller execution are still pending until the current R8 controller has fully completed.

## Server replay collection

After numerical execution, real export and isolated worker attestation, the bound server controller can call:

~~~python
from collect_rehearsal import collect_replay

report = collect_replay(requests, worker_chat_endpoint, private_replay_output, timeout=90)
~~~

The endpoint must be an explicit loopback HTTP address with port and a supported chat-completions path. The collector requires the Linux training environment. It makes one sequential request at a time without redirects, proxies or retries. Requests are persisted before I/O; each response retains the exact request hash, bounded raw body bytes, parsed events, HTTP status, usage/termination evidence and safe transport failure codes. It drains the framed response after DONE so acceptance does not depend on network chunk boundaries, and rejects premature Content-Length EOF. A failed transport stops the batch with an incomplete report.

Keep output in ignored private evaluation storage. Collecting every response does not mean every action passed. The comparison remains diagnostic and keeps both model acceptance and full-training authorization false. The caller must still verify the export/runtime/worker before and after, investigate critical discrepancies, stop the worker and discard rehearsal state. This collector has only run against synthetic transport fixtures; no live replay is claimed.

## Pinned Qwen tokenizer warning

The generic Mistral-regex warning was traced to the local loader treating a config without transformers_version as Mistral-related. The actual model_type is qwen3_5_text. Its saved regex matches the installed Qwen3.5 implementation; default loading preserves the saved pre-tokenizer. Eight synthetic English/French samples have identical token IDs through the raw tokenizer, default loader and explicit no-patch loader. Keep the pinned Qwen tokenizer unchanged; do not apply the unrelated Mistral patch. This diagnosis does not measure model accuracy. [Metadata evidence](../training/reports/qwen-tokenizer-warning-check-20261014.json).

## Completed-rehearsal export supervisor

The server-only replay_rehearsal.py supervisor connects the existing FP32 adapter merger, Colibri converter, artifact checks and exact replay collector. Its current predecessor contract is deliberately limited to Contracts after accepted R8. It does not launch numerical training, select a model, activate production or grant full-training authorization. [Preparation evidence](../training/reports/rehearsal-supervisor-preparation-20261014.json).

Prepare its private binding only after the R8 controller has finished and passed both frozen regression sets and per-application fresh controls, and after the separate numerical rehearsal has exited successfully. The binding contains:

- Canonical absolute paths for rehearsal, data, selected FP32 base, runtime, trainer, exporter, converter, server Python and a fresh output directory, plus an isolated port and model identifier.
- SHA256 identities for the supervisor, its declared HELPER_NAMES, trainer, exporter and converter. Standard-library checks run before any local helper import.
- Independent hashes of complete.json and the reviewed dataset manifest. The numerical service name, exact completed properties, InvocationID and argv must identify that same runner, input and output.
- Predecessor proof paths and hashes for pipeline-state.json, selection.json, acceptance.json, fresh.json, validation-0-collect.json, and the selected validation/acceptance/fresh before, after and stop records. Include the selected FP32 artifact fingerprint and the original accepted retained dataset.

Operator paths and raw evidence stay in ignored private evaluation storage. A self-consistent replacement of numerical evidence cannot bypass its external completion hash. An unrelated successful service cannot stand in for the numerical run. The original accepted R8 curriculum remains the retained identity even when the six reviewed target corrections apply.

Run the supervisor inside a dedicated chat-ai rehearsal/export/eval service with CPUQuota 1400%, MemoryMax 16G, MemorySwapMax 0 and KillMode control-group. The output parent must exist with at least 12 GiB free storage; reserve 16 GiB for export while keeping 10% of host memory free. Only one training, export or evaluation workload may run at a time. The supervisor uses ten export threads and the pinned four-thread Colibri serving profile for a comparable replay.

~~~sh
CHAT_AI_TRAINING_SERVER=1 python -B training/scripts/replay_rehearsal.py \
  --binding "$REPLAY_BINDING" \
  --binding-sha256 "$REPLAY_BINDING_SHA256"
~~~

Fresh child environments exclude inherited termination, model, proxy and loader overrides. Export and conversion finish before the worker starts. Requests use the original frozen capture payloads. Before/after checks cover base, runtime, tokenizer, exported artifacts, worker executable, command, environment, process creation identity, loopback listener and advertised model. The supervisor stops only its owned session even if readiness, collection or verification fails. Two small Linux checks verified cleanup after an exited parent and a simulated readiness failure, without loading a model or altering a service.

A complete transport replay can still contain incorrect actions. Its completion status therefore requires action review and keeps model acceptance and full-training authorization false. Training continues from the approved original base, never from the disposable rehearsal adapter. Real numerical execution, export and model replay are still pending; this preparation does not supply an accuracy score.


## Expected reply budget

IMPLEMENTED: preflight now rejects an expected assistant reply that exceeds the serving budget before numerical rehearsal or training. Contract conservative-target-v1 uses the lesser of 512 output tokens and the remaining 8192-token context. It conservatively counts the complete supervised suffix, including EOS, trailing template tokens and any prompt-boundary overlap.

All 4,010 prepared six-application examples pass the real pinned tokenizer and Colibri parser checks: 2,870 training, 402 validation and 738 evaluation examples. Maximum expected reply lengths are 131, 116 and 134 tokens respectively. Two long training prompts reduce the available output budget below 512, to a minimum of 488; their expected replies still fit.

All 308 training integrity tests pass, including six new tests for output overflow, exact limits, terminal formatting, prompt-boundary overlap, reduced context and invalid budgets. One reviewer found no issues. This is a preparation safeguard, not a model accuracy result. Historical inputs and scores remain unchanged. New runs must bind the updated preflight source hash; numerical rehearsal and model acceptance remain separate requirements. [Verification results](../training/reports/pretraining-output-budget-20261015.json).
