// 폴란드어 (Polish) 언어 파일

const pl = {
    // 메뉴 및 UI 관련
    translate: 'Tłumacz',
    summarize: 'Podsumuj',
    lookup: 'Wyszukaj termin',
    cancel: 'Anuluj',
    copy: 'Kopiuj',
    copied: 'Skopiowano',
    close: 'Zamknij',
    translating: 'Tłumaczenie...',
    summarizing: 'Podsumowywanie...',
    looking_up: 'Wyszukiwanie...',
    cancel_with_esc: '(ESC aby anulować)',
    image_text_recognition: 'Rozpoznawanie tekstu z obrazu',
    menu_addition_error: 'Błąd podczas dodawania menu:',
    summary_result: 'Wynik podsumowania',
    copy_term_definition: 'Skopiuj definicję terminu',
    
    //options.js
    deepl_free_api_key_error: 'Klucz API nie jest prawidłowy. Sprawdź klucz API.',
    deepl_free_api_key_warning: 'Ostrzeżenie: To nie wygląda na klucz API DeepL. Wprowadź prawidłowy darmowy klucz API DeepL.',
    deepl_pro_api_key_warning: 'Ostrzeżenie: To nie wygląda na klucz API DeepL. Wprowadź prawidłowy płatny klucz API DeepL.',
    settings_save_error: 'Błąd podczas zapisywania ustawień. Spróbuj ponownie.',
    saved_all_settings: 'Wszystkie zapisane ustawienia:',

    // 옵션 페이지 관련
    options_title: 'Ustawienia rozszerzenia do tłumaczenia',
    service_selection: 'Wybór usługi tłumaczeniowej',
    api_key: 'Klucz API',
    model_selection: 'Wybór modelu',
    api_url: 'URL API (opcjonalnie)',
    api_key_free: 'Klucz API (darmowy)',
    api_key_pro: 'Klucz API (płatny)',
    interface_language: 'Język interfejsu',
    interface_language_desc: 'Menu i komunikaty rozszerzenia będą wyświetlane w wybranym języku.',
    preferred_languages: 'Preferowane języki (można wybrać tylko jeden język)',
    save: 'Zapisz',
    settings_saved: 'Ustawienia zapisane.',
    
    // 디버그 모드
    debug_mode: 'Włącz tryb debugowania (do rozwiązywania problemów)',
    debug_mode_desc: 'Gdy tryb debugowania jest włączony, komunikaty o błędach i informacje o komunikacji API będą wyświetlane w konsoli przeglądarki.',
    api_guide_title: 'Przewodnik rejestracji API',
    claude_api_guide_title: 'Rejestracja Claude API i generowanie klucza',
    chatgpt_api_guide_title: 'Rejestracja ChatGPT API i generowanie klucza',
    grok_api_guide_title: 'Rejestracja Grok API i generowanie klucza',
    deepl_api_guide_title: 'Rejestracja DeepL API i generowanie klucza',
    deepl_api_help_title: 'Uwagi dotyczące korzystania z DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Odwiedź stronę Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Kliknij przycisk "Sign up" w prawym górnym rogu.',
    claude_guide_step3: 'Wprowadź swój adres e-mail i hasło, aby utworzyć konto.',
    claude_guide_step4: 'Po zalogowaniu przejdź do zakładki "API Keys".',
    claude_guide_step5: 'Kliknij przycisk "Create API Key".',
    claude_guide_step6: 'Nadaj kluczowi nazwę i utwórz go.',
    claude_guide_step7: 'Skopiuj wygenerowany klucz API i wklej go w pole klucza Claude API powyżej.',
    claude_guide_note1: '※ Claude API wymaga rejestracji karty kredytowej, korzystanie jest płatne.',
    claude_guide_note2: '※ Klucz API zaczyna się od formatu sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Odwiedź stronę OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Kliknij przycisk "Sign up", aby utworzyć konto.',
    chatgpt_guide_step3: 'Potwierdź swój adres e-mail.',
    chatgpt_guide_step4: 'Po zalogowaniu kliknij Dashboard obok swojego zdjęcia profilowego i wybierz "API keys" z menu po lewej stronie.',
    chatgpt_guide_step5: 'Kliknij przycisk "Create new secret key".',
    chatgpt_guide_step6: 'Nadaj kluczowi nazwę i utwórz go.',
    chatgpt_guide_step7: 'Skopiuj wygenerowany klucz API i wklej go w pole klucza ChatGPT API powyżej.',
    chatgpt_guide_note1: '※ OpenAI API wymaga rejestracji karty kredytowej, korzystanie jest płatne.',
    chatgpt_guide_note2: '※ Klucz API zaczyna się od formatu sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Odwiedź stronę X.AI (https://x.ai).',
    grok_guide_step2: 'Zaloguj się na swoje konto.',
    grok_guide_step3: 'Kliknij menu API na górze.',
    grok_guide_step4: 'Kliknij przycisk "Start building now".',
    grok_guide_step5: 'Kliknij menu API Keys po lewej stronie.',
    grok_guide_step6: 'Wygeneruj swój klucz API.',
    grok_guide_step7: 'Skopiuj wygenerowany klucz API i wklej go w pole klucza Grok API powyżej.',
    grok_guide_note1: '※ Klucz API zaczyna się od formatu xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Odwiedź stronę DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Kliknij przycisk "Sign up for free".',
    deepl_guide_step3: 'Wprowadź swój adres e-mail i hasło, aby utworzyć konto.',
    deepl_guide_step4: 'Potwierdź swój adres e-mail, aby aktywować konto.',
    deepl_guide_step5: 'Po zalogowaniu przejdź do https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Przejdź do menu API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Wklej klucz API wersji darmowej w pole DeepL API Key (darmowy) powyżej.',
    deepl_guide_step8: 'Wklej klucz API wersji płatnej w pole DeepL API Key (płatny) powyżej.',
    deepl_guide_note1: '※ Darmowa wersja DeepL API pozwala na tłumaczenie do 500 000 znaków miesięcznie.',
    deepl_guide_note2: '※ Przechodząc na wersję płatną, możesz tłumaczyć więcej tekstu.',
    deepl_guide_note3: '※ Uwaga: Po przejściu na wersję płatną nie mogłem korzystać z darmowego API. Proszę wziąć to pod uwagę.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Dla darmowego klucza API musisz użyć punktu końcowego https://api-free.deepl.com.',
    deepl_api_help_pro: 'Dla płatnego klucza API musisz użyć punktu końcowego https://api.deepl.com.',
    deepl_api_help_error: 'Jeśli otrzymujesz błąd "Wrong endpoint. Use https://api.deepl.com" podczas korzystania z darmowego klucza API:',
    deepl_api_help_check1: '1. Sprawdź, czy wybrałeś opcję DeepL API (darmowy).',
    deepl_api_help_check2: '2. Sprawdź, czy faktycznie używasz darmowego klucza API.',
    
    // 영역 및 결과 관련
    original_text: 'Tekst oryginalny',
    translation: 'Tłumaczenie',
    summary: 'Podsumowanie',
    definition: 'Definicja',
    copy_original: 'Kopiuj oryginał',
    copy_translation: 'Kopiuj tłumaczenie',
    copy_summary: 'Kopiuj podsumowanie',
    copy_both: 'Kopiuj oba',
    summarize_translation_result: 'Podsumuj wynik tłumaczenia',
    debug_info: 'Informacje debugowania',
    page_url: 'URL strony',
    page_title: 'Tytuł strony',
    target_language: 'Język docelowy',
    request_prompt: 'Zapytanie',
    api_response: 'Odpowiedź API',
    clipboard_copy_failed: 'Kopiowanie do schowka nie powiodło się',
    
    // 알림 및 오류 메시지
    canceled: 'Anulowano',
    translation_canceled: 'Tłumaczenie anulowane.',
    summary_canceled: 'Podsumowanie anulowane.',
    lookup_canceled: 'Wyszukiwanie anulowane.',
    operation_canceled: 'Operacja anulowana.',
    api_key_error: 'Błąd klucza API',
    api_key_missing: 'Klucz API nie jest ustawiony. Ustaw klucz API w ustawieniach rozszerzenia.',
    goto_settings: 'Przejdź do ustawień',
    error: 'Błąd',
    translation_failed: 'Tłumaczenie nie powiodło się:',
    summary_failed: 'Podsumowanie nie powiodło się:',
    lookup_failed: 'Wyszukiwanie nie powiodło się:',
    no_response: 'Brak odpowiedzi',
    
    // 로그 메시지
    menu_added: 'Menu dodane.',
    menu_add_error: 'Błąd podczas dodawania menu:',
    menu_removed: 'Menu tłumaczenia usunięte:',
    operation_applied: 'Obszar jest już {operation}. Wyświetlanie domyślnego menu kontekstowego.',
    already_has_operation: 'Obszar ma już {operation}. Pomijanie operacji.',
    rightclick_text: 'Tekst wybrany prawym przyciskiem myszy:',
    ctrl_rightclick: 'Wykryto Ctrl + prawy przycisk myszy: wykonywanie podsumowania',
    normal_rightclick: 'Wykryto normalny prawy przycisk myszy: wykonywanie tłumaczenia',
    doubleclick_text: 'Tekst wybrany podwójnym kliknięciem:',
    hovered_element: 'Element pod kursorem:',
    summary_response: 'Odpowiedź podsumowania:',
    range_undefined: 'Zakres nie jest zdefiniowany.',
    inline_translation_insertion_error: 'Błąd podczas wstawiania tłumaczenia w tekście:',
    inline_summary_insertion_error: 'Błąd podczas wstawiania podsumowania w tekście:',
    fallback_insertion_error: 'Błąd podczas wstawiania rozwiązania awaryjnego:',
    copy_failed: 'Kopiowanie nie powiodło się:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programowanie/Rozwój oprogramowania',
    domain_blog: 'Blog/Artykuły techniczne',
    domain_qa: 'Programowanie Q&A',
    domain_docs: 'Dokumentacja techniczna/Dokumentacja API',
    domain_academic: 'Akademickie/Badania',
    domain_news: 'Wiadomości/Aktualności',
    domain_finance: 'Finanse/Inwestycje',
    domain_medical: 'Medyczne/Zdrowie',
    domain_legal: 'Prawne',
    domain_webpage: 'Tytuł strony internetowej:',
    
    // 초기화 메시지
    extension_init: 'Inicjalizacja rozszerzenia do tłumaczenia...',
    listeners_registered: 'Zarejestrowano nasłuchiwacze zdarzeń.',
    doubleclick_registered: 'Zarejestrowano nasłuchiwacz podwójnego kliknięcia.',
    extension_ready: 'Rozszerzenie do tłumaczenia jest gotowe.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Lista plików zostanie wyświetlona tutaj.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Tłumaczenie napisów w czasie rzeczywistym zostało włączone.'
    ,subtitle_translation_disabled: 'Tłumaczenie napisów w czasie rzeczywistym zostało wyłączone.'
    ,subtitle_translation_button: 'Tłumaczenie napisów w czasie rzeczywistym'
    ,runtime_not_initialized: 'Środowisko wykonawcze Chrome nie zostało zainicjowane.'
    ,message_send_error: 'Błąd podczas wysyłania wiadomości:'
    ,translation_response_missing: 'Brak odpowiedzi tłumaczenia.'
    ,translation_error: 'Błąd tłumaczenia napisów:'
};

export default pl; 