// 루마니아어 (Romanian) 언어 파일

const ro = {
    // 메뉴 및 UI 관련
    translate: 'Traduceți',
    summarize: 'Rezumați',
    lookup: 'Căutați termen',
    cancel: 'Anulați',
    copy: 'Copiați',
    copied: 'Copiat',
    close: 'Închideți',
    translating: 'Se traduce...',
    summarizing: 'Se rezumă...',
    looking_up: 'Se caută...',
    cancel_with_esc: '(ESC pentru anulare)',
    image_text_recognition: 'Recunoaștere text din imagine',
    menu_addition_error: 'Eroare la adăugarea meniului:',
    summary_result: 'Rezultatul rezumatului',
    copy_term_definition: 'Copiați definiția termenului',
    
    //options.js
    deepl_free_api_key_error: 'Cheia API nu este validă. Vă rugăm să verificați cheia API.',
    deepl_free_api_key_warning: 'Avertisment: Aceasta nu pare a fi o cheie API DeepL. Vă rugăm să introduceți cheia API DeepL gratuită corectă.',
    deepl_pro_api_key_warning: 'Avertisment: Aceasta nu pare a fi o cheie API DeepL. Vă rugăm să introduceți cheia API DeepL plătită corectă.',
    settings_save_error: 'Eroare la salvarea setărilor. Vă rugăm să încercați din nou.',
    saved_all_settings: 'Toate setările salvate:',
    // 옵션 페이지 관련
    options_title: 'Setări extensie de traducere',
    service_selection: 'Selectare serviciu de traducere',
    api_key: 'Cheie API',
    model_selection: 'Selectare model',
    api_url: 'URL API (opțional)',
    api_key_free: 'Cheie API (gratuită)',
    api_key_pro: 'Cheie API (plătită)',
    interface_language: 'Limba interfeței',
    interface_language_desc: 'Meniurile și mesajele extensiei vor fi afișate în limba selectată.',
    preferred_languages: 'Limbi preferate (poate fi selectată doar o limbă)',
    save: 'Salvați',
    settings_saved: 'Setări salvate.',
    
    // 디버그 모드
    debug_mode: 'Activați modul de depanare (pentru rezolvarea problemelor)',
    debug_mode_desc: 'Când modul de depanare este activat, mesajele de eroare și informațiile de comunicare API vor fi afișate în consola browserului.',
    api_guide_title: 'Ghid de înregistrare API',
    claude_api_guide_title: 'Înregistrare și generare cheie Claude API',
    chatgpt_api_guide_title: 'Înregistrare și generare cheie ChatGPT API',
    grok_api_guide_title: 'Înregistrare și generare cheie Grok API',
    deepl_api_guide_title: 'Înregistrare și generare cheie DeepL API',
    deepl_api_help_title: 'Note despre utilizarea DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Vizitați site-ul Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Faceți clic pe butonul "Sign up" din colțul din dreapta sus.',
    claude_guide_step3: 'Introduceți adresa de e-mail și parola pentru a crea un cont.',
    claude_guide_step4: 'După autentificare, mergeți la fila "API Keys".',
    claude_guide_step5: 'Faceți clic pe butonul "Create API Key".',
    claude_guide_step6: 'Dați un nume cheii și creați-o.',
    claude_guide_step7: 'Copiați cheia API generată și lipiți-o în câmpul cheii Claude API de mai sus.',
    claude_guide_note1: '※ Claude API necesită înregistrarea cardului de credit, utilizarea este contra cost.',
    claude_guide_note2: '※ Cheia API începe cu formatul sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Vizitați site-ul OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Faceți clic pe butonul "Sign up" pentru a crea un cont.',
    chatgpt_guide_step3: 'Confirmați adresa de e-mail.',
    chatgpt_guide_step4: 'După autentificare, faceți clic pe Dashboard lângă poza de profil și selectați "API keys" din meniul din stânga.',
    chatgpt_guide_step5: 'Faceți clic pe butonul "Create new secret key".',
    chatgpt_guide_step6: 'Dați un nume cheii și creați-o.',
    chatgpt_guide_step7: 'Copiați cheia API generată și lipiți-o în câmpul cheii ChatGPT API de mai sus.',
    chatgpt_guide_note1: '※ OpenAI API necesită înregistrarea cardului de credit, utilizarea este contra cost.',
    chatgpt_guide_note2: '※ Cheia API începe cu formatul sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Vizitați site-ul X.AI (https://x.ai).',
    grok_guide_step2: 'Autentificați-vă în contul dvs.',
    grok_guide_step3: 'Faceți clic pe meniul API din partea de sus.',
    grok_guide_step4: 'Faceți clic pe butonul "Start building now".',
    grok_guide_step5: 'Faceți clic pe meniul API Keys din stânga.',
    grok_guide_step6: 'Generați cheia dvs. API.',
    grok_guide_step7: 'Copiați cheia API generată și lipiți-o în câmpul cheii Grok API de mai sus.',
    grok_guide_note1: '※ Cheia API începe cu formatul xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Vizitați site-ul DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Faceți clic pe butonul "Sign up for free".',
    deepl_guide_step3: 'Introduceți adresa de e-mail și parola pentru a crea un cont.',
    deepl_guide_step4: 'Confirmați adresa de e-mail pentru a activa contul.',
    deepl_guide_step5: 'După autentificare, mergeți la https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Mergeți la meniul API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Lipiți cheia API a versiunii gratuite în câmpul DeepL API Key (gratuită) de mai sus.',
    deepl_guide_step8: 'Lipiți cheia API a versiunii plătite în câmpul DeepL API Key (plătită) de mai sus.',
    deepl_guide_note1: '※ Versiunea gratuită a DeepL API permite traducerea a până la 500.000 de caractere pe lună.',
    deepl_guide_note2: '※ Prin trecerea la versiunea plătită, puteți traduce mai mult text.',
    deepl_guide_note3: '※ Notă: După trecerea la versiunea plătită, nu am putut utiliza API-ul gratuit. Vă rugăm să țineți cont de acest lucru.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Pentru cheia API gratuită, trebuie să utilizați endpoint-ul https://api-free.deepl.com.',
    deepl_api_help_pro: 'Pentru cheia API plătită, trebuie să utilizați endpoint-ul https://api.deepl.com.',
    deepl_api_help_error: 'Dacă primiți eroarea "Wrong endpoint. Use https://api.deepl.com" când utilizați cheia API gratuită:',
    deepl_api_help_check1: '1. Verificați dacă ați selectat opțiunea DeepL API (gratuită).',
    deepl_api_help_check2: '2. Verificați dacă utilizați într-adevăr o cheie API gratuită.',
    
    // 영역 및 결과 관련
    original_text: 'Text original',
    translation: 'Traducere',
    summary: 'Rezumat',
    definition: 'Definiție',
    copy_original: 'Copiați originalul',
    copy_translation: 'Copiați traducerea',
    copy_summary: 'Copiați rezumatul',
    copy_both: 'Copiați ambele',
    summarize_translation_result: 'Rezumați rezultatul traducerii',
    debug_info: 'Informații depanare',
    page_url: 'URL pagină',
    page_title: 'Titlu pagină',
    target_language: 'Limba țintă',
    request_prompt: 'Prompt solicitare',
    api_response: 'Răspuns API',
    clipboard_copy_failed: 'Copierea în clipboard a eșuat',
    
    // 알림 및 오류 메시지
    canceled: 'Anulat',
    translation_canceled: 'Traducere anulată.',
    summary_canceled: 'Rezumat anulat.',
    lookup_canceled: 'Căutare anulată.',
    operation_canceled: 'Operație anulată.',
    api_key_error: 'Eroare cheie API',
    api_key_missing: 'Cheia API nu este setată. Vă rugăm să setați cheia API în setările extensiei.',
    goto_settings: 'Mergeți la setări',
    error: 'Eroare',
    translation_failed: 'Traducerea a eșuat:',
    summary_failed: 'Rezumatul a eșuat:',
    lookup_failed: 'Căutarea a eșuat:',
    no_response: 'Niciun răspuns',
    
    // 로그 메시지
    menu_added: 'Meniu adăugat.',
    menu_add_error: 'Eroare la adăugarea meniului:',
    menu_removed: 'Meniu de traducere eliminat:',
    operation_applied: 'Zona este deja {operation}. Se afișează meniul contextual implicit.',
    already_has_operation: 'Zona are deja {operation}. Se omite operația.',
    rightclick_text: 'Text selectat cu clic dreapta:',
    ctrl_rightclick: 'Ctrl + clic dreapta detectat: se execută rezumatul',
    normal_rightclick: 'Clic dreapta normal detectat: se execută traducerea',
    doubleclick_text: 'Text selectat cu dublu clic:',
    hovered_element: 'Element sub cursor:',
    summary_response: 'Răspuns rezumat:',
    range_undefined: 'Interval nedefinit.',
    inline_translation_insertion_error: 'Eroare la inserarea traducerii inline:',
    inline_summary_insertion_error: 'Eroare la inserarea rezumatului inline:',
    fallback_insertion_error: 'Eroare la inserarea soluției de rezervă:',
    copy_failed: 'Copierea a eșuat:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programare/Dezvoltare software',
    domain_blog: 'Blog/Articole tehnice',
    domain_qa: 'Programare Î&R',
    domain_docs: 'Documentație tehnică/Documentație API',
    domain_academic: 'Academic/Cercetare',
    domain_news: 'Știri/Actualități',
    domain_finance: 'Finanțe/Investiții',
    domain_medical: 'Medical/Sănătate',
    domain_legal: 'Juridic',
    domain_webpage: 'Titlu pagină web:',
    
    // 초기화 메시지
    extension_init: 'Se inițializează extensia de traducere...',
    listeners_registered: 'Ascultători de evenimente înregistrați.',
    doubleclick_registered: 'Ascultător dublu clic înregistrat.',
    extension_ready: 'Extensia de traducere este gata.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Lista fișierelor va fi afișată aici.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Traducerea subtitrărilor în timp real a fost activată.'
    ,subtitle_translation_disabled: 'Traducerea subtitrărilor în timp real a fost dezactivată.'
    ,subtitle_translation_button: 'Traducere subtitrări în timp real'
    ,runtime_not_initialized: 'Runtime-ul Chrome nu a fost inițializat.'
    ,message_send_error: 'Eroare la trimiterea mesajului:'
    ,translation_response_missing: 'Lipsește răspunsul traducerii.'
    ,translation_error: 'Eroare la traducerea subtitrărilor:'
};

export default ro; 