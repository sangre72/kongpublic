// 네덜란드어 (Dutch) 언어 파일

const nl = {
    // 메뉴 및 UI 관련
    translate: 'Vertalen',
    summarize: 'Samenvatten',
    lookup: 'Term opzoeken',
    cancel: 'Annuleren',
    copy: 'Kopiëren',
    copied: 'Gekopieerd',
    close: 'Sluiten',
    translating: 'Vertalen...',
    summarizing: 'Samenvatten...',
    looking_up: 'Opzoeken...',
    cancel_with_esc: '(ESC om te annuleren)',
    image_text_recognition: 'Tekstherkenning van afbeelding',
    menu_addition_error: 'Fout bij het toevoegen van het menu:',
    summary_result: 'Samenvattingsresultaat',
    copy_term_definition: 'Kopieer termijn definitie',
    
    //options.js
    deepl_free_api_key_error: 'API-sleutel is niet geldig. Controleer de API-sleutel.',
    deepl_free_api_key_warning: 'Waarschuwing: Dit lijkt geen DeepL API-sleutel te zijn. Voer de juiste DeepL gratis API-sleutel in.',
    deepl_pro_api_key_warning: 'Waarschuwing: Dit lijkt geen DeepL API-sleutel te zijn. Voer de juiste DeepL betaalde API-sleutel in.',
    settings_save_error: 'Fout bij het opslaan van instellingen. Probeer het opnieuw.',
    saved_all_settings: 'Alle opgeslagen instellingen:',
            
    // 옵션 페이지 관련
    options_title: 'Instellingen vertaalextensie',
    service_selection: 'Selecteer vertaaldienst',
    api_key: 'API-sleutel',
    model_selection: 'Modelselectie',
    api_url: 'API URL (optioneel)',
    api_key_free: 'API-sleutel (gratis)',
    api_key_pro: 'API-sleutel (betaald)',
    interface_language: 'Interfacetaal',
    interface_language_desc: 'Menu\'s en berichten van de extensie worden weergegeven in de geselecteerde taal.',
    preferred_languages: 'Voorkeurstalen (slechts één taal kan worden geselecteerd)',
    save: 'Opslaan',
    settings_saved: 'Instellingen opgeslagen.',
    
    // 디버그 모드
    debug_mode: 'Debug-modus inschakelen (voor probleemoplossing)',
    debug_mode_desc: 'Wanneer de debug-modus is ingeschakeld, worden foutmeldingen en API-communicatie-informatie weergegeven in de browserconsole.',
    api_guide_title: 'API-registratiegids',
    claude_api_guide_title: 'Claude API-registratie en sleutelgeneratie',
    chatgpt_api_guide_title: 'ChatGPT API-registratie en sleutelgeneratie',
    grok_api_guide_title: 'Grok API-registratie en sleutelgeneratie',
    deepl_api_guide_title: 'DeepL API-registratie en sleutelgeneratie',
    deepl_api_help_title: 'Opmerkingen over DeepL API-gebruik',
    
    // Claude API 가이드
    claude_guide_step1: 'Bezoek de Anthropic-website (https://www.anthropic.com/api).',
    claude_guide_step2: 'Klik op de "Sign up"-knop in de rechterbovenhoek.',
    claude_guide_step3: 'Voer uw e-mailadres en wachtwoord in om een account aan te maken.',
    claude_guide_step4: 'Na het inloggen, ga naar het tabblad "API Keys".',
    claude_guide_step5: 'Klik op de "Create API Key"-knop.',
    claude_guide_step6: 'Geef de sleutel een naam en maak deze aan.',
    claude_guide_step7: 'Kopieer de gegenereerde API-sleutel en plak deze in het Claude API-sleutelveld hierboven.',
    claude_guide_note1: '※ Claude API vereist creditcardregistratie, gebruik is tegen betaling.',
    claude_guide_note2: '※ API-sleutel begint met het formaat sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Bezoek de OpenAI-website (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Klik op de "Sign up"-knop om een account aan te maken.',
    chatgpt_guide_step3: 'Bevestig uw e-mailadres.',
    chatgpt_guide_step4: 'Na het inloggen, klik op Dashboard naast uw profielfoto en selecteer "API keys" uit het linkermenu.',
    chatgpt_guide_step5: 'Klik op de "Create new secret key"-knop.',
    chatgpt_guide_step6: 'Geef de sleutel een naam en maak deze aan.',
    chatgpt_guide_step7: 'Kopieer de gegenereerde API-sleutel en plak deze in het ChatGPT API-sleutelveld hierboven.',
    chatgpt_guide_note1: '※ OpenAI API vereist creditcardregistratie, gebruik is tegen betaling.',
    chatgpt_guide_note2: '※ API-sleutel begint met het formaat sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Bezoek de X.AI-website (https://x.ai).',
    grok_guide_step2: 'Log in op uw account.',
    grok_guide_step3: 'Klik op het API-menu bovenaan.',
    grok_guide_step4: 'Klik op de "Start building now"-knop.',
    grok_guide_step5: 'Klik op het API Keys-menu aan de linkerkant.',
    grok_guide_step6: 'Genereer uw API-sleutel.',
    grok_guide_step7: 'Kopieer de gegenereerde API-sleutel en plak deze in het Grok API-sleutelveld hierboven.',
    grok_guide_note1: '※ API-sleutel begint met het formaat xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Bezoek de DeepL API-website (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Klik op de "Sign up for free"-knop.',
    deepl_guide_step3: 'Voer uw e-mailadres en wachtwoord in om een account aan te maken.',
    deepl_guide_step4: 'Bevestig uw e-mailadres om uw account te activeren.',
    deepl_guide_step5: 'Na het inloggen, ga naar https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Ga naar het API keys-menu (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Plak de API-sleutel van de gratis versie in het DeepL API Key (gratis) veld hierboven.',
    deepl_guide_step8: 'Plak de API-sleutel van de betaalde versie in het DeepL API Key (betaald) veld hierboven.',
    deepl_guide_note1: '※ De gratis versie van DeepL API staat vertaling toe tot 500.000 tekens per maand.',
    deepl_guide_note2: '※ Door over te stappen naar de betaalde versie kunt u meer tekst vertalen.',
    deepl_guide_note3: '※ Opmerking: Na overstap naar de betaalde versie kon ik de gratis API niet meer gebruiken. Houd hier rekening mee.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Voor de gratis API-sleutel moet u het eindpunt https://api-free.deepl.com gebruiken.',
    deepl_api_help_pro: 'Voor de betaalde API-sleutel moet u het eindpunt https://api.deepl.com gebruiken.',
    deepl_api_help_error: 'Als u de fout "Wrong endpoint. Use https://api.deepl.com" krijgt bij gebruik van de gratis API-sleutel:',
    deepl_api_help_check1: '1. Controleer of u de DeepL API (gratis) optie heeft geselecteerd.',
    deepl_api_help_check2: '2. Controleer of u daadwerkelijk een gratis API-sleutel gebruikt.',
    
    // 영역 및 결과 관련
    original_text: 'Originele tekst',
    translation: 'Vertaling',
    summary: 'Samenvatting',
    definition: 'Definitie',
    copy_original: 'Origineel kopiëren',
    copy_translation: 'Vertaling kopiëren',
    copy_summary: 'Samenvatting kopiëren',
    copy_both: 'Beide kopiëren',
    summarize_translation_result: 'Vertaalresultaat samenvatten',
    debug_info: 'Debug-informatie',
    page_url: 'Pagina-URL',
    page_title: 'Paginatitel',
    target_language: 'Doeltaal',
    request_prompt: 'Verzoekprompt',
    api_response: 'API-antwoord',
    clipboard_copy_failed: 'Kopiëren naar klembord mislukt',
    
    // 알림 및 오류 메시지
    canceled: 'Geannuleerd',
    translation_canceled: 'Vertaling geannuleerd.',
    summary_canceled: 'Samenvatting geannuleerd.',
    lookup_canceled: 'Term opzoeken geannuleerd.',
    operation_canceled: 'Bewerking geannuleerd.',
    api_key_error: 'API-sleutelfout',
    api_key_missing: 'API-sleutel is niet ingesteld. Stel de API-sleutel in bij de extensie-instellingen.',
    goto_settings: 'Ga naar instellingen',
    error: 'Fout',
    translation_failed: 'Vertaling mislukt:',
    summary_failed: 'Samenvatting mislukt:',
    lookup_failed: 'Term opzoeken mislukt:',
    no_response: 'Geen antwoord',
    
    // 로그 메시지
    menu_added: 'Menu toegevoegd.',
    menu_add_error: 'Fout bij toevoegen menu:',
    menu_removed: 'Vertaalmenu verwijderd:',
    operation_applied: 'Gebied is al {operation}. Standaard contextmenu weergeven.',
    already_has_operation: 'Gebied heeft al {operation}. Bewerking overslaan.',
    rightclick_text: 'Tekst geselecteerd met rechtermuisklik:',
    ctrl_rightclick: 'Ctrl + rechtermuisklik gedetecteerd: samenvatting uitvoeren',
    normal_rightclick: 'Normale rechtermuisklik gedetecteerd: vertaling uitvoeren',
    doubleclick_text: 'Tekst geselecteerd met dubbelklik:',
    hovered_element: 'Element waar muis overheen zweeft:',
    summary_response: 'Samenvattingsantwoord:',
    range_undefined: 'Bereik is niet gedefinieerd.',
    inline_translation_insertion_error: 'Fout bij invoegen inline vertaling:',
    inline_summary_insertion_error: 'Fout bij invoegen inline samenvatting:',
    fallback_insertion_error: 'Fout bij invoegen fallback:',
    copy_failed: 'Kopiëren mislukt:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmeren/Softwareontwikkeling',
    domain_blog: 'Blog/Technische artikelen',
    domain_qa: 'Programmeren V&A',
    domain_docs: 'Technische documentatie/API-documentatie',
    domain_academic: 'Academisch/Onderzoek',
    domain_news: 'Nieuws/Actualiteit',
    domain_finance: 'Financiën/Investering',
    domain_medical: 'Medisch/Gezondheidszorg',
    domain_legal: 'Juridisch',
    domain_webpage: 'Webpaginatitel:',
    
    // 초기화 메시지
    extension_init: 'Vertaalextensie initialiseren...',
    listeners_registered: 'Gebeurtenisluisteraars geregistreerd.',
    doubleclick_registered: 'Dubbelklikluisteraar geregistreerd.',
    extension_ready: 'Vertaalextensie is gereed.'

    //filePanel.js
    ,fileListWillBeShownHere: 'De lijst van bestanden wordt hier weergegeven.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Realtime ondertitelvertaling is ingeschakeld.'
    ,subtitle_translation_disabled: 'Realtime ondertitelvertaling is uitgeschakeld.'
    ,subtitle_translation_button: 'Realtime ondertitelvertaling'
    ,runtime_not_initialized: 'Chrome-runtime is niet geïnitialiseerd.'
    ,message_send_error: 'Fout bij verzenden bericht:'
    ,translation_response_missing: 'Geen vertaalantwoord.'
    ,translation_error: 'Fout bij vertalen ondertitels:'
};

export default nl; 