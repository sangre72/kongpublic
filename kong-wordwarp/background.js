// background.js
// 모듈화된 백그라운드 서비스들을 로드하는 메인 파일입니다.

// 확장 프로그램 아이콘 클릭시 옵션 페이지 열기
chrome.action.onClicked.addListener(() => {
    chrome.runtime.openOptionsPage();
});

// 서비스 모듈 로드
function loadServiceModules() {
    // 모듈 로드 순서는 의존성에 따라 중요합니다
    const moduleFiles = [
        'background/background-settings.js',
        'background/background-claude.js',
        'background/background-deepl.js', 
        'background/background-chatgpt.js',
        'background/background-grok.js',
        'background/background-summary.js',
        'background/background-core.js'
    ];

    try {
        // importScripts는 동기적으로 한 번에 여러 스크립트를 로드할 수 있습니다
        importScripts(...moduleFiles);
        console.log(`모든 모듈이 로드되었습니다 (${moduleFiles.length}/${moduleFiles.length})`);
    } catch (error) {
        console.error('모듈 로드 중 오류 발생:', error);
        // 모듈 로드에 실패했을 경우 각각의 모듈을 개별적으로 로드 시도
        for (const moduleFile of moduleFiles) {
            try {
                importScripts(moduleFile);
                console.log(`모듈 로드 완료: ${moduleFile}`);
            } catch (err) {
                console.error(`모듈 로드 실패: ${moduleFile}`, err);
            }
        }
    }
}

// 서비스 로딩 메시지
console.log('번역 확장 프로그램 백그라운드 서비스 초기화 중...');

// 서비스 워커 활성화 시 초기화
loadServiceModules();

// 서비스 워커 설치 이벤트 리스너
self.addEventListener('install', (event) => {
    console.log('서비스 워커 설치됨');
    self.skipWaiting(); // 즉시 활성화
});

// 서비스 워커 활성화 이벤트 리스너
self.addEventListener('activate', (event) => {
    console.log('서비스 워커 활성화됨');
});