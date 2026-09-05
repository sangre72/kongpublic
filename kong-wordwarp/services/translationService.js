// translationService.js
// 전역 변수로 TranslationService 클래스 노출
window.TranslationService = class {
    constructor() {
        this.isMenuVisible = false;
        this.menuTimeout = null;
        this.isCancelled = false;
        this.preferredLanguage = 'ko'; // 기본값
        this.isEnabled = true;  // 기본값은 활성화
        this.init();
    }

    init() {
        this.addStyles();
        this.loadPreferredLanguage();
        this.setupEventListeners();
        
        // 옵션 화면의 번역 기능 활성화 상태 가져오기
        chrome.storage.sync.get(['translationEnabled'], (result) => {
            this.isEnabled = result.translationEnabled !== false;  // 기본값은 true
            console.error('번역 서비스 초기 상태:', this.isEnabled ? '활성화' : '비활성화');
        });

        // 옵션 화면의 번역 기능 활성화 상태 변경 감지
        chrome.storage.onChanged.addListener((changes, namespace) => {
            if (namespace === 'sync' && changes.translationEnabled) {
                const newValue = changes.translationEnabled.newValue !== false;
                const oldValue = this.isEnabled;
                
                if (newValue !== oldValue) {
                    this.isEnabled = newValue;
                    console.error('번역 서비스 상태 변경:', this.isEnabled ? '활성화' : '비활성화');
                    
                    // 상태 변경 알림 표시
                    const notification = document.createElement('div');
                    notification.className = 'translate-ui translate-notification';
                    notification.textContent = this.isEnabled ? 
                        '번역 기능이 활성화되었습니다.' : 
                        '번역 기능이 비활성화되었습니다.';
                    notification.style.position = 'fixed';
                    notification.style.top = '10%';
                    notification.style.left = '50%';
                    notification.style.transform = 'translateX(-50%)';
                    notification.style.background = 'rgba(0, 0, 0, 0.8)';
                    notification.style.color = 'white';
                    notification.style.padding = '10px 20px';
                    notification.style.borderRadius = '5px';
                    notification.style.zIndex = '9999999';
                    notification.style.fontSize = '16px';
                    document.body.appendChild(notification);
                    
                    setTimeout(() => {
                        notification.remove();
                    }, 2000);
                }
            }
        });
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .translate-ui.translate-menu {
                position: absolute;
                z-index: 99999;
                background: white;
                color: #333333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                min-width: 150px;
            }
            
            .translate-ui.translate-button {
                display: block;
                width: 100%;
                padding: 8px;
                margin: 5px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                color: #333333;
                cursor: pointer;
                text-align: left;
                font-size: 14px;
            }
            
            .translate-ui.translate-button:hover {
                background: #f5f5f5;
            }
            
            .translate-ui.translate-result {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                padding: 20px;
                background: white;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                z-index: 10001;
                max-width: 800px;
                width: 90%;
                max-height: 80vh;
                overflow: auto;
            }
            
            .translate-ui.inline-translation {
                margin: 10px 0;
                padding: 10px;
                border-left: 3px solid #6B4EFF;
                background-color: #f5f5f5;
                color: #333;
                position: relative;
            }
            
            .translate-ui.inline-summary {
                margin: 10px 0;
                padding: 10px;
                border-left: 3px solid #FF6B4E;
                background-color: #fff9f5;
                color: #333;
                position: relative;
            }
            
            .original-term {
                color: #6B4EFF;
                text-decoration: underline;
                cursor: pointer;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    async loadPreferredLanguage() {
        const languages = await this.getPreferredLanguages();
        if (languages && languages.length > 0) {
            this.preferredLanguage = languages[0].code;
        }
    }

    setupEventListeners() {
        // 문서 클릭 이벤트 처리 (메뉴 외부 클릭 시 닫기)
        document.addEventListener('mousedown', (event) => {
            if (!event.target.closest('.translate-ui')) {
                this.hideTranslateMenu();
            }
        });

        // 마우스 버튼 동시 클릭으로 번역 기능 토글
        let middleButtonDown = false;

        document.addEventListener('mousedown', (event) => {
            if (event.button === 1) { // 중간(휠) 버튼
                middleButtonDown = true;
            } else {
                middleButtonDown = false;
            }

            if (middleButtonDown) {
                event.preventDefault(); // 기본 동작 방지
                
                // 현재 상태 가져오기
                chrome.storage.sync.get(['translationEnabled'], (result) => {
                    const newState = !(result.translationEnabled !== false);
                    
                    // 상태 업데이트
                    chrome.storage.sync.set({ translationEnabled: newState }, () => {
                        this.isEnabled = newState;
                        console.error('번역 서비스 상태 변경:', this.isEnabled ? '활성화' : '비활성화');
                        
                        // 상태 변경 알림 표시
                        const notification = document.createElement('div');
                        notification.className = 'translate-ui translate-notification';
                        notification.textContent = this.isEnabled ? 
                            '번역 기능이 활성화되었습니다.' : 
                            '번역 기능이 비활성화되었습니다.';
                        notification.style.position = 'fixed';
                        notification.style.top = '10%';
                        notification.style.left = '50%';
                        notification.style.transform = 'translateX(-50%)';
                        notification.style.background = 'rgba(0, 0, 0, 0.8)';
                        notification.style.color = 'white';
                        notification.style.padding = '10px 20px';
                        notification.style.borderRadius = '5px';
                        notification.style.zIndex = '9999999';
                        notification.style.fontSize = '16px';
                        document.body.appendChild(notification);
                        
                        setTimeout(() => {
                            notification.remove();
                        }, 2000);
                    });
                });
            }
        });

        document.addEventListener('mouseup', (event) => {
            if (event.button === 1) { // 중간(휠) 버튼
                middleButtonDown = false;
            }
        });

        // Ctrl+Shift+X 단축키로 번역 기능 토글
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.shiftKey && (event.code === 'KeyX' || event.key.toLowerCase() === 'x')) {
                event.preventDefault(); // 기본 동작 방지
                
                // 현재 상태 가져오기
                chrome.storage.sync.get(['translationEnabled'], (result) => {
                    const newState = !(result.translationEnabled !== false);
                    
                    // 상태 업데이트
                    chrome.storage.sync.set({ translationEnabled: newState }, () => {
                        this.isEnabled = newState;
                        console.error('번역 서비스 상태 변경:', this.isEnabled ? '활성화' : '비활성화');
                        
                        // 상태 변경 알림 표시
                        const notification = document.createElement('div');
                        notification.className = 'translate-ui translate-notification';
                        notification.textContent = this.isEnabled ? 
                            '번역 기능이 활성화되었습니다.' : 
                            '번역 기능이 비활성화되었습니다.';
                        notification.style.position = 'fixed';
                        notification.style.top = '10%';
                        notification.style.left = '50%';
                        notification.style.transform = 'translateX(-50%)';
                        notification.style.background = 'rgba(0, 0, 0, 0.8)';
                        notification.style.color = 'white';
                        notification.style.padding = '10px 20px';
                        notification.style.borderRadius = '5px';
                        notification.style.zIndex = '9999999';
                        notification.style.fontSize = '16px';
                        document.body.appendChild(notification);
                        
                        setTimeout(() => {
                            notification.remove();
                        }, 2000);
                    });
                });
            }
        });

        // 컨텍스트 메뉴 및 호버 기능
        let hoveredElement = null;

        document.addEventListener('mouseover', (event) => {
            if (event.target.closest('.translate-ui')) return;
            hoveredElement = event.target;
        });

        document.addEventListener('contextmenu', (event) => {
            // 번역 UI 요소에서는 기본 동작 허용
            if (event.target.closest('.translate-ui')) return;

            // 번역 기능이 비활성화되어 있으면 브라우저 기본 동작 허용
            if (!this.isEnabled) {
                console.error('번역 기능이 비활성화되어 있어 브라우저 기본 동작을 허용합니다.');
                return;
            }

            // 번역 기능이 활성화되어 있으면 항상 기본 동작 막기
            event.preventDefault();

            // 선택된 텍스트가 있는 경우
            const selectedText = window.getSelection().toString().trim();
            if (selectedText.length > 0) {
                const selection = window.getSelection();
                const range = selection.getRangeAt(0);
                
                const commonAncestor = range.commonAncestorContainer;
                const parentElement = commonAncestor.nodeType === Node.TEXT_NODE 
                    ? commonAncestor.parentElement 
                    : commonAncestor;
                
                const existingTranslation = parentElement.querySelector('.translate-ui.inline-translation');
                const existingSummary = parentElement.querySelector('.translate-ui.inline-summary');
                
                // Ctrl/Cmd + 우클릭인 경우 요약
                if (event.ctrlKey || event.metaKey) {
                    if (!existingSummary) {
                        this.summarizeInline(range, this.preferredLanguage);
                    }
                } 
                // 일반 우클릭인 경우 번역
                else {
                    if (!existingTranslation) {
                        this.translateInline(range, this.preferredLanguage);
                    }
                }
                return;
            }
            
            // 선택된 텍스트가 없고 호버된 요소가 있는 경우
            if (hoveredElement && hoveredElement.textContent.trim().length > 0) {
                const range = document.createRange();
                range.selectNodeContents(hoveredElement);
                
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                const selectedText = selection.toString().trim();
                if (selectedText.length === 0) return;
                
                const existingTranslation = hoveredElement.querySelector('.translate-ui.inline-translation');
                const existingSummary = hoveredElement.querySelector('.translate-ui.inline-summary');
                
                // Ctrl/Cmd + 우클릭인 경우 요약
                if (event.ctrlKey || event.metaKey) {
                    if (!existingSummary) {
                        this.summarizeInline(range, this.preferredLanguage);
                    }
                } 
                // 일반 우클릭인 경우 번역
                else {
                    if (!existingTranslation) {
                        this.translateInline(range, this.preferredLanguage);
                    }
                }
            }
        });

        // 단축키 지원 추가 (Alt+T 또는 Option+T로 선택 텍스트 번역)
        document.addEventListener('keydown', (e) => {
            if ((e.altKey || e.metaKey) && e.key === 't') {
                // 번역 기능이 비활성화되어 있으면 브라우저 기본 동작 허용
                if (!this.isEnabled) {
                    console.error('번역 기능이 비활성화되어 있어 브라우저 기본 동작을 허용합니다.');
                    return;
                }

                e.preventDefault();
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    const selectedText = selection.toString().trim();
                    if (selectedText.length > 0) {
                        this.translateInline(range, this.preferredLanguage);
                    }
                }
            }
        });
    }

    // 설정 가져오기 함수
    getSettings() {
        return new Promise((resolve) => {
            chrome.storage.sync.get({
                translationService: 'deepl-free',
                apiKey: '',
                serviceUrl: '',
                preferredLanguages: [
                    {code: 'ko', name: '한국어'},
                    {code: 'en', name: '영어'}
                ],
                deeplFreeApiKey: '',  // DeepL Free API 키 기본값 추가
                debug: false
            }, (result) => {
                // DeepL Free API가 선택된 경우 해당 키 사용
                if (result.translationService === 'deepl-free') {
                    result.apiKey = result.deeplFreeApiKey;
                    result.serviceUrl = 'https://api-free.deepl.com/v2/translate';
                }

                resolve(result);
            });
        });
    }

    // 선호 언어 가져오기
    getPreferredLanguages() {
        return new Promise((resolve) => {
            chrome.storage.sync.get({
                preferredLanguages: [
                    {name: '한국어', code: 'ko'},
                    {name: '영어', code: 'en'}
                ]
            }, (result) => {
                resolve(result.preferredLanguages);
            });
        });
    }

    // 언어 감지 유틸리티 함수
    detectLanguage(text) {
        // 한국어 감지 (한글 유니코드 범위: AC00-D7A3)
        const koreanRegex = /[\uAC00-\uD7A3]/;
        if (koreanRegex.test(text)) return "ko";
        
        // 일본어 감지 (히라가나, 카타카나 유니코드 범위)
        const japaneseRegex = /[\u3040-\u309F\u30A0-\u30FF]/;
        if (japaneseRegex.test(text)) return "ja";
        
        // 중국어 감지 (간체/번체 유니코드 범위)
        const chineseRegex = /[\u4E00-\u9FFF]/;
        if (chineseRegex.test(text)) return "zh";
        
        // 기타 언어는 기본적으로 영어로 가정
        return "en";
    }

    // URL 분석 및 도메인 컨텍스트 추출 함수
    analyzeUrlForContext() {
        const url = window.location.href;
        const domain = window.location.hostname;
        const path = window.location.pathname;
        
        let domainContext = '';
        
        if (domain.includes('github') || domain.includes('gitlab') || path.includes('/code/')) {
            domainContext = 'Programming/Software Development';
        } else if (domain.includes('medium') || domain.includes('blog') || domain.includes('velog')) {
            domainContext = 'Blog/Technical Article';
        } else if (domain.includes('stackoverflow') || domain.includes('stackexchange')) {
            domainContext = 'Programming Q&A';
        } else if (domain.includes('docs.') || path.includes('/docs/') || path.includes('/documentation/')) {
            domainContext = 'Technical Documentation/API Docs';
        } else if (domain.includes('academic') || domain.includes('research') || domain.includes('edu')) {
            domainContext = 'Academic/Research';
        } else if (domain.includes('news') || domain.includes('cnn') || domain.includes('bbc')) {
            domainContext = 'News/Current Affairs';
        } else if (domain.includes('finance') || domain.includes('invest') || domain.includes('stock')) {
            domainContext = 'Finance/Investment';
        } else if (domain.includes('medical') || domain.includes('health') || domain.includes('hospital')) {
            domainContext = 'Medical/Health';
        } else if (domain.includes('legal') || domain.includes('law') || domain.includes('court')) {
            domainContext = 'Legal';
        }
        
        if (!domainContext) {
            const title = document.title;
            domainContext = `Webpage Title: ${title}`;
        }
        
        return {
            url: url,
            domain: domain,
            path: path,
            domainContext: domainContext
        };
    }

    // 번역 메뉴 표시 함수
    async showTranslateMenu(event, hasImages = false) {
        this.hideTranslateMenu();
        
        const selection = window.getSelection().toString().trim();
        if (selection.length === 0) return;

        this.isMenuVisible = true;

        const menuContainer = document.createElement('div');
        menuContainer.className = 'translate-ui translate-menu';
        menuContainer.style.position = 'absolute';
        menuContainer.style.zIndex = '99999';
        menuContainer.style.background = 'white';
        menuContainer.style.color = '#333333';
        menuContainer.style.border = '1px solid #ccc';
        menuContainer.style.borderRadius = '4px';
        menuContainer.style.padding = '5px';
        menuContainer.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
        menuContainer.style.minWidth = '150px';
        menuContainer.style.opacity = '1';
        menuContainer.style.visibility = 'visible';
        menuContainer.style.display = 'block';

        const x = event.pageX;
        const y = event.pageY + 10;
        menuContainer.style.top = `${y}px`;
        menuContainer.style.left = `${x}px`;

        const languages = await this.getPreferredLanguages();
        const settings = await this.getSettings();
        const isDeepL = settings.translationService === 'deepl-free' || settings.translationService === 'deepl-pro';
        
        if (languages.length === 0) {
            languages.push(
                {name: '한국어', code: 'ko'},
                {name: '영어', code: 'en'}
            );
        }

        languages.forEach(lang => {
            const langButton = document.createElement('button');
            langButton.textContent = lang.name;
            langButton.className = 'translate-ui translate-button';
            langButton.style.display = 'block';
            langButton.style.width = '100%';
            langButton.style.padding = '8px';
            langButton.style.margin = '5px 0';
            langButton.style.border = '1px solid #ddd';
            langButton.style.borderRadius = '4px';
            langButton.style.background = 'white';
            langButton.style.color = '#333333';
            langButton.style.cursor = 'pointer';
            langButton.style.textAlign = 'left';
            langButton.style.fontSize = '14px';
            
            langButton.addEventListener('click', () => {
                this.hideTranslateMenu();
                this.translateText(selection, lang.code);
            });
            
            menuContainer.appendChild(langButton);
        });
        
        if (!isDeepL) {
            const divider = document.createElement('div');
            divider.style.borderTop = '1px solid #ddd';
            divider.style.margin = '10px 0';
            menuContainer.appendChild(divider);
            
            const summaryButton = document.createElement('button');
            summaryButton.textContent = chrome.i18n.getMessage('summarize') || '요약하기';
            summaryButton.className = 'translate-ui translate-button';
            summaryButton.style.display = 'block';
            summaryButton.style.width = '100%';
            summaryButton.style.padding = '8px';
            summaryButton.style.margin = '5px 0';
            summaryButton.style.border = '1px solid #ddd';
            summaryButton.style.borderRadius = '4px';
            summaryButton.style.background = '#f0f0f0';
            summaryButton.style.color = '#333333';
            summaryButton.style.cursor = 'pointer';
            summaryButton.style.textAlign = 'left';
            summaryButton.style.fontSize = '14px';
            
            summaryButton.addEventListener('click', () => {
                this.hideTranslateMenu();
                this.summarizeText(selection);
            });
            
            menuContainer.appendChild(summaryButton);
        }
        
        if (hasImages) {
            const imageTextButton = document.createElement('button');
            imageTextButton.textContent = chrome.i18n.getMessage('image_text_recognition') || '이미지 텍스트 인식';
            imageTextButton.className = 'translate-ui translate-button';
            imageTextButton.style.display = 'block';
            imageTextButton.style.width = '100%';
            imageTextButton.style.padding = '8px';
            imageTextButton.style.margin = '5px 0';
            imageTextButton.style.border = '1px solid #ddd';
            imageTextButton.style.borderRadius = '4px';
            imageTextButton.style.background = '#e3f2fd';
            imageTextButton.style.color = '#333333';
            imageTextButton.style.cursor = 'pointer';
            imageTextButton.style.textAlign = 'left';
            imageTextButton.style.fontSize = '14px';
            
            imageTextButton.addEventListener('click', async () => {
                this.hideTranslateMenu();
                const text = window.getSelection().toString().trim();
                // 이미지 텍스트 추출 함수 필요 (현재 미구현)
                // this.extractImageText(text);
            });
            
            menuContainer.appendChild(imageTextButton);
        }
        
        const inlineTranslateButton = document.createElement('button');
        inlineTranslateButton.textContent = chrome.i18n.getMessage('translate') || '번역';
        inlineTranslateButton.className = 'translate-ui translate-button';
        inlineTranslateButton.style.display = 'block';
        inlineTranslateButton.style.width = '100%';
        inlineTranslateButton.style.padding = '8px';
        inlineTranslateButton.style.margin = '5px 0';
        inlineTranslateButton.style.border = '1px solid #ddd';
        inlineTranslateButton.style.borderRadius = '4px';
        inlineTranslateButton.style.background = '#ede7f6';
        inlineTranslateButton.style.color = '#333333';
        inlineTranslateButton.style.cursor = 'pointer';
        inlineTranslateButton.style.textAlign = 'left';
        inlineTranslateButton.style.fontSize = '14px';
        
        inlineTranslateButton.addEventListener('click', () => {
            this.hideTranslateMenu();
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return;
            const range = selection.getRangeAt(0);
            this.translateInline(range, 'ko');
        });
        
        menuContainer.appendChild(inlineTranslateButton);

        try {
            document.body.appendChild(menuContainer);
            
            setTimeout(() => {
                const addedMenu = document.querySelector('.translate-ui.translate-menu');
                if (!addedMenu) {
                    document.body.appendChild(menuContainer);
                }
            }, 100);
        } catch (error) {
            console.error(chrome.i18n.getMessage('menu_addition_error') || '메뉴 추가 중 오류 발생:', error);
        }
    }

    // 번역 메뉴 숨기기 함수
    hideTranslateMenu() {
        document.querySelectorAll('.translate-ui.translate-menu').forEach(el => {
            el.remove();
        });
        this.isMenuVisible = false;
    }

    // 번역 함수
    translateText(text, targetLang) {
        const loadingPopup = this.createLoadingPopup('translate');
        document.body.appendChild(loadingPopup);

        const contextInfo = this.analyzeUrlForContext();
        const currentUrl = contextInfo.url;
        const pageTitle = document.title;

        const prompt = `
Current webpage: ${currentUrl}
Page title: ${pageTitle}
Context/Domain: ${contextInfo.domainContext}
Target language: ${targetLang}

Please translate the following text, considering the context of the webpage (${contextInfo.domainContext}) and maintaining appropriate terminology and style for this domain. 

IMPORTANT: Preserve ALL formatting exactly as in the original text, including:
1. Line breaks and paragraph divisions
2. Bullet points and numbered lists (ul, ol, li elements)
3. Headings and subheadings
4. Tables and table structures
5. Any HTML or markdown formatting elements
6. Indentation and spacing

For technical terms or specialized vocabulary, please include the original term in parentheses after the translation, like this: "번역된 용어 (original term)".

Text: ${text}`;

        this.isCancelled = false;
        this.safeSendMessage(
            { 
                action: 'translate', 
                text: text,
                prompt: prompt,
                targetLang: targetLang,
                model: 'claude-3-5-haiku'
            },
            (response) => {
                loadingPopup.remove();
                if (this.isCancelled) {
                    return;
                }
                
                if (response && (response.success || response.translatedText)) {
                    const translation = response.translation || response.translatedText;
                    this.showTranslationResult(text, translation, {
                        url: currentUrl,
                        title: pageTitle,
                        prompt: prompt,
                        response: translation,
                        targetLang: targetLang
                    });
                } else if (response && response.error === 'API_KEY_NOT_SET') {
                    this.showApiKeyError();
                } else if (response && this._isChromeBuiltinError(response.error)) {
                    this.showChromeBuiltinError(response.error);
                } else {
                    alert('Translation failed. Please check your settings: ' + (response ? response.error : 'No response'));
                }
            }
        );
    }

    // 로딩 팝업 생성 함수
    createLoadingPopup(type = 'translate') {
        const popup = document.createElement('div');
        popup.className = 'translate-ui translate-loading';
        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
        popup.style.background = 'white';
        popup.style.color = '#333';
        popup.style.border = '1px solid #ccc';
        popup.style.borderRadius = '8px';
        popup.style.padding = '20px';
        popup.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        popup.style.zIndex = '10001';
        popup.style.textAlign = 'center';
        
        let message = type === 'translate' ? 'Translating...' : 'Summarizing...';
        
        popup.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: center; color: #333333;">
            <div class="loading-spinner" style="border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; width: 20px; height: 20px; margin-right: 10px; animation: spin 1s linear infinite;"></div>
            <div>${message} (ESC to Cancel)</div>
          </div>
        `;
        
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.isCancelled = true;
                popup.remove();
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'info',
                        title: 'Canceled',
                        text: `${type === 'translate' ? 'Translation' : 'Summarization'} operation canceled.`,
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    alert(`${type === 'translate' ? 'Translation' : 'Summarization'} operation canceled.`);
                }
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
        
        popup.addEventListener('remove', () => {
            document.removeEventListener('keydown', escHandler);
        });
        
        return popup;
    }

    // 번역 결과 표시 함수
    showTranslationResult(originalText, translatedText, metadata) {
        const popup = document.createElement('div');
        popup.className = 'translate-ui translate-result';
        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
        popup.style.padding = '20px';
        popup.style.background = 'white';
        popup.style.color = '#333';
        popup.style.border = '1px solid #ccc';
        popup.style.borderRadius = '8px';
        popup.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
        popup.style.zIndex = '10001';
        popup.style.maxWidth = '800px';
        popup.style.width = '90%';
        popup.style.maxHeight = '80vh';
        popup.style.overflow = 'auto';

        popup.innerHTML = `
            <div style="position: relative; color: #333333; font-family: Arial, sans-serif;">
                <div style="position: absolute; top: -10px; right: -10px; display: flex;">
                    <button style="width: 24px; height: 24px; border-radius: 12px;
                               border: none; background: #f0f0f0; cursor: pointer;
                               display: flex; align-items: center; justify-content: center;
                               font-size: 14px; color: #666666; margin-right: 5px;"
                            id="copy-content-button" title="번역문 복사">📋</button>
                    <button style="width: 24px; height: 24px; border-radius: 12px;
                               border: none; background: #f0f0f0; cursor: pointer;
                               display: flex; align-items: center; justify-content: center;
                               font-size: 14px; color: #666666;"
                            id="close-button">✕</button>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <div style="font-weight: bold; color: #666666; margin-bottom: 5px;">원문</div>
                    <div id="original-content" style="padding: 10px; background: #f8f9fa; border-radius: 4px; 
                              font-family: Arial, sans-serif; color: #333333; white-space: pre-wrap; overflow-x: auto;"></div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <div style="font-weight: bold; color: #666666; margin-bottom: 5px;">번역</div>
                    <div id="translated-content" style="padding: 10px; background: #f8f9fa; border-radius: 4px;
                              font-family: Arial, sans-serif; color: #333333; white-space: pre-wrap; overflow-x: auto;"></div>
                </div>

                <div style="margin-bottom: 15px;">
                    <details>
                        <summary style="cursor: pointer; color: #666666; padding: 5px 0;">디버그 정보</summary>
                        <div style="margin-top: 10px; font-size: 12px; font-family: monospace; 
                                  white-space: pre-wrap; color: #333333;">
                            <div style="margin-bottom: 10px;">
                                <strong>페이지 URL:</strong>
                                <div style="padding: 5px; background: #f5f5f5; border-radius: 4px;">${metadata.url}</div>
                            </div>
                            <div style="margin-bottom: 10px;">
                                <strong>페이지 제목:</strong>
                                <div style="padding: 5px; background: #f5f5f5; border-radius: 4px;">${metadata.title}</div>
                            </div>
                            <div style="margin-bottom: 10px;">
                                <strong>대상 언어:</strong> ${metadata.targetLang}
                            </div>
                            <div style="margin-bottom: 10px;">
                                <strong>요청 프롬프트:</strong>
                                <div style="padding: 5px; background: #f5f5f5; border-radius: 4px;">${metadata.prompt}</div>
                            </div>
                            <div>
                                <strong>API 응답:</strong>
                                <div style="padding: 5px; background: #f5f5f5; border-radius: 4px;">${metadata.response}</div>
                            </div>
                        </div>
                    </details>
                </div>
                
                <div style="display: flex; justify-content: flex-end; margin-top: 15px; gap: 10px;">
                    <button id="copy-original"
                            style="padding: 5px 10px; border: 1px solid #ddd; border-radius: 4px;
                                   background: white; cursor: pointer; color: #333333;">원문 복사</button>
                    <button id="copy-translated"
                            style="padding: 5px 10px; border: 1px solid #ddd; border-radius: 4px;
                                   background: white; cursor: pointer; color: #333333;">번역문 복사</button>
                    <button id="copy-both"
                            style="padding: 5px 10px; border: 1px solid #ddd; border-radius: 4px;
                                   background: white; cursor: pointer; color: #333333;">둘다 복사</button>
                </div>
            </div>
        `;

        document.body.appendChild(popup);
        
        const originalContentDiv = popup.querySelector('#original-content');
        const translatedContentDiv = popup.querySelector('#translated-content');
        
        const isHTML = /<[a-z][\s\S]*>/i.test(originalText);
        
        if (isHTML) {
            originalContentDiv.innerHTML = originalText;
            translatedContentDiv.innerHTML = translatedText;
        } else {
            originalContentDiv.textContent = originalText;
            const processedText = this.processTranslatedText(translatedText);
            translatedContentDiv.innerHTML = processedText;
            
            translatedContentDiv.addEventListener('click', (e) => {
                if (e.target.classList.contains('original-term')) {
                    const term = e.target.getAttribute('data-term');
                    this.lookupTermDefinition(term, metadata.targetLang);
                }
            });
        }

        popup.querySelector('#close-button').addEventListener('click', () => popup.remove());
        
        // Add event listener for copy button in the header
        popup.querySelector('#copy-content-button').addEventListener('click', function() {
            this.copyToClipboard(translatedText, this, '번역문');
        }.bind(this));
        
        popup.querySelector('#copy-original').addEventListener('click', function() {
            this.copyToClipboard(originalText, this, '원문');
        }.bind(this));
        
        popup.querySelector('#copy-translated').addEventListener('click', function() {
            this.copyToClipboard(translatedText, this, '번역문');
        }.bind(this));

        popup.querySelector('#copy-both').addEventListener('click', function() {
            const combinedText = `${originalText}\t${translatedText}`;
            this.copyToClipboard(combinedText, this, '둘다');
        }.bind(this));

        const escKeyHandler = (e) => {
            if (e.key === 'Escape') {
                popup.remove();
                document.removeEventListener('keydown', escKeyHandler);
            }
        };
        document.addEventListener('keydown', escKeyHandler);

        const popupRemoveObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.removedNodes.length && mutation.removedNodes[0] === popup) {
                    document.removeEventListener('keydown', escKeyHandler);
                    popupRemoveObserver.disconnect();
                }
            });
        });

        popupRemoveObserver.observe(document.body, { childList: true });
    }

    // 번역된 텍스트 처리 함수
    processTranslatedText(text) {
        const pattern = /([^(]+) \(([^)]+)\)/g;
        return text.replace(pattern, (match, translatedTerm, originalTerm) => {
            return `<span class="translated-term">${translatedTerm} <span class="original-term" style="color: #6B4EFF; text-decoration: underline; cursor: pointer;" data-term="${originalTerm}">(${originalTerm})</span></span>`;
        });
    }

    // 클립보드 복사 함수
    copyToClipboard(text, button, type) {
        // a_3774: originalText를 상위 스코프에 선언(기존엔 then 내부 const라 catch 경로에서 ReferenceError)
        const originalText = button.textContent;
        navigator.clipboard.writeText(text).then(() => {
            button.textContent = `${type} 복사됨!`;
            button.style.background = '#e8f5e9';
            button.style.borderColor = '#81c784';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = 'white';
                button.style.borderColor = '#ddd';
            }, 2000);
        }).catch(err => {
            button.textContent = '복사 실패';
            button.style.background = '#ffebee';
            button.style.borderColor = '#e57373';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = 'white';
                button.style.borderColor = '#ddd';
            }, 2000);
        });
    }

    // API 키 오류 팝업
    showApiKeyError() {
        const popup = document.createElement('div');
        popup.className = 'translate-ui translate-error';
        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
        popup.style.padding = '20px';
        popup.style.background = 'white';
        popup.style.color = '#333';
        popup.style.border = '1px solid #ccc';
        popup.style.borderRadius = '8px';
        popup.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
        popup.style.zIndex = '10001';
        popup.style.maxWidth = '400px';
        popup.style.width = '90%';

        popup.innerHTML = `
            <div style="position: relative; color: #333333; font-family: Arial, sans-serif;">
                <button style="position: absolute; top: -10px; right: -10px; 
                             width: 24px; height: 24px; border-radius: 12px;
                             border: none; background: #f0f0f0; cursor: pointer;
                             display: flex; align-items: center; justify-content: center;
                             font-size: 14px; color: #666666;"
                        id="close-button">✕</button>
                
                <div style="margin-bottom: 20px; color: #d32f2f;">
                    <strong>API 키가 설정되지 않았습니다</strong>
                </div>
                
                <div style="margin-bottom: 20px; color: #333333;">
                    확장 프로그램 설정에서 Claude API 키를 입력해주세요.
                </div>

                <div style="text-align: center;">
                    <button id="go-to-options"
                            style="padding: 8px 16px; background: #6B4EFF; color: white;
                                   border: none; border-radius: 4px; cursor: pointer;">
                        설정 페이지로 이동
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(popup);

        popup.querySelector('#close-button').addEventListener('click', () => popup.remove());
        popup.querySelector('#go-to-options').addEventListener('click', () => {
            if (chrome.runtime.openOptionsPage) {
                chrome.runtime.openOptionsPage();
            } else {
                window.open(chrome.runtime.getURL('options.html'));
            }
            popup.remove();
        });

        const escKeyHandler = (e) => {
            if (e.key === 'Escape') {
                popup.remove();
                document.removeEventListener('keydown', escKeyHandler);
            }
        };
        document.addEventListener('keydown', escKeyHandler);
    }

    // 텍스트 요약 함수
    summarizeText(text) {
        const loadingPopup = this.createLoadingPopup('summarize');
        document.body.appendChild(loadingPopup);
        
        const contextInfo = this.analyzeUrlForContext();
        const currentUrl = contextInfo.url;
        const pageTitle = document.title;
        
        const prompt = `
Current webpage: ${currentUrl}
Page title: ${pageTitle}
Context/Domain: ${contextInfo.domainContext}

Please provide a concise summary of the following text in Korean, reducing it to 20-30% of the original length. Consider the context of the webpage (${contextInfo.domainContext}) when summarizing.

Retain the main points and arguments, preserving the tone and style where suitable. Organize the information logically, maintaining the paragraph structure if applicable, and include key technical terms from the original.

Text to summarize: ${text}`;

        this.isCancelled = false;
        this.safeSendMessage({
            action: 'translate',
            prompt: prompt,
            model: 'claude-3-5-haiku'
        }, response => {
            loadingPopup.remove();
            if (this.isCancelled) {
                return;
            }
            
            if (response.translatedText === 'API_KEY_NOT_SET') {
                this.showApiKeyError();
            } else if (response.translatedText) {
                this.showSummaryResult(text, response.translatedText, {
                    url: currentUrl,
                    title: pageTitle,
                    prompt: prompt,
                    response: response.translatedText
                });
            }
        });
    }

    // 요약 결과 표시 함수
    showSummaryResult(originalText, summaryText, metadata) {
        const popup = document.createElement('div');
        popup.className = 'translate-ui translate-result';
        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
        popup.style.width = '80%';
        popup.style.maxWidth = '800px';
        popup.style.maxHeight = '80vh';
        popup.style.background = 'white';
        popup.style.color = '#333';
        popup.style.border = '1px solid #ccc';
        popup.style.borderRadius = '8px';
        popup.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
        popup.style.zIndex = '10001';
        popup.style.overflow = 'hidden';
        popup.style.display = 'flex';
        popup.style.flexDirection = 'column';
        
        const header = document.createElement('div');
        header.style.padding = '15px';
        header.style.borderBottom = '1px solid #eee';
        header.style.display = 'flex';
        header.style.justifyContent = 'space-between';
        header.style.alignItems = 'center';
        header.style.color = '#333333';
        
        const title = document.createElement('div');
        title.textContent = chrome.i18n.getMessage('summary_result') || '요약 결과';
        title.style.fontWeight = 'bold';
        title.style.fontSize = '16px';
        title.style.color = '#333333';
        
        // 닫기 버튼
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.style.background = 'none';
        closeButton.style.border = 'none';
        closeButton.style.fontSize = '20px';
        closeButton.style.cursor = 'pointer';
        closeButton.style.padding = '0 5px';
        closeButton.style.color = '#666666';
        
        closeButton.addEventListener('click', () => popup.remove());
        
        // 복사 버튼 추가
        const copyButton = document.createElement('button');
        copyButton.innerHTML = '📋';
        copyButton.title = chrome.i18n.getMessage('copy_summary') || '요약 복사';
        copyButton.style.background = 'none';
        copyButton.style.border = 'none';
        copyButton.style.fontSize = '16px';
        copyButton.style.cursor = 'pointer';
        copyButton.style.padding = '0 5px';
        copyButton.style.marginRight = '5px';
        copyButton.style.color = '#666666';
        
        copyButton.addEventListener('click', () => {
            this.copyToClipboard(summaryText, copyButton, '요약');
        });
        
        // 버튼 컨테이너 생성
        const buttonContainer = document.createElement('div');
        buttonContainer.style.display = 'flex';
        buttonContainer.style.alignItems = 'center';
        
        buttonContainer.appendChild(copyButton);
        buttonContainer.appendChild(closeButton);
        
        header.appendChild(title);
        header.appendChild(buttonContainer);
        
        const content = document.createElement('div');
        content.style.padding = '15px';
        content.style.overflowY = 'auto';
        content.style.maxHeight = 'calc(80vh - 130px)';
        content.style.color = '#333333';
        
        const originalContainer = document.createElement('div');
        originalContainer.style.marginBottom = '15px';
        
        const originalHeader = document.createElement('div');
        originalHeader.style.display = 'flex';
        originalHeader.style.justifyContent = 'space-between';
        originalHeader.style.alignItems = 'center';
        originalHeader.style.cursor = 'pointer';
        originalHeader.style.padding = '8px';
        originalHeader.style.background = '#f5f5f5';
        originalHeader.style.borderRadius = '4px';
        originalHeader.style.color = '#333333';
        
        const originalTitle = document.createElement('div');
        originalTitle.textContent = chrome.i18n.getMessage('original_text') || '원본 텍스트';
        originalTitle.style.fontWeight = 'bold';
        originalTitle.style.color = '#333333';
        
        const toggleButton = document.createElement('span');
        toggleButton.textContent = '▼';
        toggleButton.style.color = '#666666';
        
        originalHeader.appendChild(originalTitle);
        originalHeader.appendChild(toggleButton);
        
        const originalTextDiv = document.createElement('div');
        originalTextDiv.textContent = originalText;
        originalTextDiv.style.padding = '8px';
        originalTextDiv.style.marginTop = '5px';
        originalTextDiv.style.color = '#333333';
        originalTextDiv.style.border = '1px solid #eee';
        originalTextDiv.style.borderRadius = '4px';
        originalTextDiv.style.whiteSpace = 'pre-wrap';
        originalTextDiv.style.fontSize = '14px';
        
        originalHeader.addEventListener('click', () => {
            if (originalTextDiv.style.display === 'none') {
                originalTextDiv.style.display = 'block';
                toggleButton.textContent = '▲';
            } else {
                originalTextDiv.style.display = 'none';
                toggleButton.textContent = '▼';
            }
        });
        
        originalContainer.appendChild(originalHeader);
        originalContainer.appendChild(originalTextDiv);
        
        const summaryContainer = document.createElement('div');
        summaryContainer.style.marginBottom = '15px';
        
        const summaryHeader = document.createElement('div');
        summaryHeader.textContent = chrome.i18n.getMessage('summary') || '요약';
        summaryHeader.style.fontWeight = 'bold';
        summaryHeader.style.padding = '8px';
        summaryHeader.style.background = '#f5f5f5';
        summaryHeader.style.borderRadius = '4px';
        summaryHeader.style.color = '#333333';
        
        const summaryTextDiv = document.createElement('div');
        summaryTextDiv.textContent = summaryText;
        summaryTextDiv.style.padding = '10px';
        summaryTextDiv.style.border = '1px solid #eee';
        summaryTextDiv.style.borderRadius = '4px';
        summaryTextDiv.style.marginTop = '5px';
        summaryTextDiv.style.whiteSpace = 'pre-wrap';
        summaryTextDiv.style.fontSize = '14px';
        summaryTextDiv.style.color = '#333333';
        
        summaryContainer.appendChild(summaryHeader);
        summaryContainer.appendChild(summaryTextDiv);
        
        content.appendChild(originalContainer);
        content.appendChild(summaryContainer);
        
        const footer = document.createElement('div');
        footer.style.padding = '15px';
        footer.style.borderTop = '1px solid #eee';
        footer.style.display = 'flex';
        footer.style.justifyContent = 'flex-end';
        footer.style.gap = '10px';
        
        const footerCopyButton = document.createElement('button');
        footerCopyButton.textContent = chrome.i18n.getMessage('copy_summary') || '요약 복사';
        footerCopyButton.style.padding = '8px 16px';
        footerCopyButton.style.border = '1px solid #ddd';
        footerCopyButton.style.borderRadius = '4px';
        footerCopyButton.style.background = 'white';
        footerCopyButton.style.cursor = 'pointer';
        footerCopyButton.style.color = '#333333';
        
        footerCopyButton.addEventListener('click', () => {
            this.copyToClipboard(summaryText, footerCopyButton, '요약');
        });
        
        footer.appendChild(footerCopyButton);
        
        popup.appendChild(header);
        popup.appendChild(content);
        popup.appendChild(footer);
        
        document.body.appendChild(popup);
        
        const escKeyHandler = (e) => {
            if (e.key === 'Escape') {
                popup.remove();
                document.removeEventListener('keydown', escKeyHandler);
            }
        };
        document.addEventListener('keydown', escKeyHandler);
    }

    // 단어 의미 찾기 함수
    lookupTermDefinition(term, targetLang) {
        const loadingPopup = this.createLoadingPopup('lookup');
        document.body.appendChild(loadingPopup);
        
        const prompt = `
Please provide a concise definition or explanation of the term "${term}" in ${targetLang}.
Include:
1. A brief definition (1-2 sentences)
2. The field or domain where this term is commonly used
3. Any important context or related concepts

Keep the explanation clear and accessible to non-experts.`;
        
        this.isCancelled = false;
        this.safeSendMessage({
            action: 'translate',
            prompt: prompt,
            model: 'claude-3-5-haiku'
        }, response => {
            loadingPopup.remove();
            if (this.isCancelled) {
                return;
            }
            
            if (response.translatedText === 'API_KEY_NOT_SET') {
                this.showApiKeyError();
            } else if (response.translatedText) {
                this.showTermDefinition(term, response.translatedText);
            }
        });
    }

    // 단어 의미 팝업 표시 함수
    showTermDefinition(term, definition) {
        const popup = document.createElement('div');
        popup.className = 'translate-ui term-definition';
        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
        popup.style.width = '400px';
        popup.style.maxWidth = '90%';
        popup.style.background = 'white';
        popup.style.color = '#333';
        popup.style.border = '1px solid #ccc';
        popup.style.borderRadius = '8px';
        popup.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
        popup.style.zIndex = '10002';
        popup.style.overflow = 'hidden';
        
        const header = document.createElement('div');
        header.style.padding = '12px 15px';
        header.style.borderBottom = '1px solid #eee';
        header.style.display = 'flex';
        header.style.justifyContent = 'space-between';
        header.style.alignItems = 'center';
        header.style.background = '#f5f5f5';
        header.style.color = '#333333';
        
        const title = document.createElement('div');
        title.textContent = `"${term}" 용어 설명`;
        title.style.fontWeight = 'bold';
        title.style.fontSize = '16px';
        title.style.color = '#333333';
        
        // 닫기 버튼 
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.style.background = 'none';
        closeButton.style.border = 'none';
        closeButton.style.fontSize = '20px';
        closeButton.style.cursor = 'pointer';
        closeButton.style.padding = '0 5px';
        closeButton.style.color = '#666666';
        
        closeButton.addEventListener('click', () => popup.remove());
        
        // 복사 버튼 추가
        const copyButton = document.createElement('button');
        copyButton.innerHTML = '📋';
        copyButton.title = chrome.i18n.getMessage('copy_term_definition') || '용어 설명 복사';
        copyButton.style.background = 'none';
        copyButton.style.border = 'none';
        copyButton.style.fontSize = '16px';
        copyButton.style.cursor = 'pointer';
        copyButton.style.padding = '0 5px';
        copyButton.style.marginRight = '5px';
        copyButton.style.color = '#666666';
        
        copyButton.addEventListener('click', () => {
            this.copyToClipboard(definition, copyButton, '');
        });
        
        // 버튼 컨테이너 생성
        const buttonContainer = document.createElement('div');
        buttonContainer.style.display = 'flex';
        buttonContainer.style.alignItems = 'center';
        
        buttonContainer.appendChild(copyButton);
        buttonContainer.appendChild(closeButton);
        
        header.appendChild(title);
        header.appendChild(buttonContainer);
        
        const content = document.createElement('div');
        content.style.padding = '15px';
        content.style.maxHeight = '300px';
        content.style.overflowY = 'auto';
        content.style.color = '#333333';
        
        const definitionText = document.createElement('div');
        definitionText.textContent = definition;
        definitionText.style.lineHeight = '1.5';
        definitionText.style.fontSize = '14px';
        definitionText.style.whiteSpace = 'pre-wrap';
        definitionText.style.color = '#333333';
        
        content.appendChild(definitionText);
        
        const footer = document.createElement('div');
        footer.style.padding = '10px 15px';
        footer.style.borderTop = '1px solid #eee';
        footer.style.display = 'flex';
        footer.style.justifyContent = 'flex-end';
        footer.style.color = '#333333';
        
        const footerCopyButton = document.createElement('button');
        footerCopyButton.textContent = chrome.i18n.getMessage('copy') || '복사';
        footerCopyButton.style.padding = '6px 12px';
        footerCopyButton.style.border = '1px solid #ddd';
        footerCopyButton.style.borderRadius = '4px';
        footerCopyButton.style.background = 'white';
        footerCopyButton.style.cursor = 'pointer';
        footerCopyButton.style.color = '#333333';
        
        footerCopyButton.addEventListener('click', () => {
            this.copyToClipboard(definition, footerCopyButton, '');
        });
        
        footer.appendChild(footerCopyButton);
        
        popup.appendChild(header);
        popup.appendChild(content);
        popup.appendChild(footer);
        
        document.body.appendChild(popup);
        
        const escKeyHandler = (e) => {
            if (e.key === 'Escape') {
                popup.remove();
                document.removeEventListener('keydown', escKeyHandler);
            }
        };
        document.addEventListener('keydown', escKeyHandler);
    }

    // 인라인 번역 함수
    translateInline(range, targetLang) {
        const loadingPopup = this.createLoadingPopup('translate');
        document.body.appendChild(loadingPopup);
        
        const selectedText = range.toString().trim();
        if (!selectedText) {
            loadingPopup.remove();
            return;
        }
        
        const commonAncestor = range.commonAncestorContainer;
        const parentElement = commonAncestor.nodeType === Node.TEXT_NODE 
            ? commonAncestor.parentElement 
            : commonAncestor;
        
        const existingTranslation = parentElement.querySelector('.translate-ui.inline-translation');
        if (existingTranslation) {
            loadingPopup.remove();
            return;
        }
        
        const existingSummary = parentElement.querySelector('.translate-ui.inline-summary');
        let textToTranslate = selectedText;
        if (existingSummary) {
            textToTranslate = existingSummary.querySelector('div:nth-child(3)').textContent;
        }
        
        const contextInfo = this.analyzeUrlForContext();
        const currentUrl = contextInfo.url;
        const pageTitle = document.title;
        
        const prompt = `
Current webpage: ${currentUrl}
Page title: ${pageTitle}
Context/Domain: ${contextInfo.domainContext}
Target language: ${targetLang}

Please translate the following text, considering the context of the webpage (${contextInfo.domainContext}) and maintaining appropriate terminology and style for this domain:

IMPORTANT: Preserve ALL formatting exactly as in the original text, including:
1. Line breaks and paragraph divisions
2. Bullet points and numbered lists (ul, ol, li elements)
3. Headings and subheadings
4. Tables and table structures
5. Any HTML or markdown formatting elements
6. Indentation and spacing
7. Don't write any other Notes
8. Don't write any other Notes
For technical terms or specialized vocabulary, please include the original term in parentheses after the translation, like this: "번역된 용어 (original term)".

Text: ${textToTranslate}`;
        
        this.isCancelled = false;
        this.safeSendMessage(
            { 
                action: 'translate', 
                text: textToTranslate,
                prompt: prompt,
                targetLang: targetLang,
                model: 'claude-3-5-haiku'
            },
            (response) => {
                loadingPopup.remove();
                if (this.isCancelled) {
                    return;
                }
                
                if (!response) {
                    console.error('응답이 없습니다.');
                    return;
                }

                if (response.error === 'RUNTIME_NOT_INITIALIZED') {
                    alert(chrome.i18n.getMessage('runtime_not_initialized') || '확장 프로그램이 제대로 초기화되지 않았습니다. 페이지를 새로고침하거나 확장 프로그램을 다시 로드해주세요.');
                    return;
                }
                
                if (response.translatedText === 'API_KEY_NOT_SET') {
                    this.showApiKeyError();
                } else if (this._isChromeBuiltinError(response.error)) {
                    this.showChromeBuiltinError(response.error);
                } else if (response.translatedText) {
                    this.insertInlineTranslation(range, textToTranslate, response.translatedText, existingSummary);
                }
            }
        );
    }

    // 인라인 번역 삽입
    insertInlineTranslation(range, originalText, translatedText, existingSummary) {
        const commonAncestor = range.commonAncestorContainer;
        const parentElement = commonAncestor.nodeType === Node.TEXT_NODE 
            ? commonAncestor.parentElement 
            : commonAncestor;
        
        const computedStyle = window.getComputedStyle(parentElement);
        
        const translationContainer = document.createElement('div');
        translationContainer.className = 'translate-ui inline-translation';
        translationContainer.style.margin = '10px 0';
        translationContainer.style.padding = '10px';
        translationContainer.style.borderLeft = '3px solid #6B4EFF';
        translationContainer.style.backgroundColor = '#f5f5f5';
        translationContainer.style.color = '#333';
        translationContainer.style.fontSize = computedStyle.fontSize;
        translationContainer.style.fontFamily = computedStyle.fontFamily;
        translationContainer.style.lineHeight = computedStyle.lineHeight;
        translationContainer.style.position = 'relative';
        
        const translationHeader = document.createElement('div');
        translationHeader.textContent = chrome.i18n.getMessage('translate') || '번역';
        translationHeader.style.fontWeight = 'bold';
        translationHeader.style.marginBottom = '5px';
        translationHeader.style.color = '#666';
        translationHeader.style.fontSize = '0.9em';
        
        const translationText = document.createElement('div');
        translationText.textContent = translatedText;
        translationText.style.whiteSpace = 'pre-wrap';
        
        // 닫기 버튼
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '✕';
        closeButton.style.position = 'absolute';
        closeButton.style.top = '5px';
        closeButton.style.right = '5px';
        closeButton.style.border = 'none';
        closeButton.style.background = 'none';
        closeButton.style.cursor = 'pointer';
        closeButton.style.color = '#999';
        closeButton.style.fontSize = '16px';
        closeButton.addEventListener('click', () => translationContainer.remove());
        
        // 복사 버튼 추가
        const copyButton = document.createElement('button');
        copyButton.innerHTML = '📋';
        copyButton.style.position = 'absolute';
        copyButton.style.top = '5px';
        copyButton.style.right = '30px';
        copyButton.style.border = 'none';
        copyButton.style.background = 'none';
        copyButton.style.cursor = 'pointer';
        copyButton.style.color = '#999';
        copyButton.style.fontSize = '16px';
        copyButton.title = '번역문 복사';
        copyButton.addEventListener('click', () => {
            this.copyToClipboard(translatedText, copyButton, '번역문');
        });
        
        translationContainer.appendChild(closeButton);
        translationContainer.appendChild(copyButton);
        translationContainer.appendChild(translationHeader);
        translationContainer.appendChild(translationText);
        
        try {
            const newRange = document.createRange();
            newRange.setStart(range.endContainer, range.endOffset);
            newRange.setEnd(range.endContainer, range.endOffset);
            
            window.getSelection().removeAllRanges();
            
            if (existingSummary) {
                existingSummary.parentNode.insertBefore(translationContainer, existingSummary.nextSibling);
            } else if (range.endContainer.nodeType === Node.TEXT_NODE) {
                const parent = range.endContainer.parentNode;
                const nextSibling = range.endContainer.splitText(range.endOffset).nextSibling;
                if (nextSibling) {
                    parent.insertBefore(translationContainer, nextSibling);
                } else {
                    parent.appendChild(translationContainer);
                }
            } else {
                const parent = range.endContainer;
                const insertPosition = range.endOffset < parent.childNodes.length 
                    ? parent.childNodes[range.endOffset] 
                    : null;
                
                if (insertPosition) {
                    parent.insertBefore(translationContainer, insertPosition);
                } else {
                    parent.appendChild(translationContainer);
                }
            }
        } catch (error) {
            console.error(chrome.i18n.getMessage('inline_translation_insertion_error') || '인라인 번역 삽입 오류:', error);
            try {
                const parent = parentElement.parentNode;
                parent.insertBefore(translationContainer, parentElement.nextSibling);
            } catch (fallbackError) {
                console.error('대체 삽입 오류:', fallbackError);
                document.body.appendChild(translationContainer);
            }
        }
    }

    // 인라인 요약 함수
    summarizeInline(range, targetLang) {
        const loadingPopup = this.createLoadingPopup('summarize');
        document.body.appendChild(loadingPopup);
        
        const selectedText = range.toString().trim();
        if (!selectedText) {
            loadingPopup.remove();
            return;
        }
        
        const commonAncestor = range.commonAncestorContainer;
        const parentElement = commonAncestor.nodeType === Node.TEXT_NODE 
            ? commonAncestor.parentElement 
            : commonAncestor;
        
        const existingSummary = parentElement.querySelector('.translate-ui.inline-summary');
        if (existingSummary) {
            loadingPopup.remove();
            return;
        }
        
        const existingTranslation = parentElement.querySelector('.translate-ui.inline-translation');
        let textToSummarize = selectedText;
        if (existingTranslation) {
            textToSummarize = existingTranslation.querySelector('div:nth-child(3)').textContent;
        }
        
        const contextInfo = this.analyzeUrlForContext();
        const currentUrl = contextInfo.url;
        const pageTitle = document.title;
        
        const prompt = `
Current webpage: ${currentUrl}
Page title: ${pageTitle}
Context/Domain: ${contextInfo.domainContext}
Target language: ${targetLang}
Please provide a concise summary of the following text in Korean, reducing it to 20-30% of the original length. Consider the context of the webpage (${contextInfo.domainContext}) when summarizing.

Retain the main points and arguments, preserving the tone and style where suitable. Organize the information logically, maintaining the paragraph structure if applicable, and include key technical terms from the original.

Text to summarize: ${textToSummarize}`;
        
        this.isCancelled = false;
        this.safeSendMessage(
            { 
                action: 'translate', 
                text: textToSummarize,
                prompt: prompt,
                isSummary: true,
                model: 'claude-3-5-haiku'
            },
            (response) => {
                loadingPopup.remove();
                if (this.isCancelled) {
                    return;
                }
                
                if (!response) {
                    console.error(chrome.i18n.getMessage('no_response') || '응답이 없습니다.');
                    return;
                }

                if (response.error === 'RUNTIME_NOT_INITIALIZED') {
                    alert(chrome.i18n.getMessage('runtime_not_initialized') || '확장 프로그램이 제대로 초기화되지 않았습니다. 페이지를 새로고침하거나 확장 프로그램을 다시 로드해주세요.');
                    return;
                }
                
                if (response.translatedText === 'API_KEY_NOT_SET') {
                    this.showApiKeyError();
                } else if (response.translatedText) {
                    this.insertInlineSummary(range, textToSummarize, response.translatedText, existingTranslation);
                } else {
                    alert(chrome.i18n.getMessage('summary_failed') || '요약에 실패했습니다: ' + (response.error || '응답 없음'));
                }
            }
        );
    }

    // 인라인 요약 삽입
    insertInlineSummary(range, originalText, summaryText, existingTranslation) {
        const commonAncestor = range.commonAncestorContainer;
        const parentElement = commonAncestor.nodeType === Node.TEXT_NODE 
            ? commonAncestor.parentElement 
            : commonAncestor;
        
        const computedStyle = window.getComputedStyle(parentElement);
        
        const summaryContainer = document.createElement('div');
        summaryContainer.className = 'translate-ui inline-summary';
        summaryContainer.style.margin = '10px 0';
        summaryContainer.style.padding = '10px';
        summaryContainer.style.borderLeft = '3px solid #FF6B4E';
        summaryContainer.style.backgroundColor = '#fff9f5';
        summaryContainer.style.color = '#333';
        summaryContainer.style.fontSize = computedStyle.fontSize;
        summaryContainer.style.fontFamily = computedStyle.fontFamily;
        summaryContainer.style.lineHeight = computedStyle.lineHeight;
        summaryContainer.style.position = 'relative';

        const summaryHeader = document.createElement('div');
        summaryHeader.textContent = chrome.i18n.getMessage('summary') || '요약';
        summaryHeader.style.fontWeight = 'bold';
        summaryHeader.style.marginBottom = '5px';
        summaryHeader.style.color = '#666';
        summaryHeader.style.fontSize = '0.9em';

        const summaryTextElement = document.createElement('div');
        summaryTextElement.textContent = summaryText;
        summaryTextElement.style.whiteSpace = 'pre-wrap';
        
        // 닫기 버튼
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '✕';
        closeButton.style.position = 'absolute';
        closeButton.style.top = '5px';
        closeButton.style.right = '5px';
        closeButton.style.border = 'none';
        closeButton.style.background = 'none';
        closeButton.style.cursor = 'pointer';
        closeButton.style.color = '#999';
        closeButton.style.fontSize = '16px';
        closeButton.addEventListener('click', () => summaryContainer.remove());
        
        // 복사 버튼 추가
        const copyButton = document.createElement('button');
        copyButton.innerHTML = '📋';
        copyButton.style.position = 'absolute';
        copyButton.style.top = '5px';
        copyButton.style.right = '30px';
        copyButton.style.border = 'none';
        copyButton.style.background = 'none';
        copyButton.style.cursor = 'pointer';
        copyButton.style.color = '#999';
        copyButton.style.fontSize = '16px';
        copyButton.title = '요약 복사';
        copyButton.addEventListener('click', () => {
            this.copyToClipboard(summaryText, copyButton, '요약');
        });
        
        summaryContainer.appendChild(closeButton);
        summaryContainer.appendChild(copyButton);
        summaryContainer.appendChild(summaryHeader);
        summaryContainer.appendChild(summaryTextElement);
        
        try {
            const newRange = document.createRange();
            newRange.setStart(range.endContainer, range.endOffset);
            newRange.setEnd(range.endContainer, range.endOffset);
            
            window.getSelection().removeAllRanges();
            
            if (existingTranslation) {
                existingTranslation.parentNode.insertBefore(summaryContainer, existingTranslation.nextSibling);
            } else if (range.endContainer.nodeType === Node.TEXT_NODE) {
                const parent = range.endContainer.parentNode;
                const nextSibling = range.endContainer.splitText(range.endOffset).nextSibling;
                if (nextSibling) {
                    parent.insertBefore(summaryContainer, nextSibling);
                } else {
                    parent.appendChild(summaryContainer);
                }
            } else {
                const parent = range.endContainer;
                const insertPosition = range.endOffset < parent.childNodes.length 
                    ? parent.childNodes[range.endOffset] 
                    : null;
                
                if (insertPosition) {
                    parent.insertBefore(summaryContainer, insertPosition);
                } else {
                    parent.appendChild(summaryContainer);
                }
            }
        } catch (error) {
            console.error(chrome.i18n.getMessage('inline_summary_insertion_error') || '인라인 요약 삽입 오류:', error);
            try {
                const parent = parentElement.parentNode;
                parent.insertBefore(summaryContainer, parentElement.nextSibling);
            } catch (fallbackError) {
                console.error('대체 삽입 오류:', fallbackError);
                document.body.appendChild(summaryContainer);
            }
        }
    }

    // ===== a_3776: Chrome 내장 온디바이스 Translator API 어댑터(무료·오프라인·서버불필요) =====
    // MV3 서비스워커엔 window/Translator 없음 → 반드시 content-script(여기)에서 실행.
    static chromeBuiltinSupported() {
        return typeof self !== 'undefined' && 'Translator' in self;
    }

    // 소스 언어 추정: 대상이 ko면 en 소스로, ko가 아니면 ko 소스로 가정.
    // LanguageDetector 있으면 정밀 감지 사용.
    async _detectSourceLang(text, targetLang) {
        try {
            if ('LanguageDetector' in self) {
                const d = await LanguageDetector.create();
                const [top] = await d.detect(text);
                if (top && top.detectedLanguage && top.detectedLanguage !== 'und') {
                    return top.detectedLanguage.split('-')[0];
                }
            }
        } catch (e) { /* fall through to heuristic */ }
        // 휴리스틱: 한글 포함 여부
        const hasKo = /[가-힣]/.test(text);
        if (targetLang === 'ko') return hasKo ? 'ko' : 'en';
        return hasKo ? 'ko' : 'en';
    }

    // 실제 번역 수행. 성공 시 {success:true, translatedText}, 실패 시 {error}.
    async translateViaChromeBuiltin(text, targetLang, onDownload) {
        if (!window.TranslationService.chromeBuiltinSupported()) {
            return { error: 'CHROME_BUILTIN_UNAVAILABLE' };
        }
        try {
            let source = await this._detectSourceLang(text, targetLang);
            if (source === targetLang) {
                // 동일언어면 반대 기본쌍으로 보정(ko↔en)
                source = targetLang === 'ko' ? 'en' : 'ko';
            }
            const avail = await Translator.availability({ sourceLanguage: source, targetLanguage: targetLang });
            if (avail === 'unavailable') {
                return { error: 'CHROME_BUILTIN_PAIR_UNAVAILABLE', pair: `${source}->${targetLang}` };
            }
            const translator = await Translator.create({
                sourceLanguage: source,
                targetLanguage: targetLang,
                monitor(m) {
                    m.addEventListener('downloadprogress', (e) => {
                        if (onDownload) onDownload(Math.round(e.loaded * 100));
                    });
                }
            });
            const translatedText = await translator.translate(text);
            return { success: true, translatedText, translation: translatedText };
        } catch (e) {
            return { error: 'CHROME_BUILTIN_ERROR', message: e.message };
        }
    }

    // 안전한 메시지 전송을 위한 헬퍼 함수
    safeSendMessage(message, callback) {
        // a_3776: chrome-builtin 번역 서비스 선택 시 백그라운드 대신 content-script에서 직접 처리.
        if (message && message.action === 'translate') {
            chrome.storage.sync.get({ translationService: 'deepl-free' }, (cfg) => {
                const useBuiltin = cfg.translationService === 'chrome-builtin';
                if (useBuiltin) {
                    if (!window.TranslationService.chromeBuiltinSupported()) {
                        if (callback) callback({ error: 'CHROME_BUILTIN_UNAVAILABLE' });
                        return;
                    }
                    this.translateViaChromeBuiltin(message.text, message.targetLang)
                        .then((r) => { if (callback) callback(r); });
                    return;
                }
                this._sendRuntimeMessage(message, callback);
            });
            return;
        }
        this._sendRuntimeMessage(message, callback);
    }

    _isChromeBuiltinError(err) {
        return err === 'CHROME_BUILTIN_UNAVAILABLE'
            || err === 'CHROME_BUILTIN_PAIR_UNAVAILABLE'
            || err === 'CHROME_BUILTIN_ERROR';
    }

    // a_3776: Chrome 내장 번역 실패 시 명확한 안내(무음 실패 금지)
    showChromeBuiltinError(err) {
        let msg;
        if (err === 'CHROME_BUILTIN_UNAVAILABLE') {
            msg = 'Chrome 내장 번역을 사용할 수 없습니다.\n데스크톱 Chrome 138 이상이 필요합니다. 설정에서 다른 번역 서비스(DeepL/Claude 등)를 선택하세요.';
        } else if (err === 'CHROME_BUILTIN_PAIR_UNAVAILABLE') {
            msg = '이 언어쌍은 Chrome 내장 번역에서 지원되지 않습니다.\n다른 번역 서비스를 선택하세요.';
        } else {
            msg = 'Chrome 내장 번역 중 오류가 발생했습니다.\n최초 사용 시 온디바이스 모델 다운로드에 시간이 걸릴 수 있습니다. 잠시 후 다시 시도하거나 다른 서비스를 선택하세요.';
        }
        alert(msg);
    }

    _sendRuntimeMessage(message, callback) {
        try {
            if (!chrome.runtime) {
                console.error(chrome.i18n.getMessage('runtime_not_initialized') || 'Chrome 런타임이 초기화되지 않았습니다.');
                if (callback) callback({ error: 'RUNTIME_NOT_INITIALIZED' });
                return;
            }

            chrome.runtime.sendMessage(message, function(response) {
                if (chrome.runtime.lastError) {
                    console.error(chrome.i18n.getMessage('message_send_error') || '메시지 전송 오류:', chrome.runtime.lastError);
                    if (callback) callback({ error: chrome.runtime.lastError.message });
                    return;
                }
                if (callback) callback(response);
            });
        } catch (error) {
            console.error(chrome.i18n.getMessage('message_send_error') || '메시지 전송 중 오류 발생:', error);
            if (callback) callback({ error: error.message });
        }
    }

    // 번역 기능 활성화/비활성화 설정
    setEnabled(enabled) {
        this.isEnabled = enabled;
        console.error('번역 서비스 상태가 변경되었습니다:', enabled ? '활성화' : '비활성화');
    }
};