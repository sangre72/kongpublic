// 러시아어 (Russian) 언어 파일

const ru = {
    // 메뉴 및 UI 관련
    translate: 'Перевести',
    summarize: 'Обобщить',
    lookup: 'Поиск термина',
    cancel: 'Отмена',
    copy: 'Копировать',
    copied: 'Скопировано',
    close: 'Закрыть',
    translating: 'Перевод...',
    summarizing: 'Обобщение...',
    looking_up: 'Поиск...',
    cancel_with_esc: '(ESC для отмены)',
    image_text_recognition: 'Распознавание текста на изображении',
    menu_addition_error: 'Ошибка добавления меню:',
    summary_result: 'Результат обобщения',
    copy_term_definition: 'Копировать определение термина',
    
    //options.js
    deepl_free_api_key_error: 'Ключ API недействителен. Пожалуйста, проверьте ключ API.',
    deepl_free_api_key_warning: 'Предупреждение: Это не кажется DeepL API ключом. Пожалуйста, введите правильный DeepL бесплатный API ключ.',
    deepl_pro_api_key_warning: 'Предупреждение: Это не кажется DeepL API ключом. Пожалуйста, введите правильный DeepL платный API ключ.',
    settings_save_error: 'Ошибка при сохранении настроек. Пожалуйста, попробуйте снова.',
    saved_all_settings: 'Все сохраненные настройки:',

    // 옵션 페이지 관련
    options_title: 'Настройки расширения перевода',
    service_selection: 'Выбор службы перевода',
    api_key: 'API ключ',
    model_selection: 'Выбор модели',
    api_url: 'URL API (необязательно)',
    api_key_free: 'API ключ (бесплатный)',
    api_key_pro: 'API ключ (платный)',
    interface_language: 'Язык интерфейса',
    interface_language_desc: 'Меню и сообщения расширения будут отображаться на выбранном языке.',
    preferred_languages: 'Предпочитаемые языки (можно выбрать только один язык)',
    save: 'Сохранить',
    settings_saved: 'Настройки сохранены.',
    
    // 디버그 모드
    debug_mode: 'Включить режим отладки (для устранения проблем)',
    debug_mode_desc: 'Когда режим отладки включен, сообщения об ошибках и информация об API будут отображаться в консоли браузера.',
    api_guide_title: 'Руководство по регистрации API',
    claude_api_guide_title: 'Регистрация и создание ключа Claude API',
    chatgpt_api_guide_title: 'Регистрация и создание ключа ChatGPT API',
    grok_api_guide_title: 'Регистрация и создание ключа Grok API',
    deepl_api_guide_title: 'Регистрация и создание ключа DeepL API',
    deepl_api_help_title: 'Примечания по использованию DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Посетите сайт Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Нажмите кнопку "Sign up" в правом верхнем углу.',
    claude_guide_step3: 'Введите email и пароль для создания аккаунта.',
    claude_guide_step4: 'После входа перейдите на вкладку "API Keys".',
    claude_guide_step5: 'Нажмите кнопку "Create API Key".',
    claude_guide_step6: 'Дайте ключу имя и создайте его.',
    claude_guide_step7: 'Скопируйте сгенерированный API ключ и вставьте его в поле ключа Claude API выше.',
    claude_guide_note1: '※ Claude API требует регистрации кредитной карты, использование платное.',
    claude_guide_note2: '※ API ключ начинается с формата sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Посетите сайт OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Нажмите кнопку "Sign up" для создания аккаунта.',
    chatgpt_guide_step3: 'Подтвердите свой email.',
    chatgpt_guide_step4: 'После входа нажмите Dashboard рядом с фото профиля и выберите "API keys" в левом меню.',
    chatgpt_guide_step5: 'Нажмите кнопку "Create new secret key".',
    chatgpt_guide_step6: 'Дайте ключу имя и создайте его.',
    chatgpt_guide_step7: 'Скопируйте сгенерированный API ключ и вставьте его в поле ключа ChatGPT API выше.',
    chatgpt_guide_note1: '※ OpenAI API требует регистрации кредитной карты, использование платное.',
    chatgpt_guide_note2: '※ API ключ начинается с формата sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Посетите сайт X.AI (https://x.ai).',
    grok_guide_step2: 'Войдите в свой аккаунт.',
    grok_guide_step3: 'Нажмите на меню API вверху.',
    grok_guide_step4: 'Нажмите кнопку "Start building now".',
    grok_guide_step5: 'Нажмите на меню API Keys слева.',
    grok_guide_step6: 'Создайте свой API ключ.',
    grok_guide_step7: 'Скопируйте сгенерированный API ключ и вставьте его в поле ключа Grok API выше.',
    grok_guide_note1: '※ API ключ начинается с формата xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Посетите сайт DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Нажмите кнопку "Sign up for free".',
    deepl_guide_step3: 'Введите email и пароль для создания аккаунта.',
    deepl_guide_step4: 'Подтвердите свой email для активации аккаунта.',
    deepl_guide_step5: 'После входа перейдите на https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Перейдите в меню API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Вставьте API ключ бесплатной версии в поле DeepL API Key (бесплатный) выше.',
    deepl_guide_step8: 'Вставьте API ключ платной версии в поле DeepL API Key (платный) выше.',
    deepl_guide_note1: '※ Бесплатная версия DeepL API позволяет переводить до 500,000 символов в месяц.',
    deepl_guide_note2: '※ При обновлении до платной версии вы можете переводить больше текста.',
    deepl_guide_note3: '※ Примечание: После обновления до платной версии я не смог использовать бесплатный API. Пожалуйста, учтите это.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Для бесплатного API ключа используйте endpoint https://api-free.deepl.com.',
    deepl_api_help_pro: 'Для платного API ключа используйте endpoint https://api.deepl.com.',
    deepl_api_help_error: 'Если при использовании бесплатного API ключа вы получаете ошибку "Wrong endpoint. Use https://api.deepl.com":',
    deepl_api_help_check1: '1. Проверьте, что вы выбрали опцию DeepL API (бесплатный).',
    deepl_api_help_check2: '2. Проверьте, что вы действительно используете бесплатный API ключ.',
    
    // 영역 및 결과 관련
    original_text: 'Исходный текст',
    translation: 'Перевод',
    summary: 'Обобщение',
    definition: 'Определение',
    copy_original: 'Копировать оригинал',
    copy_translation: 'Копировать перевод',
    copy_summary: 'Копировать обобщение',
    copy_both: 'Копировать оба',
    summarize_translation_result: 'Обобщить результат перевода',
    debug_info: 'Отладочная информация',
    page_url: 'URL страницы',
    page_title: 'Заголовок страницы',
    target_language: 'Целевой язык',
    request_prompt: 'Запрос промпта',
    api_response: 'Ответ API',
    clipboard_copy_failed: 'Не удалось скопировать в буфер обмена',
    
    // 알림 및 오류 메시지
    canceled: 'Отменено',
    translation_canceled: 'Перевод отменен.',
    summary_canceled: 'Обобщение отменено.',
    lookup_canceled: 'Поиск отменен.',
    operation_canceled: 'Операция отменена.',
    api_key_error: 'Ошибка API ключа',
    api_key_missing: 'API ключ не настроен. Пожалуйста, настройте API ключ в настройках расширения.',
    goto_settings: 'Перейти к настройкам',
    error: 'Ошибка',
    translation_failed: 'Ошибка перевода:',
    summary_failed: 'Ошибка обобщения:',
    lookup_failed: 'Ошибка поиска:',
    no_response: 'Нет ответа',
    
    // 로그 메시지
    menu_added: 'Меню добавлено.',
    menu_add_error: 'Ошибка добавления меню:',
    menu_removed: 'Меню перевода удалено:',
    operation_applied: 'Область уже {operation}. Отображается контекстное меню по умолчанию.',
    already_has_operation: 'Область уже имеет {operation}. Пропуск операции.',
    rightclick_text: 'Текст, выбранный правым кликом:',
    ctrl_rightclick: 'Обнаружен Ctrl + правый клик: выполняется обобщение',
    normal_rightclick: 'Обнаружен обычный правый клик: выполняется перевод',
    doubleclick_text: 'Текст, выбранный двойным кликом:',
    hovered_element: 'Элемент под курсором:',
    summary_response: 'Ответ обобщения:',
    range_undefined: 'Диапазон не определен.',
    inline_translation_insertion_error: 'Ошибка вставки встроенного перевода:',
    inline_summary_insertion_error: 'Ошибка вставки встроенного обобщения:',
    fallback_insertion_error: 'Ошибка вставки резервного варианта:',
    copy_failed: 'Ошибка копирования:',
    
    // 도메인 컨텍스트
    domain_programming: 'Программирование/Разработка ПО',
    domain_blog: 'Блог/Технические статьи',
    domain_qa: 'Программирование В&О',
    domain_docs: 'Техническая документация/Документация API',
    domain_academic: 'Академический/Исследования',
    domain_news: 'Новости/Текущие события',
    domain_finance: 'Финансы/Инвестиции',
    domain_medical: 'Медицина/Здоровье',
    domain_legal: 'Юридический',
    domain_webpage: 'Заголовок веб-страницы:',
    
    // 초기화 메시지
    extension_init: 'Инициализация расширения перевода...',
    listeners_registered: 'Слушатели событий зарегистрированы.',
    doubleclick_registered: 'Слушатель двойного клика зарегистрирован.',
    extension_ready: 'Расширение перевода готово.',

    //filePanel.js
    fileListWillBeShownHere: 'Список файлов будет показан здесь.',

    //subtitleService.js
    subtitle_translation_enabled: 'Перевод субтитров в реальном времени включен.',
    subtitle_translation_disabled: 'Перевод субтитров в реальном времени отключен.',
    subtitle_translation_button: 'Перевод субтитров в реальном времени',
    runtime_not_initialized: 'Runtime Chrome не инициализирован.',
    message_send_error: 'Ошибка отправки сообщения:',
    translation_response_missing: 'Отсутствует ответ перевода.',
    translation_error: 'Ошибка перевода субтитров:'
};

export default ru; 