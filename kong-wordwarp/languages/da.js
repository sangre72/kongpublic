// 덴마크어 (Danish) 언어 파일

const da = {
    // 메뉴 및 UI 관련
    translate: 'Oversæt',
    summarize: 'Opsummér',
    lookup: 'Slå op',
    cancel: 'Annuller',
    copy: 'Kopiér',
    copied: 'Kopieret',
    close: 'Luk',
    translating: 'Oversætter...',
    summarizing: 'Opsummerer...',
    looking_up: 'Slår op...',
    cancel_with_esc: '(ESC for at annullere)',
    image_text_recognition: 'Genkendelse af tekst fra billede',
    menu_addition_error: 'Fejl ved tilføjelse af menu:',
    summary_result: 'Opsummér resultat',
    copy_term_definition: 'Kopér termindefinition',
    
    //options.js
    deepl_free_api_key_error: 'API-nøgle er ugyldig. Kontroller API-nøglen.',
    deepl_free_api_key_warning: 'Advarsel: Dette ser ud til at være en DeepL API-nøgle, men det er ikke en gyldig DeepL API-nøgle.',
    deepl_pro_api_key_warning: 'Advarsel: Dette ser ud til at være en DeepL API-nøgle, men det er ikke en gyldig DeepL API-nøgle.',
    settings_save_error: 'Fejl ved gemning af indstillinger. Prøv igen.',
    saved_all_settings: 'Gemte alle indstillinger:',
    
    // 옵션 페이지 관련
    options_title: 'Indstillinger for oversættelsesudvidelse',
    service_selection: 'Valg af oversættelsestjeneste',
    api_key: 'API-nøgle',
    model_selection: 'Modelvalg',
    api_url: 'API URL (valgfrit)',
    api_key_free: 'API-nøgle (gratis)',
    api_key_pro: 'API-nøgle (betalt)',
    interface_language: 'Grænsefladesprog',
    interface_language_desc: 'Udvidelsens menuer og beskeder vil blive vist på det valgte sprog.',
    preferred_languages: 'Foretrukne sprog (kun ét sprog kan vælges)',
    save: 'Gem',
    settings_saved: 'Indstillinger gemt.',
    
    // 디버그 모드
    debug_mode: 'Aktivér fejlfindingstilstand (til fejlsøgning)',
    debug_mode_desc: 'Når fejlfindingstilstand er aktiveret, vil fejlmeddelelser og API-kommunikationsinformation blive vist i browserkonsollen.',
    api_guide_title: 'API-registreringsvejledning',
    claude_api_guide_title: 'Claude API-registrering og nøglegenerering',
    chatgpt_api_guide_title: 'ChatGPT API-registrering og nøglegenerering',
    grok_api_guide_title: 'Grok API-registrering og nøglegenerering',
    deepl_api_guide_title: 'DeepL API-registrering og nøglegenerering',
    deepl_api_help_title: 'Bemærkninger om brug af DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Besøg Anthropic-hjemmesiden (https://www.anthropic.com/api).',
    claude_guide_step2: 'Klik på "Sign up"-knappen i øverste højre hjørne.',
    claude_guide_step3: 'Indtast din e-mail og adgangskode for at oprette en konto.',
    claude_guide_step4: 'Efter login, gå til fanen "API Keys".',
    claude_guide_step5: 'Klik på knappen "Create API Key".',
    claude_guide_step6: 'Giv nøglen et navn og opret den.',
    claude_guide_step7: 'Kopiér den genererede API-nøgle og indsæt den i Claude API-nøglefeltet ovenfor.',
    claude_guide_note1: '※ Claude API kræver kreditkortregistrering, brug er mod betaling.',
    claude_guide_note2: '※ API-nøgle starter med formatet sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Besøg OpenAI-hjemmesiden (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Klik på "Sign up"-knappen for at oprette en konto.',
    chatgpt_guide_step3: 'Bekræft din e-mailadresse.',
    chatgpt_guide_step4: 'Efter login, klik på Dashboard ved siden af dit profilbillede og vælg "API keys" fra venstre menu.',
    chatgpt_guide_step5: 'Klik på knappen "Create new secret key".',
    chatgpt_guide_step6: 'Giv nøglen et navn og opret den.',
    chatgpt_guide_step7: 'Kopiér den genererede API-nøgle og indsæt den i ChatGPT API-nøglefeltet ovenfor.',
    chatgpt_guide_note1: '※ OpenAI API kræver kreditkortregistrering, brug er mod betaling.',
    chatgpt_guide_note2: '※ API-nøgle starter med formatet sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Besøg X.AI-hjemmesiden (https://x.ai).',
    grok_guide_step2: 'Log ind på din konto.',
    grok_guide_step3: 'Klik på API-menuen øverst.',
    grok_guide_step4: 'Klik på knappen "Start building now".',
    grok_guide_step5: 'Klik på API Keys-menuen til venstre.',
    grok_guide_step6: 'Generér din API-nøgle.',
    grok_guide_step7: 'Kopiér den genererede API-nøgle og indsæt den i Grok API-nøglefeltet ovenfor.',
    grok_guide_note1: '※ API-nøgle starter med formatet xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Besøg DeepL API-hjemmesiden (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Klik på knappen "Sign up for free".',
    deepl_guide_step3: 'Indtast din e-mail og adgangskode for at oprette en konto.',
    deepl_guide_step4: 'Bekræft din e-mailadresse for at aktivere kontoen.',
    deepl_guide_step5: 'Efter login, gå til https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Gå til API keys-menuen (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Indsæt API-nøglen for den gratis version i DeepL API Key (gratis)-feltet ovenfor.',
    deepl_guide_step8: 'Indsæt API-nøglen for den betalte version i DeepL API Key (betalt)-feltet ovenfor.',
    deepl_guide_note1: '※ Den gratis version af DeepL API tillader oversættelse af op til 500.000 tegn pr. måned.',
    deepl_guide_note2: '※ Ved at opgradere til den betalte version kan du oversætte mere tekst.',
    deepl_guide_note3: '※ Bemærk: Efter opgradering til den betalte version kunne jeg ikke bruge det gratis API. Tag venligst højde for dette.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'For den gratis API-nøgle skal du bruge endepunktet https://api-free.deepl.com.',
    deepl_api_help_pro: 'For den betalte API-nøgle skal du bruge endepunktet https://api.deepl.com.',
    deepl_api_help_error: 'Hvis du får fejlen "Wrong endpoint. Use https://api.deepl.com" ved brug af den gratis API-nøgle:',
    deepl_api_help_check1: '1. Kontrollér, at du har valgt DeepL API (gratis)-muligheden.',
    deepl_api_help_check2: '2. Kontrollér, at du faktisk bruger en gratis API-nøgle.',
    
    // 영역 및 결과 관련
    original_text: 'Original tekst',
    translation: 'Oversættelse',
    summary: 'Opsummering',
    definition: 'Definition',
    copy_original: 'Kopiér original',
    copy_translation: 'Kopiér oversættelse',
    copy_summary: 'Kopiér opsummering',
    copy_both: 'Kopiér begge',
    summarize_translation_result: 'Opsummér oversættelsesresultat',
    debug_info: 'Fejlfindingsinformation',
    page_url: 'Side-URL',
    page_title: 'Sidetitel',
    target_language: 'Målsprog',
    request_prompt: 'Anmodningsprompt',
    api_response: 'API-svar',
    clipboard_copy_failed: 'Kopiering til udklipsholder mislykkedes',
    
    // 알림 및 오류 메시지
    canceled: 'Annulleret',
    translation_canceled: 'Oversættelse annulleret.',
    summary_canceled: 'Opsummering annulleret.',
    lookup_canceled: 'Opslag annulleret.',
    operation_canceled: 'Operation annulleret.',
    api_key_error: 'API-nøglefejl',
    api_key_missing: 'API-nøgle er ikke indstillet. Indstil venligst API-nøglen i udvidelsesindstillingerne.',
    goto_settings: 'Gå til indstillinger',
    error: 'Fejl',
    translation_failed: 'Oversættelse mislykkedes:',
    summary_failed: 'Opsummering mislykkedes:',
    lookup_failed: 'Opslag mislykkedes:',
    no_response: 'Intet svar',
    
    // 로그 메시지
    menu_added: 'Menu tilføjet.',
    menu_add_error: 'Fejl ved tilføjelse af menu:',
    menu_removed: 'Oversættelsesmenu fjernet:',
    operation_applied: 'Område er allerede {operation}. Viser standard kontekstmenu.',
    already_has_operation: 'Område har allerede {operation}. Springer operation over.',
    rightclick_text: 'Tekst valgt med højreklik:',
    ctrl_rightclick: 'Ctrl + højreklik registreret: udfører opsummering',
    normal_rightclick: 'Normalt højreklik registreret: udfører oversættelse',
    doubleclick_text: 'Tekst valgt med dobbeltklik:',
    hovered_element: 'Element under markør:',
    summary_response: 'Opsummeringssvar:',
    range_undefined: 'Område er ikke defineret.',
    inline_translation_insertion_error: 'Fejl ved indsættelse af inline oversættelse:',
    inline_summary_insertion_error: 'Fejl ved indsættelse af inline opsummering:',
    fallback_insertion_error: 'Fejl ved indsættelse af fallback:',
    copy_failed: 'Kopiering mislykkedes:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmering/Softwareudvikling',
    domain_blog: 'Blog/Tekniske artikler',
    domain_qa: 'Programmering Q&A',
    domain_docs: 'Teknisk dokumentation/API-dokumentation',
    domain_academic: 'Akademisk/Forskning',
    domain_news: 'Nyheder/Aktualitet',
    domain_finance: 'Finans/Investering',
    domain_medical: 'Medicinsk/Sundhedspleje',
    domain_legal: 'Juridisk',
    domain_webpage: 'Websidetitel:',
    
    // 초기화 메시지
    extension_init: 'Initialiserer oversættelsesudvidelse...',
    listeners_registered: 'Begivenhedslyttere registreret.',
    doubleclick_registered: 'Dobbeltklikslytter registreret.',
    extension_ready: 'Oversættelsesudvidelse er klar.'

    ,fileListWillBeShownHere: 'Liste over filer vil blive vist her.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Realtidsoversættelse af undertekster er aktiveret.'
    ,subtitle_translation_disabled: 'Realtidsoversættelse af undertekster er deaktiveret.'
    ,subtitle_translation_button: 'Realtidsoversættelse af undertekster'
    ,runtime_not_initialized: 'Chrome runtime er ikke initialiseret.'
    ,message_send_error: 'Fejl ved afsendelse af besked:'
    ,translation_response_missing: 'Intet oversættelsessvar.'
    ,translation_error: 'Fejl ved oversættelse af undertekster:'
};

export default da; 