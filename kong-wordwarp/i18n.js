// i18n.js - 다국어 처리 유틸리티 함수

// Language code utils
function getISOLanguageCode(langCode) {
    if (!langCode) return 'en';
    
    // 중국어 특수 처리
    if (langCode.startsWith('zh')) {
        // 번체 중국어 (zh-TW, zh-HK)
        if (langCode.includes('TW') || langCode.includes('HK')) {
            return 'zh-TW';
        }
        // 간체 중국어 기본값
        return 'zh-CN';
    }
    
    // 일반적인 코드 처리 (e.g., 'ko-KR' -> 'ko')
    const baseCode = langCode.split('-')[0].toLowerCase();
    
    // 특수 언어 코드 매핑
    const codeMap = {
        'nb': 'no', // 노르웨이어 부크몰
        'nn': 'no'  // 노르웨이어 니노르스크
    };
    
    return codeMap[baseCode] || baseCode;
}

// 시스템 언어 감지
function detectSystemLanguage() {
    const browserLang = navigator.language || navigator.userLanguage || 'en';
    const langCode = getISOLanguageCode(browserLang);
    
    // 지원되는 언어 목록에서 확인
    return isLanguageSupported(langCode) ? langCode : 'en';
}

// 지원되는 언어인지 확인
function isLanguageSupported(langCode) {
    return Object.keys(allLanguages).includes(langCode);
}

// 지원되는 언어 코드 목록 반환
function getSupportedLanguages() {
    return Object.keys(allLanguages);
}

// 언어 모듈 동적 로드
async function loadLanguageModule(langCode) {
    try {
        return await import(`./languages/${langCode}.js`);
    } catch (error) {
        console.error(`Failed to load language module for ${langCode}:`, error);
        // 기본값으로 영어 모듈 로드
        return await import('./languages/en.js');
    }
}

// 다국어 메시지 반환
function i18n(key, lang) {
    const language = lang || currentLanguage;
    const langData = allLanguages[language] || allLanguages.en;
    
    return langData[key] || allLanguages.en[key] || key;
}

// 언어 데이터를 모두 모으는 객체
const allLanguages = {};

// 언어 모듈 초기화 함수
async function initializeLanguages() {
    // 모든 언어 모듈을 가져와서 allLanguages에 추가
    try {
        const languages = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'is', 'it', 'ja', 'ko', 'lt', 'nl', 'no', 'pl', 'pt', 'ro', 'sl', 'sv', 'th', 'tr', 'zh-CN', 'zh-TW'];
        
        for (const lang of languages) {
            try {
                const module = await import(`./languages/${lang}.js`);
                allLanguages[lang] = module.default;
            } catch (error) {
                console.warn(`Could not load language module for ${lang}:`, error);
            }
        }
    } catch (error) {
        console.error('Failed to initialize languages:', error);
    }
}

// 현재 언어 설정
let currentLanguage = detectSystemLanguage();

// 언어 변경 함수
function setLanguage(langCode) {
    if (isLanguageSupported(langCode)) {
        currentLanguage = langCode;
        return true;
    }
    return false;
}

// 초기화
initializeLanguages().then(() => {
    console.log('언어 모듈 초기화 완료');
    console.log('시스템 언어 감지:', currentLanguage);
});

export {
    i18n,
    setLanguage,
    detectSystemLanguage,
    getSupportedLanguages,
    currentLanguage,
    allLanguages
};