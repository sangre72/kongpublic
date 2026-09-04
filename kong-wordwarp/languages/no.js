// 노르웨이어 (Norwegian) 언어 파일

const no = {
    // 메뉴 및 UI 관련
    translate: 'Oversett',
    summarize: 'Oppsummer',
    lookup: 'Slå opp',
    cancel: 'Avbryt',
    copy: 'Kopier',
    copied: 'Kopiert',
    close: 'Lukk',
    translating: 'Oversetter...',
    summarizing: 'Oppsummerer...',
    looking_up: 'Slår opp...',
    cancel_with_esc: '(ESC for å avbryte)',
    image_text_recognition: 'Tekstgjenkjenning fra bilde',
    menu_addition_error: 'Feil ved tilføyelse av meny:',
    summary_result: 'Oppsummeringsresultat',
    copy_term_definition: 'Kopier termindefinisjon',
    
    //options.js
    deepl_free_api_key_error: 'API-nøkkel er ugyldig. Vennligst sjekk API-nøkkelen.',
    deepl_free_api_key_warning: 'Advarsel: Dette ser ikke ut til å være en DeepL API-nøkkel. Vennligst skriv inn riktig gratis DeepL API-nøkkel.',
    deepl_pro_api_key_warning: 'Advarsel: Dette ser ikke ut til å være en DeepL API-nøkkel. Vennligst skriv inn riktig betalt DeepL API-nøkkel.',
    settings_save_error: 'Feil ved lagring av innstillinger. Vennligst prøv igjen.',
    saved_all_settings: 'Alle lagrede innstillinger:',
    // 옵션 페이지 관련
    options_title: 'Innstillinger for oversettelsesutvidelse',
    service_selection: 'Valg av oversettelsestjeneste',
    api_key: 'API-nøkkel',
    model_selection: 'Modellvalg',
    api_url: 'API-URL (valgfritt)',
    api_key_free: 'API-nøkkel (gratis)',
    api_key_pro: 'API-nøkkel (betalt)',
    interface_language: 'Grensesnittspråk',
    interface_language_desc: 'Utvidelsens menyer og meldinger vil bli vist på det valgte språket.',
    preferred_languages: 'Foretrukne språk (kun ett språk kan velges)',
    save: 'Lagre',
    settings_saved: 'Innstillinger lagret.',
    
    // 디버그 모드
    debug_mode: 'Aktiver feilsøkingsmodus (for problemløsning)',
    debug_mode_desc: 'Når feilsøkingsmodus er aktivert, vil feilmeldinger og API-kommunikasjonsinformasjon vises i nettleserens konsoll.',
    api_guide_title: 'API-registreringsveiledning',
    claude_api_guide_title: 'Claude API-registrering og nøkkelgenerering',
    chatgpt_api_guide_title: 'ChatGPT API-registrering og nøkkelgenerering',
    grok_api_guide_title: 'Grok API-registrering og nøkkelgenerering',
    deepl_api_guide_title: 'DeepL API-registrering og nøkkelgenerering',
    deepl_api_help_title: 'Merknader om bruk av DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Besøk Anthropic-nettstedet (https://www.anthropic.com/api).',
    claude_guide_step2: 'Klikk på "Sign up"-knappen i øvre høyre hjørne.',
    claude_guide_step3: 'Skriv inn e-postadressen og passordet ditt for å opprette en konto.',
    claude_guide_step4: 'Etter innlogging, gå til "API Keys"-fanen.',
    claude_guide_step5: 'Klikk på "Create API Key"-knappen.',
    claude_guide_step6: 'Gi nøkkelen et navn og opprett den.',
    claude_guide_step7: 'Kopier den genererte API-nøkkelen og lim den inn i Claude API-nøkkelfeltet ovenfor.',
    claude_guide_note1: '※ Claude API krever kredittkortregistrering, bruk er mot betaling.',
    claude_guide_note2: '※ API-nøkkel starter med formatet sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Besøk OpenAI-nettstedet (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Klikk på "Sign up"-knappen for å opprette en konto.',
    chatgpt_guide_step3: 'Bekreft e-postadressen din.',
    chatgpt_guide_step4: 'Etter innlogging, klikk på Dashboard ved siden av profilbildet ditt og velg "API keys" fra menyen til venstre.',
    chatgpt_guide_step5: 'Klikk på "Create new secret key"-knappen.',
    chatgpt_guide_step6: 'Gi nøkkelen et navn og opprett den.',
    chatgpt_guide_step7: 'Kopier den genererte API-nøkkelen og lim den inn i ChatGPT API-nøkkelfeltet ovenfor.',
    chatgpt_guide_note1: '※ OpenAI API krever kredittkortregistrering, bruk er mot betaling.',
    chatgpt_guide_note2: '※ API-nøkkel starter med formatet sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Besøk X.AI-nettstedet (https://x.ai).',
    grok_guide_step2: 'Logg inn på kontoen din.',
    grok_guide_step3: 'Klikk på API-menyen øverst.',
    grok_guide_step4: 'Klikk på "Start building now"-knappen.',
    grok_guide_step5: 'Klikk på API Keys-menyen til venstre.',
    grok_guide_step6: 'Generer API-nøkkelen din.',
    grok_guide_step7: 'Kopier den genererte API-nøkkelen og lim den inn i Grok API-nøkkelfeltet ovenfor.',
    grok_guide_note1: '※ API-nøkkel starter med formatet xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Besøk DeepL API-nettstedet (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Klikk på "Sign up for free"-knappen.',
    deepl_guide_step3: 'Skriv inn e-postadressen og passordet ditt for å opprette en konto.',
    deepl_guide_step4: 'Bekreft e-postadressen din for å aktivere kontoen.',
    deepl_guide_step5: 'Etter innlogging, gå til https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Gå til API keys-menyen (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Lim inn API-nøkkelen for gratisversjonen i DeepL API Key (gratis)-feltet ovenfor.',
    deepl_guide_step8: 'Lim inn API-nøkkelen for betalversjonen i DeepL API Key (betalt)-feltet ovenfor.',
    deepl_guide_note1: '※ Gratisversjonen av DeepL API tillater oversettelse av opptil 500 000 tegn per måned.',
    deepl_guide_note2: '※ Ved å oppgradere til betalversjonen kan du oversette mer tekst.',
    deepl_guide_note3: '※ Merk: Etter oppgradering til betalversjonen kunne jeg ikke bruke gratis-API-en. Vennligst ta hensyn til dette.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'For gratis API-nøkkel må du bruke endepunktet https://api-free.deepl.com.',
    deepl_api_help_pro: 'For betalt API-nøkkel må du bruke endepunktet https://api.deepl.com.',
    deepl_api_help_error: 'Hvis du får feilen "Wrong endpoint. Use https://api.deepl.com" når du bruker gratis API-nøkkel:',
    deepl_api_help_check1: '1. Sjekk at du har valgt DeepL API (gratis)-alternativet.',
    deepl_api_help_check2: '2. Sjekk at du faktisk bruker en gratis API-nøkkel.',
    
    // 영역 및 결과 관련
    original_text: 'Originaltekst',
    translation: 'Oversettelse',
    summary: 'Sammendrag',
    definition: 'Definisjon',
    copy_original: 'Kopier original',
    copy_translation: 'Kopier oversettelse',
    copy_summary: 'Kopier sammendrag',
    copy_both: 'Kopier begge',
    summarize_translation_result: 'Oppsummer oversettelsesresultat',
    debug_info: 'Feilsøkingsinformasjon',
    page_url: 'Sideadresse',
    page_title: 'Sidetittel',
    target_language: 'Målspråk',
    request_prompt: 'Forespørselsprompt',
    api_response: 'API-svar',
    clipboard_copy_failed: 'Kopiering til utklippstavle mislyktes',
    
    // 알림 및 오류 메시지
    canceled: 'Avbrutt',
    translation_canceled: 'Oversettelse avbrutt.',
    summary_canceled: 'Oppsummering avbrutt.',
    lookup_canceled: 'Oppslag avbrutt.',
    operation_canceled: 'Operasjon avbrutt.',
    api_key_error: 'API-nøkkelfeil',
    api_key_missing: 'API-nøkkel er ikke satt. Vennligst sett API-nøkkel i utvidelsesinnstillingene.',
    goto_settings: 'Gå til innstillinger',
    error: 'Feil',
    translation_failed: 'Oversettelse mislyktes:',
    summary_failed: 'Oppsummering mislyktes:',
    lookup_failed: 'Oppslag mislyktes:',
    no_response: 'Ingen respons',
    
    // 로그 메시지
    menu_added: 'Meny lagt til.',
    menu_add_error: 'Feil ved tillegging av meny:',
    menu_removed: 'Oversettelsesmeny fjernet:',
    operation_applied: 'Området er allerede {operation}. Viser standard kontekstmeny.',
    already_has_operation: 'Området har allerede {operation}. Hopper over operasjon.',
    rightclick_text: 'Tekst valgt med høyreklikk:',
    ctrl_rightclick: 'Ctrl + høyreklikk oppdaget: utfører oppsummering',
    normal_rightclick: 'Vanlig høyreklikk oppdaget: utfører oversettelse',
    doubleclick_text: 'Tekst valgt med dobbeltklikk:',
    hovered_element: 'Element under musepeker:',
    summary_response: 'Oppsummeringssvar:',
    range_undefined: 'Område er udefinert.',
    inline_translation_insertion_error: 'Feil ved innsetting av innebygd oversettelse:',
    inline_summary_insertion_error: 'Feil ved innsetting av innebygd oppsummering:',
    fallback_insertion_error: 'Feil ved innsetting av reserveløsning:',
    copy_failed: 'Kopiering mislyktes:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmering/Programvareutvikling',
    domain_blog: 'Blogg/Tekniske artikler',
    domain_qa: 'Programmering Sp&Sv',
    domain_docs: 'Teknisk dokumentasjon/API-dokumentasjon',
    domain_academic: 'Akademisk/Forskning',
    domain_news: 'Nyheter/Aktualiteter',
    domain_finance: 'Finans/Investering',
    domain_medical: 'Medisinsk/Helse',
    domain_legal: 'Juridisk',
    domain_webpage: 'Nettsidetittel:',
    
    // 초기화 메시지
    extension_init: 'Initialiserer oversettelsesutvidelse...',
    listeners_registered: 'Hendelseslyttere registrert.',
    doubleclick_registered: 'Dobbeltklikklytter registrert.',
    extension_ready: 'Oversettelsesutvidelse er klar.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Liste over filer vil blive vist her.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Sanntidsoversettelse av undertekster er aktivert.'
    ,subtitle_translation_disabled: 'Sanntidsoversettelse av undertekster er deaktivert.'
    ,subtitle_translation_button: 'Sanntidsoversettelse av undertekster'
    ,runtime_not_initialized: 'Chrome-runtime er ikke initialisert.'
    ,message_send_error: 'Feil ved sending av melding:'
    ,translation_response_missing: 'Ingen oversettelsessvar.'
    ,translation_error: 'Feil ved oversettelse av undertekster:'
};

export default no; 