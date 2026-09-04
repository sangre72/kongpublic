// 아랍어 (Arabic) 언어 파일

const ar = {
    // 메뉴 및 UI 관련
    translate: 'ترجمة',
    summarize: 'تلخيص',
    lookup: 'بحث عن مصطلح',
    cancel: 'إلغاء',
    copy: 'نسخ',
    copied: 'تم النسخ',
    close: 'إغلاق',
    translating: 'جاري الترجمة...',
    summarizing: 'جاري التلخيص...',
    looking_up: 'جاري البحث...',
    cancel_with_esc: '(ESC للإلغاء)',
    image_text_recognition: 'التعرف على نص الصورة',
    menu_addition_error: 'خطأ في إضافة القائمة:',
    summary_result: 'نتيجة التلخيص',
    copy_term_definition: 'نسخ التعريف المصطلح',
    
    //options.js
    deepl_free_api_key_error: 'مفتاح API غير صالح. يرجى التحقق من مفتاح API.',
    deepl_free_api_key_warning: 'تحذير: لا يبدو أن هذا مفتاح API لـ DeepL. أدخل مفتاح API مجاني صحيح لـ DeepL.',
    deepl_pro_api_key_warning: 'تحذير: لا يبدو أن هذا مفتاح API لـ DeepL. أدخل مفتاح API مدفوع صحيح لـ DeepL.',
    settings_save_error: 'حدث خطأ أثناء حفظ الإعدادات. يرجى المحاولة مرة أخرى.',
    saved_all_settings: 'جميع الإعدادات المحفوظة:',
    
    // 옵션 페이지 관련
    options_title: 'إعدادات ملحق الترجمة',
    service_selection: 'اختيار خدمة الترجمة',
    api_key: 'مفتاح API',
    model_selection: 'اختيار النموذج',
    api_url: 'رابط API (اختياري)',
    api_key_free: 'مفتاح API (مجاني)',
    api_key_pro: 'مفتاح API (مدفوع)',
    interface_language: 'لغة الواجهة',
    interface_language_desc: 'ستظهر قوائم ورسائل الملحق باللغة المختارة.',
    preferred_languages: 'اللغات المفضلة (يمكن اختيار لغة واحدة فقط)',
    save: 'حفظ',
    settings_saved: 'تم حفظ الإعدادات.',
    
    // 디버그 모드
    debug_mode: 'تفعيل وضع التصحيح (لاستكشاف الأخطاء وإصلاحها)',
    debug_mode_desc: 'عند تفعيل وضع التصحيح، ستظهر رسائل الخطأ ومعلومات اتصال API في وحدة تحكم المتصفح.',
    api_guide_title: 'دليل تسجيل API',
    claude_api_guide_title: 'تسجيل Claude API وإنشاء المفتاح',
    chatgpt_api_guide_title: 'تسجيل ChatGPT API وإنشاء المفتاح',
    grok_api_guide_title: 'تسجيل Grok API وإنشاء المفتاح',
    deepl_api_guide_title: 'تسجيل DeepL API وإنشاء المفتاح',
    deepl_api_help_title: 'ملاحظات استخدام DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'قم بزيارة موقع Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'انقر على زر "Sign up" في الزاوية العلوية اليمنى.',
    claude_guide_step3: 'أدخل بريدك الإلكتروني وكلمة المرور لإنشاء حساب.',
    claude_guide_step4: 'بعد تسجيل الدخول، انتقل إلى تبويب "API Keys".',
    claude_guide_step5: 'انقر على زر "Create API Key".',
    claude_guide_step6: 'أعط المفتاح اسماً وقم بإنشائه.',
    claude_guide_step7: 'انسخ مفتاح API الذي تم إنشاؤه والصقه في حقل مفتاح Claude API أعلاه.',
    claude_guide_note1: '※ يتطلب Claude API تسجيل بطاقة ائتمان، الاستخدام مدفوع.',
    claude_guide_note2: '※ يبدأ مفتاح API بالصيغة sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'قم بزيارة موقع OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'انقر على زر "Sign up" لإنشاء حساب.',
    chatgpt_guide_step3: 'قم بتأكيد عنوان بريدك الإلكتروني.',
    chatgpt_guide_step4: 'بعد تسجيل الدخول، انقر على Dashboard بجانب صورة ملفك الشخصي واختر "API keys" من القائمة اليسرى.',
    chatgpt_guide_step5: 'انقر على زر "Create new secret key".',
    chatgpt_guide_step6: 'أعط المفتاح اسماً وقم بإنشائه.',
    chatgpt_guide_step7: 'انسخ مفتاح API الذي تم إنشاؤه والصقه في حقل مفتاح ChatGPT API أعلاه.',
    chatgpt_guide_note1: '※ يتطلب OpenAI API تسجيل بطاقة ائتمان، الاستخدام مدفوع.',
    chatgpt_guide_note2: '※ يبدأ مفتاح API بالصيغة sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'قم بزيارة موقع X.AI (https://x.ai).',
    grok_guide_step2: 'قم بتسجيل الدخول إلى حسابك.',
    grok_guide_step3: 'انقر على قائمة API في الأعلى.',
    grok_guide_step4: 'انقر على زر "Start building now".',
    grok_guide_step5: 'انقر على قائمة API Keys على اليسار.',
    grok_guide_step6: 'قم بإنشاء مفتاح API الخاص بك.',
    grok_guide_step7: 'انسخ مفتاح API الذي تم إنشاؤه والصقه في حقل مفتاح Grok API أعلاه.',
    grok_guide_note1: '※ يبدأ مفتاح API بالصيغة xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'قم بزيارة موقع DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'انقر على زر "Sign up for free".',
    deepl_guide_step3: 'أدخل بريدك الإلكتروني وكلمة المرور لإنشاء حساب.',
    deepl_guide_step4: 'قم بتأكيد عنوان بريدك الإلكتروني لتفعيل الحساب.',
    deepl_guide_step5: 'بعد تسجيل الدخول، انتقل إلى https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'اذهب إلى قائمة API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'الصق مفتاح API للنسخة المجانية في حقل DeepL API Key (مجاني) أعلاه.',
    deepl_guide_step8: 'الصق مفتاح API للنسخة المدفوعة في حقل DeepL API Key (مدفوع) أعلاه.',
    deepl_guide_note1: '※ النسخة المجانية من DeepL API تسمح بترجمة حتى 500,000 حرف شهرياً.',
    deepl_guide_note2: '※ بالانتقال إلى النسخة المدفوعة، يمكنك ترجمة المزيد من النصوص.',
    deepl_guide_note3: '※ ملاحظة: بعد الانتقال إلى النسخة المدفوعة، لم أتمكن من استخدام API المجاني. يرجى أخذ ذلك في الاعتبار.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'للمفتاح API المجاني يجب عليك استخدام نقطة النهاية https://api-free.deepl.com.',
    deepl_api_help_pro: 'للمفتاح API المدفوع يجب عليك استخدام نقطة النهاية https://api.deepl.com.',
    deepl_api_help_error: 'إذا تلقيت خطأ "Wrong endpoint. Use https://api.deepl.com" عند استخدام مفتاح API المجاني:',
    deepl_api_help_check1: '1. تحقق من أنك اخترت خيار DeepL API (مجاني).',
    deepl_api_help_check2: '2. تحقق من أنك تستخدم بالفعل مفتاح API مجاني.',
    
    // 영역 및 결과 관련
    original_text: 'النص الأصلي',
    translation: 'الترجمة',
    summary: 'الملخص',
    definition: 'التعريف',
    copy_original: 'نسخ الأصل',
    copy_translation: 'نسخ الترجمة',
    copy_summary: 'نسخ الملخص',
    copy_both: 'نسخ كليهما',
    summarize_translation_result: 'تلخيص نتيجة الترجمة',
    debug_info: 'معلومات التصحيح',
    page_url: 'رابط الصفحة',
    page_title: 'عنوان الصفحة',
    target_language: 'اللغة المستهدفة',
    request_prompt: 'طلب المطالبة',
    api_response: 'استجابة API',
    clipboard_copy_failed: 'فشل النسخ إلى الحافظة',
    
    // 알림 및 오류 메시지
    canceled: 'تم الإلغاء',
    translation_canceled: 'تم إلغاء الترجمة.',
    summary_canceled: 'تم إلغاء التلخيص.',
    lookup_canceled: 'تم إلغاء البحث عن المصطلح.',
    operation_canceled: 'تم إلغاء العملية.',
    api_key_error: 'خطأ في مفتاح API',
    api_key_missing: 'لم يتم تعيين مفتاح API. يرجى تعيين مفتاح API في إعدادات الملحق.',
    goto_settings: 'الانتقال إلى الإعدادات',
    error: 'خطأ',
    translation_failed: 'فشلت الترجمة:',
    summary_failed: 'فشل التلخيص:',
    lookup_failed: 'فشل البحث عن المصطلح:',
    no_response: 'لا توجد استجابة',
    
    // 로그 메시지
    menu_added: 'تمت إضافة القائمة.',
    menu_add_error: 'خطأ في إضافة القائمة:',
    menu_removed: 'تمت إزالة قائمة الترجمة:',
    operation_applied: 'المنطقة {operation} بالفعل. عرض القائمة السياقية الافتراضية.',
    already_has_operation: 'المنطقة لديها {operation} بالفعل. تخطي العملية.',
    rightclick_text: 'النص المحدد بالنقر بزر الماوس الأيمن:',
    ctrl_rightclick: 'تم اكتشاف Ctrl + النقر بزر الماوس الأيمن: تنفيذ التلخيص',
    normal_rightclick: 'تم اكتشاف النقر العادي بزر الماوس الأيمن: تنفيذ الترجمة',
    doubleclick_text: 'النص المحدد بالنقر المزدوج:',
    hovered_element: 'العنصر المحوم عليه:',
    summary_response: 'استجابة التلخيص:',
    range_undefined: 'النطاق غير محدد.',
    inline_translation_insertion_error: 'خطأ في إدراج الترجمة المضمنة:',
    inline_summary_insertion_error: 'خطأ في إدراج الملخص المضمن:',
    fallback_insertion_error: 'خطأ في إدراج النسخة الاحتياطية:',
    copy_failed: 'فشل النسخ:',
    
    // 도메인 컨텍스트
    domain_programming: 'البرمجة/تطوير البرمجيات',
    domain_blog: 'المدونة/المقالات التقنية',
    domain_qa: 'البرمجة س&ج',
    domain_docs: 'التوثيق التقني/توثيق API',
    domain_academic: 'أكاديمي/بحث',
    domain_news: 'أخبار/أحداث جارية',
    domain_finance: 'مالية/استثمار',
    domain_medical: 'طبي/صحة',
    domain_legal: 'قانوني',
    domain_webpage: 'عنوان صفحة الويب:',
    
    // 초기화 메시지
    extension_init: 'تهيئة ملحق الترجمة...',
    listeners_registered: 'تم تسجيل مستمعي الأحداث.',
    doubleclick_registered: 'تم تسجيل مستمع النقر المزدوج.',
    extension_ready: 'ملحق الترجمة جاهز.'

    //filePanel.js
    ,fileListWillBeShownHere: 'سيتم عرض قائمة الملفات هنا.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'تم تفعيل الترجمة الفورية للترجمات'
    ,subtitle_translation_disabled: 'تم تعطيل الترجمة الفورية للترجمات'
    ,subtitle_translation_button: 'الترجمة الفورية للترجمات'
    ,runtime_not_initialized: 'لم يتم تهيئة وقت تشغيل Chrome'
    ,message_send_error: 'خطأ في إرسال الرسالة:'
    ,translation_response_missing: 'لا توجد استجابة للترجمة'
    ,translation_error: 'خطأ في ترجمة الترجمات:'

};

export default ar; 