// 한국어 (Korean) 언어 파일

const ko = {
    // 메뉴 및 UI 관련
    translate: '번역',
    summarize: '요약',
    lookup: '용어 정의 찾기',
    cancel: '취소',
    copy: '복사',
    copied: '복사됨',
    close: '닫기',
    translating: '번역 중...',
    summarizing: '요약 중...',
    looking_up: '용어 검색 중...',
    cancel_with_esc: '(ESC로 취소)',
    image_text_recognition: '이미지 텍스트 인식',
    menu_addition_error: '메뉴 추가 중 오류 발생:',
    summary_result: '요약 결과',
    copy_term_definition: '용어 정의 복사',

    //options.js
    deepl_free_api_key_error: 'API 키가 유효하지 않습니다. API 키를 확인하세요.',
    deepl_free_api_key_warning: '경고: 이것은 DeepL API 키가 아닌 것 같습니다. 정확한 DeepL 무료 API 키를 입력하세요.',
    deepl_pro_api_key_warning: '경고: 이것은 DeepL API 키가 아닌 것 같습니다. 정확한 DeepL 유료 API 키를 입력하세요.',
    settings_save_error: '설정 저장 중 오류가 발생했습니다. 다시 시도해주세요.',
    saved_all_settings: '저장된 모든 설정:',
    
    // 옵션 페이지 관련
    options_title: '번역 확장 프로그램 설정',
    service_selection: '번역 서비스 선택',
    api_key: 'API 키',
    model_selection: '모델 선택',
    api_url: 'API URL (선택사항)',
    api_key_free: 'API 키 (무료)',
    api_key_pro: 'API 키 (유료)',
    interface_language: '인터페이스 언어',
    interface_language_desc: '선택한 언어로 확장 프로그램의 메뉴와 메시지가 표시됩니다.',
    preferred_languages: '선호하는 언어 (하나의 언어만 선택할 수 있습니다)',
    save: '저장',
    settings_saved: '설정이 저장되었습니다.',
    
    // 새로 추가된 옵션 페이지 관련 텍스트
    debug_mode: '디버그 모드 활성화 (문제 해결용)',
    debug_mode_desc: '디버그 모드를 활성화하면 오류 메시지 및 API 통신 정보가 브라우저 콘솔에 표시됩니다.',
    api_guide_title: 'API 가입 가이드',
    claude_api_guide_title: 'Claude API 가입 및 키 발급 방법',
    chatgpt_api_guide_title: 'ChatGPT API 가입 및 키 발급 방법',
    grok_api_guide_title: 'Grok API 가입 및 키 발급 방법',
    deepl_api_guide_title: 'DeepL API 가입 및 키 발급 방법',
    deepl_api_help_title: 'DeepL API 사용 시 주의사항',
    
    // Claude API 가이드
    claude_guide_step1: 'Anthropic 웹사이트(https://www.anthropic.com/api)에 접속합니다.',
    claude_guide_step2: '오른쪽 상단의 "Sign up" 버튼을 클릭합니다.',
    claude_guide_step3: '이메일과 비밀번호를 입력하여 계정을 생성합니다.',
    claude_guide_step4: '로그인 후 "API Keys" 탭으로 이동합니다.',
    claude_guide_step5: '"Create API Key" 버튼을 클릭합니다.',
    claude_guide_step6: '키 이름을 입력하고 생성합니다.',
    claude_guide_step7: '발급받은 API 키를 복사하여 위의 Claude API 키 입력란에 붙여넣습니다.',
    claude_guide_note1: '※ Claude API는 신용카드 등록이 필요하며, 사용량에 따라 요금이 청구됩니다.',
    claude_guide_note2: '※ API 키는 sk-ant-api03-... 형식으로 시작합니다.',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'OpenAI 웹사이트(https://platform.openai.com/signup)에 접속합니다.',
    chatgpt_guide_step2: '"Sign up" 버튼을 클릭하여 계정을 생성합니다.',
    chatgpt_guide_step3: '이메일 인증을 완료합니다.',
    chatgpt_guide_step4: '로그인 후 오른쪽 상단의 프로필 아이콘 우측의 Dashboard 클릭하고 좌측 메뉴의 "API keys"를 선택합니다.',
    chatgpt_guide_step5: '"Create new secret key" 버튼을 클릭합니다.',
    chatgpt_guide_step6: '키 이름을 입력하고 생성합니다.',
    chatgpt_guide_step7: '발급받은 API 키를 복사하여 위의 ChatGPT API 키 입력란에 붙여넣습니다.',
    chatgpt_guide_note1: '※ OpenAI API는 신용카드 등록이 필요하며, 사용량에 따라 요금이 청구됩니다.',
    chatgpt_guide_note2: '※ API 키는 sk-... 형식으로 시작합니다.',
    
    // Grok API 가이드
    grok_guide_step1: 'X.AI 웹사이트(https://x.ai)에 접속합니다.',
    grok_guide_step2: '계정으로 로그인합니다.',
    grok_guide_step3: '상단 API 메뉴를 클릭합니다.',
    grok_guide_step4: '"Start building now" 버튼을 클릭합니다.',
    grok_guide_step5: '좌측에 API Keys 메뉴를 클릭합니다.',
    grok_guide_step6: 'API 키를 발급받습니다.',
    grok_guide_step7: '발급받은 API 키를 복사하여 위의 Grok API 키 입력란에 붙여넣습니다.',
    grok_guide_note1: '※ API 키는 xai-... 형식으로 시작합니다.',
    
    // DeepL API 가이드
    deepl_guide_step1: 'DeepL API 웹사이트(https://www.deepl.com/pro-api)에 접속합니다.',
    deepl_guide_step2: '"Sign up for free" 버튼을 클릭합니다.',
    deepl_guide_step3: '이메일 주소와 비밀번호를 입력하여 계정을 생성합니다.',
    deepl_guide_step4: '계정 활성화를 위해 이메일 인증을 완료합니다.',
    deepl_guide_step5: '로그인 후 https://www.deepl.com/ko/your-account/subscription 계정 페이지로 이동합니다.',
    deepl_guide_step6: 'API keys 메뉴로 이동합니다(https://www.deepl.com/ko/your-account/keys)',
    deepl_guide_step7: '무료 버전의 API 키는 위의 DeepL API Key (무료) 입력란에 붙여넣습니다.',
    deepl_guide_step8: '유료 버전의 API 키는 위의 DeepL API Key (유료) 입력란에 붙여넣습니다.',
    deepl_guide_note1: '※ DeepL API 무료 버전은 월 50만 자까지 번역 가능합니다.',
    deepl_guide_note2: '※ 유료 버전으로 업그레이드하면 더 많은 텍스트를 번역할 수 있습니다.',
    deepl_guide_note3: '※ 저는 유료 버전으로 업그레이드하면 무료 버전의 API 는 사용 할 수 없었습니다. 참고하세요.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'free API 키는 https://api-free.deepl.com 엔드포인트를 사용해야 합니다.',
    deepl_api_help_pro: 'pro API 키는 https://api.deepl.com 엔드포인트를 사용해야 합니다.',
    deepl_api_help_error: '무료 API 키를 사용하면서 "Wrong endpoint. Use https://api.deepl.com" 오류가 발생한다면:',
    deepl_api_help_check1: '1. DeepL API (무료) 옵션을 선택했는지 확인하세요.',
    deepl_api_help_check2: '2. 실제로 무료 API 키를 사용하고 있는지 확인하세요.',
    
    // 영역 및 결과 관련
    original_text: '원문',
    translation: '번역',
    summary: '요약',
    definition: '정의',
    copy_original: '원문 복사',
    copy_translation: '번역문 복사',
    copy_summary: '요약 복사',
    copy_both: '둘다 복사',
    summarize_translation_result: '번역 결과 요약',
    debug_info: '디버그 정보',
    page_url: '페이지 URL',
    page_title: '페이지 제목',
    target_language: '대상 언어',
    request_prompt: '요청 프롬프트',
    api_response: 'API 응답',
    clipboard_copy_failed: '클립보드 복사 실패',
    
    // 알림 및 오류 메시지
    canceled: '취소 되었습니다',
    translation_canceled: '번역 작업이 취소되었습니다.',
    summary_canceled: '요약 작업이 취소되었습니다.',
    lookup_canceled: '용어 검색이 취소되었습니다.',
    operation_canceled: '작업이 취소되었습니다.',
    api_key_error: 'API 키 오류',
    api_key_missing: 'API 키가 설정되지 않았습니다. 확장 프로그램 설정에서 API 키를 설정해주세요.',
    goto_settings: '설정 페이지로 이동',
    error: '오류',
    translation_failed: '번역에 실패했습니다:',
    summary_failed: '요약에 실패했습니다:',
    lookup_failed: '용어 검색에 실패했습니다:',
    no_response: '응답 없음',
    
    // 로그 메시지
    menu_added: '메뉴가 추가되었습니다.',
    menu_add_error: '메뉴 추가 중 오류 발생:',
    menu_removed: '번역 메뉴 제거:',
    operation_applied: '이미 {operation}된 영역입니다. 기본 컨텍스트 메뉴를 표시합니다.',
    already_has_operation: '이미 {operation}이 포함된 영역입니다. 작업을 건너뜁니다.',
    rightclick_text: '우측 클릭으로 선택된 텍스트:',
    ctrl_rightclick: '컨트롤 + 우클릭 감지: 요약 실행',
    normal_rightclick: '일반 우클릭 감지: 번역 실행',
    doubleclick_text: '더블클릭으로 선택된 텍스트:',
    hovered_element: '호버된 요소:',
    summary_response: '요약 응답:',
    range_undefined: '범위가 정의되지 않았습니다.',
    inline_translation_insertion_error: '인라인 번역 삽입 오류:',
    inline_summary_insertion_error: '인라인 요약 삽입 오류:',
    fallback_insertion_error: '대체 삽입 오류:',
    copy_failed: '복사 실패:',
    
    // 도메인 컨텍스트
    domain_programming: '프로그래밍/소프트웨어 개발',
    domain_blog: '블로그/기술 아티클',
    domain_qa: '프로그래밍 Q&A',
    domain_docs: '기술 문서/API 문서',
    domain_academic: '학술/연구',
    domain_news: '뉴스/시사',
    domain_finance: '금융/투자',
    domain_medical: '의학/건강',
    domain_legal: '법률',
    domain_webpage: '웹페이지 제목:',
    
    // 초기화 메시지
    extension_init: '번역 확장 프로그램 초기화 중...',
    listeners_registered: '이벤트 리스너가 등록되었습니다.',
    doubleclick_registered: '더블클릭 이벤트 리스너가 등록되었습니다.',
    extension_ready: '번역 확장 프로그램이 준비되었습니다.'

    //filePanel.js
    ,fileListWillBeShownHere: '파일 목록이 여기에 표시됩니다.'

    //subtitleService.js
    ,subtitle_translation_enabled: '자막 실시간 번역이 활성화되었습니다.'
    ,subtitle_translation_disabled: '자막 실시간 번역이 비활성화되었습니다.'
    ,subtitle_translation_button: '자막 실시간 번역'
    ,runtime_not_initialized: 'Chrome 런타임이 초기화되지 않았습니다.'
    ,message_send_error: '메시지 전송 중 오류 발생:'
    ,translation_response_missing: '번역 응답이 없습니다.'
    ,translation_error: '자막 번역 오류:'
};

// 기본 내보내기로 언어 데이터 노출
export default ko;