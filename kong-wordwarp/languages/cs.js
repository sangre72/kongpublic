// 체코어 (Czech) 언어 파일

const cs = {
    // 메뉴 및 UI 관련
    translate: 'Přeložit',
    summarize: 'Shrnout',
    lookup: 'Vyhledat termín',
    cancel: 'Zrušit',
    copy: 'Kopírovat',
    copied: 'Zkopírováno',
    close: 'Zavřít',
    translating: 'Překládání...',
    summarizing: 'Shrnutí...',
    looking_up: 'Vyhledávání...',
    cancel_with_esc: '(ESC pro zrušení)',
    image_text_recognition: 'Rozpoznávání textu z obrázku',
    menu_addition_error: 'Chyba při přidávání nabídky:',
    summary_result: 'Shrnutí výsledku',
    copy_term_definition: 'Kopírovat definici termínu',
    
    //options.js
    deepl_free_api_key_error: 'Klíč API je neplatný. Zkontrolujte klíč API.',
    deepl_free_api_key_warning: 'Varování: To vypadá, že tohle není klíč API pro DeepL. Zadejte platný klíč API pro DeepL.',
    deepl_pro_api_key_warning: 'Varování: To vypadá, že tohle není klíč API pro DeepL. Zadejte platný klíč API pro DeepL.',
    settings_save_error: 'Došlo k chybě při ukládání nastavení. Zkuste to znovu.',
    saved_all_settings: 'Uložené všechny nastavení:',
        
    // 옵션 페이지 관련
    options_title: 'Nastavení překladového rozšíření',
    service_selection: 'Výběr překladové služby',
    api_key: 'API klíč',
    model_selection: 'Výběr modelu',
    api_url: 'API URL (volitelné)',
    api_key_free: 'API klíč (zdarma)',
    api_key_pro: 'API klíč (placený)',
    interface_language: 'Jazyk rozhraní',
    interface_language_desc: 'Nabídky a zprávy rozšíření budou zobrazeny ve vybraném jazyce.',
    preferred_languages: 'Preferované jazyky (lze vybrat pouze jeden jazyk)',
    save: 'Uložit',
    settings_saved: 'Nastavení bylo uloženo.',
    
    // 디버그 모드
    debug_mode: 'Povolit režim ladění (pro řešení problémů)',
    debug_mode_desc: 'Když je režim ladění povolen, chybové zprávy a informace o API komunikaci budou zobrazeny v konzoli prohlížeče.',
    api_guide_title: 'Průvodce registrací API',
    claude_api_guide_title: 'Claude API registrace a generování klíče',
    chatgpt_api_guide_title: 'ChatGPT API registrace a generování klíče',
    grok_api_guide_title: 'Grok API registrace a generování klíče',
    deepl_api_guide_title: 'DeepL API registrace a generování klíče',
    deepl_api_help_title: 'Poznámky k použití DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Navštivte webovou stránku Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Klikněte na tlačítko "Sign up" v pravém horním rohu.',
    claude_guide_step3: 'Zadejte svůj e-mail a heslo pro vytvoření účtu.',
    claude_guide_step4: 'Po přihlášení přejděte na kartu "API Keys".',
    claude_guide_step5: 'Klikněte na tlačítko "Create API Key".',
    claude_guide_step6: 'Pojmenujte klíč a vytvořte jej.',
    claude_guide_step7: 'Zkopírujte vygenerovaný API klíč a vložte jej do pole Claude API klíče výše.',
    claude_guide_note1: '※ Claude API vyžaduje registraci kreditní karty, použití je zpoplatněno.',
    claude_guide_note2: '※ API klíč začíná formátem sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Navštivte webovou stránku OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Klikněte na tlačítko "Sign up" pro vytvoření účtu.',
    chatgpt_guide_step3: 'Potvrďte svou e-mailovou adresu.',
    chatgpt_guide_step4: 'Po přihlášení klikněte na Dashboard vedle své profilové fotky a vyberte "API keys" z levé nabídky.',
    chatgpt_guide_step5: 'Klikněte na tlačítko "Create new secret key".',
    chatgpt_guide_step6: 'Pojmenujte klíč a vytvořte jej.',
    chatgpt_guide_step7: 'Zkopírujte vygenerovaný API klíč a vložte jej do pole ChatGPT API klíče výše.',
    chatgpt_guide_note1: '※ OpenAI API vyžaduje registraci kreditní karty, použití je zpoplatněno.',
    chatgpt_guide_note2: '※ API klíč začíná formátem sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Navštivte webovou stránku X.AI (https://x.ai).',
    grok_guide_step2: 'Přihlaste se ke svému účtu.',
    grok_guide_step3: 'Klikněte na nabídku API v horní části.',
    grok_guide_step4: 'Klikněte na tlačítko "Start building now".',
    grok_guide_step5: 'Klikněte na nabídku API Keys vlevo.',
    grok_guide_step6: 'Vygenerujte svůj API klíč.',
    grok_guide_step7: 'Zkopírujte vygenerovaný API klíč a vložte jej do pole Grok API klíče výše.',
    grok_guide_note1: '※ API klíč začíná formátem xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Navštivte webovou stránku DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Klikněte na tlačítko "Sign up for free".',
    deepl_guide_step3: 'Zadejte svůj e-mail a heslo pro vytvoření účtu.',
    deepl_guide_step4: 'Potvrďte svou e-mailovou adresu pro aktivaci účtu.',
    deepl_guide_step5: 'Po přihlášení přejděte na https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Přejděte do nabídky API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Vložte API klíč bezplatné verze do pole DeepL API Key (zdarma) výše.',
    deepl_guide_step8: 'Vložte API klíč placené verze do pole DeepL API Key (placený) výše.',
    deepl_guide_note1: '※ Bezplatná verze DeepL API umožňuje překlad až 500 000 znaků měsíčně.',
    deepl_guide_note2: '※ Přechodem na placenou verzi můžete překládat více textu.',
    deepl_guide_note3: '※ Poznámka: Po přechodu na placenou verzi jsem nemohl používat bezplatné API. Vezměte to prosím na vědomí.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Pro bezplatný API klíč musíte použít koncový bod https://api-free.deepl.com.',
    deepl_api_help_pro: 'Pro placený API klíč musíte použít koncový bod https://api.deepl.com.',
    deepl_api_help_error: 'Pokud při používání bezplatného API klíče dostanete chybu "Wrong endpoint. Use https://api.deepl.com":',
    deepl_api_help_check1: '1. Zkontrolujte, zda jste vybrali možnost DeepL API (zdarma).',
    deepl_api_help_check2: '2. Zkontrolujte, zda skutečně používáte bezplatný API klíč.',
    
    // 영역 및 결과 관련
    original_text: 'Původní text',
    translation: 'Překlad',
    summary: 'Shrnutí',
    definition: 'Definice',
    copy_original: 'Kopírovat originál',
    copy_translation: 'Kopírovat překlad',
    copy_summary: 'Kopírovat shrnutí',
    copy_both: 'Kopírovat obojí',
    summarize_translation_result: 'Shrnout výsledek překladu',
    debug_info: 'Informace o ladění',
    page_url: 'URL stránky',
    page_title: 'Název stránky',
    target_language: 'Cílový jazyk',
    request_prompt: 'Požadavek promptu',
    api_response: 'API odpověď',
    clipboard_copy_failed: 'Kopírování do schránky selhalo',
    
    // 알림 및 오류 메시지
    canceled: 'Zrušeno',
    translation_canceled: 'Překlad byl zrušen.',
    summary_canceled: 'Shrnutí bylo zrušeno.',
    lookup_canceled: 'Vyhledávání termínu bylo zrušeno.',
    operation_canceled: 'Operace byla zrušena.',
    api_key_error: 'Chyba API klíče',
    api_key_missing: 'API klíč není nastaven. Nastavte prosím API klíč v nastavení rozšíření.',
    goto_settings: 'Přejít na nastavení',
    error: 'Chyba',
    translation_failed: 'Překlad selhal:',
    summary_failed: 'Shrnutí selhalo:',
    lookup_failed: 'Vyhledávání termínu selhalo:',
    no_response: 'Žádná odpověď',
    
    // 로그 메시지
    menu_added: 'Nabídka byla přidána.',
    menu_add_error: 'Chyba při přidávání nabídky:',
    menu_removed: 'Překladová nabídka byla odstraněna:',
    operation_applied: 'Oblast je již {operation}. Zobrazení výchozí kontextové nabídky.',
    already_has_operation: 'Oblast již má {operation}. Přeskočení operace.',
    rightclick_text: 'Text vybraný pravým kliknutím:',
    ctrl_rightclick: 'Detekováno Ctrl + pravé kliknutí: provádění shrnutí',
    normal_rightclick: 'Detekováno normální pravé kliknutí: provádění překladu',
    doubleclick_text: 'Text vybraný dvojitým kliknutím:',
    hovered_element: 'Prvek pod kurzorem:',
    summary_response: 'Odpověď shrnutí:',
    range_undefined: 'Rozsah není definován.',
    inline_translation_insertion_error: 'Chyba při vkládání vloženého překladu:',
    inline_summary_insertion_error: 'Chyba při vkládání vloženého shrnutí:',
    fallback_insertion_error: 'Chyba při vkládání záložního řešení:',
    copy_failed: 'Kopírování selhalo:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programování/Vývoj softwaru',
    domain_blog: 'Blog/Technické články',
    domain_qa: 'Programování Q&A',
    domain_docs: 'Technická dokumentace/API dokumentace',
    domain_academic: 'Akademické/Výzkum',
    domain_news: 'Zprávy/Aktuality',
    domain_finance: 'Finance/Investice',
    domain_medical: 'Lékařské/Zdravotnictví',
    domain_legal: 'Právní',
    domain_webpage: 'Název webové stránky:',
    
    // 초기화 메시지
    extension_init: 'Inicializace překladového rozšíření...',
    listeners_registered: 'Posluchači událostí byli zaregistrováni.',
    doubleclick_registered: 'Posluchač dvojitého kliknutí byl zaregistrován.',
    extension_ready: 'Překladové rozšíření je připraveno.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Seznam souborů bude zde zobrazen.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Překlad titulků v reálném čase byl aktivován.'
    ,subtitle_translation_disabled: 'Překlad titulků v reálném čase byl deaktivován.'
    ,subtitle_translation_button: 'Překlad titulků v reálném čase'
    ,runtime_not_initialized: 'Chrome runtime nebyl inicializován.'
    ,message_send_error: 'Chyba při odesílání zprávy:'
    ,translation_response_missing: 'Chybí odpověď překladu.'
    ,translation_error: 'Chyba překladu titulků:'

};

export default cs; 