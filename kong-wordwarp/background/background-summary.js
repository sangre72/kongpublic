// background-summary.js - 요약 기능 서비스

// 텍스트 요약 함수
async function summarizeText(tabId, text, url, title, sendResponse) {
    try {
        const settings = await globalThis.settingsService.getSettings();
        
        // API 키 확인
        if (!settings.apiKey) {
            console.warn('API 키가 설정되지 않았습니다.');
            sendResponse({ error: 'API_KEY_NOT_SET' });
            return;
        }

        console.log('요약 시작');
        
        // 컨텍스트 정보 구성
        const context = {
            url: url || 'Unknown URL',
            title: title || 'Unknown Title'
        };
        
        // 요약 프롬프트 구성
        const prompt = `다음 텍스트를 한국어로 간결하게 요약해주세요. 원문의 20-30% 정도 길이로 줄이되, 주요 내용과 핵심 주장이 모두 포함되도록 해주세요. 전문 용어나 기술적 용어는 그대로 유지해주세요.

컨텍스트 정보:
URL: ${context.url}
제목: ${context.title}

텍스트:
${text}`;

        // API 요청 실행
        if (settings.service === 'claude') {
            globalThis.claudeService.translateWithPrompt(tabId, prompt, settings, sendResponse);
        } else if (settings.service === 'chatgpt') {
            globalThis.chatgptService.translateWithChatGPT(tabId, text, prompt, settings, sendResponse);
        } else if (settings.service === 'grok') {
            globalThis.grokService.translateWithGrok(tabId, text, prompt, settings, sendResponse);
        } else {
            console.warn(`요약 기능은 Claude, ChatGPT, Grok 모델만 지원합니다. 현재 서비스: ${settings.service}`);
            sendResponse({ error: `요약 기능은 Claude, ChatGPT, Grok 모델만 지원합니다.` });
        }
    } catch (error) {
        console.error('요약 처리 오류:', error.message);
        sendResponse({ error: `요약 처리 오류: ${error.message}` });
    }
}

// 모듈 내보내기
globalThis.summaryService = {
    summarizeText
};