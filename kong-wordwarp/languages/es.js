// 스페인어 (Spanish) 언어 파일

const es = {
    // 메뉴 및 UI 관련
    translate: 'Traducir',
    summarize: 'Resumir',
    lookup: 'Buscar término',
    cancel: 'Cancelar',
    copy: 'Copiar',
    copied: 'Copiado',
    close: 'Cerrar',
    translating: 'Traduciendo...',
    summarizing: 'Resumiendo...',
    looking_up: 'Buscando...',
    cancel_with_esc: '(ESC para cancelar)',
    image_text_recognition: 'Reconocimiento de texto en imagen',
    menu_addition_error: 'Error al agregar el menú:',
    summary_result: 'Resultado de resumen',
    copy_term_definition: 'Copiar definición de término',
    
    //options.js
    deepl_free_api_key_error: 'La clave API no es válida. Por favor, verifique la clave API.',
    deepl_free_api_key_warning: 'Advertencia: Esto parece no ser una clave API de DeepL. Por favor, ingrese la clave API de DeepL gratuita correcta.',
    deepl_pro_api_key_warning: 'Advertencia: Esto parece no ser una clave API de DeepL. Por favor, ingrese la clave API de DeepL de pago correcta.',
    settings_save_error: 'Error al guardar las configuraciones. Por favor, inténtelo de nuevo.',
    saved_all_settings: 'Todas las configuraciones guardadas:',
    
    // 옵션 페이지 관련
    options_title: 'Configuración de la extensión de traducción',
    service_selection: 'Selección del servicio de traducción',
    api_key: 'Clave API',
    model_selection: 'Selección del modelo',
    api_url: 'URL de API (opcional)',
    api_key_free: 'Clave API (gratuita)',
    api_key_pro: 'Clave API (de pago)',
    interface_language: 'Idioma de la interfaz',
    interface_language_desc: 'Los menús y mensajes de la extensión se mostrarán en el idioma seleccionado.',
    preferred_languages: 'Idiomas preferidos (solo se puede seleccionar un idioma)',
    save: 'Guardar',
    settings_saved: 'Configuración guardada.',
    
    // 디버그 모드
    debug_mode: 'Activar modo de depuración (para solución de problemas)',
    debug_mode_desc: 'Cuando el modo de depuración está activado, los mensajes de error y la información de comunicación API se mostrarán en la consola del navegador.',
    api_guide_title: 'Guía de registro de API',
    claude_api_guide_title: 'Registro y generación de clave Claude API',
    chatgpt_api_guide_title: 'Registro y generación de clave ChatGPT API',
    grok_api_guide_title: 'Registro y generación de clave Grok API',
    deepl_api_guide_title: 'Registro y generación de clave DeepL API',
    deepl_api_help_title: 'Notas sobre el uso de DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Visite el sitio web de Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Haga clic en el botón "Sign up" en la esquina superior derecha.',
    claude_guide_step3: 'Ingrese su correo electrónico y contraseña para crear una cuenta.',
    claude_guide_step4: 'Después de iniciar sesión, vaya a la pestaña "API Keys".',
    claude_guide_step5: 'Haga clic en el botón "Create API Key".',
    claude_guide_step6: 'Asigne un nombre a la clave y créela.',
    claude_guide_step7: 'Copie la clave API generada y péguela en el campo de clave Claude API arriba.',
    claude_guide_note1: '※ Claude API requiere registro de tarjeta de crédito, el uso es de pago.',
    claude_guide_note2: '※ La clave API comienza con el formato sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Visite el sitio web de OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Haga clic en el botón "Sign up" para crear una cuenta.',
    chatgpt_guide_step3: 'Confirme su dirección de correo electrónico.',
    chatgpt_guide_step4: 'Después de iniciar sesión, haga clic en Dashboard junto a su foto de perfil y seleccione "API keys" del menú izquierdo.',
    chatgpt_guide_step5: 'Haga clic en el botón "Create new secret key".',
    chatgpt_guide_step6: 'Asigne un nombre a la clave y créela.',
    chatgpt_guide_step7: 'Copie la clave API generada y péguela en el campo de clave ChatGPT API arriba.',
    chatgpt_guide_note1: '※ OpenAI API requiere registro de tarjeta de crédito, el uso es de pago.',
    chatgpt_guide_note2: '※ La clave API comienza con el formato sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Visite el sitio web de X.AI (https://x.ai).',
    grok_guide_step2: 'Inicie sesión en su cuenta.',
    grok_guide_step3: 'Haga clic en el menú API en la parte superior.',
    grok_guide_step4: 'Haga clic en el botón "Start building now".',
    grok_guide_step5: 'Haga clic en el menú API Keys a la izquierda.',
    grok_guide_step6: 'Genere su clave API.',
    grok_guide_step7: 'Copie la clave API generada y péguela en el campo de clave Grok API arriba.',
    grok_guide_note1: '※ La clave API comienza con el formato xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Visite el sitio web de DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Haga clic en el botón "Sign up for free".',
    deepl_guide_step3: 'Ingrese su correo electrónico y contraseña para crear una cuenta.',
    deepl_guide_step4: 'Confirme su dirección de correo electrónico para activar la cuenta.',
    deepl_guide_step5: 'Después de iniciar sesión, vaya a https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Vaya al menú API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Pegue la clave API de la versión gratuita en el campo DeepL API Key (gratuita) arriba.',
    deepl_guide_step8: 'Pegue la clave API de la versión de pago en el campo DeepL API Key (de pago) arriba.',
    deepl_guide_note1: '※ La versión gratuita de DeepL API permite traducir hasta 500.000 caracteres por mes.',
    deepl_guide_note2: '※ Al actualizar a la versión de pago, puede traducir más texto.',
    deepl_guide_note3: '※ Nota: Después de actualizar a la versión de pago, no pude usar la API gratuita. Por favor, tenga esto en cuenta.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Para la clave API gratuita, debe usar el endpoint https://api-free.deepl.com.',
    deepl_api_help_pro: 'Para la clave API de pago, debe usar el endpoint https://api.deepl.com.',
    deepl_api_help_error: 'Si recibe el error "Wrong endpoint. Use https://api.deepl.com" al usar la clave API gratuita:',
    deepl_api_help_check1: '1. Verifique que ha seleccionado la opción DeepL API (gratuita).',
    deepl_api_help_check2: '2. Verifique que está usando realmente una clave API gratuita.',
    
    // 영역 및 결과 관련
    original_text: 'Texto original',
    translation: 'Traducción',
    summary: 'Resumen',
    definition: 'Definición',
    copy_original: 'Copiar original',
    copy_translation: 'Copiar traducción',
    copy_summary: 'Copiar resumen',
    copy_both: 'Copiar ambos',
    summarize_translation_result: 'Resumir resultado de traducción',
    debug_info: 'Información de depuración',
    page_url: 'URL de la página',
    page_title: 'Título de la página',
    target_language: 'Idioma objetivo',
    request_prompt: 'Solicitud de prompt',
    api_response: 'Respuesta API',
    clipboard_copy_failed: 'Error al copiar al portapapeles',
    
    // 알림 및 오류 메시지
    canceled: 'Cancelado',
    translation_canceled: 'Traducción cancelada.',
    summary_canceled: 'Resumen cancelado.',
    lookup_canceled: 'Búsqueda cancelada.',
    operation_canceled: 'Operación cancelada.',
    api_key_error: 'Error de clave API',
    api_key_missing: 'La clave API no está configurada. Por favor, configure la clave API en la configuración de la extensión.',
    goto_settings: 'Ir a configuración',
    error: 'Error',
    translation_failed: 'Error en la traducción:',
    summary_failed: 'Error en el resumen:',
    lookup_failed: 'Error en la búsqueda:',
    no_response: 'Sin respuesta',
    
    // 로그 메시지
    menu_added: 'Menú añadido.',
    menu_add_error: 'Error al añadir menú:',
    menu_removed: 'Menú de traducción eliminado:',
    operation_applied: 'El área ya está {operation}. Mostrando menú contextual predeterminado.',
    already_has_operation: 'El área ya tiene {operation}. Omitiendo operación.',
    rightclick_text: 'Texto seleccionado con clic derecho:',
    ctrl_rightclick: 'Ctrl + clic derecho detectado: ejecutando resumen',
    normal_rightclick: 'Clic derecho normal detectado: ejecutando traducción',
    doubleclick_text: 'Texto seleccionado con doble clic:',
    hovered_element: 'Elemento bajo el cursor:',
    summary_response: 'Respuesta del resumen:',
    range_undefined: 'Rango no definido.',
    inline_translation_insertion_error: 'Error al insertar traducción en línea:',
    inline_summary_insertion_error: 'Error al insertar resumen en línea:',
    fallback_insertion_error: 'Error al insertar respaldo:',
    copy_failed: 'Error al copiar:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programación/Desarrollo de software',
    domain_blog: 'Blog/Artículos técnicos',
    domain_qa: 'Programación P&R',
    domain_docs: 'Documentación técnica/Documentación API',
    domain_academic: 'Académico/Investigación',
    domain_news: 'Noticias/Actualidad',
    domain_finance: 'Finanzas/Inversiones',
    domain_medical: 'Médico/Salud',
    domain_legal: 'Legal',
    domain_webpage: 'Título de página web:',
    
    // 초기화 메시지
    extension_init: 'Inicializando extensión de traducción...',
    listeners_registered: 'Oyentes de eventos registrados.',
    doubleclick_registered: 'Oyente de doble clic registrado.',
    extension_ready: 'La extensión de traducción está lista.'

    //filePanel.js
    ,fileListWillBeShownHere: 'La lista de archivos se mostrará aquí.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'La traducción de subtítulos en tiempo real ha sido activada.'
    ,subtitle_translation_disabled: 'La traducción de subtítulos en tiempo real ha sido desactivada.'
    ,subtitle_translation_button: 'Traducción de subtítulos en tiempo real'
    ,runtime_not_initialized: 'El runtime de Chrome no se ha inicializado.'
    ,message_send_error: 'Error al enviar mensaje:'
    ,translation_response_missing: 'No hay respuesta de traducción.'
    ,translation_error: 'Error en la traducción de subtítulos:'
};

export default es; 