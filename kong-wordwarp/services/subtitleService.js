// subtitleService.js
// 전역 변수로 SubtitleService 클래스 노출
window.SubtitleService = class {
    constructor() {
        this.isEnabled = false;  // 번역 기능 활성화 상태
        this.isSubtitleTranslationEnabled = false;
        this.subtitleObserver = null;
        this.lastTranslatedSubtitle = '';
        this.translationDebounceTimer = null;
        this.subtitleTranslationTarget = 'ko'; // 기본 번역 언어
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPreferredLanguage();
        
        // 옵션 화면의 번역 기능 활성화 상태 가져오기
        this.loadTranslationEnabledState();

        // 옵션 화면의 번역 기능 활성화 상태 변경 감지
        chrome.storage.onChanged.addListener((changes, namespace) => {
            if (namespace === 'sync' && changes.translationEnabled) {
                this.handleTranslationEnabledChange(changes.translationEnabled.newValue);
            }
        });
    }

    // 번역 기능 활성화 상태 로드
    loadTranslationEnabledState() {
        chrome.storage.sync.get(['translationEnabled'], (result) => {
            this.isEnabled = result.translationEnabled === undefined ? true : result.translationEnabled;
            console.error('자막 서비스 초기 상태:', this.isEnabled ? '활성화' : '비활성화');
        });
    }

    // 번역 기능 활성화 상태 변경 처리
    handleTranslationEnabledChange(newValue) {
        const newState = newValue !== false;
        const oldState = this.isEnabled;
        
        if (newState !== oldState) {
            this.isEnabled = newState;
            console.error('자막 서비스 상태 변경:', this.isEnabled ? '활성화' : '비활성화');
            
            // 비활성화된 경우 자막 번역 중지
            if (!this.isEnabled) {
                this.stopSubtitleTranslation();
            }
            
            // 상태 변경 알림 표시
            this.showNotification(
                this.isEnabled ? '자막 번역 기능이 활성화되었습니다.' : '자막 번역 기능이 비활성화되었습니다.'
            );
        }
    }

    // 알림 표시 함수
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'translate-ui subtitle-notification';
        notification.textContent = message;
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

    // 번역 기능 토글
    toggleTranslationEnabled() {
        chrome.storage.sync.get(['translationEnabled'], (result) => {
            const newState = !(result.translationEnabled !== false);
            chrome.storage.sync.set({ translationEnabled: newState });
        });
    }

    setupEventListeners() {
        // 단축키 지원 추가 (Alt+S 또는 Option+S로 토글)
        document.addEventListener('keydown', async (e) => {
            if ((e.altKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                
                // 설정 가져오기
                const settings = await this.getSettings();
                
                // DeepL 서비스가 아닌 경우 메시지 표시
                if(settings.translationService === 'deepl-free' || settings.translationService === 'deepl-pro') {
                }
                else {
                    // 메시지 요소 생성
                    const messageEl = document.createElement('div');
                    messageEl.style.cssText = `
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: rgba(0, 0, 0, 0.8);
                        color: white;
                        padding: 20px;
                        border-radius: 8px;
                        z-index: 999999;
                        font-size: 16px;
                    `;
                    messageEl.textContent = (settings.translationService || 'Unknown') + ' DeepL 서비스에서만 사용 가능한 기능입니다.';
                    document.body.appendChild(messageEl);
                    
                    // 5초 후 메시지 제거
                    setTimeout(() => {
                        messageEl.remove();
                    }, 5000);
                    
                    return;
                }
                
                this.toggleSubtitleTranslation();
            }

            // Ctrl+Shift+X 단축키로 자막 번역 기능 토글
            if (e.ctrlKey && e.shiftKey && (e.code === 'KeyX' || e.key.toLowerCase() === 'x')) {
                e.preventDefault(); // 기본 동작 방지
                this.toggleTranslationEnabled();
            }
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

    // 자막 번역 토글 함수
    toggleSubtitleTranslation() {
        // 번역 기능이 비활성화되어 있으면 실행하지 않음
        if (!this.isEnabled) {
            console.error('번역 기능이 비활성화되어 있습니다.');
            return;
        }

        if (this.isSubtitleTranslationEnabled) {
            this.stopSubtitleTranslation();
        } else {
            this.startSubtitleTranslation();
        }
    }

    // 자막 번역 시작
    async startSubtitleTranslation() {
        if (this.isSubtitleTranslationEnabled) return;
        
        // 선호 언어 로드
        const preferredLanguages = await this.getPreferredLanguages();
        if (preferredLanguages && preferredLanguages.length > 0) {
            this.subtitleTranslationTarget = preferredLanguages[0].code;
        }
        
        this.isSubtitleTranslationEnabled = true;
        
        // 사용자에게 알림
        const notification = document.createElement('div');
        notification.className = 'translate-ui subtitle-notification';
        notification.textContent = chrome.i18n.getMessage('subtitle_translation_enabled') || '자막 실시간 번역이 활성화되었습니다.';
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
        }, 3000);
        
        // 자막 요소 관찰 시작
        if (this.subtitleObserver) {
            this.subtitleObserver.disconnect();
        }
        
        this.subtitleObserver = new MutationObserver(this.handleSubtitleChanges.bind(this));
        this.subtitleObserver.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
        
        // 현재 페이지에 이미 있는 자막 처리
        this.checkForExistingSubtitles();
    }

    // 자막 번역 중지
    stopSubtitleTranslation() {
        if (!this.isSubtitleTranslationEnabled) return;
        
        this.isSubtitleTranslationEnabled = false;
        
        if (this.subtitleObserver) {
            this.subtitleObserver.disconnect();
            this.subtitleObserver = null;
        }
        
        // 번역된 자막 요소 제거
        const translatedElements = document.querySelectorAll('.translate-ui.subtitle-translation');
        translatedElements.forEach(el => el.remove());
        
        // 사용자에게 알림
        const notification = document.createElement('div');
        notification.className = 'translate-ui subtitle-notification';
        notification.textContent = chrome.i18n.getMessage('subtitle_translation_disabled') || '자막 실시간 번역이 비활성화되었습니다.';
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
        }, 3000);
    }

    // 현재 페이지에 있는 자막 처리
    checkForExistingSubtitles() {
        const subtitleElements = document.querySelectorAll('.player-timedtext-text-container');
        
        if (subtitleElements.length > 0) {
            subtitleElements.forEach(element => {
                // span 태그 내부의 텍스트 추출
                const subtitleText = this.extractSubtitleText(element);
                if (subtitleText && subtitleText !== this.lastTranslatedSubtitle) {
                    this.translateSubtitle(subtitleText, element);
                }
            });
        }
    }

    // 자막 요소에서 텍스트 추출하는 함수
    extractSubtitleText(subtitleElement) {
        if (!subtitleElement) return '';
        
        // 내부 span 구조 확인
        const spans = subtitleElement.querySelectorAll('span');
        if (spans.length > 0) {
            // 가장 안쪽 span의 텍스트 반환
            let text = '';
            spans.forEach(span => {
                // 더 이상 내부에 span이 없는 경우만 텍스트 추출
                if (span.querySelectorAll('span').length === 0) {
                    text += span.textContent + ' ';
                }
            });
            return text.trim();
        }
        
        // 일반적인 경우 전체 텍스트 반환
        return subtitleElement.textContent.trim();
    }

    // 자막 변경 처리
    handleSubtitleChanges(mutations) {
        if (!this.isSubtitleTranslationEnabled) return;
        
        for (const mutation of mutations) {
            // 새로운 자막 요소 추가 확인
            if (mutation.type === 'childList' && mutation.addedNodes.length) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // 자막 컨테이너 요소 확인
                        const subtitleContainer = node.classList && node.classList.contains('player-timedtext-text-container') 
                            ? node 
                            : node.querySelector('.player-timedtext-text-container');
                        
                        if (subtitleContainer) {
                            // span 태그 내부의 텍스트 추출
                            const subtitleText = this.extractSubtitleText(subtitleContainer);
                            if (subtitleText && subtitleText !== this.lastTranslatedSubtitle) {
                                this.translateSubtitle(subtitleText, subtitleContainer);
                            }
                        }
                    }
                }
            }
            
            // 자막 내용 변경 확인
            if (mutation.type === 'characterData') {
                const parentElement = mutation.target.parentElement;
                if (parentElement) {
                    const subtitleContainer = parentElement.closest('.player-timedtext-text-container');
                    if (subtitleContainer) {
                        // span 태그 내부의 텍스트 추출
                        const subtitleText = this.extractSubtitleText(subtitleContainer);
                        if (subtitleText && subtitleText !== this.lastTranslatedSubtitle) {
                            this.translateSubtitle(subtitleText, subtitleContainer);
                        }
                    }
                }
            }
        }
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

    // 자막 번역 함수
    async translateSubtitle(text, originalElement) {
        // 번역 기능이 비활성화되어 있으면 실행하지 않음
        if (!this.isEnabled) {
            console.error('번역 기능이 비활성화되어 있습니다.');
            return;
        }

        if (!this.isSubtitleTranslationEnabled || !text || text.trim().length === 0) return;
        
        // 이미 번역된 자막은 중복 번역 방지
        if (text === this.lastTranslatedSubtitle) return;
        
        this.lastTranslatedSubtitle = text;
        
        // 번역할 언어 감지
        const detectedLang = this.detectLanguage(text);
        
        // 목표 언어와 같으면 번역하지 않음
        if (detectedLang === this.subtitleTranslationTarget) {
            return;
        }
        
        // 디바운스 처리 (빠르게 바뀌는 자막 처리 최적화)
        if (this.translationDebounceTimer) {
            clearTimeout(this.translationDebounceTimer);
        }
        
        this.translationDebounceTimer = setTimeout(async () => {
            try {
                
                // 번역 서비스 설정 가져오기
                const settings = await this.getSettings();
                
                // API 키 확인
                if (!settings.apiKey) {
                    console.error(chrome.i18n.getMessage('api_key_missing') || 'API 키가 설정되지 않았습니다.');
                    return;
                }
                let prompt = "";

                // DeepL 서비스인 경우 원본 텍스트만 전송
                if(settings.translationService === 'deepl-free' || settings.translationService === 'deepl-pro') {
                    prompt = text;
                }else{
                    prompt = "Do not write any other notes. Only subtitles. " + text;
                    return;
                }

                // 번역 요청
                this.safeSendMessage({
                    action: 'translate',
                    text: text,
                    sourceLang: detectedLang,
                    targetLang: this.subtitleTranslationTarget,
                    service: settings.translationService,
                    apiKey: settings.apiKey
                }, response => {
                    if (!response) {
                        console.error(chrome.i18n.getMessage('translation_response_missing') || '번역 응답이 없습니다.');
                        return;
                    }

                    if (response.error) {
                        console.error(chrome.i18n.getMessage('translation_error') || '자막 번역 오류:', response.error);
                        if (response.error === 'RUNTIME_NOT_INITIALIZED') {
                            console.error(chrome.i18n.getMessage('runtime_not_initialized') || 'Chrome 런타임이 초기화되지 않았습니다.');
                        }
                        return;
                    }

                    if (response.translatedText) {
                        this.displayTranslatedSubtitle(response.translatedText, originalElement);
                    }
                });
            } catch (error) {
                console.error(chrome.i18n.getMessage('translation_error') || '자막 번역 중 오류 발생:', error);
            }
        }, 300); // 300ms 디바운스
    }

    // 번역된 자막 표시
    displayTranslatedSubtitle(translatedText, originalElement) {
        if (!this.isSubtitleTranslationEnabled) return;
        
        // 자막 컨테이너 찾기
        const subtitleContainer = document.querySelector('.player-timedtext');
        if (!subtitleContainer) {
            return;
        }
        
        // 기존 번역 요소 제거
        document.querySelectorAll('.translate-ui.subtitle-translation').forEach(el => el.remove());
        
        // 새 자막 컨테이너 생성
        const newSubtitleContainer = document.createElement('div');
        newSubtitleContainer.className = 'player-timedtext-text-container translate-ui subtitle-translation';
        
        // 원본 자막 요소의 스타일 복사
        newSubtitleContainer.style.display = 'block';
        newSubtitleContainer.style.whiteSpace = 'normal'; // 줄바꿈 허용
        newSubtitleContainer.style.textAlign = 'center';
        newSubtitleContainer.style.position = 'absolute';
        newSubtitleContainer.style.zIndex = '9999999'; // 매우 높은 z-index
        newSubtitleContainer.style.maxWidth = '80%'; // 너비 제한
        
        // 원본 요소의 위치와 크기 가져오기
        const originalRect = originalElement.getBoundingClientRect();
        
        // 위치 설정 (고정된 위치 사용)
        newSubtitleContainer.style.left = '50%';
        newSubtitleContainer.style.transform = 'translateX(-50%)';
        
        // 하단 고정 위치 사용 (더 안정적)
        if (originalElement.style.bottom) {
            const bottomValue = parseFloat(originalElement.style.bottom.replace('%', ''));
            // 원본 자막이 하단 10% 미만이면 위에 배치, 그렇지 않으면 아래에 배치
            if (bottomValue < 10) {
                newSubtitleContainer.style.top = '70%';
            } else {
                newSubtitleContainer.style.bottom = '5%';
            }
        } else {
            // 기본 위치 (하단 5%)
            newSubtitleContainer.style.bottom = '5%';
        }
        
        // 번역을 위한 새 span 구조 생성 (원본과 유사한 구조)
        const outerSpan = document.createElement('span');
        outerSpan.style.display = 'inline-block';
        outerSpan.style.textAlign = 'center';
        outerSpan.style.backgroundColor = 'rgba(0, 0, 0, 0.75)'; // 더 진한 배경색
        outerSpan.style.padding = '4px 8px';
        outerSpan.style.borderRadius = '4px';
        outerSpan.style.border = '1px solid rgba(255, 255, 255, 0.2)'; // 테두리 추가
        
        const innerSpan = document.createElement('span');
        innerSpan.style.cssText = 'font-size:28px;line-height:1.3;font-weight:bold;color:#ffffff;text-shadow:#000000 0px 0px 7px;font-family:Netflix Sans,Helvetica Nueue,Helvetica,Arial,sans-serif';
        
        // 번역된 텍스트 설정
        innerSpan.textContent = translatedText;
        
        // span 구조 조립
        outerSpan.appendChild(innerSpan);
        newSubtitleContainer.appendChild(outerSpan);
        
        // body에 직접 추가 (가장 확실한 방법)
        document.body.appendChild(newSubtitleContainer);
    }

    // 메뉴에 자막 번역 토글 버튼 추가
    addSubtitleTranslationButton(menuContainer) {
        const subtitleButton = document.createElement('button');
        subtitleButton.textContent = chrome.i18n.getMessage('subtitle_translation_button') || '자막 실시간 번역';
        subtitleButton.className = 'translate-ui translate-button';
        subtitleButton.style.display = 'block';
        subtitleButton.style.width = '100%';
        subtitleButton.style.padding = '8px';
        subtitleButton.style.margin = '5px 0';
        subtitleButton.style.border = '1px solid #ddd';
        subtitleButton.style.borderRadius = '4px';
        subtitleButton.style.background = this.isSubtitleTranslationEnabled ? '#e3f2fd' : '#f5f5f5';
        subtitleButton.style.color = '#333333';
        subtitleButton.style.cursor = 'pointer';
        subtitleButton.style.textAlign = 'left';
        subtitleButton.style.fontSize = '14px';
        
        subtitleButton.addEventListener('click', () => {
            // 메뉴를 직접 닫음 (translationService에 의존하지 않음)
            document.querySelectorAll('.translate-ui.translate-menu').forEach(el => {
                el.remove();
            });
            this.toggleSubtitleTranslation();
        });
        
        menuContainer.appendChild(subtitleButton);
    }

    // 안전한 메시지 전송을 위한 헬퍼 함수
    safeSendMessage(message, callback) {
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
};