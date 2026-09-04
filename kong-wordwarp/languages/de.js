// 독일어 (German) 언어 파일

const de = {
    // 메뉴 및 UI 관련
    translate: 'Übersetzen',
    summarize: 'Zusammenfassen',
    lookup: 'Begriff nachschlagen',
    cancel: 'Abbrechen',
    copy: 'Kopieren',
    copied: 'Kopiert',
    close: 'Schließen',
    translating: 'Übersetzung läuft...',
    summarizing: 'Zusammenfassung läuft...',
    looking_up: 'Begriff wird nachgeschlagen...',
    cancel_with_esc: '(ESC zum Abbrechen)',
    image_text_recognition: 'Bildtexterkennung',
    menu_addition_error: 'Fehler beim Hinzufügen des Menüs:',
    summary_result: 'Zusammenfassungsergebnis',
    copy_term_definition: 'Begriffdefinition kopieren',

   //options.js
   deepl_free_api_key_error: 'API-Schlüssel ist ungültig. Bitte überprüfen Sie den API-Schlüssel.',
   deepl_free_api_key_warning: 'Warnung: Dies scheint kein DeepL API-Schlüssel zu sein. Bitte geben Sie den genaueren DeepL-API-Schlüssel ein.',
   deepl_pro_api_key_warning: 'Warnung: Dies scheint kein DeepL API-Schlüssel zu sein. Bitte geben Sie den genaueren DeepL-API-Schlüssel ein.',
   settings_save_error: 'Fehler beim Speichern der Einstellungen. Bitte versuchen Sie es erneut.',
   saved_all_settings: 'Alle gespeicherten Einstellungen:',
    
    // 옵션 페이지 관련
    options_title: 'Einstellungen der Übersetzungserweiterung',
    service_selection: 'Übersetzungsdienst auswählen',
    api_key: 'API-Schlüssel',
    model_selection: 'Modell auswählen',
    api_url: 'API-URL (Optional)',
    api_key_free: 'API-Schlüssel (Kostenlos)',
    api_key_pro: 'API-Schlüssel (Pro)',
    interface_language: 'Schnittstellensprache',
    interface_language_desc: 'Die Menüs und Nachrichten der Erweiterung werden in der ausgewählten Sprache angezeigt.',
    preferred_languages: 'Bevorzugte Sprachen (Nur eine Sprache kann ausgewählt werden)',
    save: 'Speichern',
    settings_saved: 'Einstellungen gespeichert.',
    
    // 새로 추가된 옵션 페이지 관련 텍스트
    debug_mode: 'Debug-Modus aktivieren (zur Fehlerbehebung)',
    debug_mode_desc: 'Wenn der Debug-Modus aktiviert ist, werden Fehlermeldungen und API-Kommunikationsinformationen in der Browser-Konsole angezeigt.',
    api_guide_title: 'API-Anmeldeanleitung',
    claude_api_guide_title: 'Claude API-Registrierung und Schlüsselausstellung',
    chatgpt_api_guide_title: 'ChatGPT API-Registrierung und Schlüsselausstellung',
    grok_api_guide_title: 'Grok API-Registrierung und Schlüsselausstellung',
    deepl_api_guide_title: 'DeepL API-Registrierung und Schlüsselausstellung',
    deepl_api_help_title: 'DeepL API-Nutzungshinweise',
    
    // Claude API 가이드
    claude_guide_step1: 'Besuchen Sie die Anthropic-Website (https://www.anthropic.com/api).',
    claude_guide_step2: 'Klicken Sie auf die Schaltfläche "Sign up" in der oberen rechten Ecke.',
    claude_guide_step3: 'Geben Sie Ihre E-Mail-Adresse und Ihr Passwort ein, um ein Konto zu erstellen.',
    claude_guide_step4: 'Nach der Anmeldung navigieren Sie zum Tab "API Keys".',
    claude_guide_step5: 'Klicken Sie auf die Schaltfläche "Create API Key".',
    claude_guide_step6: 'Geben Sie einen Namen für Ihren Schlüssel ein und erstellen Sie ihn.',
    claude_guide_step7: 'Kopieren Sie den ausgestellten API-Schlüssel und fügen Sie ihn in das obige Claude API-Schlüsselfeld ein.',
    claude_guide_note1: '※ Claude API erfordert eine Kreditkartenregistrierung, und die Gebühren basieren auf der Nutzung.',
    claude_guide_note2: '※ API-Schlüssel beginnen mit dem Format sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Besuchen Sie die OpenAI-Website (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Klicken Sie auf die Schaltfläche "Sign up", um ein Konto zu erstellen.',
    chatgpt_guide_step3: 'Schließen Sie die E-Mail-Verifizierung ab.',
    chatgpt_guide_step4: 'Nach der Anmeldung klicken Sie auf Dashboard neben Ihrem Profilsymbol oben rechts und wählen dann "API keys" aus dem linken Menü.',
    chatgpt_guide_step5: 'Klicken Sie auf die Schaltfläche "Create new secret key".',
    chatgpt_guide_step6: 'Geben Sie einen Namen für Ihren Schlüssel ein und erstellen Sie ihn.',
    chatgpt_guide_step7: 'Kopieren Sie den ausgestellten API-Schlüssel und fügen Sie ihn in das obige ChatGPT API-Schlüsselfeld ein.',
    chatgpt_guide_note1: '※ OpenAI API erfordert eine Kreditkartenregistrierung, und die Gebühren basieren auf der Nutzung.',
    chatgpt_guide_note2: '※ API-Schlüssel beginnen mit dem Format sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Besuchen Sie die X.AI-Website (https://x.ai).',
    grok_guide_step2: 'Melden Sie sich mit Ihrem Konto an.',
    grok_guide_step3: 'Klicken Sie auf das API-Menü oben.',
    grok_guide_step4: 'Klicken Sie auf die Schaltfläche "Start building now".',
    grok_guide_step5: 'Klicken Sie auf das API Keys-Menü auf der linken Seite.',
    grok_guide_step6: 'Holen Sie sich Ihren API-Schlüssel.',
    grok_guide_step7: 'Kopieren Sie den ausgestellten API-Schlüssel und fügen Sie ihn in das obige Grok API-Schlüsselfeld ein.',
    grok_guide_note1: '※ API-Schlüssel beginnen mit dem Format xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Besuchen Sie die DeepL API-Website (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Klicken Sie auf die Schaltfläche "Sign up for free".',
    deepl_guide_step3: 'Geben Sie Ihre E-Mail-Adresse und Ihr Passwort ein, um ein Konto zu erstellen.',
    deepl_guide_step4: 'Schließen Sie die E-Mail-Verifizierung ab, um Ihr Konto zu aktivieren.',
    deepl_guide_step5: 'Nach der Anmeldung navigieren Sie zu https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Gehen Sie zum API keys-Menü (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Fügen Sie den API-Schlüssel der kostenlosen Version in das obige DeepL API-Schlüsselfeld (Kostenlos) ein.',
    deepl_guide_step8: 'Fügen Sie den API-Schlüssel der kostenpflichtigen Version in das obige DeepL API-Schlüsselfeld (Pro) ein.',
    deepl_guide_note1: '※ DeepL API kostenlose Version ermöglicht die Übersetzung von bis zu 500.000 Zeichen pro Monat.',
    deepl_guide_note2: '※ Ein Upgrade auf die kostenpflichtige Version ermöglicht Ihnen die Übersetzung von mehr Text.',
    deepl_guide_note3: '※ Hinweis: Ich habe festgestellt, dass ich nach dem Upgrade auf die kostenpflichtige Version die kostenlose Version der API nicht mehr nutzen konnte.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Kostenlose API-Schlüssel müssen den Endpunkt https://api-free.deepl.com verwenden.',
    deepl_api_help_pro: 'Kostenpflichtige API-Schlüssel müssen den Endpunkt https://api.deepl.com verwenden.',
    deepl_api_help_error: 'Wenn Sie einen kostenlosen API-Schlüssel verwenden und den Fehler "Wrong endpoint. Use https://api.deepl.com" erhalten:',
    deepl_api_help_check1: '1. Überprüfen Sie, ob Sie die Option DeepL API (Kostenlos) ausgewählt haben.',
    deepl_api_help_check2: '2. Überprüfen Sie, ob Sie tatsächlich einen kostenlosen API-Schlüssel verwenden.',
    
    // 영역 및 결과 관련
    original_text: 'Original',
    translation: 'Übersetzung',
    summary: 'Zusammenfassung',
    definition: 'Definition',
    copy_original: 'Original kopieren',
    copy_translation: 'Übersetzung kopieren',
    copy_summary: 'Zusammenfassung kopieren',
    copy_both: 'Beides kopieren',
    summarize_translation_result: 'Übersetzungsergebnis zusammenfassen',
    debug_info: 'Debug-Informationen',
    page_url: 'Seiten-URL',
    page_title: 'Seitentitel',
    target_language: 'Zielsprache',
    request_prompt: 'Anforderungsaufforderung',
    api_response: 'API-Antwort',
    clipboard_copy_failed: 'Kopieren in die Zwischenablage fehlgeschlagen',
    
    // 알림 및 오류 메시지
    canceled: 'Abgebrochen',
    translation_canceled: 'Die Übersetzung wurde abgebrochen.',
    summary_canceled: 'Die Zusammenfassung wurde abgebrochen.',
    lookup_canceled: 'Die Begriffssuche wurde abgebrochen.',
    operation_canceled: 'Operation wurde abgebrochen.',
    api_key_error: 'API-Schlüssel Fehler',
    api_key_missing: 'API-Schlüssel ist nicht eingestellt. Bitte setzen Sie Ihren API-Schlüssel in den Erweiterungseinstellungen.',
    goto_settings: 'Zu Einstellungen wechseln',
    error: 'Fehler',
    translation_failed: 'Übersetzung fehlgeschlagen:',
    summary_failed: 'Zusammenfassung fehlgeschlagen:',
    lookup_failed: 'Begriffssuche fehlgeschlagen:',
    no_response: 'Keine Antwort',
    
    // 로그 메시지
    menu_added: 'Menü wurde hinzugefügt.',
    menu_add_error: 'Fehler beim Hinzufügen des Menüs:',
    menu_removed: 'Übersetzungsmenü entfernt:',
    operation_applied: 'Dieser Bereich hat bereits eine {operation}. Das Standard-Kontextmenü wird angezeigt.',
    already_has_operation: 'Dieser Bereich hat bereits eine {operation}. Operation wird übersprungen.',
    rightclick_text: 'Rechtsklick-Text:',
    ctrl_rightclick: 'Strg + Rechtsklick erkannt: Zusammenfassung wird ausgeführt',
    normal_rightclick: 'Normaler Rechtsklick erkannt: Übersetzung wird ausgeführt',
    doubleclick_text: 'Doppelklick-Text:',
    hovered_element: 'Überfahrenes Element:',
    summary_response: 'Zusammenfassungsantwort:',
    range_undefined: 'Bereich ist nicht definiert.',
    inline_translation_insertion_error: 'Fehler beim Einfügen der Inline-Übersetzung:',
    inline_summary_insertion_error: 'Fehler beim Einfügen der Inline-Zusammenfassung:',
    fallback_insertion_error: 'Fallback-Einfügungsfehler:',
    copy_failed: 'Kopieren fehlgeschlagen:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmierung/Softwareentwicklung',
    domain_blog: 'Blog/Technische Artikel',
    domain_qa: 'Programmierung Q&A',
    domain_docs: 'Technische Dokumentation/API-Dokumentation',
    domain_academic: 'Akademisch/Forschung',
    domain_news: 'Nachrichten/Aktuelles',
    domain_finance: 'Finanzen/Investitionen',
    domain_medical: 'Medizin/Gesundheit',
    domain_legal: 'Recht',
    domain_webpage: 'Titel der Webseite:',
    
    // 초기화 메시지
    extension_init: 'Übersetzungserweiterung wird initialisiert...',
    listeners_registered: 'Ereignis-Listener wurden registriert.',
    doubleclick_registered: 'Doppelklick-Ereignis-Listener wurde registriert.',
    extension_ready: 'Die Übersetzungserweiterung ist bereit.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Die Liste der Dateien wird hier angezeigt.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Echtzeit-Untertitelübersetzung wurde aktiviert.'
    ,subtitle_translation_disabled: 'Echtzeit-Untertitelübersetzung wurde deaktiviert.'
    ,subtitle_translation_button: 'Echtzeit-Untertitelübersetzung'
    ,runtime_not_initialized: 'Chrome-Runtime wurde nicht initialisiert.'
    ,message_send_error: 'Fehler beim Senden der Nachricht:'
    ,translation_response_missing: 'Keine Übersetzungsantwort vorhanden.'
    ,translation_error: 'Fehler bei der Untertitelübersetzung:'
};

// 기본 내보내기로 언어 데이터 노출
export default de;