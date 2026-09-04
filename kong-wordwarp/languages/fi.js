// 핀란드어 (Finnish) 언어 파일

const fi = {
    // 메뉴 및 UI 관련
    translate: 'Käännä',
    summarize: 'Tiivistä',
    lookup: 'Etsi termi',
    cancel: 'Peruuta',
    copy: 'Kopioi',
    copied: 'Kopioitu',
    close: 'Sulje',
    translating: 'Käännetään...',
    summarizing: 'Tiivistetään...',
    looking_up: 'Etsitään...',
    cancel_with_esc: '(ESC peruuttaaksesi)',
    image_text_recognition: 'Kuvatekstin tunnistus',
    menu_addition_error: 'Virhe valikon lisäämisessä:',
    summary_result: 'Tiivistelmätulos',
    copy_term_definition: 'Kopioi termimääritelmä',
    
    //options.js
    deepl_free_api_key_error: 'API-avain ei ole kelvollinen. Tarkista API-avain.',
    deepl_free_api_key_warning: 'Varoitus: Tämä näyttää olevan ei ole DeepL API-avain. Syötä oikea DeepL vapaa API-avain.',
    deepl_pro_api_key_warning: 'Varoitus: Tämä näyttää olevan ei ole DeepL API-avain. Syötä oikea DeepL maksullinen API-avain.',
    settings_save_error: 'Virhe tallentamisessa. Yritä uudelleen.',
    saved_all_settings: 'Kaikki tallennetut asetukset:',
            
        
    // 옵션 페이지 관련
    options_title: 'Käännöslaajennuksen asetukset',
    service_selection: 'Valitse käännöspalvelu',
    api_key: 'API-avain',
    model_selection: 'Mallin valinta',
    api_url: 'API URL (valinnainen)',
    api_key_free: 'API-avain (ilmainen)',
    api_key_pro: 'API-avain (maksullinen)',
    interface_language: 'Käyttöliittymän kieli',
    interface_language_desc: 'Laajennuksen valikot ja viestit näytetään valitulla kielellä.',
    preferred_languages: 'Ensisijaiset kielet (vain yksi kieli valittavissa)',
    save: 'Tallenna',
    settings_saved: 'Asetukset tallennettu.',
    
    // 디버그 모드
    debug_mode: 'Ota virheenkorjaustila käyttöön (vianmääritystä varten)',
    debug_mode_desc: 'Virheenkorjaustilan ollessa käytössä virheilmoitukset ja API-viestintätiedot näytetään selaimen konsolissa.',
    api_guide_title: 'API-rekisteröintiopas',
    claude_api_guide_title: 'Claude API rekisteröinti ja avaimen luonti',
    chatgpt_api_guide_title: 'ChatGPT API rekisteröinti ja avaimen luonti',
    grok_api_guide_title: 'Grok API rekisteröinti ja avaimen luonti',
    deepl_api_guide_title: 'DeepL API rekisteröinti ja avaimen luonti',
    deepl_api_help_title: 'DeepL API käyttöhuomautukset',
    
    // Claude API 가이드
    claude_guide_step1: 'Siirry Anthropicin verkkosivulle (https://www.anthropic.com/api).',
    claude_guide_step2: 'Napsauta "Sign up" -painiketta oikeasta yläkulmasta.',
    claude_guide_step3: 'Syötä sähköpostiosoitteesi ja salasanasi tilin luomiseksi.',
    claude_guide_step4: 'Kirjautumisen jälkeen siirry "API Keys" -välilehdelle.',
    claude_guide_step5: 'Napsauta "Create API Key" -painiketta.',
    claude_guide_step6: 'Anna avaimelle nimi ja luo se.',
    claude_guide_step7: 'Kopioi luotu API-avain ja liitä se yllä olevaan Claude API -avainkenttään.',
    claude_guide_note1: '※ Claude API vaatii luottokortin rekisteröinnin, käyttö on maksullista.',
    claude_guide_note2: '※ API-avain alkaa muodolla sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Siirry OpenAI:n verkkosivulle (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Napsauta "Sign up" -painiketta tilin luomiseksi.',
    chatgpt_guide_step3: 'Vahvista sähköpostiosoitteesi.',
    chatgpt_guide_step4: 'Kirjautumisen jälkeen napsauta Dashboard profiilikuvasi vierestä ja valitse "API keys" vasemmasta valikosta.',
    chatgpt_guide_step5: 'Napsauta "Create new secret key" -painiketta.',
    chatgpt_guide_step6: 'Anna avaimelle nimi ja luo se.',
    chatgpt_guide_step7: 'Kopioi luotu API-avain ja liitä se yllä olevaan ChatGPT API -avainkenttään.',
    chatgpt_guide_note1: '※ OpenAI API vaatii luottokortin rekisteröinnin, käyttö on maksullista.',
    chatgpt_guide_note2: '※ API-avain alkaa muodolla sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Siirry X.AI:n verkkosivulle (https://x.ai).',
    grok_guide_step2: 'Kirjaudu tiliisi.',
    grok_guide_step3: 'Napsauta API-valikkoa ylhäällä.',
    grok_guide_step4: 'Napsauta "Start building now" -painiketta.',
    grok_guide_step5: 'Napsauta API Keys -valikkoa vasemmalla.',
    grok_guide_step6: 'Luo API-avaimesi.',
    grok_guide_step7: 'Kopioi luotu API-avain ja liitä se yllä olevaan Grok API -avainkenttään.',
    grok_guide_note1: '※ API-avain alkaa muodolla xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Siirry DeepL API:n verkkosivulle (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Napsauta "Sign up for free" -painiketta.',
    deepl_guide_step3: 'Syötä sähköpostiosoitteesi ja salasanasi tilin luomiseksi.',
    deepl_guide_step4: 'Vahvista sähköpostiosoitteesi tilin aktivoimiseksi.',
    deepl_guide_step5: 'Kirjautumisen jälkeen siirry osoitteeseen https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Mene API keys -valikkoon (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Liitä ilmaisen version API-avain yllä olevaan DeepL API Key (ilmainen) -kenttään.',
    deepl_guide_step8: 'Liitä maksullisen version API-avain yllä olevaan DeepL API Key (maksullinen) -kenttään.',
    deepl_guide_note1: '※ DeepL API:n ilmainen versio sallii kääntää 500.000 merkkiä kuukaudessa.',
    deepl_guide_note2: '※ Maksulliseen versioon siirtymällä voit kääntää enemmän tekstiä.',
    deepl_guide_note3: '※ Huomautus: Maksulliseen versioon siirtymisen jälkeen en voinut käyttää ilmaista API:a. Ota tämä huomioon.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Ilmaista API-avainta varten sinun tulee käyttää päätepistettä https://api-free.deepl.com.',
    deepl_api_help_pro: 'Maksullista API-avainta varten sinun tulee käyttää päätepistettä https://api.deepl.com.',
    deepl_api_help_error: 'Jos saat ilmaista API-avainta käyttäessäsi virheen "Wrong endpoint. Use https://api.deepl.com":',
    deepl_api_help_check1: '1. Tarkista, että olet valinnut DeepL API (ilmainen) -vaihtoehdon.',
    deepl_api_help_check2: '2. Tarkista, että käytät todella ilmaista API-avainta.',
    
    // 영역 및 결과 관련
    original_text: 'Alkuperäinen teksti',
    translation: 'Käännös',
    summary: 'Tiivistelmä',
    definition: 'Määritelmä',
    copy_original: 'Kopioi alkuperäinen',
    copy_translation: 'Kopioi käännös',
    copy_summary: 'Kopioi tiivistelmä',
    copy_both: 'Kopioi molemmat',
    summarize_translation_result: 'Tiivistä käännöstulos',
    debug_info: 'Virheenkorjaustiedot',
    page_url: 'Sivun URL',
    page_title: 'Sivun otsikko',
    target_language: 'Kohdekieli',
    request_prompt: 'Pyyntökehote',
    api_response: 'API-vastaus',
    clipboard_copy_failed: 'Leikepöydälle kopiointi epäonnistui',
    
    // 알림 및 오류 메시지
    canceled: 'Peruutettu',
    translation_canceled: 'Käännös peruutettu.',
    summary_canceled: 'Tiivistelmä peruutettu.',
    lookup_canceled: 'Termin haku peruutettu.',
    operation_canceled: 'Toiminto peruutettu.',
    api_key_error: 'API-avainvirhe',
    api_key_missing: 'API-avainta ei ole asetettu. Aseta API-avain laajennuksen asetuksissa.',
    goto_settings: 'Siirry asetuksiin',
    error: 'Virhe',
    translation_failed: 'Käännös epäonnistui:',
    summary_failed: 'Tiivistelmä epäonnistui:',
    lookup_failed: 'Termin haku epäonnistui:',
    no_response: 'Ei vastausta',
    
    // 로그 메시지
    menu_added: 'Valikko lisätty.',
    menu_add_error: 'Virhe valikon lisäämisessä:',
    menu_removed: 'Käännösvalikko poistettu:',
    operation_applied: 'Alue on jo {operation}. Näytetään oletuskontekstivalikko.',
    already_has_operation: 'Alueella on jo {operation}. Toiminto ohitetaan.',
    rightclick_text: 'Hiiren oikealla painikkeella valittu teksti:',
    ctrl_rightclick: 'Ctrl + hiiren oikea painike havaittu: suoritetaan tiivistys',
    normal_rightclick: 'Normaali hiiren oikea painike havaittu: suoritetaan käännös',
    doubleclick_text: 'Kaksoisnapsautuksella valittu teksti:',
    hovered_element: 'Korostettu elementti:',
    summary_response: 'Tiivistelmävastaus:',
    range_undefined: 'Aluetta ei ole määritelty.',
    inline_translation_insertion_error: 'Sisäisen käännöksen lisäysvirhe:',
    inline_summary_insertion_error: 'Sisäisen tiivistelmän lisäysvirhe:',
    fallback_insertion_error: 'Varasijoitusvirhe:',
    copy_failed: 'Kopiointi epäonnistui:',
    
    // 도메인 컨텍스트
    domain_programming: 'Ohjelmointi/Ohjelmistokehitys',
    domain_blog: 'Blogi/Tekniset artikkelit',
    domain_qa: 'Ohjelmointi K&V',
    domain_docs: 'Tekninen dokumentaatio/API-dokumentaatio',
    domain_academic: 'Akateeminen/Tutkimus',
    domain_news: 'Uutiset/Ajankohtaiset',
    domain_finance: 'Rahoitus/Sijoittaminen',
    domain_medical: 'Lääketieteellinen/Terveys',
    domain_legal: 'Oikeudellinen',
    domain_webpage: 'Verkkosivun otsikko:',
    
    // 초기화 메시지
    extension_init: 'Käännöslaajennuksen alustus...',
    listeners_registered: 'Tapahtumakuuntelijat rekisteröity.',
    doubleclick_registered: 'Kaksoisnapsautuksen tapahtumakuuntelija rekisteröity.',
    extension_ready: 'Käännöslaajennus valmis.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Tiedostojen lista näytetään tässä.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Reaaliaikainen tekstityksen käännös on otettu käyttöön.'
    ,subtitle_translation_disabled: 'Reaaliaikainen tekstityksen käännös on poistettu käytöstä.'
    ,subtitle_translation_button: 'Reaaliaikainen tekstityksen käännös'
    ,runtime_not_initialized: 'Chrome-ajoympäristöä ei ole alustettu.'
    ,message_send_error: 'Virhe viestin lähetyksessä:'
    ,translation_response_missing: 'Ei käännösvastausta.'
    ,translation_error: 'Virhe tekstityksen käännöksessä:'
};

export default fi; 