// 헝가리어 (Hungarian) 언어 파일

const hu = {
    // 메뉴 및 UI 관련
    translate: 'Fordítás',
    summarize: 'Összefoglalás',
    lookup: 'Kifejezés keresése',
    cancel: 'Mégse',
    copy: 'Másolás',
    copied: 'Másolva',
    close: 'Bezárás',
    translating: 'Fordítás...',
    summarizing: 'Összefoglalás...',
    looking_up: 'Keresés...',
    cancel_with_esc: '(ESC a megszakításhoz)',
    image_text_recognition: 'Képszöveg felismerés',
    menu_addition_error: 'Hiba a menü hozzáadásakor:',
    summary_result: 'Összefoglalás eredménye',
    copy_term_definition: 'Kifejezés definíciója másolása',
    
    //options.js
    deepl_free_api_key_error: 'API kulcs érvénytelen. Ellenőrizze a kulcsot.',
    deepl_free_api_key_warning: 'Figyelmeztetés: Ez nem DeepL API kulcs. Kérjük, adja meg a helyes DeepL ingyenes API kulcsot.',
    deepl_pro_api_key_warning: 'Figyelmeztetés: Ez nem DeepL API kulcs. Kérjük, adja meg a helyes DeepL fizetős API kulcsot.',
    settings_save_error: 'Hiba a beállítások mentésekor. Kérjük, próbálja újra.',
    saved_all_settings: 'Minden mentett beállítás:',
    
    // 옵션 페이지 관련
    options_title: 'Fordítási bővítmény beállításai',
    service_selection: 'Fordítási szolgáltatás kiválasztása',
    api_key: 'API kulcs',
    model_selection: 'Modell kiválasztása',
    api_url: 'API URL (opcionális)',
    api_key_free: 'API kulcs (ingyenes)',
    api_key_pro: 'API kulcs (fizetős)',
    interface_language: 'Felület nyelve',
    interface_language_desc: 'A bővítmény menüi és üzenetei a kiválasztott nyelven jelennek meg.',
    preferred_languages: 'Preferált nyelvek (csak egy nyelv választható)',
    save: 'Mentés',
    settings_saved: 'Beállítások mentve.',
    
    // 디버그 모드
    debug_mode: 'Hibakeresési mód engedélyezése (hibaelhárításhoz)',
    debug_mode_desc: 'A hibakeresési mód engedélyezésével a hibaüzenetek és API kommunikációs információk megjelennek a böngésző konzolján.',
    api_guide_title: 'API regisztrációs útmutató',
    claude_api_guide_title: 'Claude API regisztráció és kulcs generálás',
    chatgpt_api_guide_title: 'ChatGPT API regisztráció és kulcs generálás',
    grok_api_guide_title: 'Grok API regisztráció és kulcs generálás',
    deepl_api_guide_title: 'DeepL API regisztráció és kulcs generálás',
    deepl_api_help_title: 'DeepL API használati megjegyzések',
    
    // Claude API 가이드
    claude_guide_step1: 'Látogasson el az Anthropic weboldalára (https://www.anthropic.com/api).',
    claude_guide_step2: 'Kattintson a "Sign up" gombra a jobb felső sarokban.',
    claude_guide_step3: 'Adja meg e-mail címét és jelszavát a fiók létrehozásához.',
    claude_guide_step4: 'Bejelentkezés után navigáljon az "API Keys" fülre.',
    claude_guide_step5: 'Kattintson a "Create API Key" gombra.',
    claude_guide_step6: 'Adja meg a kulcs nevét és hozza létre.',
    claude_guide_step7: 'Másolja a generált API kulcsot és illessze be a fenti Claude API kulcs mezőbe.',
    claude_guide_note1: '※ A Claude API használatához bankkártya regisztráció szükséges, a használat díjköteles.',
    claude_guide_note2: '※ Az API kulcs sk-ant-api03-... formátummal kezdődik.',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Látogasson el az OpenAI weboldalára (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Kattintson a "Sign up" gombra a fiók létrehozásához.',
    chatgpt_guide_step3: 'Végezze el az e-mail címének megerősítését.',
    chatgpt_guide_step4: 'Bejelentkezés után kattintson a profilképe melletti Dashboard-ra, majd válassza az "API keys" menüpontot a bal oldali menüből.',
    chatgpt_guide_step5: 'Kattintson a "Create new secret key" gombra.',
    chatgpt_guide_step6: 'Adja meg a kulcs nevét és hozza létre.',
    chatgpt_guide_step7: 'Másolja a generált API kulcsot és illessze be a fenti ChatGPT API kulcs mezőbe.',
    chatgpt_guide_note1: '※ Az OpenAI API használatához bankkártya regisztráció szükséges, a használat díjköteles.',
    chatgpt_guide_note2: '※ Az API kulcs sk-... formátummal kezdődik.',
    
    // Grok API 가이드
    grok_guide_step1: 'Látogasson el az X.AI weboldalára (https://x.ai).',
    grok_guide_step2: 'Jelentkezzen be a fiókjával.',
    grok_guide_step3: 'Kattintson az API menüre a felső részen.',
    grok_guide_step4: 'Kattintson a "Start building now" gombra.',
    grok_guide_step5: 'Kattintson az API Keys menüre a bal oldalon.',
    grok_guide_step6: 'Generálja le az API kulcsát.',
    grok_guide_step7: 'Másolja a generált API kulcsot és illessze be a fenti Grok API kulcs mezőbe.',
    grok_guide_note1: '※ Az API kulcs xai-... formátummal kezdődik.',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Látogasson el a DeepL API weboldalára (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Kattintson a "Sign up for free" gombra.',
    deepl_guide_step3: 'Adja meg e-mail címét és jelszavát a fiók létrehozásához.',
    deepl_guide_step4: 'Végezze el az e-mail címének megerősítését a fiók aktiválásához.',
    deepl_guide_step5: 'Bejelentkezés után navigáljon a https://www.deepl.com/account/subscription oldalra.',
    deepl_guide_step6: 'Menjen az API keys menübe (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Az ingyenes verzió API kulcsát illessze be a fenti DeepL API Key (ingyenes) mezőbe.',
    deepl_guide_step8: 'A fizetős verzió API kulcsát illessze be a fenti DeepL API Key (fizetős) mezőbe.',
    deepl_guide_note1: '※ A DeepL API ingyenes verziója havi 500.000 karakterig használható.',
    deepl_guide_note2: '※ A fizetős verzióra váltással több szöveget fordíthat.',
    deepl_guide_note3: '※ Megjegyzés: A fizetős verzióra váltás után az ingyenes API már nem volt használható. Kérjük, vegye ezt figyelembe.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Az ingyenes API kulcshoz a https://api-free.deepl.com végpontot kell használni.',
    deepl_api_help_pro: 'A fizetős API kulcshoz a https://api.deepl.com végpontot kell használni.',
    deepl_api_help_error: 'Ha az ingyenes API kulcs használatakor "Wrong endpoint. Use https://api.deepl.com" hibát kap:',
    deepl_api_help_check1: '1. Ellenőrizze, hogy a DeepL API (ingyenes) opciót választotta-e.',
    deepl_api_help_check2: '2. Ellenőrizze, hogy valóban ingyenes API kulcsot használ-e.',
    
    // 영역 및 결과 관련
    original_text: 'Eredeti szöveg',
    translation: 'Fordítás',
    summary: 'Összefoglalás',
    definition: 'Definíció',
    copy_original: 'Eredeti másolása',
    copy_translation: 'Fordítás másolása',
    copy_summary: 'Összefoglalás másolása',
    copy_both: 'Mindkettő másolása',
    summarize_translation_result: 'Fordítási eredmény összefoglalása',
    debug_info: 'Hibakeresési információk',
    page_url: 'Oldal URL',
    page_title: 'Oldal címe',
    target_language: 'Célnyelv',
    request_prompt: 'Kérés promptja',
    api_response: 'API válasz',
    clipboard_copy_failed: 'Vágólapra másolás sikertelen',
    
    // 알림 및 오류 메시지
    canceled: 'Megszakítva',
    translation_canceled: 'Fordítás megszakítva.',
    summary_canceled: 'Összefoglalás megszakítva.',
    lookup_canceled: 'Kifejezés keresése megszakítva.',
    operation_canceled: 'Művelet megszakítva.',
    api_key_error: 'API kulcs hiba',
    api_key_missing: 'Nincs beállítva API kulcs. Kérjük, állítsa be az API kulcsot a bővítmény beállításaiban.',
    goto_settings: 'Ugrás a beállításokhoz',
    error: 'Hiba',
    translation_failed: 'Fordítás sikertelen:',
    summary_failed: 'Összefoglalás sikertelen:',
    lookup_failed: 'Kifejezés keresése sikertelen:',
    no_response: 'Nincs válasz',
    
    // 로그 메시지
    menu_added: 'Menü hozzáadva.',
    menu_add_error: 'Hiba a menü hozzáadásakor:',
    menu_removed: 'Fordítási menü eltávolítva:',
    operation_applied: 'A terület már {operation}. Az alapértelmezett helyi menü megjelenítése.',
    already_has_operation: 'A terület már tartalmaz {operation}t. Művelet kihagyása.',
    rightclick_text: 'Jobb kattintással kijelölt szöveg:',
    ctrl_rightclick: 'Ctrl + jobb kattintás észlelve: összefoglalás végrehajtása',
    normal_rightclick: 'Normál jobb kattintás észlelve: fordítás végrehajtása',
    doubleclick_text: 'Dupla kattintással kijelölt szöveg:',
    hovered_element: 'Kiemelt elem:',
    summary_response: 'Összefoglalás válasz:',
    range_undefined: 'Tartomány nincs definiálva.',
    inline_translation_insertion_error: 'Beágyazott fordítás beszúrási hiba:',
    inline_summary_insertion_error: 'Beágyazott összefoglalás beszúrási hiba:',
    fallback_insertion_error: 'Tartalék beszúrási hiba:',
    copy_failed: 'Másolás sikertelen:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programozás/Szoftverfejlesztés',
    domain_blog: 'Blog/Technikai cikkek',
    domain_qa: 'Programozási K&V',
    domain_docs: 'Technikai dokumentáció/API dokumentáció',
    domain_academic: 'Akadémiai/Kutatás',
    domain_news: 'Hírek/Aktualitások',
    domain_finance: 'Pénzügy/Befektetés',
    domain_medical: 'Orvosi/Egészségügyi',
    domain_legal: 'Jogi',
    domain_webpage: 'Weboldal címe:',
    
    // 초기화 메시지
    extension_init: 'Fordítási bővítmény inicializálása...',
    listeners_registered: 'Eseményfigyelők regisztrálva.',
    doubleclick_registered: 'Dupla kattintás eseményfigyelő regisztrálva.',
    extension_ready: 'Fordítási bővítmény készen áll.'

    //filePanel.js
    ,fileListWillBeShownHere: 'A fájlok listája itt jelenik meg.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'A valós idejű feliratfordítás engedélyezve.'
    ,subtitle_translation_disabled: 'A valós idejű feliratfordítás letiltva.'
    ,subtitle_translation_button: 'Valós idejű feliratfordítás'
    ,runtime_not_initialized: 'A Chrome futtatókörnyezet nincs inicializálva.'
    ,message_send_error: 'Hiba az üzenet küldésekor:'
    ,translation_response_missing: 'Nincs fordítási válasz.'
    ,translation_error: 'Hiba a felirat fordításakor:'
};

export default hu; 