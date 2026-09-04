// 포르투갈어 (Portuguese) 언어 파일

const pt = {
    // 메뉴 및 UI 관련
    translate: 'Traduzir',
    summarize: 'Resumir',
    lookup: 'Pesquisar termo',
    cancel: 'Cancelar',
    copy: 'Copiar',
    copied: 'Copiado',
    close: 'Fechar',
    translating: 'Traduzindo...',
    summarizing: 'Resumindo...',
    looking_up: 'Pesquisando...',
    cancel_with_esc: '(ESC para cancelar)',
    image_text_recognition: 'Reconhecimento de texto em imagem',
    menu_addition_error: 'Erro ao adicionar o menu:',
    summary_result: 'Resultado do resumo',
    copy_term_definition: 'Copiar definição de termo',
    
    //options.js
    deepl_free_api_key_error: 'A chave API não é válida. Por favor, verifique a chave API.',
    deepl_free_api_key_warning: 'Aviso: Isto não parece ser uma chave API DeepL. Por favor, insira a chave API DeepL gratuita correta.',
    deepl_pro_api_key_warning: 'Aviso: Isto não parece ser uma chave API DeepL. Por favor, insira a chave API DeepL paga correta.',
    settings_save_error: 'Erro ao salvar as configurações. Por favor, tente novamente.',
    saved_all_settings: 'Todas as configurações salvas:',
    // 옵션 페이지 관련
    options_title: 'Configurações da extensão de tradução',
    service_selection: 'Seleção do serviço de tradução',
    api_key: 'Chave API',
    model_selection: 'Seleção do modelo',
    api_url: 'URL da API (opcional)',
    api_key_free: 'Chave API (gratuita)',
    api_key_pro: 'Chave API (paga)',
    interface_language: 'Idioma da interface',
    interface_language_desc: 'Menus e mensagens da extensão serão exibidos no idioma selecionado.',
    preferred_languages: 'Idiomas preferidos (apenas um idioma pode ser selecionado)',
    save: 'Salvar',
    settings_saved: 'Configurações salvas.',
    
    // 디버그 모드
    debug_mode: 'Ativar modo de depuração (para solução de problemas)',
    debug_mode_desc: 'Quando o modo de depuração está ativado, mensagens de erro e informações de comunicação da API serão exibidas no console do navegador.',
    api_guide_title: 'Guia de registro da API',
    claude_api_guide_title: 'Registro e geração de chave da Claude API',
    chatgpt_api_guide_title: 'Registro e geração de chave da ChatGPT API',
    grok_api_guide_title: 'Registro e geração de chave da Grok API',
    deepl_api_guide_title: 'Registro e geração de chave da DeepL API',
    deepl_api_help_title: 'Notas sobre o uso da DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Visite o site da Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Clique no botão "Sign up" no canto superior direito.',
    claude_guide_step3: 'Digite seu e-mail e senha para criar uma conta.',
    claude_guide_step4: 'Após fazer login, vá para a aba "API Keys".',
    claude_guide_step5: 'Clique no botão "Create API Key".',
    claude_guide_step6: 'Dê um nome à chave e crie-a.',
    claude_guide_step7: 'Copie a chave API gerada e cole-a no campo da chave Claude API acima.',
    claude_guide_note1: '※ Claude API requer registro de cartão de crédito, o uso é pago.',
    claude_guide_note2: '※ A chave API começa com o formato sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Visite o site da OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Clique no botão "Sign up" para criar uma conta.',
    chatgpt_guide_step3: 'Confirme seu endereço de e-mail.',
    chatgpt_guide_step4: 'Após fazer login, clique em Dashboard ao lado da sua foto de perfil e selecione "API keys" no menu à esquerda.',
    chatgpt_guide_step5: 'Clique no botão "Create new secret key".',
    chatgpt_guide_step6: 'Dê um nome à chave e crie-a.',
    chatgpt_guide_step7: 'Copie a chave API gerada e cole-a no campo da chave ChatGPT API acima.',
    chatgpt_guide_note1: '※ OpenAI API requer registro de cartão de crédito, o uso é pago.',
    chatgpt_guide_note2: '※ A chave API começa com o formato sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Visite o site da X.AI (https://x.ai).',
    grok_guide_step2: 'Faça login na sua conta.',
    grok_guide_step3: 'Clique no menu API no topo.',
    grok_guide_step4: 'Clique no botão "Start building now".',
    grok_guide_step5: 'Clique no menu API Keys à esquerda.',
    grok_guide_step6: 'Gere sua chave API.',
    grok_guide_step7: 'Copie a chave API gerada e cole-a no campo da chave Grok API acima.',
    grok_guide_note1: '※ A chave API começa com o formato xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Visite o site da DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Clique no botão "Sign up for free".',
    deepl_guide_step3: 'Digite seu e-mail e senha para criar uma conta.',
    deepl_guide_step4: 'Confirme seu endereço de e-mail para ativar a conta.',
    deepl_guide_step5: 'Após fazer login, vá para https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Vá para o menu API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Cole a chave API da versão gratuita no campo DeepL API Key (gratuita) acima.',
    deepl_guide_step8: 'Cole a chave API da versão paga no campo DeepL API Key (paga) acima.',
    deepl_guide_note1: '※ A versão gratuita da DeepL API permite traduzir até 500.000 caracteres por mês.',
    deepl_guide_note2: '※ Ao atualizar para a versão paga, você pode traduzir mais texto.',
    deepl_guide_note3: '※ Nota: Após atualizar para a versão paga, não pude usar a API gratuita. Por favor, leve isso em consideração.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Para a chave API gratuita, você deve usar o endpoint https://api-free.deepl.com.',
    deepl_api_help_pro: 'Para a chave API paga, você deve usar o endpoint https://api.deepl.com.',
    deepl_api_help_error: 'Se você receber o erro "Wrong endpoint. Use https://api.deepl.com" ao usar a chave API gratuita:',
    deepl_api_help_check1: '1. Verifique se você selecionou a opção DeepL API (gratuita).',
    deepl_api_help_check2: '2. Verifique se você está realmente usando uma chave API gratuita.',
    
    // 영역 및 결과 관련
    original_text: 'Texto original',
    translation: 'Tradução',
    summary: 'Resumo',
    definition: 'Definição',
    copy_original: 'Copiar original',
    copy_translation: 'Copiar tradução',
    copy_summary: 'Copiar resumo',
    copy_both: 'Copiar ambos',
    summarize_translation_result: 'Resumir resultado da tradução',
    debug_info: 'Informações de depuração',
    page_url: 'URL da página',
    page_title: 'Título da página',
    target_language: 'Idioma de destino',
    request_prompt: 'Prompt de solicitação',
    api_response: 'Resposta da API',
    clipboard_copy_failed: 'Falha ao copiar para a área de transferência',
    
    // 알림 및 오류 메시지
    canceled: 'Cancelado',
    translation_canceled: 'Tradução cancelada.',
    summary_canceled: 'Resumo cancelado.',
    lookup_canceled: 'Pesquisa cancelada.',
    operation_canceled: 'Operação cancelada.',
    api_key_error: 'Erro na chave API',
    api_key_missing: 'Chave API não está definida. Por favor, defina a chave API nas configurações da extensão.',
    goto_settings: 'Ir para configurações',
    error: 'Erro',
    translation_failed: 'Falha na tradução:',
    summary_failed: 'Falha no resumo:',
    lookup_failed: 'Falha na pesquisa:',
    no_response: 'Sem resposta',
    
    // 로그 메시지
    menu_added: 'Menu adicionado.',
    menu_add_error: 'Erro ao adicionar menu:',
    menu_removed: 'Menu de tradução removido:',
    operation_applied: 'A área já está {operation}. Exibindo menu de contexto padrão.',
    already_has_operation: 'A área já tem {operation}. Pulando operação.',
    rightclick_text: 'Texto selecionado com clique direito:',
    ctrl_rightclick: 'Ctrl + clique direito detectado: executando resumo',
    normal_rightclick: 'Clique direito normal detectado: executando tradução',
    doubleclick_text: 'Texto selecionado com clique duplo:',
    hovered_element: 'Elemento sob o cursor:',
    summary_response: 'Resposta do resumo:',
    range_undefined: 'Intervalo não definido.',
    inline_translation_insertion_error: 'Erro ao inserir tradução inline:',
    inline_summary_insertion_error: 'Erro ao inserir resumo inline:',
    fallback_insertion_error: 'Erro ao inserir fallback:',
    copy_failed: 'Falha ao copiar:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programação/Desenvolvimento de software',
    domain_blog: 'Blog/Artigos técnicos',
    domain_qa: 'Programação P&R',
    domain_docs: 'Documentação técnica/Documentação API',
    domain_academic: 'Acadêmico/Pesquisa',
    domain_news: 'Notícias/Atualidades',
    domain_finance: 'Finanças/Investimentos',
    domain_medical: 'Médico/Saúde',
    domain_legal: 'Jurídico',
    domain_webpage: 'Título da página web:',
    
    // 초기화 메시지
    extension_init: 'Inicializando extensão de tradução...',
    listeners_registered: 'Ouvintes de eventos registrados.',
    doubleclick_registered: 'Ouvinte de clique duplo registrado.',
    extension_ready: 'Extensão de tradução está pronta.'

    //filePanel.js
    ,fileListWillBeShownHere: 'A lista de arquivos será exibida aqui.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Tradução de legendas em tempo real ativada.'
    ,subtitle_translation_disabled: 'Tradução de legendas em tempo real desativada.'
    ,subtitle_translation_button: 'Tradução de legendas em tempo real'
    ,runtime_not_initialized: 'Runtime do Chrome não foi inicializado.'
    ,message_send_error: 'Erro ao enviar mensagem:'
    ,translation_response_missing: 'Sem resposta de tradução.'
    ,translation_error: 'Erro na tradução de legendas:'
};

export default pt; 