// 언어 감지 및 자동 적용을 위한 이벤트 핸들러
document.addEventListener('DOMContentLoaded', function() {
    // locales.js 모듈 임포트
    try {
        // 먼저 locales.js 모듈 스크립트 요소를 생성
        const script = document.createElement('script');
        script.type = 'module';
        script.src = 'locales.js';
        document.head.appendChild(script);
        
        // 그 후 모듈 불러오기 시도
        import('./locales.js').then(localesModule => {
            // 언어 감지 초기화
            initializeLanguageDetection(localesModule);
        }).catch(error => {
            console.error('locales.js 모듈 로딩 실패:', error);
            // 폴백: 기존 로직 사용
            initializeLanguageDetection();
        });
    } catch (error) {
        console.error('locales.js 모듈 로딩 오류:', error);
        // 폴백: 기존 로직 사용
        initializeLanguageDetection();
    }
    
    // 언어 감지 및 적용 초기화
    function initializeLanguageDetection(localesModule) {
        // 지원되는 언어 목록 (라디오 버튼 ID와 일치하도록 정의)
        const supportedLanguages = [
            'ar', 'zh-CN', 'zh-TW', 'hr', 'cs', 'da', 'nl', 'en', 'fi', 'fr', 
            'de', 'el', 'he', 'hu', 'is', 'it', 'ja', 'ko', 'lt', 'no', 
            'pl', 'pt', 'ro', 'sl', 'es', 'sv', 'th', 'tr'
        ];
        
        // 인터페이스 언어 (select에서 선택 가능한 언어)
        const interfaceLanguages = [
            'ar', 'zh-CN', 'zh-TW', 'hr', 'cs', 'da', 'nl', 'en', 'fi', 'fr', 
            'de', 'el', 'he', 'hu', 'is', 'it', 'ja', 'ko', 'lt', 'no', 
            'pl', 'pt', 'ro', 'sl', 'es', 'sv', 'th', 'tr'
        ];
        
        // 페이지 언어 적용 함수
        function applyLanguage(lang) {
            // 현재 언어 설정 저장 - 사용자가 선택한 언어를 로컬 변수로 사용
            const langToUse = lang;
            
            console.log('언어 적용:', langToUse);
            
            // 모듈을 사용할 수 있으면 모듈의 함수 사용
            if (localesModule) {
                localesModule.setLanguage(langToUse).then(() => {
                    // 언어 적용 성공
                    applyLanguageToElements(langToUse);
                }).catch(error => {
                    console.error('언어 설정 실패:', error);
                });
            } else {
                // 모듈을 사용할 수 없으면 직접 처리
                applyLanguageToElements(langToUse);
            }
        }
        
        // 실제 언어 적용 함수
        function applyLanguageToElements(langToUse) {
            // data-i18n 속성이 있는 모든 요소에 대해 언어 적용
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                
                if (localesModule) {
                    // 모듈 사용
                    localesModule.getMessage(key, langToUse).then(message => {
                        applyTranslation(element, message);
                    }).catch(error => {
                        console.error(`"${key}" 번역 적용 실패:`, error);
                    });
                } else {
                    // 폴백: 내장 번역 사용
                    const message = getTranslation(key, langToUse);
                    applyTranslation(element, message);
                }
            });
            
            // 상태 메시지 요소의 텍스트도 변경
            const statusElement = document.getElementById('status');
            if (statusElement && statusElement.textContent && 
                (statusElement.textContent.includes('saved') || statusElement.textContent.includes('저장'))) {
                
                if (localesModule) {
                    localesModule.getMessage('settings_saved', langToUse).then(message => {
                        statusElement.textContent = message;
                    }).catch(() => {
                        statusElement.textContent = '설정이 저장되었습니다.';
                    });
                } else {
                    // 폴백: 내장 번역 사용
                    const message = getTranslation('settings_saved', langToUse);
                    statusElement.textContent = message || '설정이 저장되었습니다.';
                }
            }
        }
        
        // 번역 메시지 가져오기 (내장 번역)
        function getTranslation(key, lang) {
            // 내장 번역 데이터 - 필수 키만 포함
            const translations = {
                'en': {
                    'settings_saved': 'Settings saved.'
                },
                'ko': {
                    'settings_saved': '설정이 저장되었습니다.'
                },
                'ja': {
                    'settings_saved': '設定が保存されました。'
                },
                'zh-CN': {
                    'settings_saved': '设置已保存。'
                },
                'de': {
                    'settings_saved': 'Einstellungen gespeichert.'
                }
            };
            
            // 언어에 대한 번역이 있으면 반환
            if (translations[lang] && translations[lang][key]) {
                return translations[lang][key];
            }
            
            // 없으면 영어 번역 시도
            if (translations['en'] && translations['en'][key]) {
                return translations['en'][key];
            }
            
            // 영어도 없으면 키 그대로 반환
            return key;
        }
        
        // 번역 적용 헬퍼 함수
        function applyTranslation(element, text) {
            if (element.tagName === 'INPUT' && element.type === 'button') {
                element.value = text;
            } else if (element.tagName === 'CODE') {
                // code 요소는 내부 텍스트를 변경하지 않음 (엔드포인트 URL 등)
            } else {
                element.textContent = text;
            }
        }
        
        // 브라우저/OS 언어 감지
        function detectLanguage() {
            if (localesModule && localesModule.detectSystemLanguage) {
                return localesModule.detectSystemLanguage();
            }
            
            // 모듈을 사용할 수 없으면 직접 처리
            // navigator.language에서 언어 코드 가져오기 (e.g., 'ko-KR' -> 'ko')
            let browserLang = navigator.language || navigator.userLanguage || 'en';
            console.log('감지된 브라우저/OS 언어:', browserLang);
            
            // 중국어 특수 처리 (zh-CN, zh-TW 구분)
            if (browserLang.startsWith('zh')) {
                // 번체 중국어 (zh-TW, zh-HK) 감지
                if (browserLang.includes('TW') || browserLang.includes('HK')) {
                    return 'zh-TW';
                }
                // 기본적으로 간체 중국어로 설정
                return 'zh-CN';
            }
            
            // 그 외 언어는 기본 코드만 추출 (e.g., 'ko-KR' -> 'ko')
            let langCode = browserLang.split('-')[0].toLowerCase();
            
            // 일부 특수 케이스 처리
            if (langCode === 'zh') {
                return 'zh-CN'; // 기본적으로 간체 중국어
            }
            
            // 인터페이스 언어 확인 (select에서 선택 가능한 언어)
            if (interfaceLanguages.includes(langCode)) {
                return langCode;
            }
            
            // 일부 언어 코드는 매핑 필요
            const langMap = {
                'nb': 'no', // 노르웨이어 부크몰 -> 노르웨이어
                'nn': 'no'  // 노르웨이어 니노르스크 -> 노르웨이어
            };
            
            if (langMap[langCode]) {
                return langMap[langCode];
            }
            
            // 지원되지 않는 언어인 경우 기본값(영어) 반환
            return 'en';
        }
        
        // 언어 자동 적용
        function applyAutoLanguage() {
            // 저장된 설정이 있는지 확인
            chrome.storage.sync.get(['userLanguage', 'preferredLanguage'], function(result) {
                // 이미 사용자가 인터페이스 언어를 선택한 경우 해당 언어 사용
                if (result.userLanguage) {
                    console.log('저장된 인터페이스 언어 설정 사용:', result.userLanguage);
                    
                    // 언어 적용
                    applyLanguage(result.userLanguage);
                    
                    // 언어 선택 드롭다운 업데이트
                    const langSelect = document.getElementById('userLanguage');
                    if (langSelect) {
                        langSelect.value = result.userLanguage;
                    }
                } 
                // 처음 사용하는 경우 OS 언어 감지하여 적용
                else {
                    const detectedLang = detectLanguage();
                    console.log('OS 언어 감지 결과, 적용할 인터페이스 언어:', detectedLang);
                    
                    // userLanguage 선택 요소 업데이트
                    const langSelect = document.getElementById('userLanguage');
                    if (langSelect) {
                        try {
                            langSelect.value = detectedLang;
                        } catch (e) {
                            console.error('언어 선택 설정 오류:', e);
                            langSelect.value = 'en'; // 오류 시 영어로 기본 설정
                        }
                    }
                    
                    // 언어 적용
                    applyLanguage(detectedLang);
                }
                
                // 선호 언어(라디오 버튼) 설정
                if (!result.preferredLanguage) {
                    // 감지된 언어와 일치하는 라디오 버튼이 있으면 체크
                    const detectedLang = navigator.language || navigator.userLanguage || 'en';
                    let langCode = '';
                    
                    // 언어 코드 변환
                    if (detectedLang.startsWith('zh')) {
                        // 중국어 특수 처리
                        langCode = detectedLang.includes('TW') || detectedLang.includes('HK') ? 'zh-TW' : 'zh-CN';
                    } else {
                        // 기본 코드 추출
                        langCode = detectedLang.split('-')[0].toLowerCase();
                        
                        // 특수 케이스 처리
                        if (langCode === 'zh') langCode = 'zh-CN';
                        if (langCode === 'nb' || langCode === 'nn') langCode = 'no';
                    }
                    
                    // 지원되는 언어인지 확인
                    const radioButton = document.getElementById(langCode);
                    if (radioButton) {
                        radioButton.checked = true;
                    } else {
                        // 지원되지 않으면 영어로 기본 설정
                        const enRadio = document.getElementById('en');
                        if (enRadio) {
                            enRadio.checked = true;
                        }
                    }
                }
            });
        }
        
        // 인터페이스 언어 변경 이벤트 리스너 추가
        const userLanguageSelect = document.getElementById('userLanguage');
        if (userLanguageSelect) {
            userLanguageSelect.addEventListener('change', function() {
                console.log('인터페이스 언어 변경:', this.value);
                applyLanguage(this.value);
            });
        }
        
        // options.js에서 참조할 수 있도록 전역으로 노출
        window.applyLanguage = applyLanguage;
        
        // 페이지 로드 시 자동 언어 적용
        applyAutoLanguage();
    }
});

// 탭 전환 기능
document.addEventListener('DOMContentLoaded', function() {
    console.log('탭 기능 초기화');
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            console.log('탭 버튼 클릭됨:', this.getAttribute('data-tab'));
            
            // 모든 탭 버튼 비활성화
            tabButtons.forEach(function(btn) {
                btn.classList.remove('active');
                btn.style.borderBottom = 'none';
                btn.style.fontWeight = 'normal';
                btn.style.color = '#666';
            });
            
            // 클릭한 버튼 활성화
            this.classList.add('active');
            this.style.borderBottom = '2px solid #6B4EFF';
            this.style.fontWeight = 'bold';
            this.style.color = '#6B4EFF';
            
            // 모든 탭 내용 숨기기
            document.querySelectorAll('.tab-pane').forEach(function(pane) {
                pane.style.display = 'none';
                pane.classList.remove('active');
            });
            
            // 선택한 탭 내용 표시
            const targetTab = this.getAttribute('data-tab');
            const targetPane = document.getElementById(`${targetTab}-guide`);
            if (targetPane) {
                targetPane.style.display = 'block';
                targetPane.classList.add('active');
            }
        });
    });
}); 