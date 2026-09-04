// 히브리어 (Hebrew) 언어 파일

const he = {
    // 메뉴 및 UI 관련
    translate: 'תרגם',
    summarize: 'סכם',
    lookup: 'חפש מונח',
    cancel: 'בטל',
    copy: 'העתק',
    copied: 'הועתק',
    close: 'סגור',
    translating: 'מתרגם...',
    summarizing: 'מסכם...',
    looking_up: 'מחפש...',
    cancel_with_esc: '(ESC לביטול)',
    image_text_recognition: 'זיהוי טקסט מתמונה',
    menu_addition_error: 'שגיאה בהוספת תפריט:',
    summary_result: 'תוצאת סיכום',
    copy_term_definition: 'העתק תיאור מונח',

    //options.js
    deepl_free_api_key_error: 'מפתח API אינו תקין. אנא בדוק את מפתח ה-API.',
    deepl_free_api_key_warning: 'הערה: זה נראה לא להיות מפתח API של DeepL. אנא הזינו את המפתח API של DeepL החינמי הנכון.',
    deepl_pro_api_key_warning: 'הערה: זה נראה לא להיות מפתח API של DeepL. אנא הזינו את המפתח API של DeepL המשולב הנכון.',
    settings_save_error: 'שגיאה בשמירת ההגדרות. אנא נסה שנית.',
    saved_all_settings: 'כל ההגדרות השמורות:',
    

    // 옵션 페이지 관련
    options_title: 'הגדרות תוסף התרגום',
    service_selection: 'בחירת שירות תרגום',
    api_key: 'מפתח API',
    model_selection: 'בחירת מודל',
    api_url: 'כתובת API (אופציונלי)',
    api_key_free: 'מפתח API (חינם)',
    api_key_pro: 'מפתח API (בתשלום)',
    interface_language: 'שפת ממשק',
    interface_language_desc: 'תפריטים והודעות התוסף יוצגו בשפה שנבחרה.',
    preferred_languages: 'שפות מועדפות (ניתן לבחור שפה אחת בלבד)',
    save: 'שמור',
    settings_saved: 'ההגדרות נשמרו.',
    
    // 디버그 모드
    debug_mode: 'הפעל מצב ניפוי שגיאות (לפתרון בעיות)',
    debug_mode_desc: 'כאשר מצב ניפוי שגיאות מופעל, הודעות שגיאה ומידע על תקשורת API יוצגו במסוף הדפדפן.',
    api_guide_title: 'מדריך הרשמה ל-API',
    claude_api_guide_title: 'הרשמה ויצירת מפתח Claude API',
    chatgpt_api_guide_title: 'הרשמה ויצירת מפתח ChatGPT API',
    grok_api_guide_title: 'הרשמה ויצירת מפתח Grok API',
    deepl_api_guide_title: 'הרשמה ויצירת מפתח DeepL API',
    deepl_api_help_title: 'הערות לשימוש ב-DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'בקר באתר Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'לחץ על כפתור "Sign up" בפינה הימנית העליונה.',
    claude_guide_step3: 'הזן את כתובת האימייל והסיסמה שלך ליצירת חשבון.',
    claude_guide_step4: 'לאחר ההתחברות, עבור ללשונית "API Keys".',
    claude_guide_step5: 'לחץ על כפתור "Create API Key".',
    claude_guide_step6: 'תן שם למפתח וצור אותו.',
    claude_guide_step7: 'העתק את מפתח ה-API שנוצר והדבק אותו בשדה מפתח Claude API למעלה.',
    claude_guide_note1: '※ Claude API דורש רישום כרטיס אשראי, השימוש בתשלום.',
    claude_guide_note2: '※ מפתח API מתחיל בתבנית sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'בקר באתר OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'לחץ על כפתור "Sign up" ליצירת חשבון.',
    chatgpt_guide_step3: 'אשר את כתובת האימייל שלך.',
    chatgpt_guide_step4: 'לאחר ההתחברות, לחץ על Dashboard ליד תמונת הפרופיל שלך ובחר "API keys" מהתפריט השמאלי.',
    chatgpt_guide_step5: 'לחץ על כפתור "Create new secret key".',
    chatgpt_guide_step6: 'תן שם למפתח וצור אותו.',
    chatgpt_guide_step7: 'העתק את מפתח ה-API שנוצר והדבק אותו בשדה מפתח ChatGPT API למעלה.',
    chatgpt_guide_note1: '※ OpenAI API דורש רישום כרטיס אשראי, השימוש בתשלום.',
    chatgpt_guide_note2: '※ מפתח API מתחיל בתבנית sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'בקר באתר X.AI (https://x.ai).',
    grok_guide_step2: 'התחבר לחשבון שלך.',
    grok_guide_step3: 'לחץ על תפריט API בחלק העליון.',
    grok_guide_step4: 'לחץ על כפתור "Start building now".',
    grok_guide_step5: 'לחץ על תפריט API Keys בצד שמאל.',
    grok_guide_step6: 'צור את מפתח ה-API שלך.',
    grok_guide_step7: 'העתק את מפתח ה-API שנוצר והדבק אותו בשדה מפתח Grok API למעלה.',
    grok_guide_note1: '※ מפתח API מתחיל בתבנית xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'בקר באתר DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'לחץ על כפתור "Sign up for free".',
    deepl_guide_step3: 'הזן את כתובת האימייל והסיסמה שלך ליצירת חשבון.',
    deepl_guide_step4: 'אשר את כתובת האימייל שלך להפעלת החשבון.',
    deepl_guide_step5: 'לאחר ההתחברות, עבור ל-https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'עבור לתפריט API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'הדבק את מפתח ה-API של הגרסה החינמית בשדה DeepL API Key (חינם) למעלה.',
    deepl_guide_step8: 'הדבק את מפתח ה-API של הגרסה בתשלום בשדה DeepL API Key (בתשלום) למעלה.',
    deepl_guide_note1: '※ הגרסה החינמית של DeepL API מאפשרת תרגום של עד 500,000 תווים בחודש.',
    deepl_guide_note2: '※ במעבר לגרסה בתשלום תוכל לתרגם יותר טקסט.',
    deepl_guide_note3: '※ הערה: לאחר המעבר לגרסה בתשלום, לא יכולתי להשתמש ב-API החינמי. אנא קח זאת בחשבון.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'עבור מפתח API חינמי, עליך להשתמש בנקודת הקצה https://api-free.deepl.com.',
    deepl_api_help_pro: 'עבור מפתח API בתשלום, עליך להשתמש בנקודת הקצה https://api.deepl.com.',
    deepl_api_help_error: 'אם אתה מקבל את השגיאה "Wrong endpoint. Use https://api.deepl.com" בעת שימוש במפתח API חינמי:',
    deepl_api_help_check1: '1. בדוק שבחרת באפשרות DeepL API (חינם).',
    deepl_api_help_check2: '2. בדוק שאתה אכן משתמש במפתח API חינמי.',
    
    // 영역 및 결과 관련
    original_text: 'טקסט מקורי',
    translation: 'תרגום',
    summary: 'סיכום',
    definition: 'הגדרה',
    copy_original: 'העתק מקור',
    copy_translation: 'העתק תרגום',
    copy_summary: 'העתק סיכום',
    copy_both: 'העתק שניהם',
    summarize_translation_result: 'סכם תוצאת תרגום',
    debug_info: 'מידע ניפוי שגיאות',
    page_url: 'כתובת דף',
    page_title: 'כותרת דף',
    target_language: 'שפת יעד',
    request_prompt: 'בקשת הנחיה',
    api_response: 'תגובת API',
    clipboard_copy_failed: 'העתקה ללוח לא הצליחה',
    
    // 알림 및 오류 메시지
    canceled: 'בוטל',
    translation_canceled: 'התרגום בוטל.',
    summary_canceled: 'הסיכום בוטל.',
    lookup_canceled: 'החיפוש בוטל.',
    operation_canceled: 'הפעולה בוטלה.',
    api_key_error: 'שגיאת מפתח API',
    api_key_missing: 'מפתח API לא מוגדר. אנא הגדר את מפתח ה-API בהגדרות התוסף.',
    goto_settings: 'עבור להגדרות',
    error: 'שגיאה',
    translation_failed: 'התרגום נכשל:',
    summary_failed: 'הסיכום נכשל:',
    lookup_failed: 'החיפוש נכשל:',
    no_response: 'אין תגובה',
    
    // 로그 메시지
    menu_added: 'התפריט נוסף.',
    menu_add_error: 'שגיאה בהוספת תפריט:',
    menu_removed: 'תפריט התרגום הוסר:',
    operation_applied: 'האזור כבר {operation}. מציג תפריט הקשר ברירת מחדל.',
    already_has_operation: 'לאזור כבר יש {operation}. מדלג על הפעולה.',
    rightclick_text: 'טקסט שנבחר בלחיצה ימנית:',
    ctrl_rightclick: 'Ctrl + לחיצה ימנית זוהתה: מבצע סיכום',
    normal_rightclick: 'לחיצה ימנית רגילה זוהתה: מבצע תרגום',
    doubleclick_text: 'טקסט שנבחר בלחיצה כפולה:',
    hovered_element: 'אלמנט תחת העכבר:',
    summary_response: 'תגובת סיכום:',
    range_undefined: 'טווח לא מוגדר.',
    inline_translation_insertion_error: 'שגיאה בהכנסת תרגום מוטבע:',
    inline_summary_insertion_error: 'שגיאה בהכנסת סיכום מוטבע:',
    fallback_insertion_error: 'שגיאה בהכנסת גיבוי:',
    copy_failed: 'ההעתקה נכשלה:',
    
    // 도메인 컨텍스트
    domain_programming: 'תכנות/פיתוח תוכנה',
    domain_blog: 'בלוג/מאמרים טכניים',
    domain_qa: 'תכנות שאלות ותשובות',
    domain_docs: 'תיעוד טכני/תיעוד API',
    domain_academic: 'אקדמי/מחקר',
    domain_news: 'חדשות/אקטואליה',
    domain_finance: 'פיננסים/השקעות',
    domain_medical: 'רפואי/בריאות',
    domain_legal: 'משפטי',
    domain_webpage: 'כותרת דף אינטרנט:',
    
    // 초기화 메시지
    extension_init: 'מאתחל תוסף תרגום...',
    listeners_registered: 'מאזיני אירועים נרשמו.',
    doubleclick_registered: 'מאזין לחיצה כפולה נרשם.',
    extension_ready: 'תוסף התרגום מוכן.'

    //filePanel.js
    ,fileListWillBeShownHere: 'רשימת הקבצים יוצגה כאן.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'תרגום כתוביות בזמן אמת הופעל.'
    ,subtitle_translation_disabled: 'תרגום כתוביות בזמן אמת הושבת.'
    ,subtitle_translation_button: 'תרגום כתוביות בזמן אמת'
    ,runtime_not_initialized: 'זמן ריצה של Chrome לא אותחל.'
    ,message_send_error: 'שגיאה בשליחת הודעה:'
    ,translation_response_missing: 'אין תגובת תרגום.'
    ,translation_error: 'שגיאה בתרגום כתוביות:'
};

export default he; 