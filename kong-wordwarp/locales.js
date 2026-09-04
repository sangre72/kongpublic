// locales.js - 다국어 지원을 위한 언어별 메시지 관리 파일

// ES 모듈로 사용하기 위한 type="module" 설정이 필요합니다
// 이 파일을 사용하는 HTML에 <script type="module" src="locales.js"></script> 형태로 포함해야 합니다

// 언어 코드 상수 정의
const LANGUAGES = {
    AR: 'ar',     // 아랍어
    ZH_CN: 'zh-CN', // 중국어 (간체)
    ZH_TW: 'zh-TW', // 중국어 (번체)
    HR: 'hr',     // 크로아티아어
    CS: 'cs',     // 체코어
    DA: 'da',     // 덴마크어 
    NL: 'nl',     // 네덜란드어
    EN: 'en',     // 영어
    FI: 'fi',     // 핀란드어
    FR: 'fr',     // 프랑스어
    DE: 'de',     // 독일어
    EL: 'el',     // 그리스어
    HE: 'he',     // 히브리어
    HU: 'hu',     // 헝가리어
    IS: 'is',     // 아이슬란드어
    IT: 'it',     // 이탈리아어
    JA: 'ja',     // 일본어
    KO: 'ko',     // 한국어
    LT: 'lt',     // 리투아니아어
    NO: 'no',     // 노르웨이어
    PL: 'pl',     // 폴란드어
    PT: 'pt',     // 포르투갈어
    RO: 'ro',     // 루마니아어
    SL: 'sl',     // 슬로베니아어
    ES: 'es',     // 스페인어
    SV: 'sv',     // 스웨덴어
    TH: 'th',     // 태국어
    TR: 'tr'      // 터키어
};

// 언어 데이터 캐시
const loadedLanguages = {};

// 현재 선택된 언어
let currentLanguage = null;

/**
 * 언어 코드 변환 (ISO 표준 형식으로)
 * @param {string} langCode - 변환할 언어 코드
 * @returns {string} 변환된 언어 코드
 */
function getISOLanguageCode(langCode) {
    if (!langCode) return LANGUAGES.EN;
    
    // 중국어 특수 처리
    if (langCode.startsWith('zh')) {
        // 번체 중국어 (zh-TW, zh-HK)
        if (langCode.includes('TW') || langCode.includes('HK')) {
            return LANGUAGES.ZH_TW;
        }
        // 간체 중국어 기본값
        return LANGUAGES.ZH_CN;
    }
    
    // 일반적인 코드 처리 (e.g., 'ko-KR' -> 'ko')
    const baseCode = langCode.split('-')[0].toLowerCase();
    
    // 특수 언어 코드 매핑
    const codeMap = {
        'nb': LANGUAGES.NO, // 노르웨이어 부크몰
        'nn': LANGUAGES.NO  // 노르웨이어 니노르스크
    };
    
    return codeMap[baseCode] || baseCode;
}

/**
 * 시스템 언어 감지
 * @returns {string} 감지된 언어 코드
 */
function detectSystemLanguage() {
    const browserLang = navigator.language || navigator.userLanguage || LANGUAGES.EN;
    const langCode = getISOLanguageCode(browserLang);
    return isLanguageSupported(langCode) ? langCode : LANGUAGES.EN;
}

/**
 * 지원되는 언어 목록 반환
 * @returns {Array} 지원되는 언어 코드 배열
 */
function getSupportedLanguages() {
    return Object.values(LANGUAGES);
}

/**
 * 언어 코드가 지원되는지 확인
 * @param {string} langCode - 확인할 언어 코드
 * @returns {boolean} 지원 여부
 */
function isLanguageSupported(langCode) {
    return Object.values(LANGUAGES).includes(langCode);
}

/**
 * 언어 모듈 로드
 * @param {string} langCode - 로드할 언어 코드
 * @returns {Promise<Object>} 언어 데이터 객체
 */
async function loadLanguage(langCode) {
    // 이미 로드된 언어면 바로 반환
    if (loadedLanguages[langCode]) {
        return loadedLanguages[langCode];
    }
    
    // 지원되지 않는 언어면 영어로 대체
    if (!isLanguageSupported(langCode)) {
        console.warn(`지원되지 않는 언어 코드: ${langCode}, 영어로 대체합니다.`);
        langCode = LANGUAGES.EN;
    }
    
    try {
        // 언어 파일 동적 로드
        const module = await import(`./languages/${langCode}.js`);
        loadedLanguages[langCode] = module.default;
        return module.default;
    } catch (error) {
        console.error(`언어 파일 로드 실패: ${langCode}`, error);
        
        // 실패 시 영어로 대체
        if (langCode !== LANGUAGES.EN) {
            console.warn(`영어 언어 파일로 대체합니다.`);
            return loadLanguage(LANGUAGES.EN);
        }
        
        // 영어도 실패하면 빈 객체 반환
        return {};
    }
}

/**
 * 현재 언어 설정
 * @param {string} langCode - 설정할 언어 코드
 * @returns {Promise<boolean>} 설정 성공 여부
 */
export async function setLanguage(langCode) {
    const normalizedLangCode = getISOLanguageCode(langCode);
    
    try {
        // 언어 모듈 로드
        await loadLanguage(normalizedLangCode);
        currentLanguage = normalizedLangCode;
        console.log(`언어가 ${currentLanguage}로 설정되었습니다.`);
        return true;
    } catch (error) {
        console.error(`언어 설정 실패: ${langCode}`, error);
        return false;
    }
}

/**
 * 언어 메시지 반환
 * @param {string} key - 메시지 키
 * @param {string} [lang] - 사용할 언어 코드 (미지정 시 현재 언어)
 * @returns {string} 번역된 메시지 또는 키 그대로 (번역 없을 경우)
 */
export async function getMessage(key, lang) {
    const langCode = lang || currentLanguage || await initLanguage();
    
    try {
        const langData = await loadLanguage(langCode);
        // 해당 키의 번역이 없으면 영어 번역 시도
        if (!langData[key] && langCode !== LANGUAGES.EN) {
            const enLangData = await loadLanguage(LANGUAGES.EN);
            return enLangData[key] || key;
        }
        return langData[key] || key;
    } catch (error) {
        console.error(`메시지 반환 실패: ${key}`, error);
        return key;
    }
}

/**
 * 초기 언어 설정
 * @returns {Promise<string>} 설정된 언어 코드
 */
export async function initLanguage() {
    if (!currentLanguage) {
        const sysLang = detectSystemLanguage();
        await setLanguage(sysLang);
    }
    return currentLanguage;
}

/**
 * 동기식 메시지 반환 (이미 로드된 언어만 가능)
 * @param {string} key - 메시지 키
 * @param {string} [lang] - 사용할 언어 코드 (미지정 시 현재 언어)
 * @returns {string} 번역된 메시지 또는 키 그대로 (번역 없을 경우)
 */
export function i18n(key, lang) {
    const langCode = lang || currentLanguage || LANGUAGES.EN;
    
    // 언어 데이터가 로드되지 않은 경우
    if (!loadedLanguages[langCode]) {
        // 영어로 대체 시도
        if (loadedLanguages[LANGUAGES.EN]) {
            return loadedLanguages[LANGUAGES.EN][key] || key;
        }
        return key;
    }
    
    return loadedLanguages[langCode][key] || 
           (loadedLanguages[LANGUAGES.EN] ? loadedLanguages[LANGUAGES.EN][key] : key) || 
           key;
}

// 초기화
console.log('다국어 지원 모듈 초기화...');
initLanguage().then(lang => {
    console.log(`시스템 언어 감지: ${lang}`);
});