// 스웨덴어 (Swedish) 언어 파일

const sv = {
    // 메뉴 및 UI 관련
    translate: 'Översätt',
    summarize: 'Sammanfatta',
    lookup: 'Slå upp term',
    cancel: 'Avbryt',
    copy: 'Kopiera',
    copied: 'Kopierad',
    close: 'Stäng',
    translating: 'Översätter...',
    summarizing: 'Sammanfattar...',
    looking_up: 'Slår upp...',
    cancel_with_esc: '(ESC för att avbryta)',
    image_text_recognition: 'Bildtextavkänning',
    menu_addition_error: 'Fel vid tillägg av meny:',
    summary_result: 'Sammanfattningsresultat',
    copy_term_definition: 'Kopiera termindefinition',

    //options.js
    deepl_free_api_key_error: 'API-nyckel är ogiltig. Kontrollera API-nyckeln.',
    deepl_free_api_key_warning: 'Varning: Detta ser ut att inte vara en DeepL API-nyckel. Vänligen ange den korrekta DeepL gratis API-nyckeln.',
    deepl_pro_api_key_warning: 'Varning: Detta ser ut att inte vara en DeepL API-nyckel. Vänligen ange den korrekta DeepL betalning API-nyckeln.',
    settings_save_error: 'Fel vid sparande av inställningar. Vänligen försök igen.',
    saved_all_settings: 'Alla sparade inställningar:',
    
    // 옵션 페이지 관련
    options_title: 'Inställningar för översättningstillägg',
    service_selection: 'Val av översättningstjänst',
    api_key: 'API-nyckel',
    model_selection: 'Modellval',
    api_url: 'API-URL (valfritt)',
    api_key_free: 'API-nyckel (gratis)',
    api_key_pro: 'API-nyckel (betald)',
    interface_language: 'Gränssnittsspråk',
    interface_language_desc: 'Tilläggets menyer och meddelanden kommer att visas på det valda språket.',
    preferred_languages: 'Föredragna språk (endast ett språk kan väljas)',
    save: 'Spara',
    settings_saved: 'Inställningar sparade.',
    
    // 디버그 모드
    debug_mode: 'Aktivera felsökningsläge (för felsökning)',
    debug_mode_desc: 'När felsökningsläget är aktiverat kommer felmeddelanden och API-kommunikationsinformation att visas i webbläsarens konsol.',
    api_guide_title: 'API-registreringsguide',
    claude_api_guide_title: 'Claude API-registrering och nyckelgenerering',
    chatgpt_api_guide_title: 'ChatGPT API-registrering och nyckelgenerering',
    grok_api_guide_title: 'Grok API-registrering och nyckelgenerering',
    deepl_api_guide_title: 'DeepL API-registrering och nyckelgenerering',
    deepl_api_help_title: 'Anteckningar om DeepL API-användning',
    
    // Claude API 가이드
    claude_guide_step1: 'Besök Anthropics webbplats (https://www.anthropic.com/api).',
    claude_guide_step2: 'Klicka på "Sign up"-knappen i övre högra hörnet.',
    claude_guide_step3: 'Ange din e-postadress och lösenord för att skapa ett konto.',
    claude_guide_step4: 'Efter inloggning, gå till fliken "API Keys".',
    claude_guide_step5: 'Klicka på knappen "Create API Key".',
    claude_guide_step6: 'Ge nyckeln ett namn och skapa den.',
    claude_guide_step7: 'Kopiera den genererade API-nyckeln och klistra in den i Claude API-nyckelfältet ovan.',
    claude_guide_note1: '※ Claude API kräver kreditkortsregistrering, användning är avgiftsbelagd.',
    claude_guide_note2: '※ API-nyckeln börjar med formatet sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Besök OpenAIs webbplats (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Klicka på "Sign up"-knappen för att skapa ett konto.',
    chatgpt_guide_step3: 'Bekräfta din e-postadress.',
    chatgpt_guide_step4: 'Efter inloggning, klicka på Dashboard bredvid din profilbild och välj "API keys" från vänstermenyn.',
    chatgpt_guide_step5: 'Klicka på knappen "Create new secret key".',
    chatgpt_guide_step6: 'Ge nyckeln ett namn och skapa den.',
    chatgpt_guide_step7: 'Kopiera den genererade API-nyckeln och klistra in den i ChatGPT API-nyckelfältet ovan.',
    chatgpt_guide_note1: '※ OpenAI API kräver kreditkortsregistrering, användning är avgiftsbelagd.',
    chatgpt_guide_note2: '※ API-nyckeln börjar med formatet sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Besök X.AIs webbplats (https://x.ai).',
    grok_guide_step2: 'Logga in på ditt konto.',
    grok_guide_step3: 'Klicka på API-menyn högst upp.',
    grok_guide_step4: 'Klicka på knappen "Start building now".',
    grok_guide_step5: 'Klicka på API Keys-menyn till vänster.',
    grok_guide_step6: 'Generera din API-nyckel.',
    grok_guide_step7: 'Kopiera den genererade API-nyckeln och klistra in den i Grok API-nyckelfältet ovan.',
    grok_guide_note1: '※ API-nyckeln börjar med formatet xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Besök DeepL API-webbplatsen (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Klicka på knappen "Sign up for free".',
    deepl_guide_step3: 'Ange din e-postadress och lösenord för att skapa ett konto.',
    deepl_guide_step4: 'Bekräfta din e-postadress för att aktivera kontot.',
    deepl_guide_step5: 'Efter inloggning, gå till https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Gå till API keys-menyn (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Klistra in API-nyckeln för gratisversionen i DeepL API Key (gratis)-fältet ovan.',
    deepl_guide_step8: 'Klistra in API-nyckeln för betalversionen i DeepL API Key (betald)-fältet ovan.',
    deepl_guide_note1: '※ Gratisversionen av DeepL API tillåter översättning av upp till 500 000 tecken per månad.',
    deepl_guide_note2: '※ Vid uppgradering till betalversionen kan du översätta mer text.',
    deepl_guide_note3: '※ Obs: Efter uppgradering till betalversionen kunde jag inte använda gratis-API:et. Vänligen notera detta.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'För gratis API-nyckel, använd endpoint https://api-free.deepl.com.',
    deepl_api_help_pro: 'För betald API-nyckel, använd endpoint https://api.deepl.com.',
    deepl_api_help_error: 'Om du får felet "Wrong endpoint. Use https://api.deepl.com" när du använder gratis API-nyckel:',
    deepl_api_help_check1: '1. Kontrollera att du har valt DeepL API (gratis)-alternativet.',
    deepl_api_help_check2: '2. Kontrollera att du verkligen använder en gratis API-nyckel.',
    
    // 영역 및 결과 관련
    original_text: 'Originaltext',
    translation: 'Översättning',
    summary: 'Sammanfattning',
    definition: 'Definition',
    copy_original: 'Kopiera original',
    copy_translation: 'Kopiera översättning',
    copy_summary: 'Kopiera sammanfattning',
    copy_both: 'Kopiera båda',
    summarize_translation_result: 'Sammanfatta översättningsresultat',
    debug_info: 'Felsökningsinformation',
    page_url: 'Sidans URL',
    page_title: 'Sidtitel',
    target_language: 'Målspråk',
    request_prompt: 'Begäran prompt',
    api_response: 'API-svar',
    clipboard_copy_failed: 'Kunde inte kopiera till urklipp',
    
    // 알림 및 오류 메시지
    canceled: 'Avbruten',
    translation_canceled: 'Översättning avbruten.',
    summary_canceled: 'Sammanfattning avbruten.',
    lookup_canceled: 'Uppslagning avbruten.',
    operation_canceled: 'Operation avbruten.',
    api_key_error: 'API-nyckelfel',
    api_key_missing: 'API-nyckeln är inte konfigurerad. Vänligen konfigurera API-nyckeln i tilläggets inställningar.',
    goto_settings: 'Gå till inställningar',
    error: 'Fel',
    translation_failed: 'Översättning misslyckades:',
    summary_failed: 'Sammanfattning misslyckades:',
    lookup_failed: 'Uppslagning misslyckades:',
    no_response: 'Inget svar',
    
    // 로그 메시지
    menu_added: 'Meny tillagd.',
    menu_add_error: 'Fel vid tillägg av meny:',
    menu_removed: 'Översättningsmeny borttagen:',
    operation_applied: 'Området är redan {operation}. Visar standardkontextmeny.',
    already_has_operation: 'Området har redan {operation}. Hoppar över operation.',
    rightclick_text: 'Text markerad med högerklick:',
    ctrl_rightclick: 'Ctrl + högerklick upptäckt: kör sammanfattning',
    normal_rightclick: 'Normal högerklick upptäckt: kör översättning',
    doubleclick_text: 'Text markerad med dubbelklick:',
    hovered_element: 'Element under muspekaren:',
    summary_response: 'Sammanfattningssvar:',
    range_undefined: 'Intervall odefinierat.',
    inline_translation_insertion_error: 'Fel vid infogning av inline-översättning:',
    inline_summary_insertion_error: 'Fel vid infogning av inline-sammanfattning:',
    fallback_insertion_error: 'Fel vid infogning av reservalternativ:',
    copy_failed: 'Kopiering misslyckades:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmering/Mjukvaruutveckling',
    domain_blog: 'Blogg/Tekniska artiklar',
    domain_qa: 'Programmering F&S',
    domain_docs: 'Teknisk dokumentation/API-dokumentation',
    domain_academic: 'Akademiskt/Forskning',
    domain_news: 'Nyheter/Aktualiteter',
    domain_finance: 'Finans/Investeringar',
    domain_medical: 'Medicin/Hälsa',
    domain_legal: 'Juridik',
    domain_webpage: 'Webbsidans titel:',
    
    // 초기화 메시지
    extension_init: 'Initierar översättningstillägg...',
    listeners_registered: 'Händelselyssnare registrerade.',
    doubleclick_registered: 'Dubbelklickslyssnare registrerad.',
    extension_ready: 'Översättningstillägget är redo.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Listan över filer visas här.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Realtidsöversättning av undertexter är aktiverad.'
    ,subtitle_translation_disabled: 'Realtidsöversättning av undertexter är inaktiverad.'
    ,subtitle_translation_button: 'Realtidsöversättning av undertexter'
    ,runtime_not_initialized: 'Chrome-runtime är inte initierad.'
    ,message_send_error: 'Fel vid sändning av meddelande:'
    ,translation_response_missing: 'Inget översättningssvar.'
    ,translation_error: 'Fel vid översättning av undertexter:'
};

export default sv; 