// 리투아니아어 (Lithuanian) 언어 파일

const lt = {
    // 메뉴 및 UI 관련
    translate: 'Versti',
    summarize: 'Apibendrinti',
    lookup: 'Ieškoti termino',
    cancel: 'Atšaukti',
    copy: 'Kopijuoti',
    copied: 'Nukopijuota',
    close: 'Uždaryti',
    translating: 'Verčiama...',
    summarizing: 'Apibendrinama...',
    looking_up: 'Ieškoma...',
    cancel_with_esc: '(ESC atšaukimui)',
    image_text_recognition: 'Vaizdo teksto atpažinimas',
    menu_addition_error: 'Klaida pridedant meniu:',
    summary_result: 'Apibendrinimo rezultatas',
    copy_term_definition: 'Kopijuoti termino apibrėžimą',
    
    //options.js
    deepl_free_api_key_error: 'API raktas nėra teisingas. Prašome patikrinti API raktą.',
    deepl_free_api_key_warning: 'Įspėjimas: Atrodo, kad tai nėra DeepL API raktas. Įveskite teisingą nemokamą DeepL API raktą.',
    deepl_pro_api_key_warning: 'Įspėjimas: Atrodo, kad tai nėra DeepL API raktas. Įveskite teisingą mokamą DeepL API raktą.',
    settings_save_error: 'Klaida išsaugant nustatymus. Bandykite dar kartą.',
    saved_all_settings: 'Visi išsaugoti nustatymai:',
    
    // 옵션 페이지 관련
    options_title: 'Vertimo plėtinio nustatymai',
    service_selection: 'Pasirinkite vertimo paslaugą',
    api_key: 'API raktas',
    model_selection: 'Modelio pasirinkimas',
    api_url: 'API URL (pasirinktinai)',
    api_key_free: 'API raktas (nemokamas)',
    api_key_pro: 'API raktas (mokamas)',
    interface_language: 'Sąsajos kalba',
    interface_language_desc: 'Plėtinio meniu ir pranešimai bus rodomi pasirinkta kalba.',
    preferred_languages: 'Pageidaujamos kalbos (galima pasirinkti tik vieną kalbą)',
    save: 'Išsaugoti',
    settings_saved: 'Nustatymai išsaugoti.',
    
    // 디버그 모드
    debug_mode: 'Įjungti derinimo režimą (trikčių šalinimui)',
    debug_mode_desc: 'Įjungus derinimo režimą, klaidų pranešimai ir API komunikacijos informacija bus rodoma naršyklės konsolėje.',
    api_guide_title: 'API registracijos vadovas',
    claude_api_guide_title: 'Claude API registracija ir rakto generavimas',
    chatgpt_api_guide_title: 'ChatGPT API registracija ir rakto generavimas',
    grok_api_guide_title: 'Grok API registracija ir rakto generavimas',
    deepl_api_guide_title: 'DeepL API registracija ir rakto generavimas',
    deepl_api_help_title: 'DeepL API naudojimo pastabos',
    
    // Claude API 가이드
    claude_guide_step1: 'Apsilankykite Anthropic svetainėje (https://www.anthropic.com/api).',
    claude_guide_step2: 'Spustelėkite mygtuką "Sign up" viršutiniame dešiniajame kampe.',
    claude_guide_step3: 'Įveskite savo el. pašto adresą ir slaptažodį paskyros sukūrimui.',
    claude_guide_step4: 'Prisijungę pereikite į "API Keys" skirtuką.',
    claude_guide_step5: 'Spustelėkite mygtuką "Create API Key".',
    claude_guide_step6: 'Įveskite rakto pavadinimą ir sukurkite.',
    claude_guide_step7: 'Nukopijuokite sugeneruotą API raktą ir įklijuokite į aukščiau esantį Claude API rakto lauką.',
    claude_guide_note1: '※ Claude API reikalauja kreditinės kortelės registracijos, naudojimas yra mokamas.',
    claude_guide_note2: '※ API raktas prasideda formatu sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Apsilankykite OpenAI svetainėje (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Spustelėkite mygtuką "Sign up" paskyros sukūrimui.',
    chatgpt_guide_step3: 'Patvirtinkite savo el. pašto adresą.',
    chatgpt_guide_step4: 'Prisijungę spustelėkite Dashboard šalia profilio paveikslėlio ir pasirinkite "API keys" iš kairiojo meniu.',
    chatgpt_guide_step5: 'Spustelėkite mygtuką "Create new secret key".',
    chatgpt_guide_step6: 'Įveskite rakto pavadinimą ir sukurkite.',
    chatgpt_guide_step7: 'Nukopijuokite sugeneruotą API raktą ir įklijuokite į aukščiau esantį ChatGPT API rakto lauką.',
    chatgpt_guide_note1: '※ OpenAI API reikalauja kreditinės kortelės registracijos, naudojimas yra mokamas.',
    chatgpt_guide_note2: '※ API raktas prasideda formatu sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Apsilankykite X.AI svetainėje (https://x.ai).',
    grok_guide_step2: 'Prisijunkite prie savo paskyros.',
    grok_guide_step3: 'Spustelėkite API meniu viršuje.',
    grok_guide_step4: 'Spustelėkite mygtuką "Start building now".',
    grok_guide_step5: 'Spustelėkite API Keys meniu kairėje.',
    grok_guide_step6: 'Sugeneruokite savo API raktą.',
    grok_guide_step7: 'Nukopijuokite sugeneruotą API raktą ir įklijuokite į aukščiau esantį Grok API rakto lauką.',
    grok_guide_note1: '※ API raktas prasideda formatu xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Apsilankykite DeepL API svetainėje (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Spustelėkite mygtuką "Sign up for free".',
    deepl_guide_step3: 'Įveskite savo el. pašto adresą ir slaptažodį paskyros sukūrimui.',
    deepl_guide_step4: 'Patvirtinkite savo el. pašto adresą paskyros aktyvavimui.',
    deepl_guide_step5: 'Prisijungę pereikite į https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Eikite į API keys meniu (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Nemokamos versijos API raktą įklijuokite į aukščiau esantį DeepL API Key (nemokamas) lauką.',
    deepl_guide_step8: 'Mokamos versijos API raktą įklijuokite į aukščiau esantį DeepL API Key (mokamas) lauką.',
    deepl_guide_note1: '※ DeepL API nemokama versija leidžia versti iki 500.000 simbolių per mėnesį.',
    deepl_guide_note2: '※ Perėjus į mokamą versiją galėsite versti daugiau teksto.',
    deepl_guide_note3: '※ Pastaba: Perėjus į mokamą versiją, negalėjau naudoti nemokamo API. Prašome į tai atsižvelgti.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Nemokamam API raktui turite naudoti https://api-free.deepl.com galutinį tašką.',
    deepl_api_help_pro: 'Mokamam API raktui turite naudoti https://api.deepl.com galutinį tašką.',
    deepl_api_help_error: 'Jei naudojant nemokamą API raktą gaunate klaidą "Wrong endpoint. Use https://api.deepl.com":',
    deepl_api_help_check1: '1. Patikrinkite, ar pasirinkote DeepL API (nemokamą) parinktį.',
    deepl_api_help_check2: '2. Patikrinkite, ar tikrai naudojate nemokamą API raktą.',
    
    // 영역 및 결과 관련
    original_text: 'Originalus tekstas',
    translation: 'Vertimas',
    summary: 'Santrauka',
    definition: 'Apibrėžimas',
    copy_original: 'Kopijuoti originalą',
    copy_translation: 'Kopijuoti vertimą',
    copy_summary: 'Kopijuoti santrauką',
    copy_both: 'Kopijuoti abu',
    summarize_translation_result: 'Apibendrinti vertimo rezultatą',
    debug_info: 'Derinimo informacija',
    page_url: 'Puslapio URL',
    page_title: 'Puslapio pavadinimas',
    target_language: 'Tikslinė kalba',
    request_prompt: 'Užklausos tekstas',
    api_response: 'API atsakymas',
    clipboard_copy_failed: 'Nepavyko nukopijuoti į iškarpinę',
    
    // 알림 및 오류 메시지
    canceled: 'Atšaukta',
    translation_canceled: 'Vertimas atšauktas.',
    summary_canceled: 'Apibendrinimas atšauktas.',
    lookup_canceled: 'Termino paieška atšaukta.',
    operation_canceled: 'Operacija atšaukta.',
    api_key_error: 'API rakto klaida',
    api_key_missing: 'Nenustatytas API raktas. Prašome nustatyti API raktą plėtinio nustatymuose.',
    goto_settings: 'Eiti į nustatymus',
    error: 'Klaida',
    translation_failed: 'Vertimas nepavyko:',
    summary_failed: 'Apibendrinimas nepavyko:',
    lookup_failed: 'Termino paieška nepavyko:',
    no_response: 'Nėra atsakymo',
    
    // 로그 메시지
    menu_added: 'Meniu pridėtas.',
    menu_add_error: 'Klaida pridedant meniu:',
    menu_removed: 'Vertimo meniu pašalintas:',
    operation_applied: 'Sritis jau {operation}. Rodomas numatytasis kontekstinis meniu.',
    already_has_operation: 'Sritis jau turi {operation}. Operacija praleista.',
    rightclick_text: 'Dešiniuoju pelės mygtuku pažymėtas tekstas:',
    ctrl_rightclick: 'Aptiktas Ctrl + dešinysis pelės mygtukas: vykdomas apibendrinimas',
    normal_rightclick: 'Aptiktas įprastas dešinysis pelės mygtukas: vykdomas vertimas',
    doubleclick_text: 'Dvigubu paspaudimu pažymėtas tekstas:',
    hovered_element: 'Užvestas elementas:',
    summary_response: 'Apibendrinimo atsakymas:',
    range_undefined: 'Diapazonas neapibrėžtas.',
    inline_translation_insertion_error: 'Įterptinio vertimo įterpimo klaida:',
    inline_summary_insertion_error: 'Įterptinės santraukos įterpimo klaida:',
    fallback_insertion_error: 'Atsarginės kopijos įterpimo klaida:',
    copy_failed: 'Kopijavimas nepavyko:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programavimas/Programinės įrangos kūrimas',
    domain_blog: 'Tinklaraščiai/Techniniai straipsniai',
    domain_qa: 'Programavimo K&A',
    domain_docs: 'Techninė dokumentacija/API dokumentacija',
    domain_academic: 'Akademinis/Tyrimai',
    domain_news: 'Naujienos/Aktualijos',
    domain_finance: 'Finansai/Investicijos',
    domain_medical: 'Medicinos/Sveikatos',
    domain_legal: 'Teisinis',
    domain_webpage: 'Tinklalapio pavadinimas:',
    
    // 초기화 메시지
    extension_init: 'Vertimo plėtinio inicijavimas...',
    listeners_registered: 'Įvykių klausytojai užregistruoti.',
    doubleclick_registered: 'Dvigubo paspaudimo įvykio klausytojas užregistruotas.',
    extension_ready: 'Vertimo plėtinys paruoštas.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Failų sąrašas bus rodomas čia.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Subtitrų vertimas realiuoju laiku įjungtas.'
    ,subtitle_translation_disabled: 'Subtitrų vertimas realiuoju laiku išjungtas.'
    ,subtitle_translation_button: 'Subtitrų vertimas realiuoju laiku'
    ,runtime_not_initialized: 'Chrome vykdymo aplinka neinicijuota.'
    ,message_send_error: 'Klaida siunčiant pranešimą:'
    ,translation_response_missing: 'Nėra vertimo atsakymo.'
    ,translation_error: 'Klaida verčiant subtitrus:'
};

export default lt; 