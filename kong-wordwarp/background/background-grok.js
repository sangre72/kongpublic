// background-grok.js - Grok API 관련 기능

// Grok API로 번역
function translateWithGrok(tabId, text, prompt, options, sendResponse) {
    const apiUrl = 'https://api.x.ai/v1/chat/completions';
    
    console.log('Grok 번역 시작');
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${options.apiKey}`
        },
        body: JSON.stringify({
            model: "grok-3-mini-latest",
            messages: [
                {
                    role: "system",
                    content: "You are a helpful assistant that translates text."
                },
                {
                    role: "user",
                    content: prompt || `Translate to ${options.targetLang}: ${text}`
                }
            ],
            temperature: 0.7,
            max_tokens: 2000
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Grok API 응답 받음');
        
        if (data && data.choices && data.choices.length > 0 && data.choices[0].message && data.choices[0].message.content) {
            sendResponse({ translatedText: data.choices[0].message.content });
        } else {
            console.error('Grok API 응답 형식 오류:', data);
            sendResponse({ error: '응답 형식이 올바르지 않습니다.' });
        }
    })
    .catch(error => {
        console.error('Grok API 오류:', error);
        sendResponse({ error: `API 오류: ${error.message}. 잠시 후 다시 시도해주세요.` });
    });
}

// 모듈 내보내기
globalThis.grokService = {
    translateWithGrok
};