// background-core.js - 메시지 처리 및 메인 로직

// 메시지 리스너 설정
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const { action, text, prompt, url, title, targetLang, options = {} } = request;
    const tabId = sender?.tab?.id;

    if (!tabId) {
        console.error('유효한 탭 ID가 없습니다.');
        sendResponse({ error: '유효한 탭 ID가 없습니다.' });
        return false;
    }

    console.log('메시지 수신:', { action, textLength: text?.length });

    if (action === 'translate' || action === 'translateSubtitle') {
        // 설정 가져오기
        globalThis.settingsService.getSettings().then(settings => {
            if (!settings.apiKey) {
                console.error('API 키가 설정되지 않았습니다.');
                sendResponse({ error: 'API_KEY_NOT_SET' });
                return;
            }

            try {
                if (settings.debug) {
                    console.log('번역 요청:', {
                        service: settings.service,
                        hasApiKey: !!settings.apiKey,
                        targetLang: settings.targetLang
                    });
                }

                // 진행 상태 메시지 전송
                globalThis.settingsService.sendProgressToContentScript(tabId, '번역 중...');

                // 각 서비스별 번역 함수 호출
                switch (settings.service) {
                    case 'deepl-free':
                        globalThis.deeplService.translateWithDeepL(tabId, text, settings, sendResponse);
                        break;
                    case 'claude':
                        if (prompt) {
                            globalThis.claudeService.translateWithPrompt(tabId, prompt, settings, sendResponse);
                        } else {
                            globalThis.claudeService.translateWithClaude(tabId, text, settings, sendResponse);
                        }
                        break;
                    case 'deepl-pro':
                        globalThis.deeplService.translateWithDeepLPro(tabId, text, settings, sendResponse);
                        break;
                    case 'chatgpt':
                        globalThis.chatgptService.translateWithChatGPT(tabId, text, prompt, settings, sendResponse);
                        break;
                    case 'grok':
                        globalThis.grokService.translateWithGrok(tabId, text, prompt, settings, sendResponse);
                        break;
                    default:
                        const error = `지원하지 않는 번역 서비스: ${settings.service}`;
                        console.error(error);
                        sendResponse({ error });
                }
            } catch (error) {
                console.error('번역 처리 오류:', error);
                sendResponse({ error: `번역 처리 오류: ${error.message}` });
            }
        }).catch(error => {
            console.error('설정 로드 오류:', error);
            sendResponse({ error: '설정을 불러오는 중 오류가 발생했습니다.' });
        });

        // sendResponse는 비동기로 호출되므로 true 반환
        return true;
    } else if (action === 'summarize') {
        // 요약 기능 처리
        globalThis.summaryService.summarizeText(tabId, text, url, title, sendResponse);
        return true;
    }

    return false;
});