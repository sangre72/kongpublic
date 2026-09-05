// background-deepl.js - DeepL API 관련 기능

// DeepL API로 번역 (Free 버전)
async function translateWithDeepL(tabId, text, options = {}, sendResponse) {
    if (!text || text.trim().length === 0) {
        const error = '번역할 텍스트가 없습니다.';
        console.error(error);
        sendResponse({ error });
        return;
    }
    console.error(text);
    if (text.includes("Do not write any other notes. Only subtitles. ")) {
        text = text.replace("Do not write any other notes. Only subtitles. ", "");
    }
    try {
        // DeepL 설정 확인
        if (!options.apiKey) {
            const error = 'DeepL Free API 키가 설정되지 않았습니다.';
            console.error(error);
            sendResponse({ error: 'API_KEY_NOT_SET' });
            return;
        }

        if (options.debug) {
            console.log('DeepL Free 번역 시작:', {
                textLength: text.length,
                targetLang: options.targetLang,
                apiUrl: options.serviceUrl
            });
        }

        // URL 확인 - 반드시 api-free.deepl.com을 사용해야 함
        const apiUrl = 'https://api-free.deepl.com/v2/translate';
        
        // DeepL API 요청 데이터 구성
        const data = {
            text: [text],
            target_lang: options.targetLang.toUpperCase()
        };

        // 소스 언어가 'auto'가 아닌 경우에만 추가
        if (options.sourceLang && options.sourceLang !== 'auto') {
            data.source_lang = options.sourceLang.toUpperCase();
        }

        // 타임아웃 설정 (15초)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `DeepL-Auth-Key ${options.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                signal: controller.signal
            });

            // 타임아웃 취소
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();

                let errorMessage = `DeepL API 오류 (${response.status})`;

                // 특정 오류에 대한 사용자 친화적인 메시지
                if (response.status === 403) {
                    if (errorText.includes('Wrong endpoint')) {
                        errorMessage = `${chrome.i18n.getMessage('deepl_free_api_key_warning')}`;
                    } else {
                        errorMessage = `${chrome.i18n.getMessage('deepl_free_api_key_error')}`;
                    }
                } else if (response.status === 456) {
                    errorMessage = '월간 번역 한도를 초과했습니다.';
                } else if (response.status === 429) {
                    errorMessage = '너무 많은 요청을 보냈습니다. 잠시 후 다시 시도하세요.';
                } 

                sendResponse({ error: errorMessage });
                return;
            }
            console.log('DeepL API 응답:', response);

            const result = await response.json();

            if (options.debug) {
                console.log('DeepL 응답:', result);
            }

            if (result.translations && result.translations.length > 0) {
                sendResponse({ 
                    translatedText: result.translations[0].text,
                    detectedLanguage: result.translations[0].detected_source_language
                });
            } else {
                sendResponse({ error: '번역 결과가 없습니다.' });
            }
        } catch (fetchError) {
            clearTimeout(timeoutId);

            let errorMessage = '번역 요청 중 오류가 발생했습니다.';
            if (fetchError.name === 'AbortError') {
                errorMessage = '번역 요청 시간이 초과되었습니다. 네트워크 연결을 확인하세요.';
            }

            console.error('DeepL API 요청 오류:', fetchError);
            sendResponse({ error: errorMessage });
        }
    } catch (error) {
        console.error('DeepL 번역 처리 오류:', error);
        sendResponse({ error: '번역 처리 중 오류가 발생했습니다.' });
    }
}

// DeepL Pro API로 번역
async function translateWithDeepLPro(tabId, text, options = {}, sendResponse) {
    try {
        // DeepL 설정 확인
        if (!options.apiKey) {
            console.warn('DeepL Pro API 키가 설정되지 않았습니다.');
            sendResponse({ error: 'API_KEY_NOT_SET' });
            return;
        }
        if (text.includes("Do not write any other notes. Only subtitles. ")) {
            text = text.replace("Do not write any other notes. Only subtitles. ", "");
        }

        console.log('DeepL Pro 번역 시작');

        // URL 확인 - 반드시 api.deepl.com을 사용해야 함
        if (!options.serviceUrl.includes('api.deepl.com') || options.serviceUrl.includes('api-free.deepl.com')) {
            console.warn('잘못된 DeepL Pro API URL입니다. api.deepl.com으로 수정합니다.');
            options.serviceUrl = 'https://api.deepl.com/v2/translate';
        }

        // DeepL API 요청 데이터 구성
        const data = {
            text: [text],
            target_lang: options.targetLang.toUpperCase()
        };

        // 소스 언어가 'auto'가 아닌 경우에만 추가
        if (options.sourceLang !== 'auto') {
            data.source_lang = options.sourceLang.toUpperCase();
        }

        const response = await fetch(options.serviceUrl, {
            method: 'POST',
            headers: {
                'Authorization': `DeepL-Auth-Key ${options.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.text();
            console.error(`DeepL Pro API 오류: ${response.status} - ${errorData}`);
            
            // 오류가 엔드포인트 관련 오류인 경우 추가 안내
            if (errorData.includes('Wrong endpoint')) {
                console.warn('유료 API 키에는 api.deepl.com 엔드포인트를, 무료 API 키에는 api-free.deepl.com 엔드포인트를 사용해야 합니다.');
            }
            
            sendResponse({ error: `DeepL Pro API 오류: ${response.status} - ${errorData}` });
            return;
        }

        const result = await response.json();
        console.log('DeepL Pro 응답 받음');
        
        if (result.translations && result.translations.length > 0) {
            sendResponse({ translatedText: result.translations[0].text });
        } else {
            console.error('번역 결과가 없습니다.');
            sendResponse({ error: '번역 결과가 없습니다.' });
        }
    } catch (error) {
        console.error('DeepL Pro 번역 오류:', error.message);
        sendResponse({ error: `DeepL Pro 번역 오류: ${error.message}` });
    }
}

// 모듈 내보내기
globalThis.deeplService = {
    translateWithDeepL,
    translateWithDeepLPro
};