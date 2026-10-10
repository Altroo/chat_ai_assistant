# Gestion Magasin assistant discovery

Status: discovery in progress; adapter, dataset and training NOT implemented. Exact application identifier: `gestion_magasin`. The shared Qwen3.5-0.8B model and Colibri runtime will be reused; no new model download or parallel training job is planned.

## Verified architecture and application modules

Django/DRF, PostgreSQL, JWT/dj-rest-auth, Redis, Celery, Channels and django-simple-history. The existing `ai_assistant` package is text assistance, not the new business chat adapter. Native backend modules are `account`, `store`, `catalog`, `stock`, `sales`, `finance`, `attendance`, `reporting`, notifications and websockets. Next.js 16/React 19 uses MUI, Redux Toolkit and the existing `magasinApi` client. The authenticated root is `src/app/dashboard/layout.tsx`.

Verified entities include Store/StoreMembership/Role; Product/Category/ProductUnit/ProductStockTrackingItem; StockBalance/StockMovement/StockAddRequest/StockTransfer/Purchase/InventorySession and their lines; Customer/PaymentMode/Promotion/Sale and their lines; Expense/ExpenseCategory; Employee/AttendanceRecord. Operational records have native history. Product catalogue records are global; stock balances and most business transactions belong to a store.

Frontend routes include dashboard, article, stock, store-stock, stock-transfers, purchases, inventory, stores, sales, pos, caise, promotions, expenses, pointage and users. Detail/edit pages exist for the corresponding primary records. Do not invent a customer detail route: no standalone customer page was found in the route inventory. Keep the existing `caise` spelling in navigation.

## Native security and scope

`store/permissions.py` defines the existing roles: direction, responsable, vendeur and lecture. Active StoreMembership plus active Store controls access. Native WRITE_ROLES are direction/responsable/vendeur; MANAGEMENT_ROLES are direction/responsable. Staff has native store bypasses. Reuse these helpers, not a replacement role hierarchy.

Account flags include read/print/create/edit/delete plus promotion creation and wholesale-sale permissions. The frontend uses these flags in addition to store scope. Endpoint enforcement varies by operation; the adapter must respect the actual action checks and permitted fields. User administration and activity history remain administrator-only.

`pointage_only` is a critical exception. `account/middleware.py` explicitly blocks non-attendance API paths for these accounts, while store helper functions intentionally grant access to active stores for attendance. It is unsafe to interpret those helper results as general financial/catalogue access. A future assistant entry point for these accounts must explicitly retain an attendance-only capability set and be tested through the real middleware. No middleware exception has been added yet.

Attendance has another explicit native scope rule: the special attendance store with code `mbr-south` exposes the existing broader attendance view. Outside that scope, native employee queries filter active unlinked commercial-advisor records. Reuse the actual attendance query functions and test this boundary; do not improvise a company filter.

The existing store tabs use the membership API, route `store_id`, and a local selected-store preference. Native tab changes do not always update the URL. Assistant integration therefore needs a trusted backend scope plus explicit frontend tab-change synchronization; local storage or URL values alone cannot authorize a store. Global-stock pages and attendance scope require their existing special handling.

## Authoritative business calculations and actions

`stock/services.py` owns locked stock movement, sales/returns, validated transfers, purchase receipt and inventory validation. `sales/services.py` owns sale creation and voiding. An assistant must call native operations and preserve their effects, validation and history; changing raw balances or deleting a confirmed sale directly would be incorrect.

`reporting/views.py` and ReportingScopeFilter provide existing scoped reports. Confirmed sales, received purchases, expenses, native stock valuation and sales-line margins are separately calculated. The dashboard `net_total` is sales minus expenses minus received purchases; it must not be presented as audited accounting profit. `today_cash_total` uses today's paid sale amounts regardless of the requested report period, and its query does not restrict payment mode to physical cash. Labels must explain the actual metric. Global catalogue counts/expiration counts must not be represented as store-only stock counts. The report endpoint currently returns several broader fields together; any assistant adapter must return a bounded selected result rather than forwarding the full payload.

Sale PDF generation is an existing native capability. Transfers/inventories/purchases have separate state-changing confirmation endpoints; these must not be confused with read-only navigation or ordinary descriptive edits.

## Implementation gates

1. Finish native endpoint/serializer/filter and frontend page permission mapping before creating tools.
2. Define bounded, permission-aware record search/navigation for real modules, including descriptive queries and bare slash usage.
3. Reuse the shared MUI chat/robot, active store behavior, English/French suggestions and conversation isolation.
4. Integrate native financial reports with accurate labels, period semantics and store scope.
5. Add only tested native mutations behind exact confirmation and actor-attributed history; preserve catalogue/global and related-record boundaries.
6. Generate approved synthetic EN/FR data from registered capabilities, freeze held-out cases before baseline, retain prior application curricula, and train only after the preceding run/evaluation finishes.
7. Test real JWT middleware, role/flag combinations, membership revocation, attendance-only access, global-stock access, malicious records, confirmation retries and cross-store history before release.

No production data has been extracted for training. No Gestion Magasin source, deployment or database was modified during this discovery.
