# Verification and acceptance record

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

## All 275 complete-shape development cases independently verified - 18 October 2026

The unchanged original scorer and a separate completion verifier reproduced every complete-action, tool, argument and structure count. Case IDs, expected actions, shard order, model/runtime bindings and the event-log prefix match. Before/after serving proofs are identical. All three workers and the controller stopped, all evaluator stderr files are empty, and the production inference container stayed healthy and unchanged.

Facturation scored 110/133 complete actions and 89/111 exact arguments; Management Projet 74/78 and 51/54; Design Workflow 63/64 and 45/46. Facturation and Management Projet fail the inherited development gates. Design Workflow passes development only, with a decline from its original baseline. No V3 acceptance/control evaluation ran; historical scores remain unchanged.

Numerical verification covered all 2,283 selected updates, 24 changed/nonzero-gradient layers, unchanged frozen weights and saved/live equality. Actual Colibri export diagnostics matched 14/14 targets, compared with 13/14 in the training runtime and 13/14 exact runtime agreement. These are diagnostic observations, not acceptance percentages.

The one reviewer found no new wrong gold action or supplier-form contract break in its bounded review of 164 unique development rows across 132 scenario groups, including all 133 Facturation rows. Three article-search calls are native-equivalent aliases but remain failures under frozen exact scoring. Twenty-one other parsed planning errors and four invalid outputs remain. Raw invalid responses require investigation before assigning an export/runtime or model cause.

The report records real request latency, wall-time output rate and a one-second CPU/RAM sample with explicit limits on interpretation. These checks do not certify production business workflows or any of the six applications as accepted.

[Actual completion, unchanged development scores and measured performance](../training/reports/facturation-replay-v3-en-fr-development.json).

Earlier entries below retain their original observation state.

## Conditional replay V3 serial queue verified - 17 October 2026

Nine tests pass in 26.799 seconds using only local synthetic dataset metadata. They reconstruct the exact reviewed V3 base from tracked sources, preserve every current training row and original new-app suffix, and run the existing full metadata/schema/lineage preflight on the Contracts, Gestion Magasin and Reservation preparations. Negative checks reject the old R11 parent, skipped Contracts stage, loss of 556 current Facturation rows even with an updated hash, modified evaluation inputs, unsafe paths and overwritten artifacts.

All original input hashes remain unchanged. The single reviewer cleared both exact source files, including the complete-preflight test. No model weights, optimizer, inference, database or server numerical workload was used. These checks do not establish semantic independence, model accuracy, accepted predecessor identity or deployment readiness.

Run: `.venv-training/bin/python -B -m unittest training.tests.test_serial_after_facturation_replay_v3 -v`.

[Preparation results and explicit limitations](../training/reports/facturation-replay-v3-future-serial-preparation.json).

Earlier entries below retain their original observation state.

## Current complete Facturation backend regression run - 17 October 2026

The tracked backend at commit eb427df and shared assistant source passed 2,657 tests and 41 subtests in 120.28 seconds; total harness time was 122.84 seconds. Standalone vendored Colibri tests were excluded from Django collection. Existing application adapter, authorization, confirmation-history, business and logistics tests remained included.

The local harness disabled parent environment-file loading and restricted database connections to the isolated test database and local maintenance database. It used synthetic fixtures, verified all 1,660 source hashes before and after execution, and separately confirmed deletion of its uniquely scoped test database. The one reviewer checked actual evidence. All 1,086 warnings are retained in the private log, including warnings caused by the synthetic JWT test key.

No model inference or numerical training ran locally. These results do not replace the unchanged model development, acceptance and additional-control evaluations, or prove production end-to-end behavior.

[Verified complete backend results](../training/reports/facturation-current-backend-regressions.json).

Earlier entries below retain their original observation state.

## Successor export and evaluation guards checked offline - 17 October 2026

Fifty-four offline checks pass: twelve export-admission, nine one-shot export-launch, eleven development-worker, fourteen development-controller and eight completion-verifier tests. They cover the original invocation, terminal completion, source/model/runtime bindings, resource reserve, changed providers, unchanged case/target/scoring contracts, export byte-serialization binding and explicit cleanup. Even perfect synthetic fixture metrics cannot grant model acceptance.

The single reviewer cleared the exact private helper sources and original-invocation admission payload. The original 275-case development input hash, frozen worker implementation and scoring remain unchanged. Actual export/development bindings still require terminal evidence and review before execution; no live evaluation ran during training.

The running numerical process was observed at 23/2,283 updates. A three-second CPU sample and cumulative memory counters are documented separately from model accuracy and complete-run performance. No new acceptance score or production activation is claimed.

[Offline checks, preserved controls and execution gates](../training/reports/facturation-replay-v3-evaluation-preparation.json).

Earlier entries below retain their original observation state.

## Actual complete-shape server admission and early updates - 17 October 2026

All 2,975 training and 275 development rows passed the real server tokenizer round-trip, Colibri prompt-prefix parity, parser, loss-boundary, semantic-alignment and output-budget checks. Maximum sequences are 7,745 and 7,496 tokens within the 8,192-token context; every target fits and no truncation is allowed.

The exact 26-source/nine-data snapshot, original selected checkpoint-600 FP32 model and frozen runtime were verified. The single reviewer cleared the source, exact handoff payloads and actual launch evidence. Sixty-one implementation tests and seventeen staging/one-shot/resource simulations passed. Four actual launch-file hashes, command, original invocation identity and resource profile were independently verified.

At 2026-10-17T15:09:32Z, fourteen baseline diagnostics and 3 selected optimizer updates were recorded; early losses and gradients are finite. Production inference stayed healthy and unchanged. No completion, model-accuracy, application-security acceptance or production E2E claim follows from these observations.

[Actual server launch evidence](../training/reports/facturation-replay-v3-server-launch.json).

Earlier entries below retain their original observation state.

## Independent coverage checks before the next numerical run - 17 October 2026

Four real Colibri diagnostic requests completed HTTP/SSE with finish reasons and output counts of 95, 56, 56 and 56 tokens under the 512-token limit. The three quote requests generated a business-number string in the internal-ID field; the stock request generated an unsupported supplier field and misplaced its product filter. Runtime parsing and schema validation correctly rejected these outputs. Thirteen collected files, equal before/after identities, the original successful invocation and owned-worker cleanup were verified. Production inference stayed healthy and unchanged. No application operation ran and original benchmark scores remain unchanged.

The successor preparation passes 25 tests, including independent workflow/resource/argument-key coverage, quote discovery before deletion in both languages, whole contrast blocks, nested field/type distinctions, strict provenance, arbitrary-history rejection, source-byte preservation and isolated-directory admission. Seven runner and twenty-nine export tests pass, including numerical/capture/resource AST parity, pinned predecessor and manifest admission, source binding and cleanup failures.

These are implementation checks and four failure diagnostics. They do not prove general model accuracy, application security acceptance or production end-to-end behavior. V3 tokenizer admission, training, Colibri development evaluation and acceptance/control tests remain pending.

[Actual diagnostic evidence](../training/reports/facturation-replay-v2-invalid-output-diagnostic.json) and [preparation checks](../training/reports/facturation-replay-v3-preparation.json).

Earlier entries below retain their original observation state.

## All 275 joint-context development cases independently verified - 17 October 2026

IMPLEMENTED and verified as evaluation: all 275 original inputs, case IDs, expected targets and shard order match. Raw booleans and the frozen scorer reproduce the reported tool, argument, structure and full-action metrics. Bound model/runtime artifacts, before/after serving proofs, explicit event-log prefix and original source controls match. All three owned workers and the controller stopped; stderr files are empty and the production inference model remains healthy and unchanged.

The measured candidate fails the Facturation and Management Projet development gates; Design Workflow passes its development gate. This is not application acceptance or a new acceptance-suite score. Native-equivalent argument aliases remain failures under the unchanged frozen exact scoring.

With three four-thread workers, all 275 request latencies averaged 17.70 seconds and P95 was 24.75 seconds. This includes prompt prefill and excludes business-tool execution. The 271 available output-usage records average 3.27 completion tokens per request wall second; this is not decoder-only generation speed. Parsed first-visible-event timing is also not claimed as raw time to first token.

[Verified comparison, methodology and limitations](../training/reports/facturation-replay-v2-en-fr-development.json).

Earlier entries below retain their original observation state.

## Actual joint-context completion and Colibri replay - 17 October 2026

Independent evidence checks verified all 1,171 contiguous updates in the pinned selected-row order, finite loss/gradient values, all-layer updates, unchanged frozen weights and saved/live-adapter equality. All six numerical evidence hashes match. The original numerical invocation exited successfully.

The actual export completed 14 real Colibri replay requests. Every response was schema-valid, matched its diagnostic target and agreed with the training-runtime action. All seven export evidence hashes and current model/runtime artifacts were checked; before/after proofs match and owned-worker cleanup completed.

The single reviewer cleared the actual 24-file development handoff. Frozen input and baseline pins, 275 original cases and the inherited evaluator AST check passed before comparison launch. The broader development evaluation is running; implementation simulations and replay diagnostics are not general model accuracy or security acceptance.

The current logistics field/route/guidance review found no mismatch. This read-only compatibility review is separate from model accuracy and production E2E tests.

[Executed completion, actual export and timestamped development progress](../training/reports/facturation-replay-v2-pilot-completion.json).

Earlier entries below retain their original observation state.

## Actual server preflight and reviewed handoff - 17 October 2026

The actual server metadata preflight passed all 2,975 training and 275 original development rows: tokenizer round-trip, runtime-prefix parity, loss boundary, semantic alignment and output-budget checks with a 512-token cap. The smallest available output budgets were 488 training tokens and 512 development tokens; every target fits. Maximum sequence lengths remain 7,745 and 7,496 within 8,192 tokens; no truncation is allowed. Source/data/runtime identities and production health were unchanged.

The reviewed 22-source/9-data snapshot passed isolated admission. Seventeen stage/launch tests and 34 future export/development simulations pass. The frozen evaluator/scorer, original 275 cases and baseline are unchanged. Later stages have not executed.

At 2026-10-17T04:40:27Z, the original numerical invocation had completed 14 baseline captures and one finite update. Model acceptance, performance and after-training captures remain pending. A passed implementation simulation does not forecast 95 percent accuracy.

[Actual launch and source/model/resource checks](../training/reports/facturation-replay-v2-server-launch.json).

Earlier entries below retain their original observation state.

## Joint-context replay preparation checks - 17 October 2026

Seventeen successor preparation tests pass. They verify the 116 inherited examples remain eligible; complete optional-state blocks; all declared joint retention features; bilingual current-page payment schedules, previous-year service fees and missing-details contexts; language switching; pinned training-language provenance; unknown labels; deterministic unique selection; frozen controls; manifest/data tamper rejection; and an actual subprocess admission with only copied helpers plus prepared data.

Seven runner checks and twenty-nine export/isolation checks pass. AST comparisons confirm numerical, capture, resource and cleanup functions remain unchanged. Twenty-seven prior export tests pass in the same 80-test invocation. The twelve frozen V1 preparation tests passed separately. These are implementation checks, not model tests or accuracy predictions.

The single reviewer found and re-reviewed a portable-admission defect; the isolated regression now passes. No new numerical run, Colibri model evaluation or acceptance result has occurred for this successor.

[Checks, source hashes and pinned selection](../training/reports/facturation-replay-v2-preparation.json).

Earlier entries below retain their original observation state.

## Full replay-trial development verification - 17 October 2026

IMPLEMENTED and verified: all 275 frozen development inputs were evaluated through the original Colibri/provider/settings/scorer. The independent verifier checks source pins before controller import, exact ordered shard inputs, request/case identity, booleans and frozen assessments, model/runtime artifacts, step/model/context/token/thread settings, the combined result's before-proof hash, and the explicit event-log prefix range.

Final before/after serving proofs are byte-identical. The exact three owned worker names and step-306 stop record confirm cleanup; the original controller stopped and all stderr files are empty. Production inference remains healthy and unchanged.

The measured development actions are Facturation 110/133 (82.71%), Management Projet 72/78 (92.31%) and Design Workflow 64/64 (100.00%). Exact arguments are 89/111 (80.18%), 49/54 (90.74%) and 46/46 (100.00%), respectively. Structure is valid for 133/133 Facturation, 76/78 Management Projet (97.44%) and 64/64 Design Workflow cases. Facturation and Management Projet fail the development targets; Design Workflow passes this set only.

These are model-planning development results, not new acceptance or native-security certification. The candidate is rejected for activation/extension; no longer numerical run is admitted by these results.

[Complete metrics, verification and limits](../training/reports/facturation-replay-v1-en-fr-development.json).

Earlier entries below retain their original observation state.

## Completed replay trial and real Colibri export - 17 October 2026

IMPLEMENTED and verified: 306 contiguous updates follow the selected row order; metrics are finite, all 24 intended layers updated, frozen parameters stayed unchanged, and saved/live adapter equality passed. Fourteen baseline and fourteen trained captures are preserved. The single reviewer independently confirmed the numerical evidence and found no reporting or handoff blocker.

The real export completed all fourteen paired streamed requests with fourteen schema-valid Colibri actions and fourteen target matches. Thirteen actions agree validly across runtimes, and zero changed from framework-correct to Colibri-incorrect. Before/after serving proofs are byte-identical and the owned worker stopped. These small diagnostics are not an acceptance or security certification.

PARTIALLY IMPLEMENTED: the original 275-case development comparison is running with its before-serving proof, three isolated workers and unchanged provider/settings/scorer. The observation at 2026-10-17T03:46:39.114630+00:00 records six completed cases and zero controller stderr bytes. Complete development scoring and the existing separate acceptance/native security gates remain pending.

[Actual completion evidence and timestamped progress](../training/reports/facturation-replay-v1-pilot-completion.json).

Earlier entries below retain their original observation state.

## Actual replay-trial admission and early progress - 17 October 2026

IMPLEMENTED and verified: the exact staged sources/data, actual selected FP32 model and frozen runtime passed admission checks. The one-shot launch used the reviewed 14-thread, 32 GiB, swap-disabled profile. Reserving the full limit at preview left 12.89 GiB available, exceeding the 6.20 GiB spare-memory requirement.

At 2026-10-17T01:18:19Z, the original service remained running with 14 completed baseline captures and two contiguous updates matching the selected row order. Production inference remained healthy with its original start identity. Early losses/gradients passed the runner's finite-value checks.

PARTIALLY IMPLEMENTED: completion checks, all-layer update/frozen-parameter evidence, saved/live adapter equality, trained captures, export, development and acceptance are pending. No accuracy or native authorization certification is inferred from these admission and progress checks.

[Launch evidence and limits](../training/reports/facturation-replay-v1-server-launch.json).

Earlier entries below retain their original observation state.

## Server metadata checks and execution guard tests - 17 October 2026

All 2,975 training and 275 development rows pass actual server tokenizer/Colibri-prefix, argument round-trip, loss-boundary, semantic-alignment, context and target-output-budget checks. Source/data/runtime/tokenizer bookends match and production inference is healthy and unchanged. This is metadata validation, not inference or numerical training.

Thirty-six runner/export tests pass, including exact numerical-function parity, local-training rejection, reviewed-data admission, overlapping-optimizer detection, wrong predecessor checkpoint/report rejection, complete invocation/layer/finite-loss checks, export failure handling and owned-worker cleanup. Seven staging and nine launcher checks also pass. Together with twelve preparation tests, 64 offline checks pass.

No server staging, actual FP32 rehash, numerical dispatch, new accuracy score or native authorization certification is claimed by this preparation report. The private handoff review is cleared; actual runtime admission and all model acceptance gates remain necessary.

[Measured preflight and test groups](../training/reports/facturation-replay-v1-execution-preparation.json).

Earlier entries below retain their original observation state.

## Coherent contrast/replay preparation checks - 17 October 2026

Twelve metadata/schema tests pass in 14.290 seconds. They verify original source bytes/targets, complete optional-state blocks, all 154 declared contrast axes, independent retained tool/argument/intent coverage, four-source scheduling through the tail, unique deterministic selection, rejected incomplete/uncontrolled contrasts, source-label conflict rejection, preserved additional-control identity/policy, and wrong-manifest/tampered-split rejection.

The round-trip check validates 2,975 training and 275 original development rows with zero exact input-label conflicts or exact cross-split input overlap. It loads no model weights, executes no optimizer and reads no acceptance/additional-control case files. This does not establish semantic independence, model accuracy, native permission safety or deployment readiness.

The single reviewer cleared the control-policy inheritance fix. Server tokenizer/template/context checks and numerical/export/evaluation work remain planned. No new model score exists.

[Actual preparation checks](../training/reports/facturation-replay-v1-preparation.json).

Earlier entries below retain their original observation state.

## Completed V2 pilot development comparison - 17 October 2026

IMPLEMENTED and verified: all 275 original development cases completed through Colibri. Independent recomputation reproduced every reported metric and target gate. All bound file hashes match, before/after serving proofs are byte-identical, stderr is empty and all three workers stopped.

The candidate failed the Facturation and Management Projet development gates; Design Workflow passed this development set. Facturation exact actions were 107/133 (80.45%), Management Projet 72/78 (92.31%) and Design Workflow 64/64 (100.00%). Corresponding exact-argument counts were 85/111 (76.58%), 48/54 (88.89%) and 46/46 (100.00%).

This comparison is not acceptance or native-security certification. All existing acceptance cases/scoring remain unchanged. No new acceptance score, full V2 epoch, model activation or later-application training is claimed. The failed pilot will not seed a longer run.

[Verified complete development comparison](../training/reports/facturation-focus-v2-en-fr-development.json).

Earlier entries below retain their original observation state.

## Real V2 numerical and Colibri execution - 17 October 2026

IMPLEMENTED and verified: the original numerical invocation exited successfully after 92 contiguous selected updates and 14 before/14 after captures. It verified saved/live adapter equality, frozen-parameter stability, and nonzero gradients/updates in all 24 intended layers. The export supervisor then completed the actual FP32 merge, Colibri conversion, 14-request streamed replay, artifact checks and owned-worker cleanup.

The paired replay had 12/14 identical valid actions and 11/14 target matches in each runtime. One development target match was lost in Colibri. These counts must not be presented as 14 successful correctness tests or as 95% model accuracy.

PARTIALLY IMPLEMENTED: the 275-row development comparison has started with actual before-serving proof for all three workers. Model/runtime artifacts, worker identity, four threads each, 8192-token context, 512-token output budget and no-thinking settings match the prepared comparison. No completed new development score exists yet. The unchanged acceptance suites and independent native security checks remain necessary; production inference is unchanged.

[Execution evidence and timestamped progress](../training/reports/facturation-focus-v2-pilot-completion.json).

Earlier entries below retain their original observation state.

## V2 export and development handoff checks - 16 October 2026

Thirty-four focused offline tests pass: nine export-dispatch tests, eleven development-worker adapter tests and fourteen controller tests. They check source/inventory guards, successful trial admission, resource limits, single dispatch, failure preservation, correct export-unit status, unchanged evaluator reuse, exact baseline/case identity, retained metric comparisons and rejection of substituted or reordered export bindings.

The original worker launch/settings, scorer and 275 shared development cases are reused. The controller verifies the launch binding's ordered content against both its pretty serialized input and compact completed-export bytes. Runtime admission and launch records are separately hash-pinned. The single reviewer found no remaining issues; all 17 current and 79 historical evaluation controls remain unchanged.

These are synthetic guard tests, not model measurements. No live export or development-worker execution has occurred. They do not establish 95% accuracy, successful training completion, native authorization, activation permission or production readiness.

[Preparation evidence](../training/reports/facturation-focus-v2-development-preparation.json).

Earlier entries below retain their original observation state.

## Completed focused evaluation verified from original evidence - 16 October 2026

IMPLEMENTED and verified: the final reporter recomputed every development, regression and additional-control assessment from the original event shards, inputs and unchanged scorer. It checked exact case coverage/order, summary settings, model/runtime/tokenizer artifacts, matching before/after worker proofs and successful shutdown of all three workers for every phase. All five candidate comparisons, 275 shared development cases, 438 regressions and 48 additional controls are complete.

| Application | Full regression actions | Exact regression arguments | Additional-control actions | Acceptance |
| --- | ---: | ---: | ---: | --- |
| facturation | 96/108 (88.89%) | 74/86 (86.05%) | 9/16 (56.25%) | Failed |
| management_projet | 192/200 (96.00%) | 141/148 (95.27%) | 16/16 (100.00%) | Failed |
| design_workflow | 121/130 (93.08%) | 91/100 (91.00%) | 14/16 (87.50%) | Failed |

All application acceptance decisions remain false. Facturation passes this suite's critical-model-case gate but fails full-action and exact-argument targets; Management Projet and Design Workflow still have failing critical-model cases. These are planning tests, not proof of a backend authorization bypass or native security certification.

Nine synthetic pilot-launch tests pass, including active-workload rejection, no dispatch/writes in preview, changed-source/model-evidence rejection, memory reserve, exact resource profile and a second-call rejection after failed dispatch. The single reviewer found no remaining issues. Seventeen current and 79 historical evaluation controls remain unchanged. These launcher tests are preparation checks, not model accuracy measurements.

[Verified complete evaluation](../training/reports/facturation-focus-v1-en-fr-evaluation.json).

SUBSEQUENT OBSERVATION, 23:14 UTC: actual selected FP32 files, tokenizer/configuration, export metadata and serving artifacts were verified against the completed report. A metadata-only preview passed before the isolated 92-update server pilot started with 14 CPU threads and a 32 GiB memory ceiling. The pilot is running; no pilot accuracy improvement, longer-epoch admission or activation is claimed. Its adapter must not seed a subsequent full run.

Earlier entries below retain their original observation state.

## Facturation V2 export/replay supervisor - 16 October 2026

All 27 synthetic tests pass, including rejection of incomplete candidate/regression reports, mismatched terminal/app gates, changed model selection, wrong curriculum/captures, altered serving evidence and incorrect FP32/report/export metadata bindings. Existing numerical-invocation, source-admission, resource-isolation, export-flow and process-cleanup tests remain in scope.

Only bootstrap, predecessor validation, numerical-runner identity and input dependency checks differ from the reviewed V1 supervisor. Export execution, resource and cleanup functions remain AST-identical. The single reviewer found no remaining issues; current/historical frozen evaluation controls are unchanged.

These are synthetic guard tests. They neither load model weights nor demonstrate real export parity, a model accuracy gain, native authorization or production readiness. Completed predecessor evidence, actual selected-FP32 observation and the numerical pilot remain pending. [Supervisor evidence](../training/reports/facturation-focus-v2-replay-preparation.json).

Earlier entries below retain their original observation state.

## Facturation V2 pilot admission and server preflight - 16 October 2026

Twelve tests pass for bounded deterministic selection, date/filter pair coverage, bilingual category coverage, retained tool groups, captures, changed-manifest/parent/data rejection, and concurrent-workload rejection. AST comparison confirms the numerical, capture and resource-control functions are unchanged from the reviewed V1 runner. The first test invocation lacked temporary-file permissions for three tamper fixtures; the rerun with isolated temporary-file access passed all tests.

Server metadata checks pass all 1,620 examples for tokenizer/Colibri prompt parity, strict target parsing, token loss boundaries, semantic weighting and conservative output budgets. Sources, data, runtime and tokenizer/configuration checksums remain unchanged. These checks did not load model weights or run numerical training.

The 92 selected training updates cover 154 declared axes and all ten new categories in both languages. Twelve training and two development captures are planned diagnostics. This is not every Cartesian combination, a forecast of 95% accuracy, or native security certification. Terminal predecessor binding, server resource admission and actual pilot/export/development comparison remain pending. [Verified preparation](../training/reports/facturation-focus-v2-pilot-preparation.json).

Earlier entries below retain their original observation state.

## Facturation V2 preparation verified - 16 October 2026

All 13 focused tests pass, covering exact Cartesian cells, fixed request/context components, independent date labels, leap/year boundaries, optional unpaid/limit combinations, full unquoted remarks, trusted navigation/selection, source-hash rejection and held-out request exclusions. Native metadata validation accepts all 440 additions with database connections prohibited. The single reviewer checked all 320 matrix cells and 120 other bilingual rows; no incorrect targets remain.

The 1,047 parent training rows and all 133 validation rows remain byte-identical. The parent generator is checked against its manifest before invoking helpers. The reviewed supplier-workflow source update is an explicit exact-hash transition; other unexpected native changes still fail. Complete model inputs vary with the application's normal tool shortlist and are not claimed constant across optional-filter variants.

These are dataset and source checks, not new model accuracy, executed business operations or production security certification. Full token/template/parser preflight, new pilot admission and numerical execution remain pending. The active previous-curriculum evaluation and its scoring are unchanged. [Preparation results](../training/reports/facturation-focus-v2-preparation.json).

Earlier entries below retain their original observation state.

## Facturation completed epoch verified; functional evaluation pending - 16 October 2026

IMPLEMENTED and verified: the completed report is bound to the original successful training invocation, all 1,047 contiguous updates, the original selected FP32 base, frozen datasets and reviewed configuration. Final validation completed. Recorded duration was 34,166.99 seconds, excluding initial loading/encoding; peak process RSS was 7.714 GiB.

Final weighted loss was 0.06773017 against the starting 0.04873197. All four new weighted-loss checkpoints remain above that baseline, so loss selection retains step 0. This is not functional checkpoint selection or accuracy acceptance.

The reviewed read-only inspector verified the final 28,536,776-byte adapter, all 192 F32 tensor headers, contiguous byte ranges, checksum and matching LoRA configuration. It loaded no model weights and did not certify finite tensor values or numerical correctness.

A source-only semantic review covered 133 development rows (104 scenario groups) and 116 additions, recomputing all 90 added date-bound rows. It found no new semantic defects. Six development rows permit equivalent article-search argument aliases; original exact scoring remains unchanged. This review did not execute business queries or model inference.

PARTIALLY IMPLEMENTED: four sequential Colibri checkpoint comparisons are underway. Any selected changed candidate still requires the original three-app development, regression and additional-control gates. These checks do not establish native security, frontend behavior, all-app acceptance or production readiness. No model activation or later-application training occurred. [Verified training completion](../training/reports/facturation-focus-v1-training-completion.json).

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


All application tests use controlled fixtures in the isolated local PostgreSQL database. No destructive test ran against production business data. Model selection metrics are separate from backend authorization tests.

## Backend

The latest assistant/stock/delivery suite passed **816 tests** in `backend-final-ai-stock.log` (47.44seconds), including native stock reversal, confirmation history and permission-filtered knowledge retrieval. The complete backend suite then passed **2,272 tests and 30 subtests** in78.67seconds after the final routing and bilingual-knowledge fixes. Seven initial async-task failures came from the demo settings overriding eager mode; restoring the inherited isolated-test behavior fixed them. The static-asset guard was updated for build-only non-secret environment assignments. Standalone vendored Colibri command-line diagnostics are explicitly excluded from Django pytest discovery.

Coverage includes anonymous/disabled access, existing roles, company and related-record consistency, global staff-user lookup, native stock-only superuser access, unsupported schemas, bounded search/detail/navigation, read-only stock/logistics services, financial calculations, revoked permissions, stale references, JSON/SSE/cached history delivery, prompt-like record data, knowledge-source revocation, split-token human labels, and single-use confirmed mutation with durable actor audit.

Run from `facturation_backend`:

```sh
.venv-mac/bin/python -m pytest chat_ai/tests.py chat_ai/test_*.py \
  --ds=facturation_backend.settings_ai_test --reuse-db -q
```

Use pytest, not Django's unittest runner: these tests are pytest functions. Do not run concurrent test processes against the same reused database.

## Frontend

The whole-project run covered251suites/2452tests, with five stale expectations corrected (explicit list navigation and existing logistics endpoint coverage). The affected167tests then passed. The final retry-context pass added four regressions and passed62chat tests; TypeScript, ESLint and the assistant-enabled production build passed. Retry retains original invoice/language context after route changes.

Set `NEXT_PUBLIC_DOMAIN_URL_PREFIX=''` when running local route tests; the actual app reads this configured prefix. Do not change production route constants to compensate for a missing test environment variable.

```sh
NEXT_PUBLIC_DOMAIN_URL_PREFIX='' bun x jest src/components/chat-ai \
  src/components/pages/dashboard/shared/company-documents-list/companyDocumentsWrapperList.test.tsx \
  src/components/pages/dashboard/shared/company-documents-view/companyDocumentsWrapperView.test.tsx --runInBand
NEXT_PUBLIC_DOMAIN_URL_PREFIX='' bun x tsc --noEmit --incremental false
```

## Real browser checks completed

MCP Playwright uses the dedicated QA tab with a real local Next/Daphne/Colibri setup and guarded synthetic application records.

- Desktop/mobile placeholder center measured exactly equal to input-container and send-button centers.
- Approved theme blue and white icons; decorative/redundant controls removed.
- Bare `/voir` returns usage and an example in an assistant message box.
- AI result → invoice detail → explicit invoice list preserves company context, rather than browser history.
- Company switch clears old scope; history previews and exact-row deletion were checked.
- At a 390×360 short viewport the composer remained reachable; no horizontal overflow. This is not a physical-device virtual-keyboard test.
- Confirmed a dummy invoice note edit through the actual preview/modal/API. UI displayed **Remarque**. Database verification found `AI Test editor` in the durable AI audit, a request instruction identifier, and `ai-editor@example.invalid` in the native document history. Evidence: `confirmed-form-labels.png`.

The latest added module cards have passing renderer/permission tests; complete real-model browser flows for every module are still pending. Do not describe mocked-provider security tests as actual model E2E accuracy.

## Final model measurements and acceptance

Server-only v4 training, conversion, the frozen 80-case comparison and dedicated performance measurements are complete. Tool selection improved from44/80 to50/80; exact arguments from18/76 to24/76; structured output from61/80 to73/80. The95/95/99% targets remain unmet. Failure examples and immutable methodology are in AI_FINE_TUNING.md and curated training/reports; no labels or scoring were changed after inference.

The separate final server sample completed8/8requests: sequential mean8.34s, p95(maximum of4)9.74s; concurrency2 mean12.29s, p95(maximum of4)17.66s; runtime decode56.94tokens/s excluding prefill, peak process RSS2.58GiB, approximately4busy CPU cores. This small sample is not broad load certification.

Approved bilingual retrieval replaces unreliable generated workflow prose. Development retrieval regressions passed20/20top-three and15accent/plural variants top-one. Physical-device virtual-keyboard and assistive-technology certification remain unperformed. Broad model acceptance is explicitly incomplete.

## Additional real checks
- Human-labelled payment-terms shortcut: real API preview uses **Termes de paiement**; raw database key absent. No additional edit was confirmed during this check.
- Real local model article search returned AI-E2E with existing field labels. Card → article detail → explicit article list preserved company and chat state.
- Real local model stock question failed intent selection: returned an inventory instead of quantities. This remains a recorded E2E failure.
- Frontend production build passed. Isolated Linux Colibri Docker image passed authenticated private-host/auth-denial checks as non-root, read-only, no published ports; container removed. `docker-validation.json` records image hash and the corrected initial shard-permission failure.

Latest scope correction: English/French only.275 affected backend tests and101 chat frontend tests passed after runtime schema/fallback/context changes. Language detection checks cover both switch directions and validated interface fallback. Completed language-scope model results are recorded in AI_FINE_TUNING.md; v4 training/evaluation is complete and remains below acceptance targets.

Final dummy UI confirmation replay was verified before and after execution. The invoice remark, native history actor and durable AI actor ID match the authenticated `ai-editor@example.invalid`. Production business mutations are excluded from smoke testing.


Final local browser retests passed invoice/client-and-product search, quote search, invoice/quote detail-to-list navigation, history restoration, company switching without old-scope content, and verified English workflow followed by French status explanations. Confirmed dummy edit replay preserves its native/durable actor history. V4 retests passed explicit collected-payment summaries in both languages and exact positional follow-ups. The original failures remain in raw evidence; no blanket model acceptance is claimed.


Exact English/French positional follow-ups now resolve through stored conversation references and the same authorized `previous_results` tool. Twenty-eight new tests cover normal positions, negation, extra conditions, mismatched resource names, foreign records, expired state, revoked membership and out-of-range indexes. The complete assistant suite passed747tests after this change. This is application-side reference resolution; it does not change frozen raw-model evaluation scores.


## Final regression sequence

After the full2,272-test backend run, the assistant suite passed765tests (39.13seconds). The final independent review then narrowed help routing to avoid overriding specific-record and compound requests;52focused reference/help tests passed after that change. Four Docker/static-asset tests passed after excluding additional runtime secret patterns. The frontend's last native-navigation/chat run passed75tests, TypeScript, ESLint and production build. Actual MCP desktop-to-mobile resizing, drawer Escape/roundtrip, single FAB and chat accessibility passed.

The local v4 French status explanation initially failed with a truncated repetitive model call. That failure is retained in final-local-v4-ui-review.json. Exact retry after verified-help dispatch passed in0.826s; a fresh English workflow passed in1.337s. These trusted application handlers are excluded from raw-model accuracy figures.


## Module catalogue regression - 2026-10-08

The full assistant/backend suite passed **819 tests in 44.16 seconds** after the permission-derived module catalogue and exact capability-question handlers. Chat UI/client tests passed **112 tests in 7.73 seconds**; TypeScript and changed-file ESLint passed. Tests cover every bare module's existing tool mapping, usage examples, filter-preserving planner hints, native staff-only users, stock-only superusers without membership, denied write shortcuts, localized capabilities and the exact English logistics-access question without model inference or business queries. Raw logs remain ignored.

The prepared authenticated production checklist separately passed **12/12 checks**: one dashboard FAB, current company, bare help, natural invoice lookup, safe detail/list navigation, English/French workflows, verified collected-payment equality, history, company isolation, article lookup, mobile fit and anonymous-login absence. These selected application workflows do not replace the frozen model benchmark. The subsequent module release passed nine additional checks, detailed below.


## Production module verification - 2026-10-09

The reviewed frontend/backend release passed **9/9 actual MCP Playwright checks** with the existing authenticated production account. The slash catalogue exactly matches the active-company backend catalogue and native staff/edit/delete/print permissions. It includes all 14 supported modules and six permitted actions for this account.

The exact English logistics-access question from the user’s screenshot now returns safe English permission-derived guidance in 0.833 seconds; the French equivalent in the same conversation takes 0.845 seconds. Bare `/stock`, `/logistique` and `/articles` return usage/examples plus bounded authorized cards in 1.859, 0.824 and 0.834 seconds. These trusted handlers make no model-planning call and are not counted as model accuracy.

One model-planned descriptive article search matched the native visible designation and reference in 7.908 seconds. The scrollable menu reaches its last permitted action and preserves composer visibility at desktop 1121×1050 and mobile 390×844. No observed horizontal overflow, erroneous aria-hidden ancestor, generic unavailable warning or tested database-field identifier remained. Original viewport, conversation and authenticated session were preserved.

Evidence: [production-module-shortcuts-checks.json](../training/reports/production-module-shortcuts-checks.json). Timings are individual browser wall times, not TTFT/P95/throughput. Only the current authorized account was exercised; non-staff/revocation variants use automated backend tests. No production business mutation, physical-keyboard certification, exhaustive model/filter test or sustained load was performed. The prior failure is retained separately, and frozen model targets remain unmet.

Release verification also checked all nine Git remote heads, clean production source checkouts, installed core hash, current model start time, backend `/api/health/` HTTP 200 with the trusted HTTPS proxy header, and native frontend login HTTP 200. For an internal HTTP health probe, use the registered route with the configured trusted-proxy HTTPS header.

## Shared interface release - 2026-10-10

The canonical MUI interface and native adapters passed 125 Facturation and 55 Management Projet assistant frontend tests. Design Workflow's bold author-label change passed its 26 assistant tests. Bare-slash permission-filtered help passed 12 focused Facturation and 3 Management Projet backend tests; the latter includes English/French subcases. The affected Facturation form suites passed 190 tests. TypeScript/changed-source lint and all three frontend production builds passed.

Actual MCP Playwright verification used only local synthetic accounts and real local backend responses. The visual matrix contains 24 captures (three applications, two themes, empty/populated, shortcuts closed/open) and eight side-by-side comparisons. Both MUI apps match the reference's enabled Send background exactly: light #4F46E5, dark #6159E6, white icon, full opacity. Opening help inserts `/` into an empty draft; Send returns authorized help and closes the picker. Existing prose and arguments survive command changes. Bold author labels are present in all three apps.

Additional checks covered mobile 390×844 and 390×420 sizing, six-line input without clipping, focus wrapping, Escape, close/reopen draft retention, new-conversation reset, company-switch isolation, actual AI result/detail/list navigation, native confirmation priority and cancellation. Physical-device virtual-keyboard and assistive-technology certification are not claimed.

Release verification matched all 18 requested remote heads, confirmed deployed UI source and byte-identical MUI copies, healthy application containers and anonymous production login HTTP 200. Authenticated production interactions were not repeated for this UI revision. Management Projet remains disabled in production; shared inference and V5 training continued. These application checks do not count toward raw-model accuracy.

## Saved-checkpoint comparison verification - 2026-10-12

All 825 validation calls completed and their model/process/artifact, dataset and scoring hashes passed pre/post checks. Step 600 won the fixed validation-only selection rule. All 63 training tests, including eight checkpoint-selection tests, passed. The single reviewer found no remaining publisher issues after clarification-dependency and complete-output checks were added. Temporary workers stopped; production remained unchanged. The existing 438-case acceptance evaluation for the identical selected candidate remains failed and was not repeated. [Measured results](../training/reports/shared-v5r5-functional-validation.json).

## V5r6 preparation checks and CPU resource probe - 2026-10-12

IMPLEMENTED and verified: saved-checkpoint evaluation used three four-thread workers (12 threads total). All 825 comparisons completed. Finished R2/R4/R5 evaluation services were then stopped to release RAM; all weights/results and production inference were preserved. Training remains configured for 14 of 16 logical threads, retaining the 10% memory reserve.

Two unsaved, 7,662-token checkpointed optimizer updates passed in 188.31 and 173.61 seconds, with 6.34 GiB peak RSS and genuine updates in all 24 intended layers. Disabling gradient checkpointing failed before any successful update at both 20 GiB and 26 GiB limits. The initial 22 GiB attempt failed admission before launching; a duplicate-stop cleanup bookkeeping error was independently recovered. All probe processes are stopped and production remained healthy. Retain gradient checkpointing; no measured speed improvement from extra activation memory is claimed. [Resource evidence](../training/reports/cpu-training-resource-comparison-20261012.json).

PARTIALLY IMPLEMENTED: V5r6 retains the exact 1,803 prior training rows and all 275 validation rows, adding 166 synthetic English/French examples for date bounds, combined unpaid/customer/product filters, current-page reads and literal field values. Total: 1,969 training rows. All 438 frozen evaluation cases remain unchanged. Two native-routing/target wording issues were corrected before training and reviewed by the single reviewer.

All 69 training-integrity tests pass. Native audit passes all 166 new tool/schema selections and eight Facturation explicit targets; independent review also checked eight Management Projet explicit targets. Metadata preflight passes all 2,244 training/validation rows and 438 evaluation cases, with no local weights or training. [Metadata checks](../training/reports/shared-v5r6-en-fr-metadata-preflight.json), [native audit](../training/reports/shared-v5r6-native-curriculum-audit.json). These are data/preparation checks, not model accuracy. No V5r6 full optimization has started; selected-base binding, server preflight and launch-time capacity remain pending.

Management Projet and the next three application assistants remain disabled. No production model replacement; future application training stays sequential after acceptance.

## V5r6 resumed server checks and training launch - 2026-10-12

PARTIALLY IMPLEMENTED - current run: V5r6 server training has started from the verified V5r5 step-600 checkpoint. One complete epoch covers 1,969 English/French training rows; all 275 validation rows and 438 held-out cases remain unchanged. The run uses 14 CPU threads, a 16 GiB limit with at least 10% host memory reserved, gradient checkpointing, 24 LoRA layers and a learning rate of 0.00001. Validation/checkpoint selection runs every 300 steps, with the unchanged baseline eligible. There is no V5r6 accuracy score or production activation yet. [Verified run start](../training/reports/shared-v5r6-en-fr-training-start.json).

IMPLEMENTED and verified: the exact training base matches 473 previously verified FP32 tensors, all three attested tokenizer files and the full shard index. Server metadata checks passed 1,969 training and 275 validation rows. Two resumed capacity updates passed across all 24 layers; the earlier user-interrupted attempt is preserved and does not count as a completed capacity test.


## Draggable launcher verification - 2026-10-12

The same dependency-free hook is synchronized into all six frontends; Design Workflow retains its native interface. Assistant suites passed **358 tests**: Facturation 137, Management Projet 67, Design Workflow 38, Contracts 37, Gestion Magasin 41 and Réservation 38. All six TypeScript checks, scoped ESLint checks and optimized production builds passed. The single reviewer’s scrollbar-gutter finding was fixed and covered by a regression; final review reported no remaining findings.

MCP Playwright checks used isolated local dummy accounts and native backend responses. All six apps passed mouse dragging without opening chat, opening after a drag, position preservation when closing chat, keyboard movement and reset, mobile bounds, real Chromium touch input, and next-page interaction. The five additional application checks also verified position retention through client navigation. Light/dark desktop and mobile screenshots were inspected. Contracts correctly hides the launcher while its native mobile drawer is open.

The initial 96px bottom offset clears the tested pagination in five apps. Gestion Magasin’s footer overlaps the default launcher by 12.5px at 1440×900; moving the launcher clears it, and the actual next-page click then succeeds. This release provides a movable control, not automatic collision detection. Position resets on reload. Physical-device testing was not performed.

The deployed Facturation launcher was additionally checked through the existing authenticated production account: exact mouse movement, drag-click suppression, keyboard movement and Home reset passed. No model requests or business writes were made. The live screenshot contains only the launcher crop; private browser evidence remains excluded from Git. These UI tests do not establish model accuracy or change application activation gates.

Release verification: all 18 frontend remote heads matched their reviewed commits; all six deployed source trees matched the changed-file hashes. All six containers were healthy and contained the compiled launcher. Native frontend login routes and backend health routes returned HTTPS 200. Production environment/configuration hashes, database-volume mounts, 44 supporting container identities and the training process were unchanged. Existing assistant activation settings were preserved.

## Named list return regression checks - 2026-10-12

Local related tests: facturation 851, management_projet 195, design_workflow 78, contracts 160, gestion_magasin 84, reservation 299. All six TypeScript checks, scoped lint runs and production builds pass.

Tests cover explicit destination parameters, page/page_size/ordering, namespaced grids, same-origin absolute routes, company/store isolation, invalid or blocked storage, fresh navigation and direct-link fallbacks. New hook regressions cover Next canonical query arriving before browser history and the internal-history-marker synchronization bypass. Real MCP browser checks used isolated synthetic local data; no production business write was performed.

All six named user-list returns retain pagination after reload. The five MUI apps preserve existing sorting and non-default page sizes; Facturation articles and Gestion Magasin catalog preserve active company/store scope at page 3 and 25 rows. Native next/previous and page-size controls were also exercised in Gestion Magasin. No claim is made that in-memory filters survive a detail visit.

Production verification: all 36 frontend/backend remote references match, all six live frontend bundles contain the helper and their containers are healthy. All six frontend HTTPS routes and backend health endpoints return 200. Facturation passed an authenticated native named-list return with page 2, five rows and last-name sorting, then reload. No business records were changed. The other apps have local authenticated browser evidence plus live bundle/health checks, not a claimed authenticated production business-flow test. [Sanitized release report](../training/reports/list-return-release-20261012.json).
