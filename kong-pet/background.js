// KongPet background service worker
// a_3819 pivot: Gemini/AI DROPPED. Species use FIXED bundled krea2 art (no photo, no key).
// Only remaining network use = Coupang Partners affiliate (optional, user-supplied keys).

// ---------- Coupang Partners HMAC + product endpoints ----------
const COUPANG_HOST = 'https://api-gateway.coupang.com';
const COUPANG_PATH = '/v2/providers/affiliate_open_api/apis/openapi/v1/products/search';
const COUPANG_BEST_BASE = '/v2/providers/affiliate_open_api/apis/openapi/v1/products/bestcategories';
// Coupang category: 반려동물용품(pet supplies) root = 1010.
const PET_CATEGORY = 1010;

function cpDatetime() {
    const d = new Date();
    const p = n => String(n).padStart(2, '0');
    return d.getUTCFullYear().toString().slice(2) + p(d.getUTCMonth() + 1) + p(d.getUTCDate())
        + 'T' + p(d.getUTCHours()) + p(d.getUTCMinutes()) + p(d.getUTCSeconds()) + 'Z';
}
async function hmacSha256Hex(secret, message) {
    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
    const sig = await crypto.subtle.sign('HMAC', key, enc.encode(message));
    return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}
function normItems(data) {
    return (data?.data?.productData || data?.data || []).map(p => ({
        name: p.productName, price: p.productPrice, image: p.productImage, url: p.productUrl,
        discount: p.discountRate || 0, isRocket: p.isRocket
    }));
}
async function coupangGet(accessKey, secretKey, path, query) {
    const method = 'GET';
    const datetime = cpDatetime();
    const message = datetime + method + path + query;         // path + query (no '?')
    const signature = await hmacSha256Hex(secretKey, message);
    const authorization = `CEA algorithm=HmacSHA256, access-key=${accessKey}, signed-date=${datetime}, signature=${signature}`;
    const url = `${COUPANG_HOST}${path}${query ? '?' + query : ''}`;
    const res = await fetch(url, { method, headers: { 'Authorization': authorization, 'Content-Type': 'application/json;charset=UTF-8' } });
    if (!res.ok) throw new Error(`Coupang ${res.status}: ${await res.text()}`);
    return normItems(await res.json());
}
function coupangBest(ak, sk, catId, limit = 20) { return coupangGet(ak, sk, `${COUPANG_BEST_BASE}/${catId}`, `limit=${limit}`); }
function coupangSearch(ak, sk, keyword, limit = 20) { return coupangGet(ak, sk, COUPANG_PATH, `keyword=${encodeURIComponent(keyword)}&limit=${limit}`); }
function pickSlots(bestItems, searchItems) {
    const best = bestItems?.[0] || searchItems?.[0] || null;
    const discount = (searchItems?.length ? [...searchItems].sort((a, b) => (b.discount || 0) - (a.discount || 0))[0] : null);
    const fresh = searchItems?.length ? searchItems[searchItems.length - 1] : null;
    return { best, discount, fresh };
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'KONGPET_COUPANG') {
        (async () => {
            try {
                const { coupangAccessKey, coupangSecretKey } = await chrome.storage.sync.get(['coupangAccessKey', 'coupangSecretKey']);
                if (!coupangAccessKey || !coupangSecretKey) throw new Error('NO_COUPANG_KEY');
                const [bestItems, searchItems] = await Promise.all([
                    coupangBest(coupangAccessKey, coupangSecretKey, PET_CATEGORY, 20).catch(() => []),
                    coupangSearch(coupangAccessKey, coupangSecretKey, msg.keyword, 20).catch(() => [])
                ]);
                sendResponse({ ok: true, slots: pickSlots(bestItems, searchItems) });
            } catch (e) { sendResponse({ ok: false, error: String(e.message || e) }); }
        })();
        return true;
    }
});

chrome.action.onClicked?.addListener(() => chrome.runtime.openOptionsPage());
