// 중국어 간체 (Chinese Simplified) 언어 파일

const zhCN = {
    // 메뉴 및 UI 관련
    translate: '翻译',
    summarize: '摘要',
    lookup: '查找术语定义',
    cancel: '取消',
    copy: '复制',
    copied: '已复制',
    close: '关闭',
    translating: '翻译中...',
    summarizing: '摘要生成中...',
    looking_up: '术语搜索中...',
    cancel_with_esc: '(按ESC取消)',
    image_text_recognition: '图像文字识别',
    menu_addition_error: '添加菜单时出错:',
    summary_result: '摘要结果',
    copy_term_definition: '复制术语定义',
    
    //options.js
    deepl_free_api_key_error: 'API密钥无效。请检查API密钥。',
    deepl_free_api_key_warning: '警告：这似乎不是一个DeepL API密钥。请输入正确的DeepL免费API密钥。',
    deepl_pro_api_key_warning: '警告：这似乎不是一个DeepL API密钥。请输入正确的DeepL付费API密钥。',
    settings_save_error: '保存设置时出错。请重试。',
    saved_all_settings: '所有已保存的设置：',
    
    // 옵션 페이지 관련
    options_title: '翻译扩展程序设置',
    service_selection: '选择翻译服务',
    api_key: 'API密钥',
    model_selection: '选择模型',
    api_url: 'API URL (可选)',
    api_key_free: 'API密钥（免费）',
    api_key_pro: 'API密钥（付费）',
    interface_language: '界面语言',
    interface_language_desc: '扩展程序的菜单和消息将以选定的语言显示。',
    preferred_languages: '首选语言（只能选择一种语言）',
    save: '保存',
    settings_saved: '设置已保存。',
    
    // 새로 추가된 옵션 페이지 관련 텍스트
    debug_mode: '启用调试模式（用于故障排除）',
    debug_mode_desc: '启用调试模式后，错误消息和API通信信息将显示在浏览器控制台中。',
    api_guide_title: 'API注册指南',
    claude_api_guide_title: 'Claude API注册和密钥获取方法',
    chatgpt_api_guide_title: 'ChatGPT API注册和密钥获取方法',
    grok_api_guide_title: 'Grok API注册和密钥获取方法',
    deepl_api_guide_title: 'DeepL API注册和密钥获取方法',
    deepl_api_help_title: '使用DeepL API时的注意事项',
    
    // Claude API 가이드
    claude_guide_step1: '访问Anthropic网站(https://www.anthropic.com/api)。',
    claude_guide_step2: '点击右上角的"Sign up"按钮。',
    claude_guide_step3: '输入您的电子邮件和密码创建账户。',
    claude_guide_step4: '登录后，导航到"API Keys"标签。',
    claude_guide_step5: '点击"Create API Key"按钮。',
    claude_guide_step6: '输入密钥名称并创建。',
    claude_guide_step7: '复制生成的API密钥并粘贴到上面的Claude API密钥字段中。',
    claude_guide_note1: '※ Claude API需要注册信用卡，根据使用情况收费。',
    claude_guide_note2: '※ API密钥格式以sk-ant-api03-...开头。',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: '访问OpenAI网站(https://platform.openai.com/signup)。',
    chatgpt_guide_step2: '点击"Sign up"按钮创建账户。',
    chatgpt_guide_step3: '完成电子邮件验证。',
    chatgpt_guide_step4: '登录后，点击右上角个人资料图标旁边的Dashboard，然后从左侧菜单选择"API keys"。',
    chatgpt_guide_step5: '点击"Create new secret key"按钮。',
    chatgpt_guide_step6: '输入密钥名称并创建。',
    chatgpt_guide_step7: '复制生成的API密钥并粘贴到上面的ChatGPT API密钥字段中。',
    chatgpt_guide_note1: '※ OpenAI API需要注册信用卡，根据使用情况收费。',
    chatgpt_guide_note2: '※ API密钥格式以sk-...开头。',
    
    // Grok API 가이드
    grok_guide_step1: '访问X.AI网站(https://x.ai)。',
    grok_guide_step2: '使用您的账户登录。',
    grok_guide_step3: '点击顶部的API菜单。',
    grok_guide_step4: '点击"Start building now"按钮。',
    grok_guide_step5: '点击左侧的API Keys菜单。',
    grok_guide_step6: '获取您的API密钥。',
    grok_guide_step7: '复制生成的API密钥并粘贴到上面的Grok API密钥字段中。',
    grok_guide_note1: '※ API密钥格式以xai-...开头。',
    
    // DeepL API 가이드
    deepl_guide_step1: '访问DeepL API网站(https://www.deepl.com/pro-api)。',
    deepl_guide_step2: '点击"Sign up for free"按钮。',
    deepl_guide_step3: '输入您的电子邮件地址和密码创建账户。',
    deepl_guide_step4: '完成电子邮件验证以激活您的账户。',
    deepl_guide_step5: '登录后，导航到https://www.deepl.com/account/subscription。',
    deepl_guide_step6: '转到API keys菜单(https://www.deepl.com/account/keys)。',
    deepl_guide_step7: '将免费版API密钥粘贴到上面的DeepL API Key (免费)字段中。',
    deepl_guide_step8: '将付费版API密钥粘贴到上面的DeepL API Key (付费)字段中。',
    deepl_guide_note1: '※ DeepL API免费版每月可翻译多达50万字符。',
    deepl_guide_note2: '※ 升级到付费版可以翻译更多文本。',
    deepl_guide_note3: '※ 请注意，升级到付费版后，我无法使用免费版API。',
    
    // DeepL API 도움말
    deepl_api_help_free: '免费API密钥必须使用https://api-free.deepl.com端点。',
    deepl_api_help_pro: '付费API密钥必须使用https://api.deepl.com端点。',
    deepl_api_help_error: '如果您使用免费API密钥并收到"Wrong endpoint. Use https://api.deepl.com"错误：',
    deepl_api_help_check1: '1. 检查您是否选择了DeepL API（免费）选项。',
    deepl_api_help_check2: '2. 验证您实际上使用的是免费API密钥。',
    
    // 영역 및 결과 관련
    original_text: '原文',
    translation: '翻译',
    summary: '摘要',
    definition: '定义',
    copy_original: '复制原文',
    copy_translation: '复制翻译',
    copy_summary: '复制摘要',
    copy_both: '复制两者',
    summarize_translation_result: '总结翻译结果',
    debug_info: '调试信息',
    page_url: '页面URL',
    page_title: '页面标题',
    target_language: '目标语言',
    request_prompt: '请求提示',
    api_response: 'API响应',
    clipboard_copy_failed: '复制到剪贴板失败',
    
    // 알림 및 오류 메시지
    canceled: '已取消',
    translation_canceled: '翻译操作已取消。',
    summary_canceled: '摘要操作已取消。',
    lookup_canceled: '术语查询已取消。',
    operation_canceled: '操作已取消。',
    api_key_error: 'API密钥错误',
    api_key_missing: 'API密钥未设置。请在扩展程序设置中设置您的API密钥。',
    goto_settings: '转到设置页面',
    error: '错误',
    translation_failed: '翻译失败:',
    summary_failed: '摘要失败:',
    lookup_failed: '术语查询失败:',
    no_response: '无响应',
    
    // 로그 메시지
    menu_added: '菜单已添加。',
    menu_add_error: '添加菜单时出错:',
    menu_removed: '翻译菜单已移除:',
    operation_applied: '该区域已有{operation}。显示默认上下文菜单。',
    already_has_operation: '该区域已包含{operation}。跳过操作。',
    rightclick_text: '右键点击选择的文本:',
    ctrl_rightclick: '检测到Ctrl+右键点击: 执行摘要',
    normal_rightclick: '检测到普通右键点击: 执行翻译',
    doubleclick_text: '双击选择的文本:',
    hovered_element: '悬停元素:',
    summary_response: '摘要响应:',
    range_undefined: '范围未定义。',
    inline_translation_insertion_error: '内联翻译插入错误:',
    inline_summary_insertion_error: '内联摘要插入错误:',
    fallback_insertion_error: '备用插入错误:',
    copy_failed: '复制失败:',
    
    // 도메인 컨텍스트
    domain_programming: '编程/软件开发',
    domain_blog: '博客/技术文章',
    domain_qa: '编程问答',
    domain_docs: '技术文档/API文档',
    domain_academic: '学术/研究',
    domain_news: '新闻/时事',
    domain_finance: '金融/投资',
    domain_medical: '医学/健康',
    domain_legal: '法律',
    domain_webpage: '网页标题:',
    
    // 초기화 메시지
    extension_init: '正在初始化翻译扩展程序...',
    listeners_registered: '事件监听器已注册。',
    doubleclick_registered: '双击事件监听器已注册。',
    extension_ready: '翻译扩展程序已准备就绪。'

    //filePanel.js
    ,fileListWillBeShownHere: '文件列表将显示在这里。'

    //subtitleService.js
    ,subtitle_translation_enabled: '实时字幕翻译已启用。'
    ,subtitle_translation_disabled: '实时字幕翻译已禁用。'
    ,subtitle_translation_button: '实时字幕翻译'
    ,runtime_not_initialized: 'Chrome运行时未初始化。'
    ,message_send_error: '发送消息时出错:'
    ,translation_response_missing: '没有翻译响应。'
    ,translation_error: '字幕翻译错误:'
};

export default zhCN;