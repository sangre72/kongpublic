/* kong-upbit-helper background service worker (a_3640).
 * WHY: content-script fetch to api.upbit.com is CORS-blocked(page origin upbit.com ≠ api.upbit.com,
 *   'Failed to fetch' 실증). MV3 host_permissions 로 cross-origin 을 허용받는 곳은 background(SW)이므로
 *   후보/캔들 fetch 를 여기서 수행하고 content-script 에 message 로 전달한다.
 */
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "kuh-candles") {
    const { market, unit, count } = msg;
    const url = `https://api.upbit.com/v1/candles/minutes/${unit}?market=${encodeURIComponent(market)}&count=${count}`;
    fetch(url, { headers: { accept: "application/json" } })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("api " + r.status))))
      .then((d) => sendResponse({ ok: true, data: d }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // async sendResponse
  }
  return false;
});
