// 아이슬란드어 (Icelandic) 언어 파일

const is = {
    // 메뉴 및 UI 관련
    translate: 'Þýða',
    summarize: 'Draga saman',
    lookup: 'Fletta upp',
    cancel: 'Hætta við',
    copy: 'Afrita',
    copied: 'Afritað',
    close: 'Loka',
    translating: 'Þýði...',
    summarizing: 'Dreg saman...',
    looking_up: 'Fletti upp...',
    cancel_with_esc: '(ESC til að hætta við)',
    image_text_recognition: 'Textalestur úr mynd',
    menu_addition_error: 'Villa við að bæta við valmynd:',
    summary_result: 'Dreg saman niðurstöðu',
    copy_term_definition: 'Afrita skilgreiningu ték',

    //options.js
    deepl_free_api_key_error: 'API-nøkkulinn er ugyldur. Vennurðu API-nøkkulinn.',
    deepl_free_api_key_warning: 'Varning: Detta ser ut att inte vara ett DeepL API-nyckel. Vänligen ange det korrekta DeepL gratis API-nyckeln.',
    deepl_pro_api_key_warning: 'Varning: Detta ser ut att inte vara ett DeepL API-nyckel. Vänligen ange det korrekta DeepL betalning API-nyckeln.',
    settings_save_error: 'Fel vid sparande av inställningar. Vänligen försök igen.',
    saved_all_settings: 'Alla sparade inställningar:',
    
    // 옵션 페이지 관련
    options_title: 'Stillingar þýðingarviðbótar',
    service_selection: 'Val á þýðingarþjónustu',
    api_key: 'API lykill',
    model_selection: 'Val á líkani',
    api_url: 'API vefslóð (valfrjálst)',
    api_key_free: 'API lykill (ókeypis)',
    api_key_pro: 'API lykill (greitt)',
    interface_language: 'Viðmótstungumál',
    interface_language_desc: 'Valmyndir og skilaboð viðbótarinnar verða birt á völdu tungumáli.',
    preferred_languages: 'Valin tungumál (aðeins er hægt að velja eitt tungumál)',
    save: 'Vista',
    settings_saved: 'Stillingar vistaðar.',
    
    // 디버그 모드
    debug_mode: 'Virkja villuleitarham (fyrir villuleit)',
    debug_mode_desc: 'Þegar villuleitarhamur er virkur verða villuskilaboð og API samskiptaupplýsingar birtar í vafrakonsólunni.',
    api_guide_title: 'API skráningarleiðbeiningar',
    claude_api_guide_title: 'Claude API skráning og lyklagerð',
    chatgpt_api_guide_title: 'ChatGPT API skráning og lyklagerð',
    grok_api_guide_title: 'Grok API skráning og lyklagerð',
    deepl_api_guide_title: 'DeepL API skráning og lyklagerð',
    deepl_api_help_title: 'Athugasemdir um notkun DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Heimsæktu Anthropic vefsíðuna (https://www.anthropic.com/api).',
    claude_guide_step2: 'Smelltu á "Sign up" hnappinn efst í hægra horni.',
    claude_guide_step3: 'Sláðu inn netfangið þitt og lykilorð til að búa til reikning.',
    claude_guide_step4: 'Eftir innskráningu, farðu í "API Keys" flipann.',
    claude_guide_step5: 'Smelltu á "Create API Key" hnappinn.',
    claude_guide_step6: 'Gefðu lyklinum nafn og búðu hann til.',
    claude_guide_step7: 'Afritaðu API lykilinn sem var búinn til og límdu hann í Claude API lykil reitinn hér að ofan.',
    claude_guide_note1: '※ Claude API krefst kreditkortaskráningar, notkun er gjaldskyld.',
    claude_guide_note2: '※ API lykill byrjar á sniðinu sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Heimsæktu OpenAI vefsíðuna (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Smelltu á "Sign up" hnappinn til að búa til reikning.',
    chatgpt_guide_step3: 'Staðfestu netfangið þitt.',
    chatgpt_guide_step4: 'Eftir innskráningu, smelltu á Dashboard við hliðina á prófílmyndinni þinni og veldu "API keys" úr valmyndinni vinstra megin.',
    chatgpt_guide_step5: 'Smelltu á "Create new secret key" hnappinn.',
    chatgpt_guide_step6: 'Gefðu lyklinum nafn og búðu hann til.',
    chatgpt_guide_step7: 'Afritaðu API lykilinn sem var búinn til og límdu hann í ChatGPT API lykil reitinn hér að ofan.',
    chatgpt_guide_note1: '※ OpenAI API krefst kreditkortaskráningar, notkun er gjaldskyld.',
    chatgpt_guide_note2: '※ API lykill byrjar á sniðinu sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Heimsæktu X.AI vefsíðuna (https://x.ai).',
    grok_guide_step2: 'Skráðu þig inn á reikninginn þinn.',
    grok_guide_step3: 'Smelltu á API valmyndina efst.',
    grok_guide_step4: 'Smelltu á "Start building now" hnappinn.',
    grok_guide_step5: 'Smelltu á API Keys valmyndina vinstra megin.',
    grok_guide_step6: 'Búðu til API lykilinn þinn.',
    grok_guide_step7: 'Afritaðu API lykilinn sem var búinn til og límdu hann í Grok API lykil reitinn hér að ofan.',
    grok_guide_note1: '※ API lykill byrjar á sniðinu xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Heimsæktu DeepL API vefsíðuna (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Smelltu á "Sign up for free" hnappinn.',
    deepl_guide_step3: 'Sláðu inn netfangið þitt og lykilorð til að búa til reikning.',
    deepl_guide_step4: 'Staðfestu netfangið þitt til að virkja reikninginn.',
    deepl_guide_step5: 'Eftir innskráningu, farðu á https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Farðu í API keys valmyndina (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Límdu ókeypis útgáfu API lykilinn í DeepL API Key (ókeypis) reitinn hér að ofan.',
    deepl_guide_step8: 'Límdu greidda útgáfu API lykilinn í DeepL API Key (greitt) reitinn hér að ofan.',
    deepl_guide_note1: '※ Ókeypis útgáfa DeepL API leyfir þýðingu á allt að 500.000 stöfum á mánuði.',
    deepl_guide_note2: '※ Með því að uppfæra í greidda útgáfu getur þú þýtt meira af texta.',
    deepl_guide_note3: '※ Athugið: Eftir uppfærslu í greidda útgáfu gat ég ekki notað ókeypis API. Vinsamlegast hafðu það í huga.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Fyrir ókeypis API lykil þarftu að nota endapunktinn https://api-free.deepl.com.',
    deepl_api_help_pro: 'Fyrir greiddan API lykil þarftu að nota endapunktinn https://api.deepl.com.',
    deepl_api_help_error: 'Ef þú færð villuna "Wrong endpoint. Use https://api.deepl.com" við notkun ókeypis API lykils:',
    deepl_api_help_check1: '1. Athugaðu hvort þú hafir valið DeepL API (ókeypis) valkostinn.',
    deepl_api_help_check2: '2. Athugaðu hvort þú sért í raun að nota ókeypis API lykil.',
    
    // 영역 및 결과 관련
    original_text: 'Upprunalegur texti',
    translation: 'Þýðing',
    summary: 'Samantekt',
    definition: 'Skilgreining',
    copy_original: 'Afrita upprunalega',
    copy_translation: 'Afrita þýðingu',
    copy_summary: 'Afrita samantekt',
    copy_both: 'Afrita hvort tveggja',
    summarize_translation_result: 'Draga saman þýðingarniðurstöðu',
    debug_info: 'Villuleitarupplýsingar',
    page_url: 'Síðuslóð',
    page_title: 'Síðutitill',
    target_language: 'Marktungumál',
    request_prompt: 'Beiðni',
    api_response: 'API svar',
    clipboard_copy_failed: 'Afritun á klemmuspjald mistókst',
    
    // 알림 및 오류 메시지
    canceled: 'Hætt við',
    translation_canceled: 'Hætt við þýðingu.',
    summary_canceled: 'Hætt við samantekt.',
    lookup_canceled: 'Hætt við uppflettingu.',
    operation_canceled: 'Hætt við aðgerð.',
    api_key_error: 'API lykill villa',
    api_key_missing: 'API lykill er ekki stilltur. Vinsamlegast stilltu API lykil í stillingum viðbótarinnar.',
    goto_settings: 'Fara í stillingar',
    error: 'Villa',
    translation_failed: 'Þýðing mistókst:',
    summary_failed: 'Samantekt mistókst:',
    lookup_failed: 'Uppfletting mistókst:',
    no_response: 'Ekkert svar',
    
    // 로그 메시지
    menu_added: 'Valmynd bætt við.',
    menu_add_error: 'Villa við að bæta við valmynd:',
    menu_removed: 'Þýðingarvalmynd fjarlægð:',
    operation_applied: 'Svæðið er þegar {operation}. Sýni sjálfgefna samhengisvalmynd.',
    already_has_operation: 'Svæðið hefur þegar {operation}. Sleppi aðgerð.',
    rightclick_text: 'Texti valinn með hægri smelli:',
    ctrl_rightclick: 'Ctrl + hægri smellur greindur: framkvæmi samantekt',
    normal_rightclick: 'Venjulegur hægri smellur greindur: framkvæmi þýðingu',
    doubleclick_text: 'Texti valinn með tvísmelli:',
    hovered_element: 'Sveimað yfir einingu:',
    summary_response: 'Samantektarsvar:',
    range_undefined: 'Svið er óskilgreint.',
    inline_translation_insertion_error: 'Villa við að setja inn innfellda þýðingu:',
    inline_summary_insertion_error: 'Villa við að setja inn innfellda samantekt:',
    fallback_insertion_error: 'Villa við að setja inn varaútgáfu:',
    copy_failed: 'Afritun mistókst:',
    
    // 도메인 컨텍스트
    domain_programming: 'Forritun/Hugbúnaðarþróun',
    domain_blog: 'Blogg/Tæknigreinar',
    domain_qa: 'Forritun Sp&Sv',
    domain_docs: 'Tækniskjöl/API skjöl',
    domain_academic: 'Fræðilegt/Rannsóknir',
    domain_news: 'Fréttir/Málefni líðandi stundar',
    domain_finance: 'Fjármál/Fjárfestingar',
    domain_medical: 'Læknisfræði/Heilbrigði',
    domain_legal: 'Lögfræði',
    domain_webpage: 'Vefsíðutitill:',
    
    // 초기화 메시지
    extension_init: 'Frumstilli þýðingarviðbót...',
    listeners_registered: 'Atburðahlustendur skráðir.',
    doubleclick_registered: 'Tvísmellshlustandi skráður.',
    extension_ready: 'Þýðingarviðbót er tilbúin.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Listi yfir skrár verður sýnd hér.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Rauntímaþýðing á skjátextum hefur verið virkjuð.'
    ,subtitle_translation_disabled: 'Rauntímaþýðing á skjátextum hefur verið gerð óvirk.'
    ,subtitle_translation_button: 'Rauntímaþýðing á skjátextum'
    ,runtime_not_initialized: 'Chrome keyrsluumhverfi hefur ekki verið frumstillt.'
    ,message_send_error: 'Villa við að senda skilaboð:'
    ,translation_response_missing: 'Ekkert þýðingarsvar.'
    ,translation_error: 'Villa við þýðingu á skjátextum:'
};

export default is; 