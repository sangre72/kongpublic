// 영어 (English) 언어 파일

const en = {
    // 메뉴 및 UI 관련
    translate: 'Translate',
    summarize: 'Summarize',
    lookup: 'Look up term',
    cancel: 'Cancel',
    copy: 'Copy',
    copied: 'Copied',
    close: 'Close',
    translating: 'Translating...',
    summarizing: 'Summarizing...',
    looking_up: 'Looking up term...',
    cancel_with_esc: '(Press ESC to cancel)',
    image_text_recognition: 'Image Text Recognition',
    menu_addition_error: 'Error adding menu:',
    summary_result: 'Summary Result',
    copy_term_definition: 'Copy Term Definition',
    
    //options.js
    deepl_free_api_key_error: 'API key is invalid. Please check the API key.',
    deepl_free_api_key_warning: 'Warning: This seems to be not a DeepL API key. Please enter the correct DeepL free API key.',
    deepl_pro_api_key_warning: 'Warning: This seems to be not a DeepL API key. Please enter the correct DeepL paid API key.',
    settings_save_error: 'Error saving settings. Please try again.',
    saved_all_settings: 'All saved settings:',
            
    // 옵션 페이지 관련
    options_title: 'Translation Extension Settings',
    service_selection: 'Select Translation Service',
    api_key: 'API Key',
    model_selection: 'Select Model',
    api_url: 'API URL (Optional)',
    api_key_free: 'API Key (Free)',
    api_key_pro: 'API Key (Pro)',
    interface_language: 'Interface Language',
    interface_language_desc: 'The extension menus and messages will be displayed in the selected language.',
    preferred_languages: 'Preferred Languages (Only one language can be selected)',
    save: 'Save',
    settings_saved: 'Settings saved.',
    
    // 새로 추가된 옵션 페이지 관련 텍스트
    debug_mode: 'Enable Debug Mode (for troubleshooting)',
    debug_mode_desc: 'When debug mode is enabled, error messages and API communication information will be displayed in the browser console.',
    api_guide_title: 'API Sign-up Guide',
    claude_api_guide_title: 'Claude API Registration and Key Issuance',
    chatgpt_api_guide_title: 'ChatGPT API Registration and Key Issuance',
    grok_api_guide_title: 'Grok API Registration and Key Issuance',
    deepl_api_guide_title: 'DeepL API Registration and Key Issuance',
    deepl_api_help_title: 'DeepL API Usage Notes',
    
    // Claude API 가이드
    claude_guide_step1: 'Go to the Anthropic website (https://www.anthropic.com/api).',
    claude_guide_step2: 'Click the "Sign up" button in the top right corner.',
    claude_guide_step3: 'Enter your email and password to create an account.',
    claude_guide_step4: 'After logging in, navigate to the "API Keys" tab.',
    claude_guide_step5: 'Click the "Create API Key" button.',
    claude_guide_step6: 'Enter a name for your key and create it.',
    claude_guide_step7: 'Copy the issued API key and paste it into the Claude API key field above.',
    claude_guide_note1: '※ Claude API requires credit card registration, and charges will be based on usage.',
    claude_guide_note2: '※ API keys start with the format sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Go to the OpenAI website (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Click the "Sign up" button to create an account.',
    chatgpt_guide_step3: 'Complete the email verification.',
    chatgpt_guide_step4: 'After logging in, click Dashboard next to your profile icon in the top right, then select "API keys" from the left menu.',
    chatgpt_guide_step5: 'Click the "Create new secret key" button.',
    chatgpt_guide_step6: 'Enter a name for your key and create it.',
    chatgpt_guide_step7: 'Copy the issued API key and paste it into the ChatGPT API key field above.',
    chatgpt_guide_note1: '※ OpenAI API requires credit card registration, and charges will be based on usage.',
    chatgpt_guide_note2: '※ API keys start with the format sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Go to the X.AI website (https://x.ai).',
    grok_guide_step2: 'Log in with your account.',
    grok_guide_step3: 'Click the API menu at the top.',
    grok_guide_step4: 'Click the "Start building now" button.',
    grok_guide_step5: 'Click the API Keys menu on the left.',
    grok_guide_step6: 'Get your API key.',
    grok_guide_step7: 'Copy the issued API key and paste it into the Grok API key field above.',
    grok_guide_note1: '※ API keys start with the format xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Go to the DeepL API website (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Click the "Sign up for free" button.',
    deepl_guide_step3: 'Enter your email address and password to create an account.',
    deepl_guide_step4: 'Complete the email verification to activate your account.',
    deepl_guide_step5: 'After logging in, navigate to https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Go to the API keys menu (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Paste the free version API key into the DeepL API Key (Free) field above.',
    deepl_guide_step8: 'Paste the paid version API key into the DeepL API Key (Pro) field above.',
    deepl_guide_note1: '※ DeepL API free version allows translation of up to 500,000 characters per month.',
    deepl_guide_note2: '※ Upgrading to the paid version allows you to translate more text.',
    deepl_guide_note3: '※ Note: I found that after upgrading to the paid version, I could no longer use the free version API.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Free API keys must use the https://api-free.deepl.com endpoint.',
    deepl_api_help_pro: 'Paid API keys must use the https://api.deepl.com endpoint.',
    deepl_api_help_error: 'If you are using a free API key and getting the error "Wrong endpoint. Use https://api.deepl.com" error:',
    deepl_api_help_check1: '1. Check that you have selected the DeepL API (Free) option.',
    deepl_api_help_check2: '2. Verify that you are actually using a free API key.',
    
    // 영역 및 결과 관련
    original_text: 'Original',
    translation: 'Translation',
    summary: 'Summary',
    definition: 'Definition',
    copy_original: 'Copy Original',
    copy_translation: 'Copy Translation',
    copy_summary: 'Copy Summary',
    copy_both: 'Copy Both',
    summarize_translation_result: 'Summarize Translation Result',
    debug_info: 'Debug Info',
    page_url: 'Page URL',
    page_title: 'Page Title',
    target_language: 'Target Language',
    request_prompt: 'Request Prompt',
    api_response: 'API Response',
    clipboard_copy_failed: 'Clipboard copy failed',
    
    // 알림 및 오류 메시지
    canceled: 'Canceled',
    translation_canceled: 'Translation has been canceled.',
    summary_canceled: 'Summary has been canceled.',
    lookup_canceled: 'Term lookup has been canceled.',
    operation_canceled: 'Operation has been canceled.',
    api_key_error: 'API Key Error',
    api_key_missing: 'API key is not set. Please set your API key in the extension settings.',
    goto_settings: 'Go to Settings',
    error: 'Error',
    translation_failed: 'Translation failed:',
    summary_failed: 'Summary failed:',
    lookup_failed: 'Term lookup failed:',
    no_response: 'No response',
    
    // 로그 메시지
    menu_added: 'Menu has been added.',
    menu_add_error: 'Error adding menu:',
    menu_removed: 'Translation menu removed:',
    operation_applied: 'This area already has a {operation}. Showing default context menu.',
    already_has_operation: 'This area already has a {operation}. Skipping operation.',
    rightclick_text: 'Right-clicked text:',
    ctrl_rightclick: 'Ctrl + right-click detected: Running summarization',
    normal_rightclick: 'Normal right-click detected: Running translation',
    doubleclick_text: 'Double-clicked text:',
    hovered_element: 'Hovered element:',
    summary_response: 'Summary response:',
    range_undefined: 'Range is undefined.',
    inline_translation_insertion_error: 'Inline translation insertion error:',
    inline_summary_insertion_error: 'Inline summary insertion error:',
    fallback_insertion_error: 'Fallback insertion error:',
    copy_failed: 'Copy failed:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programming/Software Development',
    domain_blog: 'Blog/Technical Article',
    domain_qa: 'Programming Q&A',
    domain_docs: 'Technical Documentation/API Docs',
    domain_academic: 'Academic/Research',
    domain_news: 'News',
    domain_finance: 'Finance/Investment',
    domain_medical: 'Medical/Health',
    domain_legal: 'Legal',
    domain_webpage: 'Webpage title:',
    
    // 초기화 메시지
    extension_init: 'Initializing translation extension...',
    listeners_registered: 'Event listeners have been registered.',
    doubleclick_registered: 'Double-click event listener has been registered.',
    extension_ready: 'Translation extension is ready.'

    //filePanel.js
    ,fileListWillBeShownHere: 'The list of files will be shown here.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Real-time subtitle translation has been enabled.'
    ,subtitle_translation_disabled: 'Real-time subtitle translation has been disabled.'
    ,subtitle_translation_button: 'Real-time subtitle translation'
    ,runtime_not_initialized: 'Chrome runtime has not been initialized.'
    ,message_send_error: 'Error sending message:'
    ,translation_response_missing: 'No translation response.'
    ,translation_error: 'Subtitle translation error:'
};

export default en;