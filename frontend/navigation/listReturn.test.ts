import { listReturnUrl, rememberListPagination } from './listReturn';

beforeEach(() => { window.sessionStorage.clear(); window.history.replaceState({}, '', '/dashboard'); });
afterEach(() => jest.restoreAllMocks());

it('returns from a detail to page three of the named list, preserving size and ordering', () => {
	rememberListPagination('/dashboard/articles?company_id=7&page=3&page_size=25&ordering=-name');
	window.history.replaceState({}, '', '/dashboard/articles/42?company_id=7');
	expect(listReturnUrl('/dashboard/articles?company_id=7')).toBe('/dashboard/articles?company_id=7&page=3&page_size=25&ordering=-name');
});

it('keeps an AI deep-link return pointed at its named list when there is no saved state', () => {
	rememberListPagination('/dashboard/tasks?page=8');
	window.history.replaceState({}, '', '/dashboard/users/42');
	expect(listReturnUrl('/dashboard/users')).toBe('/dashboard/users');
});

it.each(['company_id', 'store_id'] as const)('never copies another %s scope', scope => {
	rememberListPagination('/dashboard/articles?page=3', { [scope]: 7 });
	expect(listReturnUrl(`/dashboard/articles?${scope}=8`)).toBe(`/dashboard/articles?${scope}=8`);
	expect(listReturnUrl(`/dashboard/articles?${scope}=7`)).toBe(`/dashboard/articles?${scope}=7&page=3`);
	expect(listReturnUrl('/dashboard/articles')).toBe('/dashboard/articles');
});

it('uses the effective authorized selector scope when the list URL has no scope', () => {
	rememberListPagination('/dashboard/articles?page=3&page_size=10', { store_id: 9 });
	expect(listReturnUrl('/dashboard/articles?store_id=9')).toContain('page=3');
});

it('preserves explicit destination values, other query parameters and its anchor', () => {
	rememberListPagination('/dashboard/users?page=3&page_size=25&ordering=name');
	expect(listReturnUrl('/dashboard/users?page=2&archived=false#results')).toBe('/dashboard/users?page=2&archived=false&page_size=25&ordering=name#results');
});

it('keeps independent grids and does not store search text or other data', () => {
	rememberListPagination('/dashboard/stock?page=3&requests_page=2&requests_page_size=5&search=private&token=secret');
	const result = listReturnUrl('/dashboard/stock');
	expect(result).toBe('/dashboard/stock?page=3&requests_page=2&requests_page_size=5');
	expect(JSON.stringify(window.sessionStorage)).not.toMatch(/private|secret/);
});

it('clears the old page when the user later visits the fresh list', () => {
	rememberListPagination('/dashboard/users?page=3&ordering=name');
	rememberListPagination('/dashboard/users');
	expect(listReturnUrl('/dashboard/users')).toBe('/dashboard/users');
});

it('rejects malformed saved data and never takes a destination or scope from storage', () => {
	rememberListPagination('/dashboard/users?page=3');
	const key = window.sessionStorage.key(0)!;
	window.sessionStorage.setItem(key, '{broken');
	expect(listReturnUrl('/dashboard/users')).toBe('/dashboard/users');
	window.sessionStorage.setItem(key, JSON.stringify([['page','3'], ['company_id','9'], ['returnTo','https://example.test'], ['ordering','javascript:alert(1)'], ['page_size','-1']]));
	expect(listReturnUrl('/dashboard/users')).toBe('/dashboard/users?page=3');
});

it('rejects invalid page/size values and a foreign-origin source', () => {
	rememberListPagination('/dashboard/users?page=-3&page_size=999&ordering=%3Cscript%3E');
	rememberListPagination('https://example.test/dashboard/users?page=5');
	expect(listReturnUrl('/dashboard/users')).toBe('/dashboard/users');
});

it('keeps normal navigation working when storage is blocked', () => {
	jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
	jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
	expect(() => rememberListPagination('/dashboard/users?page=3')).not.toThrow();
	expect(listReturnUrl('/dashboard/users')).toBe('/dashboard/users');
});

it('supports the same-origin absolute URLs used by production native routes', () => {
	const base = window.location.origin;
	rememberListPagination(`${base}/dashboard/users?page=3&page_size=10`);
	expect(listReturnUrl(`${base}/dashboard/users`)).toBe(`${base}/dashboard/users?page=3&page_size=10`);
	expect(listReturnUrl('https://elsewhere.test/dashboard/users')).toBe('https://elsewhere.test/dashboard/users');
	expect(listReturnUrl('//elsewhere.test/dashboard/users')).toBe('//elsewhere.test/dashboard/users');
});
