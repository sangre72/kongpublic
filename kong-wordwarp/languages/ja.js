// 일본어 (Japanese) 언어 파일

const ja = {
    // メニューとUI関連
    translate: '翻訳',
    summarize: '要約',
    lookup: '用語検索',
    cancel: 'キャンセル',
    copy: 'コピー',
    copied: 'コピー済み',
    close: '閉じる',
    translating: '翻訳中...',
    summarizing: '要約中...',
    looking_up: '用語検索中...',
    cancel_with_esc: '(ESCでキャンセル)',
    image_text_recognition: '画像テキスト認識',
    menu_addition_error: 'メニューの追加中にエラーが発生しました:',
    summary_result: '要約結果',
    copy_term_definition: '用語定義のコピー',

    //options.js
    deepl_free_api_key_error: 'APIキーが無効です。APIキーを確認してください。',
    deepl_free_api_key_warning: '警告: これはDeepL APIキーではありません。正しいDeepL無料APIキーを入力してください。',
    deepl_pro_api_key_warning: '警告: これはDeepL APIキーではありません。正しいDeepL有料APIキーを入力してください。',
    settings_save_error: '設定の保存中にエラーが発生しました。もう一度試してください。',
    saved_all_settings: 'すべての保存された設定:',
    
    // オプションページ関連
    options_title: '翻訳拡張機能の設定',
    service_selection: '翻訳サービスを選択',
    api_key: 'APIキー',
    model_selection: 'モデルを選択',
    api_url: 'API URL (オプション)',
    api_key_free: 'APIキー（無料）',
    api_key_pro: 'APIキー（有料）',
    interface_language: 'インターフェース言語',
    interface_language_desc: '選択した言語で拡張機能のメニューとメッセージが表示されます。',
    preferred_languages: '優先言語（一つの言語のみ選択可能）',
    save: '保存',
    settings_saved: '設定が保存されました。',
    
    // デバッグモード
    debug_mode: 'デバッグモードを有効化（トラブルシューティング用）',
    debug_mode_desc: 'デバッグモードを有効にすると、エラーメッセージやAPI通信情報がブラウザコンソールに表示されます。',
    api_guide_title: 'API登録ガイド',
    claude_api_guide_title: 'Claude API登録とキー発行方法',
    chatgpt_api_guide_title: 'ChatGPT API登録とキー発行方法',
    grok_api_guide_title: 'Grok API登録とキー発行方法',
    deepl_api_guide_title: 'DeepL API登録とキー発行方法',
    deepl_api_help_title: 'DeepL API利用時の注意点',
    
    // Claude API ガイド
    claude_guide_step1: 'Anthropicウェブサイト(https://www.anthropic.com/api)にアクセスします。',
    claude_guide_step2: '右上の「Sign up」ボタンをクリックします。',
    claude_guide_step3: 'メールアドレスとパスワードを入力してアカウントを作成します。',
    claude_guide_step4: 'ログインしたら、「API Keys」タブに移動します。',
    claude_guide_step5: '「Create API Key」ボタンをクリックします。',
    claude_guide_step6: 'キーの名前を入力して作成します。',
    claude_guide_step7: '発行されたAPIキーをコピーして上のClaude APIキーフィールドに貼り付けます。',
    claude_guide_note1: '※ Claude APIはクレジットカード登録が必要で、使用量に基づいて料金が請求されます。',
    claude_guide_note2: '※ APIキーはsk-ant-api03-...形式で始まります。',
    
    // ChatGPT API ガイド
    chatgpt_guide_step1: 'OpenAI ウェブサイト(https://platform.openai.com/signup)にアクセスします。',
    chatgpt_guide_step2: '「Sign up」ボタンをクリックしてアカウントを作成します。',
    chatgpt_guide_step3: 'メール認証を完了します。',
    chatgpt_guide_step4: 'ログインしたら、右上のプロフィールアイコンの右側のダッシュボードをクリックして左側のメニューの「API keys」を選択します。',
    chatgpt_guide_step5: '「Create new secret key」ボタンをクリックします。',
    chatgpt_guide_step6: 'キーの名前を入力して作成します。',
    chatgpt_guide_step7: '発行されたAPIキーをコピーして上のChatGPT APIキーフィールドに貼り付けます。',
    chatgpt_guide_note1: '※ OpenAI APIはクレジットカード登録が必要で、使用量に基づいて料金が請求されます。',
    chatgpt_guide_note2: '※ APIキーはsk-...形式で始まります。',
    
    // Grok API ガイド
    grok_guide_step1: 'X.AI ウェブサイト(https://x.ai)にアクセスします。',
    grok_guide_step2: 'アカウントでログインします。',
    grok_guide_step3: '上部のAPIメニューをクリックします。',
    grok_guide_step4: '「Start building now」ボタンをクリックします。',
    grok_guide_step5: '左側のAPI Keysメニューをクリックします。',
    grok_guide_step6: 'APIキーを発行します。',
    grok_guide_step7: '発行されたAPIキーをコピーして上のGrok APIキーフィールドに貼り付けます。',
    grok_guide_note1: '※ APIキーはxai-...形式で始まります。',
    
    // DeepL API ガイド
    deepl_guide_step1: 'DeepL API ウェブサイト(https://www.deepl.com/pro-api)にアクセスします。',
    deepl_guide_step2: '「Sign up for free」ボタンをクリックします。',
    deepl_guide_step3: 'メールアドレスとパスワードを入力してアカウントを作成します。',
    deepl_guide_step4: 'アカウントをアクティベートするためにメール認証を完了します。',
    deepl_guide_step5: 'ログインしたらhttps://www.deepl.com/account/subscriptionアカウントページに移動します。',
    deepl_guide_step6: 'API keysメニューに移動します(https://www.deepl.com/account/keys)',
    deepl_guide_step7: '無料バージョンのAPIキーを上のDeepL API Key（無料）フィールドに貼り付けます。',
    deepl_guide_step8: '有料バージョンのAPIキーを上のDeepL API Key（有料）フィールドに貼り付けます。',
    deepl_guide_note1: '※ DeepL API無料バージョンは月50万文字まで翻訳可能です。',
    deepl_guide_note2: '※ 有料バージョンにアップグレードすると、より多くのテキストを翻訳できます。',
    deepl_guide_note3: '※ 注意: 有料バージョンにアップグレードすると、無料バージョンのAPIは使用できなくなりました。ご参考までに。',
    
    // DeepL API ヘルプ
    deepl_api_help_free: '無料APIキーはhttps://api-free.deepl.comエンドポイントを使用する必要があります。',
    deepl_api_help_pro: '有料APIキーはhttps://api.deepl.comエンドポイントを使用する必要があります。',
    deepl_api_help_error: '無料APIキーを使用しているときに「Wrong endpoint. Use https://api.deepl.com」エラーが発生した場合:',
    deepl_api_help_check1: '1. DeepL API（無料）オプションを選択したことを確認してください。',
    deepl_api_help_check2: '2. 実際に無料APIキーを使用しているかどうかを確認してください。',
    
    // 領域と結果関連
    original_text: '原文',
    translation: '翻訳',
    summary: '要約',
    definition: '定義',
    copy_original: '原文をコピー',
    copy_translation: '翻訳をコピー',
    copy_summary: '要約をコピー',
    copy_both: '両方をコピー',
    summarize_translation_result: '翻訳結果の要約',
    debug_info: 'デバッグ情報',
    page_url: 'ページURL',
    page_title: 'ページタイトル',
    target_language: '対象言語',
    request_prompt: 'リクエストプロンプト',
    api_response: 'APIレスポンス',
    clipboard_copy_failed: 'クリップボードへのコピーに失敗しました',
    
    // 通知とエラーメッセージ
    canceled: 'キャンセルされました',
    translation_canceled: '翻訳作業がキャンセルされました。',
    summary_canceled: '要約作業がキャンセルされました。',
    lookup_canceled: '用語検索がキャンセルされました。',
    operation_canceled: '操作がキャンセルされました。',
    api_key_error: 'APIキーエラー',
    api_key_missing: 'APIキーが設定されていません。拡張機能の設定でAPIキーを設定してください。',
    goto_settings: '設定ページに移動',
    error: 'エラー',
    translation_failed: '翻訳に失敗しました:',
    summary_failed: '要約に失敗しました:',
    lookup_failed: '用語検索に失敗しました:',
    no_response: '応答なし',
    
    // ログメッセージ
    menu_added: 'メニューが追加されました。',
    menu_add_error: 'メニュー追加中にエラーが発生しました:',
    menu_removed: '翻訳メニューを削除しました:',
    operation_applied: 'すでに{operation}されている領域です。デフォルトのコンテキストメニューを表示します。',
    already_has_operation: 'すでに{operation}が含まれている領域です。操作をスキップします。',
    rightclick_text: '右クリックで選択されたテキスト:',
    ctrl_rightclick: 'Ctrl + 右クリック検出: 要約実行',
    normal_rightclick: '通常の右クリック検出: 翻訳実行',
    doubleclick_text: 'ダブルクリックで選択されたテキスト:',
    hovered_element: 'ホバーされた要素:',
    summary_response: '要約レスポンス:',
    range_undefined: '範囲が定義されていません。',
    inline_translation_insertion_error: 'インライン翻訳の挿入エラー:',
    inline_summary_insertion_error: 'インライン要約の挿入エラー:',
    fallback_insertion_error: '代替挿入エラー:',
    copy_failed: 'コピーに失敗しました:',
    
    // ドメインコンテキスト
    domain_programming: 'プログラミング/ソフトウェア開発',
    domain_blog: 'ブログ/技術記事',
    domain_qa: 'プログラミングQ&A',
    domain_docs: '技術文書/APIドキュメント',
    domain_academic: '学術/研究',
    domain_news: 'ニュース/時事',
    domain_finance: '金融/投資',
    domain_medical: '医学/健康',
    domain_legal: '法律',
    domain_webpage: 'ウェブページタイトル:',
    
    // 初期化メッセージ
    extension_init: '翻訳拡張機能を初期化中...',
    listeners_registered: 'イベントリスナーが登録されました。',
    doubleclick_registered: 'ダブルクリックイベントリスナーが登録されました。',
    extension_ready: '翻訳拡張機能の準備ができました。'

    //filePanel.js
    ,fileListWillBeShownHere: 'ファイルリストはここに表示されます。'

    //subtitleService.js
    ,subtitle_translation_enabled: '字幕のリアルタイム翻訳が有効になりました。'
    ,subtitle_translation_disabled: '字幕のリアルタイム翻訳が無効になりました。'
    ,subtitle_translation_button: '字幕のリアルタイム翻訳'
    ,runtime_not_initialized: 'Chromeランタイムが初期化されていません。'
    ,message_send_error: 'メッセージ送信中にエラーが発生しました:'
    ,translation_response_missing: '翻訳応答がありません。'
    ,translation_error: '字幕の翻訳エラー:'
};

// 기본 내보내기로 언어 데이터 노출
export default ja; 