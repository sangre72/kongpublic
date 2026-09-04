// 터키어 (Turkish) 언어 파일

const tr = {
    // 메뉴 및 UI 관련
    translate: 'Çevir',
    summarize: 'Özetle',
    lookup: 'Terim ara',
    cancel: 'İptal',
    copy: 'Kopyala',
    copied: 'Kopyalandı',
    close: 'Kapat',
    translating: 'Çevriliyor...',
    summarizing: 'Özetleniyor...',
    looking_up: 'Aranıyor...',
    cancel_with_esc: '(İptal için ESC)',
    image_text_recognition: 'Görüntü metin tanıma',
    menu_addition_error: 'Menü ekleme hatası:',
    summary_result: 'Özet sonucu',
    copy_term_definition: 'Terim tanımını kopyala',
    
    //options.js
    deepl_free_api_key_error: 'API anahtarı geçersiz. Lütfen API anahtarını kontrol edin.',
    deepl_free_api_key_warning: 'Uyarı: Bu bir DeepL API anahtarı gibi görünmüyor. Lütfen doğru DeepL ücretsiz API anahtarını girin.',
    deepl_pro_api_key_warning: 'Uyarı: Bu bir DeepL API anahtarı gibi görünmüyor. Lütfen doğru DeepL ücretli API anahtarını girin.',
    settings_save_error: 'Ayarlar kaydedilirken hata oluştu. Lütfen tekrar deneyin.',
    saved_all_settings: 'Tüm kaydedilen ayarlar:',
    
    // 옵션 페이지 관련
    options_title: 'Çeviri eklentisi ayarları',
    service_selection: 'Çeviri servisi seçimi',
    api_key: 'API anahtarı',
    model_selection: 'Model seçimi',
    api_url: 'API URL (isteğe bağlı)',
    api_key_free: 'API anahtarı (ücretsiz)',
    api_key_pro: 'API anahtarı (ücretli)',
    interface_language: 'Arayüz dili',
    interface_language_desc: 'Eklentinin menüleri ve mesajları seçilen dilde görüntülenecektir.',
    preferred_languages: 'Tercih edilen diller (sadece bir dil seçilebilir)',
    save: 'Kaydet',
    settings_saved: 'Ayarlar kaydedildi.',
    
    // 디버그 모드
    debug_mode: 'Hata ayıklama modunu etkinleştir (sorun giderme için)',
    debug_mode_desc: 'Hata ayıklama modu etkinleştirildiğinde, hata mesajları ve API iletişim bilgileri tarayıcı konsolunda görüntülenecektir.',
    api_guide_title: 'API kayıt kılavuzu',
    claude_api_guide_title: 'Claude API kaydı ve anahtar oluşturma',
    chatgpt_api_guide_title: 'ChatGPT API kaydı ve anahtar oluşturma',
    grok_api_guide_title: 'Grok API kaydı ve anahtar oluşturma',
    deepl_api_guide_title: 'DeepL API kaydı ve anahtar oluşturma',
    deepl_api_help_title: 'DeepL API kullanımı hakkında notlar',
    
    // Claude API 가이드
    claude_guide_step1: 'Anthropic web sitesini ziyaret edin (https://www.anthropic.com/api).',
    claude_guide_step2: 'Sağ üst köşedeki "Sign up" düğmesine tıklayın.',
    claude_guide_step3: 'Hesap oluşturmak için e-posta adresinizi ve şifrenizi girin.',
    claude_guide_step4: 'Giriş yaptıktan sonra, "API Keys" sekmesine gidin.',
    claude_guide_step5: '"Create API Key" düğmesine tıklayın.',
    claude_guide_step6: 'Anahtara bir isim verin ve oluşturun.',
    claude_guide_step7: 'Oluşturulan API anahtarını kopyalayın ve yukarıdaki Claude API anahtarı alanına yapıştırın.',
    claude_guide_note1: '※ Claude API kredi kartı kaydı gerektirir, kullanım ücretlidir.',
    claude_guide_note2: '※ API anahtarı sk-ant-api03-... formatıyla başlar.',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'OpenAI web sitesini ziyaret edin (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Hesap oluşturmak için "Sign up" düğmesine tıklayın.',
    chatgpt_guide_step3: 'E-posta adresinizi onaylayın.',
    chatgpt_guide_step4: 'Giriş yaptıktan sonra, profil fotoğrafınızın yanındaki Dashboard\'a tıklayın ve sol menüden "API keys"i seçin.',
    chatgpt_guide_step5: '"Create new secret key" düğmesine tıklayın.',
    chatgpt_guide_step6: 'Anahtara bir isim verin ve oluşturun.',
    chatgpt_guide_step7: 'Oluşturulan API anahtarını kopyalayın ve yukarıdaki ChatGPT API anahtarı alanına yapıştırın.',
    chatgpt_guide_note1: '※ OpenAI API kredi kartı kaydı gerektirir, kullanım ücretlidir.',
    chatgpt_guide_note2: '※ API anahtarı sk-... formatıyla başlar.',
    
    // Grok API 가이드
    grok_guide_step1: 'X.AI web sitesini ziyaret edin (https://x.ai).',
    grok_guide_step2: 'Hesabınıza giriş yapın.',
    grok_guide_step3: 'Üstteki API menüsüne tıklayın.',
    grok_guide_step4: '"Start building now" düğmesine tıklayın.',
    grok_guide_step5: 'Soldaki API Keys menüsüne tıklayın.',
    grok_guide_step6: 'API anahtarınızı oluşturun.',
    grok_guide_step7: 'Oluşturulan API anahtarını kopyalayın ve yukarıdaki Grok API anahtarı alanına yapıştırın.',
    grok_guide_note1: '※ API anahtarı xai-... formatıyla başlar.',
    
    // DeepL API 가이드
    deepl_guide_step1: 'DeepL API web sitesini ziyaret edin (https://www.deepl.com/pro-api).',
    deepl_guide_step2: '"Sign up for free" düğmesine tıklayın.',
    deepl_guide_step3: 'Hesap oluşturmak için e-posta adresinizi ve şifrenizi girin.',
    deepl_guide_step4: 'Hesabı etkinleştirmek için e-posta adresinizi onaylayın.',
    deepl_guide_step5: 'Giriş yaptıktan sonra, https://www.deepl.com/account/subscription adresine gidin.',
    deepl_guide_step6: 'API keys menüsüne gidin (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Ücretsiz sürüm API anahtarını yukarıdaki DeepL API Key (ücretsiz) alanına yapıştırın.',
    deepl_guide_step8: 'Ücretli sürüm API anahtarını yukarıdaki DeepL API Key (ücretli) alanına yapıştırın.',
    deepl_guide_note1: '※ DeepL API\'nin ücretsiz sürümü ayda 500.000 karaktere kadar çeviri yapmanıza izin verir.',
    deepl_guide_note2: '※ Ücretli sürüme yükselttiğinizde daha fazla metin çevirebilirsiniz.',
    deepl_guide_note3: '※ Not: Ücretli sürüme yükseltildikten sonra ücretsiz API\'yi kullanamadım. Lütfen bunu göz önünde bulundurun.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Ücretsiz API anahtarı için endpoint https://api-free.deepl.com kullanın.',
    deepl_api_help_pro: 'Ücretli API anahtarı için endpoint https://api.deepl.com kullanın.',
    deepl_api_help_error: 'Ücretsiz API anahtarını kullanırken "Wrong endpoint. Use https://api.deepl.com" hatasını alırsanız:',
    deepl_api_help_check1: '1. DeepL API (ücretsiz) seçeneğini seçtiğinizi kontrol edin.',
    deepl_api_help_check2: '2. Gerçekten ücretsiz bir API anahtarı kullandığınızı kontrol edin.',
    
    // 영역 및 결과 관련
    original_text: 'Orijinal metin',
    translation: 'Çeviri',
    summary: 'Özet',
    definition: 'Tanım',
    copy_original: 'Orijinali kopyala',
    copy_translation: 'Çeviriyi kopyala',
    copy_summary: 'Özeti kopyala',
    copy_both: 'İkisini de kopyala',
    summarize_translation_result: 'Çeviri sonucunu özetle',
    debug_info: 'Hata ayıklama bilgisi',
    page_url: 'Sayfa URL\'si',
    page_title: 'Sayfa başlığı',
    target_language: 'Hedef dil',
    request_prompt: 'İstek promptu',
    api_response: 'API yanıtı',
    clipboard_copy_failed: 'Panoya kopyalanamadı',
    
    // 알림 및 오류 메시지
    canceled: 'İptal edildi',
    translation_canceled: 'Çeviri iptal edildi.',
    summary_canceled: 'Özetleme iptal edildi.',
    lookup_canceled: 'Arama iptal edildi.',
    operation_canceled: 'İşlem iptal edildi.',
    api_key_error: 'API anahtarı hatası',
    api_key_missing: 'API anahtarı yapılandırılmamış. Lütfen eklenti ayarlarında API anahtarını yapılandırın.',
    goto_settings: 'Ayarlara git',
    error: 'Hata',
    translation_failed: 'Çeviri başarısız:',
    summary_failed: 'Özetleme başarısız:',
    lookup_failed: 'Arama başarısız:',
    no_response: 'Yanıt yok',
    
    // 로그 메시지
    menu_added: 'Menü eklendi.',
    menu_add_error: 'Menü ekleme hatası:',
    menu_removed: 'Çeviri menüsü kaldırıldı:',
    operation_applied: 'Alan zaten {operation}. Varsayılan bağlam menüsü gösteriliyor.',
    already_has_operation: 'Alan zaten {operation} sahip. İşlem atlanıyor.',
    rightclick_text: 'Sağ tıklamayla seçilen metin:',
    ctrl_rightclick: 'Ctrl + sağ tıklama algılandı: özetleme çalıştırılıyor',
    normal_rightclick: 'Normal sağ tıklama algılandı: çeviri çalıştırılıyor',
    doubleclick_text: 'Çift tıklamayla seçilen metin:',
    hovered_element: 'Fare imlecinin altındaki öğe:',
    summary_response: 'Özet yanıtı:',
    range_undefined: 'Aralık tanımlanmamış.',
    inline_translation_insertion_error: 'Satır içi çeviri ekleme hatası:',
    inline_summary_insertion_error: 'Satır içi özet ekleme hatası:',
    fallback_insertion_error: 'Yedek ekleme hatası:',
    copy_failed: 'Kopyalama başarısız:',
    
    // 도메인 컨텍스트
    domain_programming: 'Programlama/Yazılım geliştirme',
    domain_blog: 'Blog/Teknik makaleler',
    domain_qa: 'Programlama S&C',
    domain_docs: 'Teknik dokümantasyon/API dokümantasyonu',
    domain_academic: 'Akademik/Araştırma',
    domain_news: 'Haberler/Güncel olaylar',
    domain_finance: 'Finans/Yatırım',
    domain_medical: 'Tıp/Sağlık',
    domain_legal: 'Hukuk',
    domain_webpage: 'Web sayfası başlığı:',
    
    // 초기화 메시지
    extension_init: 'Çeviri eklentisi başlatılıyor...',
    listeners_registered: 'Olay dinleyicileri kaydedildi.',
    doubleclick_registered: 'Çift tıklama dinleyicisi kaydedildi.',
    extension_ready: 'Çeviri eklentisi hazır.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Dosya listesi burada görüntülenecektir.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Gerçek zamanlı altyazı çevirisi etkinleştirildi.'
    ,subtitle_translation_disabled: 'Gerçek zamanlı altyazı çevirisi devre dışı bırakıldı.'
    ,subtitle_translation_button: 'Gerçek zamanlı altyazı çevirisi'
    ,runtime_not_initialized: 'Chrome çalışma zamanı başlatılmadı.'
    ,message_send_error: 'Mesaj gönderme hatası:'
    ,translation_response_missing: 'Çeviri yanıtı yok.'
    ,translation_error: 'Altyazı çeviri hatası:'
};

export default tr; 