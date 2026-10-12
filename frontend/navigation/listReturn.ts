/** Remember pagination only; return destinations always come from native application routes. */
export type ListScope = { company_id?: number | string | null; store_id?: number | string | null };
const PREFIX = 'list-pagination:v1:';
const PAGE_SIZES = new Set(['5', '10', '25', '50', '100']);

function storageKey(url: URL, scope: ListScope = {}) {
	return PREFIX + JSON.stringify([url.pathname, ...(['company_id', 'store_id'] as const).map(
		key => String(scope[key] ?? url.searchParams.get(key) ?? ''),
	)]);
}

function validParameter(key: string, value: string) {
	if (!/^(?:[a-z][a-z0-9_]*_)?(?:page|page_size|ordering)$/.test(key)) return false;
	if (key === 'page_size' || key.endsWith('_page_size')) return PAGE_SIZES.has(value);
	if (key === 'ordering' || key.endsWith('_ordering')) return /^-?[a-zA-Z_][a-zA-Z0-9_]{0,99}$/.test(value);
	return /^[1-9][0-9]{0,5}$/.test(value);
}

export function rememberListPagination(href: string, scope: ListScope = {}) {
	if (typeof window === 'undefined') return;
	try {
		const url = new URL(href, window.location.origin);
		if (url.origin !== window.location.origin) return;
		const values = [...url.searchParams].filter(([key, value]) => validParameter(key, value));
		window.sessionStorage.setItem(storageKey(url, scope), JSON.stringify(values));
	} catch {
		// Browsers that block storage still retain normal URL pagination/navigation.
	}
}

export function listReturnUrl(target: string): string {
	if (typeof window === 'undefined') return target;
	const absolute = /^https?:\/\//.test(target);
	if ((!target.startsWith('/') && !absolute) || target.startsWith('//') || target.includes('\\')) return target;
	try {
		const url = new URL(target, window.location.origin);
		if (url.origin !== window.location.origin || url.username || url.password) return target;
		const raw = window.sessionStorage.getItem(storageKey(url));
		if (!raw || raw.length > 8192) return target;
		const values: unknown = JSON.parse(raw);
		if (!Array.isArray(values) || values.length > 32) return target;
		let changed = false;
		for (const item of values) {
			if (!Array.isArray(item) || item.length !== 2) continue;
			const [key, value] = item;
			if (typeof key !== 'string' || typeof value !== 'string' || !validParameter(key, value) || url.searchParams.has(key)) continue;
			url.searchParams.set(key, value);
			changed = true;
		}
		return changed ? (absolute ? url.href : url.pathname + url.search + url.hash) : target;
	} catch {
		return target;
	}
}
