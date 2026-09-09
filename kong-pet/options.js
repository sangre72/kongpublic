// KongPet options (a_3819: fixed bundled art, no AI).
// species select -> preview bundled poses -> name -> store resident pet.
const POSES = { dog: ['idle', 'wag', 'tilt'], cat: ['idle', 'loaf', 'groom'], fish: ['idle', 'flare'] };
const POSE_LABEL = { idle: '기본', wag: '꼬리흔들', tilt: '갸웃', loaf: '식빵', groom: '세수', flare: '지느러미' };
const SP_KEYWORD = { dog: '강아지 용품', cat: '고양이 용품', fish: '어항 용품' };
// 16:9 scene backdrops per species (first = default)
const BGS = { dog: [['dog_field', '들녘']], cat: [['cat_home', '집']], fish: [['fish_aquarium', '어항'], ['fish_nightsea', '밤바다']] };

let species = null, bgKey = null;
const $ = id => document.getElementById(id);
const url = (sp, pose) => chrome.runtime.getURL(`assets/pets/${sp}/${pose}.png`);
const bgUrl = key => chrome.runtime.getURL(`assets/bg/${key}.jpg`);
function setStatus(el, msg, cls) { el.className = 'status' + (cls ? ' ' + cls : ''); el.innerHTML = msg; }

// ---- species select -> preview ----
document.querySelectorAll('.species').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.species').forEach(b => b.classList.remove('sel'));
        btn.classList.add('sel'); species = btn.dataset.sp;
        const grid = $('preview'); grid.innerHTML = '';
        POSES[species].forEach(pose => {
            const d = document.createElement('div'); d.className = 'opt';
            d.innerHTML = `<img src="${url(species, pose)}" alt="${pose}"><div class="lbl">${POSE_LABEL[pose] || pose}</div>`;
            grid.appendChild(d);
        });
        // bg scene picker (default = first)
        bgKey = BGS[species][0][0];
        const bgGrid = $('bgPreview'); bgGrid.innerHTML = '';
        BGS[species].forEach(([key, label], i) => {
            const d = document.createElement('div'); d.className = 'opt' + (i === 0 ? ' sel' : '');
            d.innerHTML = `<img src="${bgUrl(key)}" alt="${label}" style="aspect-ratio:16/9"><div class="lbl">${label}</div>`;
            d.addEventListener('click', () => { bgGrid.querySelectorAll('.opt').forEach(x => x.classList.remove('sel')); d.classList.add('sel'); bgKey = key; });
            bgGrid.appendChild(d);
        });
        $('apply').disabled = false;
    });
});

// ---- apply: build fixed pose map + store ----
$('apply').addEventListener('click', () => {
    if (!species) return;
    const petName = $('petName').value.trim() || '콩이';
    const poses = {};
    POSES[species].forEach(p => { poses[p] = url(species, p); });
    const pet = { species, name: petName, poses, avatar: poses.idle, bg: bgUrl(bgKey), bgKey, keyword: SP_KEYWORD[species], mood: 80, energy: 80, ts: Date.now() };
    chrome.storage.local.set({ kongpet: pet }, () => {
        setStatus($('applyStatus'), `"${petName}" 상주 캐릭터로 저장됨 ✓ (새 탭/새로고침 시 나타나요)`, 'ok');
        showCurrent(pet);
    });
});

// ---- coupang keys ----
$('saveKey').addEventListener('click', () => {
    const coupangAccessKey = $('coupangAccessKey').value.trim();
    const coupangSecretKey = $('coupangSecretKey').value.trim();
    chrome.storage.sync.set({ coupangAccessKey, coupangSecretKey }, () => {
        setStatus($('keyStatus'), '저장됨 ✓', 'ok');
    });
});

function showCurrent(pet) {
    $('currentCard').style.display = 'block';
    $('currentAvatar').src = pet.avatar; $('currentName').textContent = pet.name;
}

// ---- restore ----
chrome.storage.sync.get(['coupangAccessKey', 'coupangSecretKey'], d => {
    if (d.coupangAccessKey) $('coupangAccessKey').value = d.coupangAccessKey;
    if (d.coupangSecretKey) $('coupangSecretKey').value = d.coupangSecretKey;
});
chrome.storage.local.get(['kongpet'], d => {
    if (d.kongpet) {
        showCurrent(d.kongpet);
        const b = document.querySelector(`.species[data-sp="${d.kongpet.species}"]`);
        if (b) b.click();
    }
});
