# Pre-training correctness checks

IMPLEMENTED and verified as preparation: the single semantic review found one confirmed financial-definition mismatch in Gestion Magasin and four ambiguous Contracts requests. The corrected native wording states that the metric sums paid amounts on confirmed sales created today and currently marked paid, across payment modes; it does not filter payment dates. Four Contracts requests now explicitly identify the customer. Versioned source datasets retain all targets, contexts, histories and split order, including the affected French history duplicate.

All 193 training tests and 58 PostgreSQL assistant tests plus 6 subtests pass. The native six-sale fixture covers creation date, current payment status, store isolation and payment modes. Metadata checks pass all 3,272 cumulative training/validation rows and 738 evaluation cases without weights or inference. One historical-input hash check found by review was fixed and mutation-tested. [Correction evidence](../training/reports/native-semantic-corrections-20261014.json), [metadata evidence](../training/reports/shared-v8r9-en-fr-metadata-preflight.json).

PARTIALLY IMPLEMENTED: queued preparations now use Contracts V6r9, Gestion Magasin V7r9 and Reservation V8r9. These names identify future dataset revisions, not a new running training job. The active R8 run and all original inputs/results remain unchanged. Do not start the superseded V6r8/V7r8/V8r8 preparations. Fresh accepted-predecessor bindings, native-source verification, numerical rehearsal and real Colibri export comparison remain required before the next full run. All 90 GM evaluation envelopes have refreshed native metadata, including two revised questions, so they require fresh baseline/candidate predictions. Historical scores must not be relabelled as measurements on the corrected inputs.

PARTIALLY IMPLEMENTED: exact rehearsal replay helpers are prepared and reviewed. All 187 training integrity tests pass, including 15 new comparison tests. The helpers bind the exact sent payload, preserve structured clarification arguments and failed responses, validate token usage and compare actions without normalizing defaults. The numerical rehearsal, real export, network collection and live worker attestation remain pending. Current R8 training and its frozen controller are unchanged. [Comparison preparation](../training/reports/cpu-rehearsal-comparison-preparation-20261014.json).

PARTIALLY IMPLEMENTED: the static audit and server rehearsal runner are prepared. All 172 training integrity tests pass, including 13 rehearsal contract tests with synthetic fixtures. Metadata preparation passes the current R8 curriculum and all three queued stages. The numerical rehearsal has not run; adapter export and Colibri comparison have not run. [Preparation evidence](../training/reports/cpu-rehearsal-preparation-20261014.json).

The purpose is to detect mistakes before another full training run. This does not predict 95% accuracy or replace per-application acceptance testing.

## Before launching

The operator must verify that the preceding controller has completed training, checkpoint comparison and acceptance evaluation. Idle services between controller phases are insufficient. Bind the selected base model, exact dataset, retained curriculum, trainer source and full-run configuration before starting. A later application also requires its predecessor to pass the existing acceptance gates.

Only one training, rehearsal, export or evaluation workload runs at a time. The runner rejects active competing training processes and relevant running, starting or stopping services. Production inference is allowed to remain running. The existing server launcher must retain the resource budget and at least 10% available system memory; no additional model is downloaded.

Run the static audit first:

~~~sh
python -B training/scripts/audit_training_inputs.py --data "$REHEARSAL_DATA" --output "$REHEARSAL_AUDIT"
~~~

This validates full dataset hashes, declared application scope, trusted-context labels, explicit English/French metadata, tool schemas, exact conflicting labels, exact split overlap and schedule coverage. Exact comparisons do not prove semantic independence or every business label.

## Server rehearsal

The rehearse_cpu.py runner validates the full cumulative curriculum and predecessor before selecting optimization rows. It extracts only five named functions from the hash-pinned trainer, without running that file's top-level CLI. Its encoding and loss functions match the shared and serial trainers. The trainer's adjacent semantic-loss and LoRA helpers must match the rehearsal helpers before use, plan creation and completion.

The current metadata preparations select:

| Curriculum | Optimization rows | Trained-row captures | Development-validation captures |
| --- | ---: | ---: | ---: |
| Shared R8 | 48 | 6 | 6 |
| Contracts V6r8 | 59 | 8 | 8 |
| Gestion Magasin V7r8 | 72 | 10 | 10 |
| Reservation V8r8 | 84 | 12 | 12 |

Captures are selected before inference, without outcome-based selection. Every trained-row capture belongs to the selected optimization rows. Only training rows receive updates. No acceptance case is used for optimization or checkpoint selection.

The following illustrates the Contracts rehearsal inside the approved server execution environment. The model, runtime, output and reviewed source checksum are operator bindings. The dataset must be refreshed if the accepted predecessor curriculum changes.

~~~sh
CHAT_AI_TRAINING_SERVER=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B training/scripts/rehearse_cpu.py \
  --stage contrat \
  --data training/datasets/shared-v6r8-en-fr \
  --retained-data training/datasets/shared-v5r8-en-fr \
  --model "$REHEARSAL_BASE_MODEL" \
  --runtime "$REHEARSAL_RUNTIME" \
  --trainer training/scripts/train_cpu_serial_v3.py \
  --trainer-sha256 "$REHEARSAL_TRAINER_SHA256" \
  --output "$REHEARSAL_OUTPUT" \
  --threads 14 --max-seq-length 8192 \
  --learning-rate 0.00001 --semantic-loss-weight 4 \
  --lora-layers 24 --lora-rank 16 --lora-alpha 32
~~~

These explicit settings match the current reviewed training configuration. The next run must use its own reviewed full-training settings. Rehearsals retain seed 17, BF16, SDPA, nonreentrant gradient checkpointing, batch size one, AdamW with zero weight decay and gradient clipping at one. Installed library versions and actual optimizer defaults are recorded.

The runner checks finite losses, gradients, parameters and optimizer state. All intended layers must participate and must receive nonzero gradients and actual adapter updates over the selected examples. It also verifies that frozen base parameters remain unchanged.

Before/after captures preserve independently rendered prompts through hashes, raw generated token IDs, replies, parsed actions, schema validity, termination state and errors. Complete tool calls are accepted without requiring a final EOS token, matching the serving path. Training and validation results remain separate.

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
