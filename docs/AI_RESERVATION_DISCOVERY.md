# Réservation assistant discovery

Status: preliminary native discovery; assistant adapter, dataset and model acceptance are NOT implemented. Exact application identifier: `reservation`. Use the existing shared model and Colibri runtime. No extra model or training job has been started.

## Actual architecture and records

Django/DRF, PostgreSQL, JWT authentication and django-simple-history; Next.js/React with MUI and Redux Toolkit. The authenticated frontend root is `src/app/dashboard/layout.tsx`. Existing text AI endpoints are separate from the planned permission-aware business assistant.

Verified entities: Building, Apartment, Reservation, Cost, dynamic PaymentSourceOption/CostCategoryOption, Local/LocalTypeOption/Loyer, HiltonReport/ApartmentRevenue/ManualLine and report settings. Buildings group apartments and commercial premises. Reservations reference an apartment, guest name, check-in/out, amount in MAD, payment source, returned-amount flag and notes. Records preserve their native creator/history relationships. The inspected schema has no company membership model or company-tab context; do not invent one.

Native routes include reservations, buildings, costs, calendar/planning/occupancy, balance, locaux, local planning/dashboard, Hilton reports, account settings and users. Apartments appear within the building-detail screen; there is no standalone apartment frontend route. Apartment navigation must resolve its authorized building page. Use actual route definitions; detailed report screens are not arbitrary model-generated URLs.

## Permissions and security boundaries

`core/permissions.py` implements existing staff bypass and per-user read/create/edit/delete flags. `can_access_hilton_reports` is a distinct capability, and report settings are staff-only. Existing write views use these helpers. The assistant must revalidate them for each call, confirmation and history replay, including reports, navigation metadata and knowledge documents.

Ordinary read endpoints mostly require authenticated identity; the frontend has the native read flag. The assistant should respect that read flag as the user requested. There is no verified per-building membership restriction to invent. A selected building may narrow a query, but cannot grant permissions. Hilton-only report data, opening balances and manual adjustments must remain behind the dedicated flag and must not be exposed through another tool. Hilton create/update/delete are a native permission exception: these endpoints and the frontend screen use Hilton access, without the generic create/edit/delete flags. Any future supported action must model that actual capability separately, with exact confirmation and history; do not claim the generic flags describe these endpoints. Native deletion permits only the latest Hilton report.

One existing non-AI boundary needs explicit care: `ToggleAmountReturnedView` currently checks authentication and boolean input without calling the native edit-permission helper. Do not expose that endpoint as an unrestricted assistant mutation. Its inclusion would require enforcing the existing edit permission and exact confirmation. No existing view was changed during discovery.

## Native calculations and semantics

Reservation `nights` uses check-out minus check-in. Occupancy/date calculations are already implemented in native views and must be reused rather than approximated by the model. Search uses ReservationFilter for guest, apartment/building, payment source, arrival/departure dates, year/month and numeric comparisons; assistant arguments must be bounded and valid.

The Balance endpoint specifically includes Airbnb and Bank payment sources, grouped by arrival year, with returned/not-returned totals. That does not represent all cash receipts or profit. Ordinary dashboard revenue follows its existing reservation-date basis. Keep these definitions explicit in answers.

LocalDashboardView labels a value as benefit but computes it as paid rents for the selected year. The assistant should describe it as paid rent under the verified calculation, not infer accounting profit. Native local planning also synthesizes due-but-unrecorded rents for eligible months in the current year using rental start date; missing database rows do not necessarily mean no rent is due.

HiltonReport owns its special opening balance, payment-source totals, manual costs and adjustments. Native recalculation defines net balance using opening balance plus cash revenue minus adjustments and costs. Do not duplicate or reinterpret that calculation, and do not call a recalculation method that saves during a read-only query. The preview endpoint has different semantics: it returns opening balance plus gross revenue for its displayed net total, whereas saved-report recalculation uses cash revenue minus adjustments/costs. Preview also calls `HiltonReportSettings.load()`, which uses `get_or_create`; it is not guaranteed read-only. A future read tool should return the authorized saved report and clearly identify its period/version, rather than call preview and present it as an equivalent final report.

## Remaining work

- Finish view/serializer/filter/route coverage and source-only permission mapping.
- Register real bounded search/details/navigation/report tools and descriptive EN/FR shortcuts, with useful bare-command help.
- Use the same shared robot/chat component; omit a company-tab row because there is no company-tab feature.
- Reuse native forms and confirmed supported mutations with actor history; keep financial/status changes outside unsupported generic edits.
- Add persistent owner-scoped conversations, permission-aware knowledge and real middleware/security tests using synthetic fixtures.
- Generate a versioned synthetic curriculum only after tools are registered; freeze held-out scenarios before baseline and train serially after earlier gates.

The separate login dark-mode correction is already published and verified live. No other Réservation source, permissions, records or deployment settings were modified during this discovery.
