// background-chatgpt.js - ChatGPT API 관련 기능

// ChatGPT API로 번역
function translateWithChatGPT(tabId, text, prompt, options, sendResponse) {
    const model = options.serviceUrl || 'gpt-4o';
    const apiUrl = 'https://api.openai.com/v1/chat/completions';
    
    console.log('ChatGPT 번역 시작');
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${options.apiKey}`
        },
        body: JSON.stringify({
            model: model,
            messages: [
                {
                    role: "user",
                    content: prompt || `Translate to ${options.targetLang}: ${text}`
                }
            ],
            temperature: 0.7,
            max_tokens: 1024
        })
    })
    .then(async response => {
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error('ChatGPT API 에러 응답:', errorData);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('ChatGPT 응답 받음');
        
        if (data && data.choices && data.choices.length > 0 && data.choices[0].message && data.choices[0].message.content) {
            sendResponse({ translatedText: data.choices[0].message.content });
        } else {
            console.error('ChatGPT API 응답 형식 오류:', data);
            sendResponse({ error: '응답 형식이 올바르지 않습니다.' });
        }
    })
    .catch(error => {
        console.error('ChatGPT API 요청 오류:', error);
        sendResponse({ error: `API 오류: ${error.message}. 잠시 후 다시 시도해주세요.` });
    });
}

// 모듈 내보내기
globalThis.chatgptService = {
    translateWithChatGPT
};