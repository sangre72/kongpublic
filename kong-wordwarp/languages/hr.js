// 크로아티아어 (Croatian) 언어 파일

const hr = {
    // 메뉴 및 UI 관련
    translate: 'Prevedi',
    summarize: 'Sažmi',
    lookup: 'Pretraži pojam',
    cancel: 'Odustani',
    copy: 'Kopiraj',
    copied: 'Kopirano',
    close: 'Zatvori',
    translating: 'Prevođenje...',
    summarizing: 'Sažimanje...',
    looking_up: 'Pretraživanje...',
    cancel_with_esc: '(ESC za odustajanje)',
    image_text_recognition: 'Prepoznavanje teksta sa slike',
    menu_addition_error: 'Greška pri dodavanju izbornika:',
    summary_result: 'Rezultat sažimanja',
    copy_term_definition: 'Kopiraj definiciju termina',
    
    //options.js
    deepl_free_api_key_error: 'API ključ nije valjan. Provjerite API ključ.',
    deepl_free_api_key_warning: 'Upozorenje: Čini se da ovo nije DeepL API ključ. Molimo unesite ispravan besplatni DeepL API ključ.',
    deepl_pro_api_key_warning: 'Upozorenje: Čini se da ovo nije DeepL API ključ. Molimo unesite ispravan plaćeni DeepL API ključ.',
    settings_save_error: 'Greška pri spremanju postavki. Molimo pokušajte ponovno.',
    saved_all_settings: 'Sve spremljene postavke:',
            
    
    // 옵션 페이지 관련
    options_title: 'Postavke dodatka za prevođenje',
    service_selection: 'Odabir usluge prevođenja',
    api_key: 'API ključ',
    model_selection: 'Odabir modela',
    api_url: 'API URL (opcionalno)',
    api_key_free: 'API ključ (besplatni)',
    api_key_pro: 'API ključ (plaćeni)',
    interface_language: 'Jezik sučelja',
    interface_language_desc: 'Izbornici i poruke dodatka bit će prikazani na odabranom jeziku.',
    preferred_languages: 'Preferirani jezici (može se odabrati samo jedan jezik)',
    save: 'Spremi',
    settings_saved: 'Postavke su spremljene.',
    
    // 디버그 모드
    debug_mode: 'Omogući način za otklanjanje pogrešaka (za rješavanje problema)',
    debug_mode_desc: 'Kada je način za otklanjanje pogrešaka omogućen, poruke o pogreškama i informacije o API komunikaciji bit će prikazane u konzoli preglednika.',
    api_guide_title: 'Vodič za registraciju API-ja',
    claude_api_guide_title: 'Claude API registracija i generiranje ključa',
    chatgpt_api_guide_title: 'ChatGPT API registracija i generiranje ključa',
    grok_api_guide_title: 'Grok API registracija i generiranje ključa',
    deepl_api_guide_title: 'DeepL API registracija i generiranje ključa',
    deepl_api_help_title: 'Napomene o korištenju DeepL API-ja',
    
    // Claude API 가이드
    claude_guide_step1: 'Posjetite Anthropic web stranicu (https://www.anthropic.com/api).',
    claude_guide_step2: 'Kliknite na gumb "Sign up" u gornjem desnom kutu.',
    claude_guide_step3: 'Unesite svoju e-mail adresu i lozinku za stvaranje računa.',
    claude_guide_step4: 'Nakon prijave, idite na karticu "API Keys".',
    claude_guide_step5: 'Kliknite na gumb "Create API Key".',
    claude_guide_step6: 'Dajte ključu ime i stvorite ga.',
    claude_guide_step7: 'Kopirajte generirani API ključ i zalijepite ga u gornje polje Claude API ključa.',
    claude_guide_note1: '※ Claude API zahtijeva registraciju kreditne kartice, korištenje je uz naplatu.',
    claude_guide_note2: '※ API ključ počinje s formatom sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Posjetite OpenAI web stranicu (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Kliknite na gumb "Sign up" za stvaranje računa.',
    chatgpt_guide_step3: 'Potvrdite svoju e-mail adresu.',
    chatgpt_guide_step4: 'Nakon prijave, kliknite na Dashboard pored svoje profilne slike i odaberite "API keys" iz lijevog izbornika.',
    chatgpt_guide_step5: 'Kliknite na gumb "Create new secret key".',
    chatgpt_guide_step6: 'Dajte ključu ime i stvorite ga.',
    chatgpt_guide_step7: 'Kopirajte generirani API ključ i zalijepite ga u gornje polje ChatGPT API ključa.',
    chatgpt_guide_note1: '※ OpenAI API zahtijeva registraciju kreditne kartice, korištenje je uz naplatu.',
    chatgpt_guide_note2: '※ API ključ počinje s formatom sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Posjetite X.AI web stranicu (https://x.ai).',
    grok_guide_step2: 'Prijavite se na svoj račun.',
    grok_guide_step3: 'Kliknite na API izbornik na vrhu.',
    grok_guide_step4: 'Kliknite na gumb "Start building now".',
    grok_guide_step5: 'Kliknite na API Keys izbornik s lijeve strane.',
    grok_guide_step6: 'Generirajte svoj API ključ.',
    grok_guide_step7: 'Kopirajte generirani API ključ i zalijepite ga u gornje polje Grok API ključa.',
    grok_guide_note1: '※ API ključ počinje s formatom xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Posjetite DeepL API web stranicu (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Kliknite na gumb "Sign up for free".',
    deepl_guide_step3: 'Unesite svoju e-mail adresu i lozinku za stvaranje računa.',
    deepl_guide_step4: 'Potvrdite svoju e-mail adresu za aktivaciju računa.',
    deepl_guide_step5: 'Nakon prijave, idite na https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Idite na izbornik API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Zalijepite API ključ besplatne verzije u gornje polje DeepL API Key (besplatni).',
    deepl_guide_step8: 'Zalijepite API ključ plaćene verzije u gornje polje DeepL API Key (plaćeni).',
    deepl_guide_note1: '※ Besplatna verzija DeepL API-ja omogućuje prevođenje do 500.000 znakova mjesečno.',
    deepl_guide_note2: '※ Prelaskom na plaćenu verziju možete prevoditi više teksta.',
    deepl_guide_note3: '※ Napomena: Nakon prelaska na plaćenu verziju, nisam mogao koristiti besplatni API. Molimo uzmite to u obzir.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Za besplatni API ključ morate koristiti krajnju točku https://api-free.deepl.com.',
    deepl_api_help_pro: 'Za plaćeni API ključ morate koristiti krajnju točku https://api.deepl.com.',
    deepl_api_help_error: 'Ako dobijete pogrešku "Wrong endpoint. Use https://api.deepl.com" pri korištenju besplatnog API ključa:',
    deepl_api_help_check1: '1. Provjerite jeste li odabrali opciju DeepL API (besplatni).',
    deepl_api_help_check2: '2. Provjerite koristite li zaista besplatni API ključ.',
    
    // 영역 및 결과 관련
    original_text: 'Izvorni tekst',
    translation: 'Prijevod',
    summary: 'Sažetak',
    definition: 'Definicija',
    copy_original: 'Kopiraj izvornik',
    copy_translation: 'Kopiraj prijevod',
    copy_summary: 'Kopiraj sažetak',
    copy_both: 'Kopiraj oboje',
    summarize_translation_result: 'Sažmi rezultat prijevoda',
    debug_info: 'Informacije o otklanjanju pogrešaka',
    page_url: 'URL stranice',
    page_title: 'Naslov stranice',
    target_language: 'Ciljni jezik',
    request_prompt: 'Zahtjev upita',
    api_response: 'API odgovor',
    clipboard_copy_failed: 'Kopiranje u međuspremnik nije uspjelo',
    
    // 알림 및 오류 메시지
    canceled: 'Otkazano',
    translation_canceled: 'Prevođenje je otkazano.',
    summary_canceled: 'Sažimanje je otkazano.',
    lookup_canceled: 'Pretraživanje pojma je otkazano.',
    operation_canceled: 'Operacija je otkazana.',
    api_key_error: 'Pogreška API ključa',
    api_key_missing: 'API ključ nije postavljen. Molimo postavite API ključ u postavkama dodatka.',
    goto_settings: 'Idi na postavke',
    error: 'Pogreška',
    translation_failed: 'Prevođenje nije uspjelo:',
    summary_failed: 'Sažimanje nije uspjelo:',
    lookup_failed: 'Pretraživanje pojma nije uspjelo:',
    no_response: 'Nema odgovora',
    
    // 로그 메시지
    menu_added: 'Izbornik je dodan.',
    menu_add_error: 'Pogreška pri dodavanju izbornika:',
    menu_removed: 'Izbornik za prevođenje je uklonjen:',
    operation_applied: 'Područje je već {operation}. Prikazivanje zadanog kontekstnog izbornika.',
    already_has_operation: 'Područje već ima {operation}. Preskakanje operacije.',
    rightclick_text: 'Tekst odabran desnim klikom:',
    ctrl_rightclick: 'Otkrivena je kombinacija Ctrl + desni klik: izvršavanje sažimanja',
    normal_rightclick: 'Otkriven je normalan desni klik: izvršavanje prevođenja',
    doubleclick_text: 'Tekst odabran dvostrukim klikom:',
    hovered_element: 'Element preko kojeg je miš prešao:',
    summary_response: 'Odgovor sažetka:',
    range_undefined: 'Raspon nije definiran.',
    inline_translation_insertion_error: 'Pogreška pri umetanju ugrađenog prijevoda:',
    inline_summary_insertion_error: 'Pogreška pri umetanju ugrađenog sažetka:',
    fallback_insertion_error: 'Pogreška pri umetanju rezervne opcije:',
    copy_failed: 'Kopiranje nije uspjelo:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programiranje/Razvoj softvera',
    domain_blog: 'Blog/Tehnički članci',
    domain_qa: 'Programiranje P&O',
    domain_docs: 'Tehnička dokumentacija/API dokumentacija',
    domain_academic: 'Akademsko/Istraživanje',
    domain_news: 'Vijesti/Aktualnosti',
    domain_finance: 'Financije/Ulaganje',
    domain_medical: 'Medicinsko/Zdravstvo',
    domain_legal: 'Pravno',
    domain_webpage: 'Naslov web stranice:',
    
    // 초기화 메시지
    extension_init: 'Inicijalizacija dodatka za prevođenje...',
    listeners_registered: 'Slušatelji događaja su registrirani.',
    doubleclick_registered: 'Slušatelj dvostrukog klika je registriran.',
    extension_ready: 'Dodatak za prevođenje je spreman.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Popis datoteka bit će prikazan ovdje.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Prijevod titlova u stvarnom vremenu je omogućen.'
    ,subtitle_translation_disabled: 'Prijevod titlova u stvarnom vremenu je onemogućen.'
    ,subtitle_translation_button: 'Prijevod titlova u stvarnom vremenu'
    ,runtime_not_initialized: 'Chrome runtime nije inicijaliziran.'
    ,message_send_error: 'Greška pri slanju poruke:'
    ,translation_response_missing: 'Nema odgovora prijevoda.'
    ,translation_error: 'Greška pri prevođenju titlova:'
};

export default hr; 