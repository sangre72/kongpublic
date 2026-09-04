// 이탈리아어 (Italian) 언어 파일

const it = {
    // 메뉴 및 UI 관련
    translate: 'Traduci',
    summarize: 'Riassumi',
    lookup: 'Cerca termine',
    cancel: 'Annulla',
    copy: 'Copia',
    copied: 'Copiato',
    close: 'Chiudi',
    translating: 'Traduzione in corso...',
    summarizing: 'Riassunto in corso...',
    looking_up: 'Ricerca in corso...',
    cancel_with_esc: '(ESC per annullare)',
    image_text_recognition: 'Riconoscimento testo da immagine',
    menu_addition_error: 'Errore nell\'aggiunta del menu:',
    summary_result: 'Riassunto risultato',
    copy_term_definition: 'Copia definizione termine',

    //options.js
    deepl_free_api_key_error: 'La chiave API non è valida. Per favore, verifica la chiave API.',
    deepl_free_api_key_warning: 'Attenzione: Questo non sembra essere una chiave API di DeepL. Per favore, inserisci la chiave API di DeepL gratuita corretta.',
    deepl_pro_api_key_warning: 'Attenzione: Questo non sembra essere una chiave API di DeepL. Per favore, inserisci la chiave API di DeepL pagata corretta.',
    settings_save_error: 'Errore nella salvataggio delle impostazioni. Per favore, riprova.',
    saved_all_settings: 'Tutte le impostazioni salvate:',
    
    // 옵션 페이지 관련
    options_title: 'Impostazioni estensione di traduzione',
    service_selection: 'Selezione servizio di traduzione',
    api_key: 'Chiave API',
    model_selection: 'Selezione modello',
    api_url: 'URL API (opzionale)',
    api_key_free: 'Chiave API (gratuita)',
    api_key_pro: 'Chiave API (a pagamento)',
    interface_language: 'Lingua interfaccia',
    interface_language_desc: 'Menu e messaggi dell\'estensione saranno visualizzati nella lingua selezionata.',
    preferred_languages: 'Lingue preferite (è possibile selezionare una sola lingua)',
    save: 'Salva',
    settings_saved: 'Impostazioni salvate.',
    
    // 디버그 모드
    debug_mode: 'Attiva modalità debug (per risoluzione problemi)',
    debug_mode_desc: 'Quando la modalità debug è attiva, i messaggi di errore e le informazioni di comunicazione API saranno visualizzati nella console del browser.',
    api_guide_title: 'Guida registrazione API',
    claude_api_guide_title: 'Registrazione e generazione chiave Claude API',
    chatgpt_api_guide_title: 'Registrazione e generazione chiave ChatGPT API',
    grok_api_guide_title: 'Registrazione e generazione chiave Grok API',
    deepl_api_guide_title: 'Registrazione e generazione chiave DeepL API',
    deepl_api_help_title: 'Note sull\'utilizzo dell\'API DeepL',
    
    // Claude API 가이드
    claude_guide_step1: 'Visita il sito web di Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Clicca sul pulsante "Sign up" nell\'angolo in alto a destra.',
    claude_guide_step3: 'Inserisci la tua email e password per creare un account.',
    claude_guide_step4: 'Dopo il login, vai alla scheda "API Keys".',
    claude_guide_step5: 'Clicca sul pulsante "Create API Key".',
    claude_guide_step6: 'Dai un nome alla chiave e creala.',
    claude_guide_step7: 'Copia la chiave API generata e incollala nel campo della chiave Claude API qui sopra.',
    claude_guide_note1: '※ Claude API richiede la registrazione di una carta di credito, l\'utilizzo è a pagamento.',
    claude_guide_note2: '※ La chiave API inizia con il formato sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Visita il sito web di OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Clicca sul pulsante "Sign up" per creare un account.',
    chatgpt_guide_step3: 'Conferma il tuo indirizzo email.',
    chatgpt_guide_step4: 'Dopo il login, clicca su Dashboard accanto alla tua foto profilo e seleziona "API keys" dal menu a sinistra.',
    chatgpt_guide_step5: 'Clicca sul pulsante "Create new secret key".',
    chatgpt_guide_step6: 'Dai un nome alla chiave e creala.',
    chatgpt_guide_step7: 'Copia la chiave API generata e incollala nel campo della chiave ChatGPT API qui sopra.',
    chatgpt_guide_note1: '※ OpenAI API richiede la registrazione di una carta di credito, l\'utilizzo è a pagamento.',
    chatgpt_guide_note2: '※ La chiave API inizia con il formato sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Visita il sito web X.AI (https://x.ai).',
    grok_guide_step2: 'Accedi al tuo account.',
    grok_guide_step3: 'Clicca sul menu API in alto.',
    grok_guide_step4: 'Clicca sul pulsante "Start building now".',
    grok_guide_step5: 'Clicca sul menu API Keys a sinistra.',
    grok_guide_step6: 'Genera la tua chiave API.',
    grok_guide_step7: 'Copia la chiave API generata e incollala nel campo della chiave Grok API qui sopra.',
    grok_guide_note1: '※ La chiave API inizia con il formato xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Visita il sito web DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Clicca sul pulsante "Sign up for free".',
    deepl_guide_step3: 'Inserisci la tua email e password per creare un account.',
    deepl_guide_step4: 'Conferma il tuo indirizzo email per attivare l\'account.',
    deepl_guide_step5: 'Dopo il login, vai su https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Vai al menu API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Incolla la chiave API della versione gratuita nel campo DeepL API Key (gratuita) qui sopra.',
    deepl_guide_step8: 'Incolla la chiave API della versione a pagamento nel campo DeepL API Key (a pagamento) qui sopra.',
    deepl_guide_note1: '※ La versione gratuita di DeepL API permette di tradurre fino a 500.000 caratteri al mese.',
    deepl_guide_note2: '※ Passando alla versione a pagamento puoi tradurre più testo.',
    deepl_guide_note3: '※ Nota: Dopo il passaggio alla versione a pagamento, non ho potuto utilizzare l\'API gratuita. Si prega di tenerne conto.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Per la chiave API gratuita, devi utilizzare l\'endpoint https://api-free.deepl.com.',
    deepl_api_help_pro: 'Per la chiave API a pagamento, devi utilizzare l\'endpoint https://api.deepl.com.',
    deepl_api_help_error: 'Se ricevi l\'errore "Wrong endpoint. Use https://api.deepl.com" quando utilizzi la chiave API gratuita:',
    deepl_api_help_check1: '1. Verifica di aver selezionato l\'opzione DeepL API (gratuita).',
    deepl_api_help_check2: '2. Verifica di star effettivamente utilizzando una chiave API gratuita.',
    
    // 영역 및 결과 관련
    original_text: 'Testo originale',
    translation: 'Traduzione',
    summary: 'Riassunto',
    definition: 'Definizione',
    copy_original: 'Copia originale',
    copy_translation: 'Copia traduzione',
    copy_summary: 'Copia riassunto',
    copy_both: 'Copia entrambi',
    summarize_translation_result: 'Riassumi risultato traduzione',
    debug_info: 'Informazioni debug',
    page_url: 'URL pagina',
    page_title: 'Titolo pagina',
    target_language: 'Lingua di destinazione',
    request_prompt: 'Richiesta prompt',
    api_response: 'Risposta API',
    clipboard_copy_failed: 'Copia negli appunti fallita',
    
    // 알림 및 오류 메시지
    canceled: 'Annullato',
    translation_canceled: 'Traduzione annullata.',
    summary_canceled: 'Riassunto annullato.',
    lookup_canceled: 'Ricerca annullata.',
    operation_canceled: 'Operazione annullata.',
    api_key_error: 'Errore chiave API',
    api_key_missing: 'Chiave API non impostata. Imposta la chiave API nelle impostazioni dell\'estensione.',
    goto_settings: 'Vai alle impostazioni',
    error: 'Errore',
    translation_failed: 'Traduzione fallita:',
    summary_failed: 'Riassunto fallito:',
    lookup_failed: 'Ricerca fallita:',
    no_response: 'Nessuna risposta',
    
    // 로그 메시지
    menu_added: 'Menu aggiunto.',
    menu_add_error: 'Errore nell\'aggiunta del menu:',
    menu_removed: 'Menu di traduzione rimosso:',
    operation_applied: 'L\'area è già {operation}. Visualizzazione menu contestuale predefinito.',
    already_has_operation: 'L\'area ha già {operation}. Salto operazione.',
    rightclick_text: 'Testo selezionato con clic destro:',
    ctrl_rightclick: 'Ctrl + clic destro rilevato: esecuzione riassunto',
    normal_rightclick: 'Clic destro normale rilevato: esecuzione traduzione',
    doubleclick_text: 'Testo selezionato con doppio clic:',
    hovered_element: 'Elemento sotto il cursore:',
    summary_response: 'Risposta riassunto:',
    range_undefined: 'Intervallo non definito.',
    inline_translation_insertion_error: 'Errore nell\'inserimento della traduzione inline:',
    inline_summary_insertion_error: 'Errore nell\'inserimento del riassunto inline:',
    fallback_insertion_error: 'Errore nell\'inserimento del fallback:',
    copy_failed: 'Copia fallita:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmazione/Sviluppo software',
    domain_blog: 'Blog/Articoli tecnici',
    domain_qa: 'Programmazione D&R',
    domain_docs: 'Documentazione tecnica/Documentazione API',
    domain_academic: 'Accademico/Ricerca',
    domain_news: 'Notizie/Attualità',
    domain_finance: 'Finanza/Investimenti',
    domain_medical: 'Medico/Salute',
    domain_legal: 'Legale',
    domain_webpage: 'Titolo pagina web:',
    
    // 초기화 메시지
    extension_init: 'Inizializzazione estensione di traduzione...',
    listeners_registered: 'Listener eventi registrati.',
    doubleclick_registered: 'Listener doppio clic registrato.',
    extension_ready: 'Estensione di traduzione pronta.'

    //filePanel.js
    ,fileListWillBeShownHere: 'La lista dei file sarà mostrata qui.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'La traduzione dei sottotitoli in tempo reale è stata attivata.'
    ,subtitle_translation_disabled: 'La traduzione dei sottotitoli in tempo reale è stata disattivata.'
    ,subtitle_translation_button: 'Traduzione dei sottotitoli in tempo reale'
    ,runtime_not_initialized: 'Il runtime di Chrome non è stato inizializzato.'
    ,message_send_error: 'Errore durante l\'invio del messaggio:'
    ,translation_response_missing: 'Nessuna risposta di traduzione.'
    ,translation_error: 'Errore nella traduzione dei sottotitoli:'
};

export default it; 