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
