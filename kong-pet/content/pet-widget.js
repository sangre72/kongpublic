// KongPet resident widget: floating avatar bottom-right.
// a_3817: per-species pose state-machine + Coupang 추천 용품 panel.
// a_3820: crossfade pose transitions (dual-layer) + varied/lifelike idle timing.
(function () {
    if (window.__kongpetLoaded) return; window.__kongpetLoaded = true;

    const REACT = {
        dog: ['멍! 🐾', '산책 갈까요?', '꼬리 흔들흔들~', '오늘도 좋은 하루!'],
        cat: ['냐옹~ 🐱', '식빵 굽는 중…', '쓰다듬어 주세요', '골골골~'],
        fish: ['뽀글뽀글 🐠', '반짝반짝!', '물이 시원해요~', '헤엄헤엄~']
    };
    const DAY = 86400000;
    let widget, bubble, panel, pet, poseKeys = [], poseIdx = 0;
    let imgA, imgB, activeImg, idleTimer, curState = null, stage;

    function render(p) {
        if (!p || !p.poses) return;
        pet = p; poseKeys = Object.keys(p.poses); poseIdx = Math.max(0, poseKeys.indexOf('idle'));
        if (!widget) {
            stage = document.createElement('div'); stage.id = 'kongpet-stage';
            document.documentElement.appendChild(stage);
            widget = document.createElement('div'); widget.id = 'kongpet-widget'; widget.title = p.name || 'KongPet';
            widget.classList.add('kp-' + p.species);
            imgA = document.createElement('img'); imgB = document.createElement('img');
            imgA.alt = imgB.alt = p.name || 'pet';
            widget.appendChild(imgA); widget.appendChild(imgB);
            widget.addEventListener('click', react);
            document.documentElement.appendChild(widget);
            bubble = document.createElement('div'); bubble.id = 'kongpet-bubble'; document.documentElement.appendChild(bubble);
            activeImg = imgA;
            scheduleIdle();
        }
        // scene backdrop (optional)
        if (stage) stage.style.backgroundImage = p.bg ? `url("${p.bg}")` : '';
        // initial pose (no fade)
        curState = poseKeys[poseIdx];
        activeImg.src = pet.poses[curState] || pet.poses.idle;
        activeImg.classList.add('kp-on');
        loadCoupang();
    }

    // crossfade to a pose: load into the hidden layer, then swap opacity.
    function setPose(state) {
        const src = pet.poses[state]; if (!src || state === curState) return;
        curState = state;
        const next = (activeImg === imgA) ? imgB : imgA;
        const swap = () => { next.classList.add('kp-on'); activeImg.classList.remove('kp-on'); activeImg = next; };
        next.onload = swap;
        next.src = src;
        if (next.complete && next.naturalWidth) swap(); // cached
    }

    // varied idle timing: base hold jitters 5.5–9.5s; sometimes hold 'idle' twice (double-idle) → lifelike.
    function scheduleIdle() {
        clearTimeout(idleTimer);
        const delay = 5500 + Math.floor(Math.random() * 4000);
        idleTimer = setTimeout(() => {
            if (widget && poseKeys.length >= 2) {
                const cur = poseKeys[poseIdx];
                // 30% chance to linger on idle again instead of advancing
                if (cur !== 'idle' || Math.random() > 0.3) {
                    poseIdx = (poseIdx + 1) % poseKeys.length;
                }
                setPose(poseKeys[poseIdx]);
            }
            scheduleIdle();
        }, delay);
    }

    let hideT;
    function say(t) { if (!bubble) return; bubble.textContent = t; bubble.classList.add('show'); clearTimeout(hideT); hideT = setTimeout(() => bubble.classList.remove('show'), 2200); }

    function react() {
        widget.classList.remove('kongpet-react'); void widget.offsetWidth; widget.classList.add('kongpet-react');
        const lines = REACT[pet.species] || REACT.dog;
        say(lines[Math.floor(Math.random() * lines.length)]);
        // pop to a non-idle pose on click for feedback, then resume cycle
        const alt = poseKeys.find(k => k !== 'idle');
        if (alt) { poseIdx = poseKeys.indexOf(alt); setPose(alt); scheduleIdle(); }
    }

    // ---- Coupang 4-slot panel (cached once/day) ----
    function itemCard(it) {
        if (!it) return `<div class="kp-empty">상품 없음</div>`;
        return `<a class="kp-shop-item" href="${it.url}" target="_blank" rel="noopener">
            <img src="${it.image}" alt=""><div class="kp-txt"><div class="kp-shop-nm">${(it.name||'').slice(0,30)}</div>
            <div class="kp-shop-pr">${it.price ? it.price.toLocaleString()+'원' : ''}${it.discount ? ` <span class="kp-dc">-${it.discount}%</span>` : ''}</div></div></a>`;
    }
    function buildPanel(slots) {
        if (!panel) { panel = document.createElement('div'); panel.id = 'kongpet-shop'; document.documentElement.appendChild(panel); }
        const s = slots || {};
        panel.innerHTML =
            `<div class="kp-shop-hd">🛒 추천 용품 <span class="kp-min" id="kp-min">─</span></div>` +
            `<div class="kp-slot kp-ad"><div class="kp-slot-lbl">광고</div><div class="kp-ad-ph">광고 자리 (추후 제공)</div></div>` +
            `<div class="kp-slot"><div class="kp-slot-lbl">오늘의 베스트</div>${itemCard(s.best)}</div>` +
            `<div class="kp-slot"><div class="kp-slot-lbl">할인 베스트</div>${itemCard(s.discount)}</div>` +
            `<div class="kp-slot"><div class="kp-slot-lbl">신상품</div>${itemCard(s.fresh)}</div>` +
            `<div class="kp-shop-ft">쿠팡파트너스 · 수수료를 받을 수 있음</div>`;
        const m = document.getElementById('kp-min');
        if (m) m.addEventListener('click', e => { e.stopPropagation(); panel.classList.toggle('kp-collapsed'); });
    }
    function loadCoupang() {
        if (!pet.keyword) return;
        chrome.storage.local.get(['kongpet_shop'], d => {
            const c = d.kongpet_shop;
            if (c && c.keyword === pet.keyword && (Date.now() - c.ts) < DAY) { buildPanel(c.slots); return; }
            chrome.runtime.sendMessage({ type: 'KONGPET_COUPANG', keyword: pet.keyword }, resp => {
                if (resp && resp.ok && resp.slots) {
                    chrome.storage.local.set({ kongpet_shop: { keyword: pet.keyword, slots: resp.slots, ts: Date.now() } });
                    buildPanel(resp.slots);
                }
                // NO_COUPANG_KEY / error -> silently skip (keys optional)
            });
        });
    }

    chrome.storage.local.get(['kongpet'], d => { if (d.kongpet) { render(d.kongpet); setTimeout(() => say(`안녕! 나는 ${d.kongpet.name} 🐾`), 1200); } });
    chrome.storage.onChanged.addListener((ch, area) => { if (area === 'local' && ch.kongpet?.newValue) render(ch.kongpet.newValue); });
})();
