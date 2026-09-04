// background-settings.js - 설정 관련 기능

// 설정 가져오기
function getSettings() {
    return new Promise((resolve) => {
        // 기본값 설정
        const defaultSettings = {
            translationService: 'deepl-free',
            apiKey: '',
            serviceUrl: 'https://api-free.deepl.com/v2/translate',
            
            // 각 서비스별 API 키
            claudeApiKey: '',
            chatgptApiKey: '',
            grokApiKey: '',
            deeplFreeApiKey: '',
            deeplProApiKey: '',
            
            // 언어 설정
            sourceLang: 'auto',
            targetLang: 'ko',
            preferredLanguages: [
                {code: 'ko', name: '한국어'},
                {code: 'en', name: '영어'}
            ],
            userLanguage: 'ko',
            
            // 디버그 모드
            debug: false
        };

        // 저장된 설정 가져오기
        chrome.storage.sync.get(defaultSettings, (items) => {
            console.log('저장된 설정:', items);

            // 결과 객체 생성
            const settings = {
                service: items.translationService,
                apiKey: '',  // 기본값 빈 문자열
                serviceUrl: '',  // 기본값 빈 문자열
                sourceLang: items.sourceLang,
                targetLang: items.targetLang,
                debug: items.debug,
                preferredLanguages: items.preferredLanguages,
                userLanguage: items.userLanguage
            };

            // 현재 선택된 서비스에 맞게 API 키와 URL 설정
            switch (items.translationService) {
                case 'claude':
                    settings.apiKey = items.claudeApiKey;
                    settings.serviceUrl = 'https://api.anthropic.com/v1/messages';
                    break;
                case 'chatgpt':
                    settings.apiKey = items.chatgptApiKey;
                    settings.serviceUrl = 'https://api.openai.com/v1/chat/completions';
                    break;
                case 'grok':
                    settings.apiKey = items.grokApiKey;
                    settings.serviceUrl = 'https://api.x.ai/v1/chat/completions';
                    break;
                case 'deepl-free':
                    settings.apiKey = items.deeplFreeApiKey;
                    settings.serviceUrl = 'https://api-free.deepl.com/v2/translate';
                    break;
                case 'deepl-pro':
                    settings.apiKey = items.deeplProApiKey;
                    settings.serviceUrl = 'https://api.deepl.com/v2/translate';
                    break;
                default:
                    console.warn('알 수 없는 번역 서비스:', items.translationService);
                    break;
            }

            if (settings.debug) {
                console.log('최종 설정:', {
                    ...settings,
                    apiKey: settings.apiKey ? '설정됨' : '없음'
                });
            }

            resolve(settings);
        });
    });
}

// 메시지 핸들러 함수
function sendProgressToContentScript(tabId, message) {
    // 탭 ID가 없는 경우 처리
    if (!tabId) {
        console.warn('탭 ID가 없어 진행 상태를 보낼 수 없습니다');
        return;
    }
    
    // 탭 존재 여부 확인
    chrome.tabs.get(tabId, function(tab) {
        if (chrome.runtime.lastError) {
            console.warn('탭이 존재하지 않습니다:', chrome.runtime.lastError.message);
            return;
        }
        
        try {
            chrome.tabs.sendMessage(tabId, {
                action: 'translationProgress',
                message: message
            }, function(response) {
                if (chrome.runtime.lastError) {
                    // 에러가 있더라도 무시
                    console.warn('진행 상태 전송 오류(무시됨):', chrome.runtime.lastError.message);
                }
            });
        } catch (error) {
            console.error('진행 상태 전송 중 오류 발생:', error);
        }
    });
}

function sendResponseToContentScript(tabId, translatedText, detectedLanguage) {
    // 탭 ID가 없는 경우 처리
    if (!tabId) {
        console.warn('탭 ID가 없어 번역 결과를 보낼 수 없습니다');
        return;
    }
    
    // 탭 존재 여부 확인
    chrome.tabs.get(tabId, function(tab) {
        if (chrome.runtime.lastError) {
            console.warn('탭이 존재하지 않습니다:', chrome.runtime.lastError.message);
            return;
        }
        
        try {
            chrome.tabs.sendMessage(tabId, {
                action: 'translationResult',
                translatedText: translatedText,
                detectedLanguage: detectedLanguage
            }, function(response) {
                if (chrome.runtime.lastError) {
                    // 에러가 있더라도 무시
                    console.warn('번역 결과 전송 오류(무시됨):', chrome.runtime.lastError.message);
                }
            });
        } catch (error) {
            console.error('번역 결과 전송 중 오류 발생:', error);
        }
    });
}

function sendDebugToContentScript(tabId, message) {
    // 먼저 탭이 존재하는지 확인
    if (!tabId) {
        console.warn('탭 ID가 없어 디버그 메시지를 보낼 수 없습니다:', message);
        return;
    }
    
    // 탭 존재 여부 확인
    chrome.tabs.get(tabId, function(tab) {
        if (chrome.runtime.lastError) {
            console.warn('탭이 존재하지 않습니다:', chrome.runtime.lastError.message);
            return;
        }
        
        try {
            chrome.tabs.sendMessage(tabId, {
                action: 'debug',
                message: message
            }, function(response) {
                if (chrome.runtime.lastError) {
                    // 에러가 있더라도 무시 (Receiving end does not exist 등의 에러)
                    console.warn('메시지 전송 오류(무시됨):', chrome.runtime.lastError.message);
                }
            });
        } catch (error) {
            console.error('메시지 전송 중 오류 발생:', error);
        }
    });
}

// 모듈 내보내기 - window 대신 globalThis 사용
globalThis.settingsService = {
    getSettings,
    sendProgressToContentScript,
    sendResponseToContentScript,
    sendDebugToContentScript
};