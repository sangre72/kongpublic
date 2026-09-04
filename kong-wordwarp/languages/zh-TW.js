// 중국어 번체 (Chinese Traditional) 언어 파일

const zhTW = {
    // 메뉴 및 UI 관련
    translate: '翻譯',
    summarize: '摘要',
    lookup: '查詢術語定義',
    cancel: '取消',
    copy: '複製',
    copied: '已複製',
    close: '關閉',
    translating: '翻譯中...',
    summarizing: '摘要生成中...',
    looking_up: '術語搜索中...',
    cancel_with_esc: '(按ESC取消)',
    image_text_recognition: '圖像文字識別',
    menu_addition_error: '添加菜單時出錯:',
    summary_result: '摘要結果',
    copy_term_definition: '複製術語定義',
    
    //options.js
    deepl_free_api_key_error: 'API密鑰無效。請檢查API密鑰。',
    deepl_free_api_key_warning: '警告：這似乎不是一個DeepL API密鑰。請輸入正確的DeepL免費API密鑰。',
    deepl_pro_api_key_warning: '警告：這似乎不是一個DeepL API密鑰。請輸入正確的DeepL付費API密鑰。',
    settings_save_error: '保存設置時出錯。請重試。',
    saved_all_settings: '所有已保存的設置：',
    
    // 옵션 페이지 관련
    options_title: '翻譯擴展程序設置',
    service_selection: '選擇翻譯服務',
    api_key: 'API密鑰',
    model_selection: '選擇模型',
    api_url: 'API URL (可選)',
    api_key_free: 'API密鑰（免費）',
    api_key_pro: 'API密鑰（付費）',
    interface_language: '界面語言',
    interface_language_desc: '擴展程序的菜單和消息將以選定的語言顯示。',
    preferred_languages: '首選語言（只能選擇一種語言）',
    save: '保存',
    settings_saved: '設置已保存。',
    
    // 새로 추가된 옵션 페이지 관련 텍스트
    debug_mode: '啟用調試模式（用於故障排除）',
    debug_mode_desc: '啟用調試模式後，錯誤消息和API通信信息將顯示在瀏覽器控制台中。',
    api_guide_title: 'API註冊指南',
    claude_api_guide_title: 'Claude API註冊和密鑰獲取方法',
    chatgpt_api_guide_title: 'ChatGPT API註冊和密鑰獲取方法',
    grok_api_guide_title: 'Grok API註冊和密鑰獲取方法',
    deepl_api_guide_title: 'DeepL API註冊和密鑰獲取方法',
    deepl_api_help_title: '使用DeepL API時的注意事項',
    
    // Claude API 가이드
    claude_guide_step1: '訪問Anthropic網站(https://www.anthropic.com/api)。',
    claude_guide_step2: '點擊右上角的"Sign up"按鈕。',
    claude_guide_step3: '輸入您的電子郵件和密碼創建帳戶。',
    claude_guide_step4: '登錄後，導航到"API Keys"標籤。',
    claude_guide_step5: '點擊"Create API Key"按鈕。',
    claude_guide_step6: '輸入密鑰名稱並創建。',
    claude_guide_step7: '複製生成的API密鑰並粘貼到上面的Claude API密鑰字段中。',
    claude_guide_note1: '※ Claude API需要註冊信用卡，根據使用情況收費。',
    claude_guide_note2: '※ API密鑰格式以sk-ant-api03-...開頭。',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: '訪問OpenAI網站(https://platform.openai.com/signup)。',
    chatgpt_guide_step2: '點擊"Sign up"按鈕創建帳戶。',
    chatgpt_guide_step3: '完成電子郵件驗證。',
    chatgpt_guide_step4: '登錄後，點擊右上角個人資料圖標旁邊的Dashboard，然後從左側菜單選擇"API keys"。',
    chatgpt_guide_step5: '點擊"Create new secret key"按鈕。',
    chatgpt_guide_step6: '輸入密鑰名稱並創建。',
    chatgpt_guide_step7: '複製生成的API密鑰並粘貼到上面的ChatGPT API密鑰字段中。',
    chatgpt_guide_note1: '※ OpenAI API需要註冊信用卡，根據使用情況收費。',
    chatgpt_guide_note2: '※ API密鑰格式以sk-...開頭。',
    
    // Grok API 가이드
    grok_guide_step1: '訪問X.AI網站(https://x.ai)。',
    grok_guide_step2: '使用您的帳戶登錄。',
    grok_guide_step3: '點擊頂部的API菜單。',
    grok_guide_step4: '點擊"Start building now"按鈕。',
    grok_guide_step5: '點擊左側的API Keys菜單。',
    grok_guide_step6: '獲取您的API密鑰。',
    grok_guide_step7: '複製生成的API密鑰並粘貼到上面的Grok API密鑰字段中。',
    grok_guide_note1: '※ API密鑰格式以xai-...開頭。',
    
    // DeepL API 가이드
    deepl_guide_step1: '訪問DeepL API網站(https://www.deepl.com/pro-api)。',
    deepl_guide_step2: '點擊"Sign up for free"按鈕。',
    deepl_guide_step3: '輸入您的電子郵件地址和密碼創建帳戶。',
    deepl_guide_step4: '完成電子郵件驗證以激活您的帳戶。',
    deepl_guide_step5: '登錄後，導航到https://www.deepl.com/account/subscription。',
    deepl_guide_step6: '轉到API keys菜單(https://www.deepl.com/account/keys)。',
    deepl_guide_step7: '將免費版API密鑰粘貼到上面的DeepL API Key（免費）字段中。',
    deepl_guide_step8: '將付費版API密鑰粘貼到上面的DeepL API Key（付費）字段中。',
    deepl_guide_note1: '※ DeepL API免費版每月可翻譯多達50萬字符。',
    deepl_guide_note2: '※ 升級到付費版可以翻譯更多文本。',
    deepl_guide_note3: '※ 請注意，升級到付費版後，我無法使用免費版API。',
    
    // DeepL API 도움말
    deepl_api_help_free: '免費API密鑰必須使用https://api-free.deepl.com端點。',
    deepl_api_help_pro: '付費API密鑰必須使用https://api.deepl.com端點。',
    deepl_api_help_error: '如果您使用免費API密鑰並收到"Wrong endpoint. Use https://api.deepl.com"錯誤：',
    deepl_api_help_check1: '1. 檢查您是否選擇了DeepL API（免費）選項。',
    deepl_api_help_check2: '2. 驗證您實際上使用的是免費API密鑰。',
    
    // 영역 및 결과 관련
    original_text: '原文',
    translation: '翻譯',
    summary: '摘要',
    definition: '定義',
    copy_original: '複製原文',
    copy_translation: '複製翻譯',
    copy_summary: '複製摘要',
    copy_both: '複製兩者',
    summarize_translation_result: '總結翻譯結果',
    debug_info: '調試信息',
    page_url: '頁面URL',
    page_title: '頁面標題',
    target_language: '目標語言',
    request_prompt: '請求提示',
    api_response: 'API響應',
    clipboard_copy_failed: '複製到剪貼板失敗',
    
    // 알림 및 오류 메시지
    canceled: '已取消',
    translation_canceled: '翻譯操作已取消。',
    summary_canceled: '摘要操作已取消。',
    lookup_canceled: '術語查詢已取消。',
    operation_canceled: '操作已取消。',
    api_key_error: 'API密鑰錯誤',
    api_key_missing: 'API密鑰未設置。請在擴展程序設置中設置您的API密鑰。',
    goto_settings: '轉到設置頁面',
    error: '錯誤',
    translation_failed: '翻譯失敗:',
    summary_failed: '摘要失敗:',
    lookup_failed: '術語查詢失敗:',
    no_response: '無響應',
    
    // 로그 메시지
    menu_added: '菜單已添加。',
    menu_add_error: '添加菜單時出錯:',
    menu_removed: '翻譯菜單已移除:',
    operation_applied: '該區域已有{operation}。顯示默認上下文菜單。',
    already_has_operation: '該區域已包含{operation}。跳過操作。',
    rightclick_text: '右鍵點擊選擇的文本:',
    ctrl_rightclick: '檢測到Ctrl+右鍵點擊: 執行摘要',
    normal_rightclick: '檢測到普通右鍵點擊: 執行翻譯',
    doubleclick_text: '雙擊選擇的文本:',
    hovered_element: '懸停元素:',
    summary_response: '摘要響應:',
    range_undefined: '範圍未定義。',
    inline_translation_insertion_error: '內聯翻譯插入錯誤:',
    inline_summary_insertion_error: '內聯摘要插入錯誤:',
    fallback_insertion_error: '備用插入錯誤:',
    copy_failed: '複製失敗:',
    
    // 도메인 컨텍스트
    domain_programming: '程式設計/軟體開發',
    domain_blog: '博客/技術文章',
    domain_qa: '程式設計問答',
    domain_docs: '技術文檔/API文檔',
    domain_academic: '學術/研究',
    domain_news: '新聞/時事',
    domain_finance: '金融/投資',
    domain_medical: '醫學/健康',
    domain_legal: '法律',
    domain_webpage: '網頁標題:',
    
    // 초기화 메시지
    extension_init: '正在初始化翻譯擴展程序...',
    listeners_registered: '事件監聽器已註冊。',
    doubleclick_registered: '雙擊事件監聽器已註冊。',
    extension_ready: '翻譯擴展程序已準備就緒。'

    //filePanel.js
    ,fileListWillBeShownHere: '文件列表將顯示在這裡。'

    //subtitleService.js
    ,subtitle_translation_enabled: '即時字幕翻譯已啟用。'
    ,subtitle_translation_disabled: '即時字幕翻譯已停用。'
    ,subtitle_translation_button: '即時字幕翻譯'
    ,runtime_not_initialized: 'Chrome執行環境尚未初始化。'
    ,message_send_error: '傳送訊息時發生錯誤:'
    ,translation_response_missing: '沒有翻譯回應。'
    ,translation_error: '字幕翻譯錯誤:'
};

export default zhTW;