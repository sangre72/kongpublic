// 번역 서비스 옵션 표시 관리
function showServiceOptions(service) {
    // 모든 서비스 옵션 숨기기
    document.querySelectorAll('.service-option').forEach(option => {
        option.classList.remove('active');
    });
    
    // 선택된 서비스 옵션 표시
    const serviceOption = document.getElementById(`${service}-options`);
    if (serviceOption) {
        serviceOption.classList.add('active');
    } else {
        console.warn(`서비스 옵션을 찾을 수 없음: ${service}-options`);
    }
}

// 설정 저장
function saveOptions() {
    const translationService = document.getElementById('translationService').value;
    
    // 모든 API 키 정보 가져오기
    const claudeApiKey = document.getElementById('claudeApiKey').value;
    const chatgptApiKey = document.getElementById('chatgptApiKey').value;
    const grokApiKey = document.getElementById('grokApiKey').value;
    const deeplFreeApiKey = document.getElementById('deeplFreeApiKey').value;
    const deeplProApiKey = document.getElementById('deeplProApiKey').value;
    
    // 마우스 우클릭 휠 활성화 상태 가져오기
    const mouseWheelEnabledCheckbox = document.getElementById('mouseWheelEnabled');
    const mouseWheelEnabled = mouseWheelEnabledCheckbox ? mouseWheelEnabledCheckbox.checked : false;
    
    // DeepL API 키 패턴 확인 - 사용자 편의를 위해
    if (translationService === 'deepl-free' && deeplFreeApiKey) {
        // 무료 버전 API 키는 일반적으로 숫자와 문자로 이루어짐
        if (deeplFreeApiKey.startsWith('sk-') || deeplFreeApiKey.startsWith('xai-')) {
            const status = document.getElementById('status');
            status.textContent = chrome.i18n.getMessage('deepl_free_api_key_warning') || '경고: 이것은 DeepL API 키가 아닌 것 같습니다. 정확한 DeepL 무료 API 키를 입력하세요.';
            status.className = 'status error';
            status.style.display = 'block';
            setTimeout(() => {
                status.style.display = 'none';
            }, 5000);
            return;
        }
    }
    
    if (translationService === 'deepl-pro' && deeplProApiKey) {
        // 유료 버전 API 키도 확인
        if (deeplProApiKey.startsWith('sk-') || deeplProApiKey.startsWith('xai-')) {
            const status = document.getElementById('status');
            status.textContent = chrome.i18n.getMessage('deepl_pro_api_key_warning') || '경고: 이것은 DeepL API 키가 아닌 것 같습니다. 정확한 DeepL 유료 API 키를 입력하세요.';
            status.className = 'status error';
            status.style.display = 'block';
            setTimeout(() => {
                status.style.display = 'none';
            }, 5000);
            return;
        }
    }
    
    // 선호 언어 정보 가져오기 (라디오 버튼)
    const selectedRadio = document.querySelector('.language-item input[type="radio"]:checked');
    let preferredLanguage = null;
    
    if (selectedRadio) {
        preferredLanguage = {
            code: selectedRadio.id,
            name: selectedRadio.value,
            displayName: selectedRadio.nextElementSibling.textContent
        };
    } else {
        // 기본값 설정 (한국어)
        preferredLanguage = {
            code: 'ko',
            name: 'Korean',
            displayName: '한국어 (Korean)'
        };
    }

    // 사용자 인터페이스 언어 가져오기
    const userLanguage = document.getElementById('userLanguage').value;
    
    // 디버그 모드 설정 (있는 경우)
    const debugModeCheckbox = document.getElementById('debugMode');
    const debugMode = debugModeCheckbox ? debugModeCheckbox.checked : false;
    
    // 번역 기능 활성화 체크박스
    const translationEnabledCheckbox = document.getElementById('translationEnabled');
    const translationEnabled = translationEnabledCheckbox ? translationEnabledCheckbox.checked : false;
    
    // 설정 저장
    const settings = {
        translationService: translationService,
        preferredLanguage: preferredLanguage, // 단일 객체로 변경
        userLanguage: userLanguage,
        
        // 각 서비스별 API 키 개별 저장
        claudeApiKey: claudeApiKey || '',
        chatgptApiKey: chatgptApiKey || '',
        grokApiKey: grokApiKey || '',
        deeplFreeApiKey: deeplFreeApiKey || '',
        deeplProApiKey: deeplProApiKey || '',
        
        // 소스 언어 및 타겟 언어
        sourceLang: 'auto',
        targetLang: preferredLanguage ? preferredLanguage.code : 'ko', // 선택한 언어로 타겟 설정
        
        // 디버그 모드
        debug: debugMode,
        
        // 마우스 우클릭 휠 활성화 상태
        mouseWheelEnabled: mouseWheelEnabled,
        
        // 번역 기능 활성화 상태
        translationEnabled: translationEnabled
    };
    
    console.log('저장할 설정:', settings);
    
    // 실제 저장
    chrome.storage.sync.set(settings, () => {
        if (chrome.runtime.lastError) {
            console.error(chrome.i18n.getMessage('settings_save_error') || '설정 저장 오류:', chrome.runtime.lastError);
            
            const status = document.getElementById('status');
            status.textContent = chrome.i18n.getMessage('settings_save_error') || '설정 저장 중 오류가 발생했습니다. 다시 시도해주세요.';
            status.className = 'status error';
            status.style.display = 'block';
            
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
            return;
        }
        
        const status = document.getElementById('status');
        // Get the current language from the userLanguage dropdown
        const currentLang = document.getElementById('userLanguage').value;
        // 메시지 출력 - locales 직접 참조 대신 getMessage 함수 사용 또는 기본 메시지 출력
        try {
            if (typeof locales !== 'undefined' && locales[currentLang] && locales[currentLang].settings_saved) {
                status.textContent = locales[currentLang].settings_saved;
            } else if (window.applyLanguage) {
                // options-utils.js의 함수 사용
                window.applyLanguage(currentLang);
                status.textContent = chrome.i18n.getMessage('settings_saved') || '설정이 저장되었습니다.';
            } else {
                // 기본 메시지
                status.textContent = chrome.i18n.getMessage('settings_saved') || '설정이 저장되었습니다.';
            }
        } catch (error) {
            console.error('상태 메시지 설정 오류:', error);
            status.textContent = chrome.i18n.getMessage('settings_saved') || '설정이 저장되었습니다.';
        }
        status.className = 'status success';
        status.style.display = 'block';
        
        // 저장 후 설정이 제대로 저장되었는지 확인
        chrome.storage.sync.get(null, (data) => {
            console.log('저장 후 설정:', data);
        });
        
        setTimeout(() => {
            status.style.display = 'none';
        }, 2000);
    });
}

// 저장된 설정 불러오기
function restoreOptions() {
    // 설정 로딩 전에 현재 저장된 모든 데이터 출력 (디버깅용)
    chrome.storage.sync.get(null, (data) => {
        console.log(chrome.i18n.getMessage('saved_all_settings') || '저장된 모든 설정:', data);
        
        // 기본값 설정
        const defaultSettings = {
            translationService: 'deepl-free',
            claudeApiKey: '',
            chatgptApiKey: '',
            grokApiKey: '',
            deeplFreeApiKey: '',
            deeplProApiKey: '',
            sourceLang: 'auto',
            targetLang: 'ko',
            preferredLanguage: {  // 단일 객체로 변경
                code: 'ko',
                name: 'Korean',
                displayName: '한국어 (Korean)'
            },
            userLanguage: 'ko',
            debug: false,
            mouseWheelEnabled: false,  // 마우스 우클릭 휠 활성화 기본값 추가
            translationEnabled: false  // 번역 기능 활성화 기본값 추가
        };
        
        // 데이터가 없으면 기본값 사용
        const items = Object.keys(data).length === 0 ? defaultSettings : data;
                
        // 번역 서비스 선택
        const translationServiceSelect = document.getElementById('translationService');
        if (translationServiceSelect) {
            translationServiceSelect.value = items.translationService || 'deepl-free';
            showServiceOptions(translationServiceSelect.value);
        }
        
        // 각 서비스별 API 키 설정
        const claudeApiKeyInput = document.getElementById('claudeApiKey');
        if (claudeApiKeyInput) claudeApiKeyInput.value = items.claudeApiKey || '';
        
        const chatgptApiKeyInput = document.getElementById('chatgptApiKey');
        if (chatgptApiKeyInput) chatgptApiKeyInput.value = items.chatgptApiKey || '';
        
        const grokApiKeyInput = document.getElementById('grokApiKey');
        if (grokApiKeyInput) grokApiKeyInput.value = items.grokApiKey || '';
        
        const deeplFreeApiKeyInput = document.getElementById('deeplFreeApiKey');
        if (deeplFreeApiKeyInput) deeplFreeApiKeyInput.value = items.deeplFreeApiKey || '';
        
        const deeplProApiKeyInput = document.getElementById('deeplProApiKey');
        if (deeplProApiKeyInput) deeplProApiKeyInput.value = items.deeplProApiKey || '';
        
        // 사용자 인터페이스 언어 설정
        const userLanguageSelect = document.getElementById('userLanguage');
        if (userLanguageSelect) {
            userLanguageSelect.value = items.userLanguage || 'ko';
        }
        
        // 디버그 모드 설정
        const debugModeCheckbox = document.getElementById('debugMode');
        if (debugModeCheckbox) {
            debugModeCheckbox.checked = items.debug || false;
        }
        
        // 마우스 우클릭 휠 활성화 상태 설정
        const mouseWheelEnabledCheckbox = document.getElementById('mouseWheelEnabled');
        if (mouseWheelEnabledCheckbox) {
            mouseWheelEnabledCheckbox.checked = items.mouseWheelEnabled || false;
        }
        
        // 번역 기능 활성화 상태 설정
        const translationEnabledCheckbox = document.getElementById('translationEnabled');
        if (translationEnabledCheckbox) {
            translationEnabledCheckbox.checked = items.translationEnabled || false;
        }
        
        // 선호 언어 적용 - options-utils.js에서 처리됨
        // applyLanguage(items.userLanguage || 'ko');
        
        // 선호 언어 라디오 버튼 설정
        if (items.preferredLanguage && items.preferredLanguage.code) {
            
            // 선택된 언어 라디오 버튼 체크
            const radioButton = document.getElementById(items.preferredLanguage.code);
            if (radioButton) {
                radioButton.checked = true;
            } else {
                
                // 기존 데이터 마이그레이션 (이전 버전과의 호환성을 위해)
                if (items.preferredLanguages && Array.isArray(items.preferredLanguages) && items.preferredLanguages.length > 0) {
                    const firstPreferredLang = items.preferredLanguages[0];
                    
                    const oldRadioButton = document.getElementById(firstPreferredLang.code);
                    if (oldRadioButton) {
                        oldRadioButton.checked = true;
                    }
                }
            }
        }
    });
}

// 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', () => {
    // 서비스 변경 이벤트 리스너
    const translationServiceSelect = document.getElementById('translationService');
    if (translationServiceSelect) {
        translationServiceSelect.addEventListener('change', () => {
            showServiceOptions(translationServiceSelect.value);
        });
    }
    
    // 저장 버튼 이벤트 리스너
    const saveButton = document.getElementById('save');
    if (saveButton) {
        saveButton.addEventListener('click', saveOptions);
    }
    
    // 설정 불러오기
    restoreOptions();
});