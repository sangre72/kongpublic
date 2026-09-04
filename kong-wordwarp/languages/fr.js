// 프랑스어 (French) 언어 파일

const fr = {
    // 메뉴 및 UI 관련
    translate: 'Traduire',
    summarize: 'Résumer',
    lookup: 'Rechercher',
    cancel: 'Annuler',
    copy: 'Copier',
    copied: 'Copié',
    close: 'Fermer',
    translating: 'Traduction en cours...',
    summarizing: 'Résumé en cours...',
    looking_up: 'Recherche en cours...',
    cancel_with_esc: '(ESC pour annuler)',
    image_text_recognition: 'Reconnaissance de texte sur image',
    menu_addition_error: 'Erreur lors de l\'ajout du menu :',
    summary_result: 'Résultat du résumé',
    copy_term_definition: 'Copier la définition du terme',
    
    //options.js
    deepl_free_api_key_error: 'La clé API n\'est pas valide. Veuillez vérifier la clé API.',
    deepl_free_api_key_warning: 'Attention: Cela semble ne pas être une clé API DeepL. Veuillez entrer la clé API DeepL gratuite correcte.',
    deepl_pro_api_key_warning: 'Attention: Cela semble ne pas être une clé API DeepL. Veuillez entrer la clé API DeepL payante correcte.',
    settings_save_error: 'Erreur lors de la sauvegarde des paramètres. Veuillez réessayer.',
    saved_all_settings: 'Tous les paramètres sauvegardés:',
            
    
    // 옵션 페이지 관련
    options_title: 'Paramètres de l\'extension de traduction',
    service_selection: 'Sélection du service de traduction',
    api_key: 'Clé API',
    model_selection: 'Sélection du modèle',
    api_url: 'URL API (optionnel)',
    api_key_free: 'Clé API (gratuite)',
    api_key_pro: 'Clé API (payante)',
    interface_language: 'Langue de l\'interface',
    interface_language_desc: 'Les menus et messages de l\'extension seront affichés dans la langue sélectionnée.',
    preferred_languages: 'Langues préférées (une seule langue peut être sélectionnée)',
    save: 'Enregistrer',
    settings_saved: 'Paramètres enregistrés.',
    
    // 디버그 모드
    debug_mode: 'Activer le mode débogage (pour le dépannage)',
    debug_mode_desc: 'Lorsque le mode débogage est activé, les messages d\'erreur et les informations de communication API seront affichés dans la console du navigateur.',
    api_guide_title: 'Guide d\'inscription API',
    claude_api_guide_title: 'Inscription et génération de clé Claude API',
    chatgpt_api_guide_title: 'Inscription et génération de clé ChatGPT API',
    grok_api_guide_title: 'Inscription et génération de clé Grok API',
    deepl_api_guide_title: 'Inscription et génération de clé DeepL API',
    deepl_api_help_title: 'Notes sur l\'utilisation de l\'API DeepL',
    
    // Claude API 가이드
    claude_guide_step1: 'Visitez le site web d\'Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Cliquez sur le bouton "Sign up" dans le coin supérieur droit.',
    claude_guide_step3: 'Entrez votre e-mail et mot de passe pour créer un compte.',
    claude_guide_step4: 'Après la connexion, allez dans l\'onglet "API Keys".',
    claude_guide_step5: 'Cliquez sur le bouton "Create API Key".',
    claude_guide_step6: 'Donnez un nom à la clé et créez-la.',
    claude_guide_step7: 'Copiez la clé API générée et collez-la dans le champ de clé Claude API ci-dessus.',
    claude_guide_note1: '※ L\'API Claude nécessite l\'enregistrement d\'une carte de crédit, l\'utilisation est payante.',
    claude_guide_note2: '※ La clé API commence par le format sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Visitez le site web d\'OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Cliquez sur le bouton "Sign up" pour créer un compte.',
    chatgpt_guide_step3: 'Confirmez votre adresse e-mail.',
    chatgpt_guide_step4: 'Après la connexion, cliquez sur Dashboard à côté de votre photo de profil et sélectionnez "API keys" dans le menu de gauche.',
    chatgpt_guide_step5: 'Cliquez sur le bouton "Create new secret key".',
    chatgpt_guide_step6: 'Donnez un nom à la clé et créez-la.',
    chatgpt_guide_step7: 'Copiez la clé API générée et collez-la dans le champ de clé ChatGPT API ci-dessus.',
    chatgpt_guide_note1: '※ L\'API OpenAI nécessite l\'enregistrement d\'une carte de crédit, l\'utilisation est payante.',
    chatgpt_guide_note2: '※ La clé API commence par le format sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Visitez le site web X.AI (https://x.ai).',
    grok_guide_step2: 'Connectez-vous à votre compte.',
    grok_guide_step3: 'Cliquez sur le menu API en haut.',
    grok_guide_step4: 'Cliquez sur le bouton "Start building now".',
    grok_guide_step5: 'Cliquez sur le menu API Keys à gauche.',
    grok_guide_step6: 'Générez votre clé API.',
    grok_guide_step7: 'Copiez la clé API générée et collez-la dans le champ de clé Grok API ci-dessus.',
    grok_guide_note1: '※ La clé API commence par le format xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Visitez le site web DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Cliquez sur le bouton "Sign up for free".',
    deepl_guide_step3: 'Entrez votre e-mail et mot de passe pour créer un compte.',
    deepl_guide_step4: 'Confirmez votre adresse e-mail pour activer le compte.',
    deepl_guide_step5: 'Après la connexion, allez sur https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Allez dans le menu API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Collez la clé API de la version gratuite dans le champ DeepL API Key (gratuite) ci-dessus.',
    deepl_guide_step8: 'Collez la clé API de la version payante dans le champ DeepL API Key (payante) ci-dessus.',
    deepl_guide_note1: '※ La version gratuite de l\'API DeepL permet de traduire jusqu\'à 500 000 caractères par mois.',
    deepl_guide_note2: '※ En passant à la version payante, vous pouvez traduire plus de texte.',
    deepl_guide_note3: '※ Note : Après le passage à la version payante, je n\'ai pas pu utiliser l\'API gratuite. Veuillez en tenir compte.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Pour la clé API gratuite, vous devez utiliser le point de terminaison https://api-free.deepl.com.',
    deepl_api_help_pro: 'Pour la clé API payante, vous devez utiliser le point de terminaison https://api.deepl.com.',
    deepl_api_help_error: 'Si vous recevez l\'erreur "Wrong endpoint. Use https://api.deepl.com" lors de l\'utilisation de la clé API gratuite :',
    deepl_api_help_check1: '1. Vérifiez que vous avez sélectionné l\'option DeepL API (gratuite).',
    deepl_api_help_check2: '2. Vérifiez que vous utilisez bien une clé API gratuite.',
    
    // 영역 및 결과 관련
    original_text: 'Texte original',
    translation: 'Traduction',
    summary: 'Résumé',
    definition: 'Définition',
    copy_original: 'Copier l\'original',
    copy_translation: 'Copier la traduction',
    copy_summary: 'Copier le résumé',
    copy_both: 'Copier les deux',
    summarize_translation_result: 'Résumer le résultat de la traduction',
    debug_info: 'Informations de débogage',
    page_url: 'URL de la page',
    page_title: 'Titre de la page',
    target_language: 'Langue cible',
    request_prompt: 'Invite de requête',
    api_response: 'Réponse API',
    clipboard_copy_failed: 'Échec de la copie dans le presse-papiers',
    
    // 알림 및 오류 메시지
    canceled: 'Annulé',
    translation_canceled: 'Traduction annulée.',
    summary_canceled: 'Résumé annulé.',
    lookup_canceled: 'Recherche annulée.',
    operation_canceled: 'Opération annulée.',
    api_key_error: 'Erreur de clé API',
    api_key_missing: 'La clé API n\'est pas définie. Veuillez définir la clé API dans les paramètres de l\'extension.',
    goto_settings: 'Aller aux paramètres',
    error: 'Erreur',
    translation_failed: 'Échec de la traduction :',
    summary_failed: 'Échec du résumé :',
    lookup_failed: 'Échec de la recherche :',
    no_response: 'Aucune réponse',
    
    // 로그 메시지
    menu_added: 'Menu ajouté.',
    menu_add_error: 'Erreur lors de l\'ajout du menu :',
    menu_removed: 'Menu de traduction supprimé :',
    operation_applied: 'La zone est déjà {operation}. Affichage du menu contextuel par défaut.',
    already_has_operation: 'La zone a déjà {operation}. Ignorer l\'opération.',
    rightclick_text: 'Texte sélectionné par clic droit :',
    ctrl_rightclick: 'Ctrl + clic droit détecté : exécution du résumé',
    normal_rightclick: 'Clic droit normal détecté : exécution de la traduction',
    doubleclick_text: 'Texte sélectionné par double-clic :',
    hovered_element: 'Élément survolé :',
    summary_response: 'Réponse du résumé :',
    range_undefined: 'Plage non définie.',
    inline_translation_insertion_error: 'Erreur lors de l\'insertion de la traduction en ligne :',
    inline_summary_insertion_error: 'Erreur lors de l\'insertion du résumé en ligne :',
    fallback_insertion_error: 'Erreur lors de l\'insertion de la solution de secours :',
    copy_failed: 'Échec de la copie :',
    
    // 도메인 컨텍스트
    domain_programming: 'Programmation/Développement logiciel',
    domain_blog: 'Blog/Articles techniques',
    domain_qa: 'Programmation Q&R',
    domain_docs: 'Documentation technique/Documentation API',
    domain_academic: 'Académique/Recherche',
    domain_news: 'Actualités/Événements actuels',
    domain_finance: 'Finance/Investissement',
    domain_medical: 'Médical/Santé',
    domain_legal: 'Juridique',
    domain_webpage: 'Titre de la page web :',
    
    // 초기화 메시지
    extension_init: 'Initialisation de l\'extension de traduction...',
    listeners_registered: 'Écouteurs d\'événements enregistrés.',
    doubleclick_registered: 'Écouteur de double-clic enregistré.',
    extension_ready: 'L\'extension de traduction est prête.'

    //filePanel.js
    ,fileListWillBeShownHere: 'La liste des fichiers sera affichée ici.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'La traduction des sous-titres en temps réel a été activée.'
    ,subtitle_translation_disabled: 'La traduction des sous-titres en temps réel a été désactivée.'
    ,subtitle_translation_button: 'Traduction des sous-titres en temps réel'
    ,runtime_not_initialized: 'Le runtime Chrome n\'a pas été initialisé.'
    ,message_send_error: 'Erreur lors de l\'envoi du message :'
    ,translation_response_missing: 'Pas de réponse de traduction.'
    ,translation_error: 'Erreur de traduction des sous-titres :'
};

export default fr; 