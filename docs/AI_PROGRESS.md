# Phase 1 progress — facturation

Current step: corrected starter-question release deployed and verified; Phase 1 implementation report remains available for user review. The user subsequently authorized the Management Projet integration and shared-model Design Workflow training; their separate progress documents describe that work. Broad model-quality acceptance is incomplete; do not interpret successful basic workflows as a 95% accuracy result.

## IMPLEMENTED and verified
- Reusable Python provider/orchestrator/registry, Django integration,17 typed tools, native permissions, company/object checks, bounded read results, safe navigation and financial calculations reused from Facturation.
- Supported document/client edits and deletion require exact-target confirmation and fresh native permissions. Native history and durable AI audit identify the requesting user. Stock reversal for delivery deletion uses the shared native service.
- Authenticated root FAB, native theme/components, responsive chat, company-tab scope, history, cancellation, retries, slash help, human form labels and explicit detail-to-list navigation.
-12 reviewed bilingual knowledge documents, incremental synchronization, permission filtering before ranking, exact-version history protection. General help delivers verified procedures; specific business questions use the local model. Exact positional follow-ups use authorized saved references.
- Server-only v4 LoRA training completed410steps; validation loss0.117782→0.068355. No private business records used. Colibri CPU export and artifact hashes verified.
- Current production: all three repositories released through local commits/Git; all nine remote heads verified. Backend and frontend native HTTP routes return 200; private model remains healthy with the same model identity and start time.
- Latest module-shortcut changes: 819 assistant/backend tests and 112 chat frontend tests passed; TypeScript, ESLint and the assistant-enabled production build passed.
- Full backend2,272tests+30subtests passed; final assistant765tests passed, then52 focused help/reference regressions after review. Four Docker/static-asset tests passed. Frontend75 final native/chat tests, TypeScript, ESLint and production build passed.
- Real local v4 checks passed invoice/client/product search, quote/article search, EN/FR collected-payment summaries, unpaid/ordinal follow-ups, navigation/list return and reviewed EN/FR workflow answers. Original model failures remain recorded separately.
- Public-repository audit found no actual credentials or private business artifacts in release commits. Runtime environments, keys, browser state, raw reports, weights and checkpoints are ignored. Application code is edited locally and released via Git pushes.

## Suggestion-button update — 2026-10-09
- IMPLEMENTED: complete permission-filtered English/French starter questions, immediate sending on click, active-company isolation and explicit click-to-send instructions. Slash-menu entries remain editable drafts.
- Validation: 831 assistant backend/security tests and 115 chat frontend tests passed; TypeScript, ESLint, production frontend build and source/wheel checks passed. The single reviewer found no unresolved code issues.
- Initial production UI release: each of the five questions sent exactly once in the active company. Unpaid invoices, recent quotes, stock and invoice workflow completed safely; desktop/mobile fit, native English metadata and slash drafting passed.
- Preserved failures: original logistics wording returned INVALID_MODEL_OUTPUT; its clearer French/English replacement completed successfully as separate normal chat requests. An English fresh-conversation unpaid search incorrectly selected the previous-results tool; audit confirmed CONTEXT_EXPIRED from that unavailable tool, with unchanged user authorization. The corrected catalogue omits this tool until a nonempty result set exists. A private provider probe then selected the correct unpaid-invoice search. The stock probe confirmed the native minimum-status filter; empty production cards alone were not treated as filter evidence.
- Final corrected release: 10/10 actual production button-click checks passed (five French, five English), with one exact request per click and correct company scope. Both final stock questions independently selected the native minimum-status filter in private provider probes. Source heads and installed wheel were verified, services healthy, model unchanged. Observed production stock lists were empty; no live threshold values were inferred. Evidence: [sanitized starter checks](../training/reports/production-starter-suggestions-checks.json).
- These targeted checks do not replace the held-out model evaluation, whose last recorded scores remain below target. The catalogue correction has not been rescored against that dataset.

## Measured model limits
Frozen independent80 cases: tool selection50/80 (62.5%); exact arguments24/76 (31.58%); schema73/80 (91.25%). Base:44/80,18/76,61/80. Targets95/95/99 are UNMET. Complex filters, limits, operation choice and malformed calls remain weaknesses. The application's deterministic help/reference handlers are not credited as model accuracy.

Dedicated server8-request sample: sequential mean8.34s, p95(maximum of4)9.74s; concurrency2 mean12.29s, p95(maximum of4)17.66s. Decode56.94tokens/s excludes prefill; peak process RSS2.58GiB and about4busy CPU cores. This small sample is not a load-capacity certification.

## Production verification
- Prepared production checklist: 12/12 passed, including dashboard FAB, invoice/article search, financial equality, company/history isolation, bilingual workflows, navigation, mobile fit and public-login absence. The new module release passed nine additional production checks: permitted catalogue, English/French capability answers, stock/logistics/article reads, described article search and desktop/mobile menu fit.

## PARTIALLY IMPLEMENTED
- Overall model acceptance remains below target, despite passing the tested basic application workflows.

## Remaining limitations
- Complex model requests may omit filters or ask for clarification; inspect returned record details before selecting an action. Exact-target confirmation is mandatory for supported writes.
- Stock, logistics, account and payment adapters are read-only. Supported writes are bounded document/client actions, not all operations in every module.
- Full physical-device keyboard and assistive-technology certification remains unperformed.
- Phase 2 is explicitly authorized for Management Projet. Design Workflow shared-model training is also authorized; its application release is separate. The user subsequently authorized the remaining named applications; their integrations remain planned and must reuse the shared model.

Historical work log: [AI_PROGRESS_HISTORY.md](AI_PROGRESS_HISTORY.md). Detailed evidence: [AI_TESTING.md](AI_TESTING.md), [AI_FINE_TUNING.md](AI_FINE_TUNING.md), and training/reports.

## Shared UI revision — 2026-10-10

IMPLEMENTED locally: canonical Design Workflow-based MUI interface, identical Facturation and Management Projet copies, local SVG robot/icons, scoped palette, optional company row, bold author labels, meaningful immediate suggestions, accessible shortcuts, draft-safe command switching, bare-slash help and mobile input sizing. Existing business handlers and permissions remain authoritative. Management Projet production activation is still disabled.

Verified with local synthetic logins: 24 actual screenshots covering reference/Facturation/Management Projet × light/dark × empty/populated × shortcuts closed/open, eight side-by-side comparisons, mobile 390×844 and 390×420, six-line input, Escape/focus wrapping, draft preservation, company switching, AI detail-to-list navigation, native confirmation priority and cancellation. No API responses were replaced for these browser checks. Physical-device keyboard and assistive-technology certification remain unperformed.

Automated validation: Facturation 125 assistant frontend tests; Management Projet 55; Facturation 12 focused backend tests; Management Projet 3 focused backend tests (including English/French subcases); 190 existing Facturation form tests. TypeScript, assistant ESLint and both production frontend builds passed. Design Workflow’s requested bold labels passed its 26 assistant tests and production build. One reviewer completed the review with no remaining blocker after fixes.

IMPLEMENTED: reviewed source published to company, personal and production for the central repository, Facturation frontend/backend, Management Projet frontend/backend and Design Workflow frontend. All 18 remote heads matched. Three frontend production builds, deployed-source comparisons, container health and anonymous HTTPS login checks passed. No backend migration was needed. The eleven Facturation form return fixes are published. Management Projet’s effective production AI setting remains false; the shared inference process and training unit were not restarted.

PLANNED: remaining shared UI integrations. The six-app navigation follow-up is recorded below. Shared V5 server training continues; no V5 accuracy score is available yet. Colibri upstream PRs remain explicitly deferred.


## Six-app return navigation — 2026-10-10

IMPLEMENTED and verified locally: all remaining history-based return controls removed from facturation, management_projet, design_workflow, contracts, gestion_magasin and reservation. The Holding portal is excluded. Contracts has four corrected list/form destinations, Gestion Magasin 22 and Reservation ten. Six not-found pages keep their explicit Home/dashboard action instead of a history-dependent Return button.

Gestion Magasin returns preserve the applicable store for articles, stock, inventory, sales, expenses and attendance. List selection accepts the URL hint only when the store belongs to a visible active membership. Cross-store lists keep their existing destinations. Manual store changes synchronize an existing store hint without undoing the native pagination reset or discarding sorting and anchor parameters. The stock-detail destination still follows its stock/store-stock label.

Validation: 297 focused frontend tests passed across the six apps; the broader Magasin/pagination run passed 69 tests (overlapping coverage, not an additional unique count). Scoped ESLint, TypeScript and all six production builds passed. Regressions cover authorized deep links, invalid/unknown store hints, revoked membership, restricted store visibility, tab changes and pagination preservation. One reviewer completed the final review with no remaining findings. Local browser checks confirmed explicit 404-to-dashboard navigation in Facturation, Management Projet and Design Workflow. Source scans found no remaining history navigation calls. Sensitive-added-content checks passed.

Publication: IMPLEMENTED. All six reviewed frontend commits are published to company, personal and production; all 18 remote heads matched. Deployed source matches the reviewed files in each app, all six frontend containers are healthy and all six login routes return HTTP 200. Production browser verification confirmed Facturation’s 404 Home navigation; the other checked apps reached their expected sign-in pages without active browser sessions. Authenticated navigation for those apps was verified locally where available, not claimed as a complete production business-flow test. No backend, database, model, permission or training configuration changes were included. The training process retained its original process identity; the shared inference service remained healthy with its original start time.

## Serial training and Contracts preparation — 2026-10-10

PARTIALLY IMPLEMENTED: Contracts (`contrat`) native adapter and shared UI are under local validation. See [discovery](AI_CONTRACTS_DISCOVERY.md), [actual checks and remaining gates](AI_CONTRACTS_PROGRESS.md), and the [single-job training queue](AI_TRAINING_QUEUE.md). The current shared V5 run continues; no Contracts training or model accuracy is claimed.

The user's additional login-theme request is limited to Contracts and Réservation, with Facturation as the reference. Local desktop/mobile screenshots confirm matching dark canvas, transparent outlined fields, heading size and a theme toggle 16px from the top/right. Theme switching preserves typed input and persists across reload. IMPLEMENTED: the two theme fixes are published to company, personal and production; all six remote heads matched. Exact-source production builds and 26 existing auth/theme tests per app passed. Live Contracts desktop and Réservation mobile login checks confirmed the palette, outlined fields and top-right toggle; both containers are healthy. The training process retained its original PID.

## Contracts adapter preparation — 2026-10-10

PARTIALLY IMPLEMENTED: native permission/company tools, confirmed writes with actor history, EN/FR knowledge, history and canonical MUI UI are verified locally. Final checks: 576 backend tests plus 4 subtests; 60 final assistant/form frontend tests, TypeScript, ESLint and production build passed. Local dummy browser checks include scope isolation, read-only denial, actual PDF, confirmed deletion/audit, history and eight-state visual comparison. See [Contracts progress](AI_CONTRACTS_PROGRESS.md). The shared next-stage dataset passed tokenizer/Colibri preflight; Contracts model training/accuracy and activation are still incomplete. Shared V5 remains the only active training job.

Contracts source is now published disabled: backend `00503a910cda`, frontend `875524520cc0`, six remote heads verified; additive migration/knowledge sync and native health checks passed with existing business row counts unchanged. Gestion Magasin and Réservation have preliminary source discovery documents; their adapters/datasets remain unimplemented.
