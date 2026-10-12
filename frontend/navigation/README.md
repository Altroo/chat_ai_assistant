# Named list returns

`listReturn.ts` is shared by the six authorized application frontends. Identical copies live in each app at `src/utils/listReturn.ts`; the adjacent tests exercise the contract.

Native view/form return buttons supply their existing named list route to `listReturnUrl`. Only validated `page`, `page_size` and `ordering` parameters (including named grids) are restored from session storage. The key includes the list path and native company/store scope. Explicit destination parameters win. A direct record link with no saved state returns to the ordinary named list. Fresh list navigation starts with its own URL state.

Pagination hooks read Next.js `useSearchParams`, so the destination query is available before browser history commits. Page and sort controls use `history.replaceState(null, '', url)` to let Next synchronize its route state. Passing Next's internal history state would bypass that synchronization.

Current company/store selectors pass their effective scope when recording pagination, even when the initial list URL omits it. Navigation, permissions and records remain owned by the native app. Search text and business payloads are not stored. Existing in-memory search filters are not restored by this helper. Design Workflow's users table supports pagination; its unpaginated project board remains unchanged and has no invented sorting controls.

After changes, compare all six copies, run helper/hook and related view/form tests, then verify a real list/detail/list round trip with a non-default page size and sorting where supported. Include reload, fresh sidebar navigation, direct record links and scoped company/store tabs.
