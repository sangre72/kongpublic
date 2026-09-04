// 슬로베니아어 (Slovenian) 언어 파일

const sl = {
    // 메뉴 및 UI 관련
    translate: 'Prevedi',
    summarize: 'Povzemi',
    lookup: 'Poišči izraz',
    cancel: 'Prekliči',
    copy: 'Kopiraj',
    copied: 'Kopirano',
    close: 'Zapri',
    translating: 'Prevajanje...',
    summarizing: 'Povzemanje...',
    looking_up: 'Iskanje...',
    cancel_with_esc: '(ESC za preklic)',
    image_text_recognition: 'Prepoznavanje besedila iz slike',
    menu_addition_error: 'Napaka pri dodajanju menija:',
    summary_result: 'Rezultat povzemanja',
    copy_term_definition: 'Kopiraj definicijo termina',
    
    //options.js
    deepl_free_api_key_error: 'Ključ API ni veljaven. Prosimo, preverite ključ API.',
    deepl_free_api_key_warning: 'Opozorilo: Zdi se, da to ni DeepL API ključ. Prosimo, vnesite pravilen brezplačen DeepL API ključ.',
    deepl_pro_api_key_warning: 'Opozorilo: Zdi se, da to ni DeepL API ključ. Prosimo, vnesite pravilen plačljiv DeepL API ključ.',
    settings_save_error: 'Napaka pri shranjevanju nastavitev. Prosimo, poskusite znova.',
    saved_all_settings: 'Vse shranjene nastavitve:',
                
    // 옵션 페이지 관련
    options_title: 'Nastavitve razširitve za prevajanje',
    service_selection: 'Izbira prevajalske storitve',
    api_key: 'API ključ',
    model_selection: 'Izbira modela',
    api_url: 'API URL (neobvezno)',
    api_key_free: 'API ključ (brezplačen)',
    api_key_pro: 'API ključ (plačljiv)',
    interface_language: 'Jezik vmesnika',
    interface_language_desc: 'Meniji in sporočila razširitve bodo prikazani v izbranem jeziku.',
    preferred_languages: 'Priljubljeni jeziki (izbran je lahko samo en jezik)',
    save: 'Shrani',
    settings_saved: 'Nastavitve shranjene.',
    
    // 디버그 모드
    debug_mode: 'Vklopi način razhroščevanja (za odpravljanje težav)',
    debug_mode_desc: 'Ko je način razhroščevanja vklopljen, bodo sporočila o napakah in informacije o komunikaciji API prikazane v konzoli brskalnika.',
    api_guide_title: 'Vodič za registracijo API',
    claude_api_guide_title: 'Registracija in generiranje ključa Claude API',
    chatgpt_api_guide_title: 'Registracija in generiranje ključa ChatGPT API',
    grok_api_guide_title: 'Registracija in generiranje ključa Grok API',
    deepl_api_guide_title: 'Registracija in generiranje ključa DeepL API',
    deepl_api_help_title: 'Opombe o uporabi DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Obiščite spletno stran Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Kliknite gumb "Sign up" v zgornjem desnem kotu.',
    claude_guide_step3: 'Vnesite svoj e-poštni naslov in geslo za ustvarjanje računa.',
    claude_guide_step4: 'Po prijavi pojdite na zavihek "API Keys".',
    claude_guide_step5: 'Kliknite gumb "Create API Key".',
    claude_guide_step6: 'Poimenujte ključ in ga ustvarite.',
    claude_guide_step7: 'Kopirajte ustvarjeni API ključ in ga prilepite v polje Claude API ključa zgoraj.',
    claude_guide_note1: '※ Claude API zahteva registracijo kreditne kartice, uporaba je plačljiva.',
    claude_guide_note2: '※ API ključ se začne s formatom sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Obiščite spletno stran OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Kliknite gumb "Sign up" za ustvarjanje računa.',
    chatgpt_guide_step3: 'Potrdite svoj e-poštni naslov.',
    chatgpt_guide_step4: 'Po prijavi kliknite Dashboard poleg svoje profilne slike in izberite "API keys" iz levega menija.',
    chatgpt_guide_step5: 'Kliknite gumb "Create new secret key".',
    chatgpt_guide_step6: 'Poimenujte ključ in ga ustvarite.',
    chatgpt_guide_step7: 'Kopirajte ustvarjeni API ključ in ga prilepite v polje ChatGPT API ključa zgoraj.',
    chatgpt_guide_note1: '※ OpenAI API zahteva registracijo kreditne kartice, uporaba je plačljiva.',
    chatgpt_guide_note2: '※ API ključ se začne s formatom sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Obiščite spletno stran X.AI (https://x.ai).',
    grok_guide_step2: 'Prijavite se v svoj račun.',
    grok_guide_step3: 'Kliknite meni API na vrhu.',
    grok_guide_step4: 'Kliknite gumb "Start building now".',
    grok_guide_step5: 'Kliknite meni API Keys na levi strani.',
    grok_guide_step6: 'Ustvarite svoj API ključ.',
    grok_guide_step7: 'Kopirajte ustvarjeni API ključ in ga prilepite v polje Grok API ključa zgoraj.',
    grok_guide_note1: '※ API ključ se začne s formatom xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Obiščite spletno stran DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Kliknite gumb "Sign up for free".',
    deepl_guide_step3: 'Vnesite svoj e-poštni naslov in geslo za ustvarjanje računa.',
    deepl_guide_step4: 'Potrdite svoj e-poštni naslov za aktivacijo računa.',
    deepl_guide_step5: 'Po prijavi pojdite na https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Pojdite v meni API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Prilepite API ključ brezplačne različice v polje DeepL API Key (brezplačen) zgoraj.',
    deepl_guide_step8: 'Prilepite API ključ plačljive različice v polje DeepL API Key (plačljiv) zgoraj.',
    deepl_guide_note1: '※ Brezplačna različica DeepL API omogoča prevajanje do 500.000 znakov na mesec.',
    deepl_guide_note2: '※ S prehodom na plačljivo različico lahko prevedete več besedila.',
    deepl_guide_note3: '※ Opomba: Po prehodu na plačljivo različico nisem mogel uporabljati brezplačnega API-ja. Prosimo, upoštevajte to.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Za brezplačni API ključ morate uporabiti končno točko https://api-free.deepl.com.',
    deepl_api_help_pro: 'Za plačljivi API ključ morate uporabiti končno točko https://api.deepl.com.',
    deepl_api_help_error: 'Če pri uporabi brezplačnega API ključa prejmete napako "Wrong endpoint. Use https://api.deepl.com":',
    deepl_api_help_check1: '1. Preverite, ali ste izbrali možnost DeepL API (brezplačen).',
    deepl_api_help_check2: '2. Preverite, ali dejansko uporabljate brezplačni API ključ.',
    
    // 영역 및 결과 관련
    original_text: 'Izvirno besedilo',
    translation: 'Prevod',
    summary: 'Povzetek',
    definition: 'Definicija',
    copy_original: 'Kopiraj izvirnik',
    copy_translation: 'Kopiraj prevod',
    copy_summary: 'Kopiraj povzetek',
    copy_both: 'Kopiraj oboje',
    summarize_translation_result: 'Povzemi rezultat prevoda',
    debug_info: 'Informacije o razhroščevanju',
    page_url: 'URL strani',
    page_title: 'Naslov strani',
    target_language: 'Ciljni jezik',
    request_prompt: 'Zahteva za poziv',
    api_response: 'API odgovor',
    clipboard_copy_failed: 'Kopiranje v odložišče ni uspelo',
    
    // 알림 및 오류 메시지
    canceled: 'Preklicano',
    translation_canceled: 'Prevajanje preklicano.',
    summary_canceled: 'Povzemanje preklicano.',
    lookup_canceled: 'Iskanje preklicano.',
    operation_canceled: 'Operacija preklicana.',
    api_key_error: 'Napaka API ključa',
    api_key_missing: 'API ključ ni nastavljen. Prosimo, nastavite API ključ v nastavitvah razširitve.',
    goto_settings: 'Pojdi na nastavitve',
    error: 'Napaka',
    translation_failed: 'Prevajanje ni uspelo:',
    summary_failed: 'Povzemanje ni uspelo:',
    lookup_failed: 'Iskanje ni uspelo:',
    no_response: 'Ni odgovora',
    
    // 로그 메시지
    menu_added: 'Meni dodan.',
    menu_add_error: 'Napaka pri dodajanju menija:',
    menu_removed: 'Meni za prevajanje odstranjen:',
    operation_applied: 'Območje je že {operation}. Prikazovanje privzetega kontekstnega menija.',
    already_has_operation: 'Območje že ima {operation}. Preskok operacije.',
    rightclick_text: 'Besedilo izbrano z desnim klikom:',
    ctrl_rightclick: 'Ctrl + desni klik zaznan: izvajanje povzemanja',
    normal_rightclick: 'Običajni desni klik zaznan: izvajanje prevajanja',
    doubleclick_text: 'Besedilo izbrano z dvojnim klikom:',
    hovered_element: 'Element pod kazalcem:',
    summary_response: 'Odgovor povzetka:',
    range_undefined: 'Območje ni določeno.',
    inline_translation_insertion_error: 'Napaka pri vstavljanju vgrajenega prevoda:',
    inline_summary_insertion_error: 'Napaka pri vstavljanju vgrajenega povzetka:',
    fallback_insertion_error: 'Napaka pri vstavljanju nadomestne rešitve:',
    copy_failed: 'Kopiranje ni uspelo:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programiranje/Razvoj programske opreme',
    domain_blog: 'Blog/Tehnični članki',
    domain_qa: 'Programiranje V&O',
    domain_docs: 'Tehnična dokumentacija/API dokumentacija',
    domain_academic: 'Akademsko/Raziskovanje',
    domain_news: 'Novice/Aktualno',
    domain_finance: 'Finance/Naložbe',
    domain_medical: 'Medicinsko/Zdravje',
    domain_legal: 'Pravno',
    domain_webpage: 'Naslov spletne strani:',
    
    // 초기화 메시지
    extension_init: 'Inicializacija razširitve za prevajanje...',
    listeners_registered: 'Poslušalci dogodkov registrirani.',
    doubleclick_registered: 'Poslušalec dvojnega klika registriran.',
    extension_ready: 'Razširitev za prevajanje je pripravljena.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Seznam datotek bo prikazan tukaj.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Prevajanje podnapisov v realnem času je omogočeno.'
    ,subtitle_translation_disabled: 'Prevajanje podnapisov v realnem času je onemogočeno.'
    ,subtitle_translation_button: 'Prevajanje podnapisov v realnem času'
    ,runtime_not_initialized: 'Chrome izvajalnik ni inicializiran.'
    ,message_send_error: 'Napaka pri pošiljanju sporočila:'
    ,translation_response_missing: 'Ni odgovora prevoda.'
    ,translation_error: 'Napaka pri prevajanju podnapisov:'
};

export default sl; 