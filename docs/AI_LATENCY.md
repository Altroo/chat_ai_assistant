# AI response latency

## Measured untrained 4B baseline

The current Qwen3.5-4B measurement covers 133 synthetic Facturation planner requests through Colibri with seven CPU threads. Business tools were not executed. It is a model-request benchmark, not a complete frontend or database workflow measurement.

| Request group | Count | Mean | Median | Observed P95 |
| --- | --- | --- | --- | --- |
| All primary requests | 133 | 38.114 s | 31.331 s | 118.628 s |
| Correct full actions | 77 | 35.268 s | 31.106 s | 51.141 s |

The 77 correct requests average 65.6 generated tokens and 2,502.6 prompt tokens. Their latency remains substantial with short outputs. Usage was recorded for 125/133 cases; the eight missing records are not imputed. None of the recorded completions reaches 256 tokens. The saved baseline lacks per-request native phase profiles, so prompt processing and decoding costs have not been separately established.

## Recorded baseline latency cohorts - 22 October 2026

Further analysis of the same 133 saved baseline requests reproduces the existing mean, median and nearest-rank P95. These are recorded untrained-model measurements, with no additional inference. Token usage is available for 125 cases; the eight missing records remain separate.

| Prompt-token band | Cases | Mean prompt tokens | Mean completion tokens | Mean request latency |
| --- | --- | --- | --- | --- |
| Below 2,000 | 22 | 1,690.0 | 50.6 | 23.140 s |
| 2,000 to 2,999 | 77 | 2,350.4 | 69.1 | 32.753 s |
| 3,000 or more | 26 | 4,333.3 | 71.0 | 65.021 s |

The four cases expecting the previous_results tool average 124.255 seconds, 7,346 prompt tokens and 37 completion tokens. These cases overlap the bands above and are a small subset. Follow-up context and tool-schema size are priorities for phase profiling and controlled prompt-reduction tests after training. Changes must retain authorization, reference revalidation and the unchanged quality gates.

Prompt-length associations do not establish causality or isolate prefill cost. First-visible-provider-event measurements are not native token TTFT or frontend timings. No new inference, runtime change or latency improvement is claimed. [Source, cohort definitions and recorded statistics](../training/reports/qwen35-4b-baseline-latency-triage-v1.json).

## Verified code findings

The inspected Facturation greeting handler resolves complete English/French greetings before model creation, retaining backend authorization, persistence and delivery checks. This is a local code finding, not a production greeting latency measurement. Standalone thanks and other acknowledgements need separate coverage.

The inspected Colibri engine supports phase profiling and prefix-reuse diagnostics. Prefix reuse is already enabled by default unless explicitly disabled. Its recurrent-state reuse is all-or-nothing; adding a generic cache flag is not an established optimization.

The frozen single-slot engine starts its native generation timer after prompt prefill. Its profile interval includes generation, sampling and output handling. Subtracting that interval from request latency leaves other overhead, including possible prefill, queueing, tokenization, state handling and transport. That residual must not be reported as pure prefill time.

A passive wrapper and isolated evaluation runner are reviewed and tested as preparation. They preserve original requests, output budgets, labels and quality events, then record one matching engine profile per request when available. Missing or ambiguous telemetry remains missing; it does not change accuracy results. No new numerical profiling or speed improvement has been measured. [Preparation and limits](../training/reports/qwen35-4b-evaluation-preparation-v1.json).

## Next measurements and changes

After the current training job releases the CPU, profile the selected checkpoint in an isolated Colibri worker. Record native phase timings and prefix decisions, request latency, time to first visible output, output buffering, token counts, RAM and CPU. Measure cold and warm requests separately. Compare useful thread counts within the approved CPU budget.

Evaluate static-prefix reuse and reduced prompt/schema overhead only with exact permission boundaries, unchanged tool meaning and the required quality/security regressions. Do not cache business answers across users or companies. Backend authorization remains mandatory for every tool and delivery.

Measure native greetings, acknowledgements, shortcut help, model-planned searches and complete application responses as separate paths. Keep their test counts and limitations explicit. No latency improvement or production change is claimed by this preparation.

[Actual baseline analysis and evaluation controls](../training/reports/qwen35-4b-comparison-preparation-v1.json).

## Prepared fourteen-thread comparison - 22 October 2026

A separate fourteen-thread Colibri replay is prepared from the unchanged seven-thread evaluation runner. It preserves the same 133 ordered cases, model export, context/output budgets, labels and scorer. Its admission, worker units and results are separate; it cannot become a canonical primary candidate. All 18 offline tests passed locally and on the Linux training server. The single reviewer cleared the source after a queued-controller concurrency guard fix.

This is preparation only. Training completion, actual export review and a separate execution admission are required before inference. No faster response time has been demonstrated. Controlled cold/warm repetitions and full application timings remain pending. [Source bindings, tests and execution limits](../training/reports/qwen35-4b-thread-latency-preparation-v1.json).

## Prepared CPU precision comparison - 22 October 2026

The inspected frozen Colibri CPU loader supports requested four-bit packing for eligible tagged matrices. One prepared profile targets the output head and dense MLP; another requests all supported dense components. They reuse the same model export and seven-thread resource budget. The canonical seven-thread checkpoint comparison and separate fourteen-thread replay remain unchanged.

The precision replay passed all 20 offline tests locally and on the Linux server, and the single reviewer cleared its preparation. Admission, unit names and result paths are separate from canonical candidates, with the requested profile bound to admission. No inference has run.

Actual four-bit coverage remains unverified: the CPU loader can retain int8 after an allocation failure and does not expose per-matrix precision counters. These are requested-configuration tests. Quantization can reduce accuracy, and no speed or RAM improvement is claimed. Full quality/security checks and cold/warm repetitions remain required. [Source, tests and limits](../training/reports/qwen35-4b-precision-latency-preparation-v1.json).

## Trained-checkpoint measurements started - 22 October 2026

Facturation's 632-update training run and all four Colibri exports are complete. Checkpoint 158 has started the canonical seven-thread, 133-case replay with passive native phase profiles. No complete trained-model latency result or improvement is available yet. The other checkpoints, selected-model fourteen-thread and requested precision comparisons, cold/warm repetitions and complete application timings remain pending. The 38.114-second figure above still belongs to the untrained baseline.

[Completed training and current measurement scope](../training/reports/qwen35-4b-pilot-training-completion-v1.json).

## Recorded first-checkpoint phase sample and prepared chunk comparison - 22 October 2026

A read-only snapshot at 13:30 UTC matches all 48 completed request records to their native phase profiles. These are the first ordered checkpoint-158 development cases, not a representative random sample or the selected model.

| Recorded interval | Cases | Mean | Observed P95 |
| --- | --- | --- | --- |
| Full model request | 48 | 32.758 s | 46.230 s |
| Native post-prefill generation interval | 48 | 5.322 s | 8.039 s |
| Time outside that interval | 48 | 27.436 s | 38.824 s |

Time outside the measured interval accounts for 83.754% of matched request time. It includes other overhead and must not be labelled pure prefill. The native interval includes generation, sampling and output handling. Its aggregate token rate is 12.667 completion tokens per interval second, not end-to-end throughput or pure decode speed. The same 48 baseline cases average 33.454 seconds; this partial pair does not establish a selected-model improvement.

A separate replay now requests 512-row CPU prefill chunks, versus the frozen source's 128-row default. It preserves all 133 ordered questions, schemas, expected actions, scoring and seven-thread serving limits. All 18 local and Linux offline checks pass, and preparation has one-reviewer clearance. Actual chunk sizes, request latency, memory and cancellation effects remain unmeasured. The replay needs separate model/export admission and cannot replace a canonical checkpoint.

The conservative tool-shortlist trial retains all 133 expected actions but reduces total schema characters by only 3.462%. It is deferred without numerical inference or production source changes. Thread-count and requested precision comparisons remain separately prepared and unexecuted.

[Bound controls, measured partial sample and remaining requirements](../training/reports/qwen35-4b-prefill-latency-preparation-v1.json).
