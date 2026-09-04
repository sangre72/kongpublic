// background-claude.js - Claude API 관련 기능

// Claude API로 번역
async function translateWithClaude(tabId, text, options = {}, sendResponse) {
    try {
        // Claude 설정 확인
        if (!options.apiKey) {
            console.warn('Claude API 키가 설정되지 않았습니다.');
            sendResponse({ error: 'API_KEY_NOT_SET' });
            return;
        }

        console.log('Claude 번역 시작');

        // Claude API 요청 데이터 구성
        const data = {
            model: "claude-3-5-sonnet-20240620",
            max_tokens: 4000,
            messages: [
                {
                    role: "user",
                    content: `Translate the following text from ${options.sourceLang === 'auto' ? 'detected language' : options.sourceLang} to ${options.targetLang}:\n\n${text}`
                }
            ]
        };

        const response = await fetch(options.serviceUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01',
                'x-api-key': options.apiKey,
                'anthropic-dangerous-direct-browser-access': 'true'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.text();
            console.error(`Claude API 오류: ${response.status} - ${errorData}`);
            sendResponse({ error: `Claude API 오류: ${response.status} - ${errorData}` });
            return;
        }

        const result = await response.json();
        console.log('Claude 응답 받음');
        
        if (result.content && Array.isArray(result.content) && result.content.length > 0) {
            sendResponse({ translatedText: result.content[0].text });
        } else {
            console.error('번역 결과가 없습니다.');
            sendResponse({ error: '번역 결과가 없습니다.' });
        }
    } catch (error) {
        console.error('Claude 번역 오류:', error.message);
        sendResponse({ error: `Claude 번역 오류: ${error.message}` });
    }
}

// 프롬프트 기반 번역 함수
function translateWithPrompt(tabId, prompt, options, sendResponse) {
    const apiUrl = 'https://api.anthropic.com/v1/messages';
    
    console.log('Claude 프롬프트 번역 시작');
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01',
            'x-api-key': options.apiKey,
            'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify({
            model: "claude-3-5-haiku-20241022",
            max_tokens: 1024,
            temperature: 0.7,
            messages: [
                {
                    role: "user",
                    content: prompt
                }
            ],
            stream: false
        })
    })
    .then(async response => {
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error('API 에러 응답:', errorData);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Claude API 응답 받음');
        
        if (data && data.content && Array.isArray(data.content) && data.content[0] && data.content[0].text) {
            sendResponse({ translatedText: data.content[0].text });
        } else {
            console.error('API 응답 형식 오류:', data);
            sendResponse({ error: '응답 형식이 올바르지 않습니다.' });
        }
    })
    .catch(error => {
        console.error('API 요청 오류:', error);
        sendResponse({ error: `API 오류: ${error.message}. 잠시 후 다시 시도해주세요.` });
    });
}

// 모듈 내보내기
globalThis.claudeService = {
    translateWithClaude,
    translateWithPrompt
};