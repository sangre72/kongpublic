// 그리스어 (Greek) 언어 파일

const el = {
    // 메뉴 및 UI 관련
    translate: 'Μετάφραση',
    summarize: 'Περίληψη',
    lookup: 'Αναζήτηση όρου',
    cancel: 'Ακύρωση',
    copy: 'Αντιγραφή',
    copied: 'Αντιγράφηκε',
    close: 'Κλείσιμο',
    translating: 'Μετάφραση...',
    summarizing: 'Δημιουργία περίληψης...',
    looking_up: 'Αναζήτηση...',
    cancel_with_esc: '(ESC για ακύρωση)',
    image_text_recognition: 'Αναγνώριση κειμένου εικόνας',
    menu_addition_error: 'Σφάλμα κατά την προσθήκη του μενού:',
    summary_result: 'Αποτέλεσμα περίληψης',
    copy_term_definition: 'Αντιγραφή ορισμού όρου',
    
     //options.js
     deepl_free_api_key_error: 'Το API key δεν είναι έγκυρο. Παρακαλούμε ελέγξτε το API key.',
     deepl_free_api_key_warning: 'Προειδοποίηση: Αυτό δεν φαίνεται να είναι ένα DeepL API key. Παρακαλούμε εισάγετε το σωστό DeepL free API key.',
     deepl_pro_api_key_warning: 'Προειδοποίηση: Αυτό δεν φαίνεται να είναι ένα DeepL API key. Παρακαλούμε εισάγετε το σωστό DeepL paid API key.',
     settings_save_error: 'Σφάλμα κατά την αποθήκευση των ρυθμίσεων. Παρακαλούμε προσπαθείστε ξανά.',
     saved_all_settings: 'Όλες οι αποθηκευμένες ρυθμίσεις:',
     
    // 옵션 페이지 관련
    options_title: 'Ρυθμίσεις επέκτασης μετάφρασης',
    service_selection: 'Επιλογή υπηρεσίας μετάφρασης',
    api_key: 'Κλειδί API',
    model_selection: 'Επιλογή μοντέλου',
    api_url: 'URL API (προαιρετικό)',
    api_key_free: 'Κλειδί API (δωρεάν)',
    api_key_pro: 'Κλειδί API (επί πληρωμή)',
    interface_language: 'Γλώσσα διεπαφής',
    interface_language_desc: 'Τα μενού και τα μηνύματα της επέκτασης θα εμφανίζονται στην επιλεγμένη γλώσσα.',
    preferred_languages: 'Προτιμώμενες γλώσσες (μόνο μία γλώσσα μπορεί να επιλεγεί)',
    save: 'Αποθήκευση',
    settings_saved: 'Οι ρυθμίσεις αποθηκεύτηκαν.',
    
    // 디버그 모드
    debug_mode: 'Ενεργοποίηση λειτουργίας εντοπισμού σφαλμάτων (για αντιμετώπιση προβλημάτων)',
    debug_mode_desc: 'Όταν η λειτουργία εντοπισμού σφαλμάτων είναι ενεργοποιημένη, τα μηνύματα σφαλμάτων και οι πληροφορίες επικοινωνίας API θα εμφανίζονται στην κονσόλα του προγράμματος περιήγησης.',
    api_guide_title: 'Οδηγός εγγραφής API',
    claude_api_guide_title: 'Εγγραφή Claude API και δημιουργία κλειδιού',
    chatgpt_api_guide_title: 'Εγγραφή ChatGPT API και δημιουργία κλειδιού',
    grok_api_guide_title: 'Εγγραφή Grok API και δημιουργία κλειδιού',
    deepl_api_guide_title: 'Εγγραφή DeepL API και δημιουργία κλειδιού',
    deepl_api_help_title: 'Σημειώσεις χρήσης DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'Επισκεφθείτε τον ιστότοπο της Anthropic (https://www.anthropic.com/api).',
    claude_guide_step2: 'Κάντε κλικ στο κουμπί "Sign up" στην πάνω δεξιά γωνία.',
    claude_guide_step3: 'Εισαγάγετε το email και τον κωδικό πρόσβασής σας για να δημιουργήσετε λογαριασμό.',
    claude_guide_step4: 'Μετά τη σύνδεση, μεταβείτε στην καρτέλα "API Keys".',
    claude_guide_step5: 'Κάντε κλικ στο κουμπί "Create API Key".',
    claude_guide_step6: 'Δώστε ένα όνομα στο κλειδί και δημιουργήστε το.',
    claude_guide_step7: 'Αντιγράψτε το κλειδί API που δημιουργήθηκε και επικολλήστε το στο παραπάνω πεδίο κλειδιού Claude API.',
    claude_guide_note1: '※ Το Claude API απαιτεί εγγραφή πιστωτικής κάρτας, η χρήση είναι επί πληρωμή.',
    claude_guide_note2: '※ Το κλειδί API ξεκινά με τη μορφή sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'Επισκεφθείτε τον ιστότοπο της OpenAI (https://platform.openai.com/signup).',
    chatgpt_guide_step2: 'Κάντε κλικ στο κουμπί "Sign up" για να δημιουργήσετε λογαριασμό.',
    chatgpt_guide_step3: 'Επιβεβαιώστε τη διεύθυνση email σας.',
    chatgpt_guide_step4: 'Μετά τη σύνδεση, κάντε κλικ στο Dashboard δίπλα στην εικόνα προφίλ σας και επιλέξτε "API keys" από το αριστερό μενού.',
    chatgpt_guide_step5: 'Κάντε κλικ στο κουμπί "Create new secret key".',
    chatgpt_guide_step6: 'Δώστε ένα όνομα στο κλειδί και δημιουργήστε το.',
    chatgpt_guide_step7: 'Αντιγράψτε το κλειδί API που δημιουργήθηκε και επικολλήστε το στο παραπάνω πεδίο κλειδιού ChatGPT API.',
    chatgpt_guide_note1: '※ Το OpenAI API απαιτεί εγγραφή πιστωτικής κάρτας, η χρήση είναι επί πληρωμή.',
    chatgpt_guide_note2: '※ Το κλειδί API ξεκινά με τη μορφή sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'Επισκεφθείτε τον ιστότοπο της X.AI (https://x.ai).',
    grok_guide_step2: 'Συνδεθείτε στο λογαριασμό σας.',
    grok_guide_step3: 'Κάντε κλικ στο μενού API στην κορυφή.',
    grok_guide_step4: 'Κάντε κλικ στο κουμπί "Start building now".',
    grok_guide_step5: 'Κάντε κλικ στο μενού API Keys στα αριστερά.',
    grok_guide_step6: 'Δημιουργήστε το κλειδί API σας.',
    grok_guide_step7: 'Αντιγράψτε το κλειδί API που δημιουργήθηκε και επικολλήστε το στο παραπάνω πεδίο κλειδιού Grok API.',
    grok_guide_note1: '※ Το κλειδί API ξεκινά με τη μορφή xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'Επισκεφθείτε τον ιστότοπο του DeepL API (https://www.deepl.com/pro-api).',
    deepl_guide_step2: 'Κάντε κλικ στο κουμπί "Sign up for free".',
    deepl_guide_step3: 'Εισαγάγετε το email και τον κωδικό πρόσβασής σας για να δημιουργήσετε λογαριασμό.',
    deepl_guide_step4: 'Επιβεβαιώστε τη διεύθυνση email σας για να ενεργοποιήσετε το λογαριασμό.',
    deepl_guide_step5: 'Μετά τη σύνδεση, μεταβείτε στη διεύθυνση https://www.deepl.com/account/subscription.',
    deepl_guide_step6: 'Πηγαίνετε στο μενού API keys (https://www.deepl.com/account/keys).',
    deepl_guide_step7: 'Επικολλήστε το κλειδί API της δωρεάν έκδοσης στο παραπάνω πεδίο DeepL API Key (δωρεάν).',
    deepl_guide_step8: 'Επικολλήστε το κλειδί API της επί πληρωμή έκδοσης στο παραπάνω πεδίο DeepL API Key (επί πληρωμή).',
    deepl_guide_note1: '※ Η δωρεάν έκδοση του DeepL API επιτρέπει τη μετάφραση έως 500.000 χαρακτήρων ανά μήνα.',
    deepl_guide_note2: '※ Μεταβαίνοντας στην επί πληρωμή έκδοση μπορείτε να μεταφράσετε περισσότερο κείμενο.',
    deepl_guide_note3: '※ Σημείωση: Μετά τη μετάβαση στην επί πληρωμή έκδοση, δεν μπορούσα να χρησιμοποιήσω το δωρεάν API. Παρακαλώ λάβετε το υπόψη.',
    
    // DeepL API 도움말
    deepl_api_help_free: 'Για το δωρεάν κλειδί API πρέπει να χρησιμοποιήσετε το τελικό σημείο https://api-free.deepl.com.',
    deepl_api_help_pro: 'Για το επί πληρωμή κλειδί API πρέπει να χρησιμοποιήσετε το τελικό σημείο https://api.deepl.com.',
    deepl_api_help_error: 'Εάν λαμβάνετε το σφάλμα "Wrong endpoint. Use https://api.deepl.com" κατά τη χρήση του δωρεάν κλειδιού API:',
    deepl_api_help_check1: '1. Ελέγξτε ότι έχετε επιλέξει την επιλογή DeepL API (δωρεάν).',
    deepl_api_help_check2: '2. Ελέγξτε ότι χρησιμοποιείτε πραγματικά ένα δωρεάν κλειδί API.',
    
    // 영역 및 결과 관련
    original_text: 'Αρχικό κείμενο',
    translation: 'Μετάφραση',
    summary: 'Περίληψη',
    definition: 'Ορισμός',
    copy_original: 'Αντιγραφή πρωτοτύπου',
    copy_translation: 'Αντιγραφή μετάφρασης',
    copy_summary: 'Αντιγραφή περίληψης',
    copy_both: 'Αντιγραφή και των δύο',
    summarize_translation_result: 'Περίληψη αποτελέσματος μετάφρασης',
    debug_info: 'Πληροφορίες εντοπισμού σφαλμάτων',
    page_url: 'URL σελίδας',
    page_title: 'Τίτλος σελίδας',
    target_language: 'Γλώσσα-στόχος',
    request_prompt: 'Αίτημα προτροπής',
    api_response: 'Απάντηση API',
    clipboard_copy_failed: 'Η αντιγραφή στο πρόχειρο απέτυχε',
    
    // 알림 및 오류 메시지
    canceled: 'Ακυρώθηκε',
    translation_canceled: 'Η μετάφραση ακυρώθηκε.',
    summary_canceled: 'Η περίληψη ακυρώθηκε.',
    lookup_canceled: 'Η αναζήτηση όρου ακυρώθηκε.',
    operation_canceled: 'Η λειτουργία ακυρώθηκε.',
    api_key_error: 'Σφάλμα κλειδιού API',
    api_key_missing: 'Δεν έχει οριστεί κλειδί API. Παρακαλώ ορίστε το κλειδί API στις ρυθμίσεις της επέκτασης.',
    goto_settings: 'Μετάβαση στις ρυθμίσεις',
    error: 'Σφάλμα',
    translation_failed: 'Η μετάφραση απέτυχε:',
    summary_failed: 'Η περίληψη απέτυχε:',
    lookup_failed: 'Η αναζήτηση όρου απέτυχε:',
    no_response: 'Καμία απάντηση',
    
    // 로그 메시지
    menu_added: 'Το μενού προστέθηκε.',
    menu_add_error: 'Σφάλμα κατά την προσθήκη του μενού:',
    menu_removed: 'Το μενού μετάφρασης αφαιρέθηκε:',
    operation_applied: 'Η περιοχή είναι ήδη {operation}. Εμφάνιση προεπιλεγμένου μενού περιβάλλοντος.',
    already_has_operation: 'Η περιοχή έχει ήδη {operation}. Παράλειψη λειτουργίας.',
    rightclick_text: 'Κείμενο που επιλέχθηκε με δεξί κλικ:',
    ctrl_rightclick: 'Εντοπίστηκε Ctrl + δεξί κλικ: εκτέλεση περίληψης',
    normal_rightclick: 'Εντοπίστηκε κανονικό δεξί κλικ: εκτέλεση μετάφρασης',
    doubleclick_text: 'Κείμενο που επιλέχθηκε με διπλό κλικ:',
    hovered_element: 'Στοιχείο που επισημάνθηκε:',
    summary_response: 'Απάντηση περίληψης:',
    range_undefined: 'Το εύρος δεν έχει οριστεί.',
    inline_translation_insertion_error: 'Σφάλμα εισαγωγής ενσωματωμένης μετάφρασης:',
    inline_summary_insertion_error: 'Σφάλμα εισαγωγής ενσωματωμένης περίληψης:',
    fallback_insertion_error: 'Σφάλμα εισαγωγής εφεδρικής λύσης:',
    copy_failed: 'Η αντιγραφή απέτυχε:',
    
    // 도메인 컨텍스트
    domain_programming: 'Προγραμματισμός/Ανάπτυξη λογισμικού',
    domain_blog: 'Ιστολόγιο/Τεχνικά άρθρα',
    domain_qa: 'Προγραμματισμός Ε&Α',
    domain_docs: 'Τεχνική τεκμηρίωση/Τεκμηρίωση API',
    domain_academic: 'Ακαδημαϊκό/Έρευνα',
    domain_news: 'Ειδήσεις/Επικαιρότητα',
    domain_finance: 'Οικονομικά/Επενδύσεις',
    domain_medical: 'Ιατρικό/Υγεία',
    domain_legal: 'Νομικό',
    domain_webpage: 'Τίτλος ιστοσελίδας:',
    
    // 초기화 메시지
    extension_init: 'Αρχικοποίηση επέκτασης μετάφρασης...',
    listeners_registered: 'Οι ακροατές συμβάντων καταχωρήθηκαν.',
    doubleclick_registered: 'Ο ακροατής διπλού κλικ καταχωρήθηκε.',
    extension_ready: 'Η επέκταση μετάφρασης είναι έτοιμη.'

    //filePanel.js
    ,fileListWillBeShownHere: 'Η λίστα των αρχείων θα εμφανιστεί εδώ.'

    //subtitleService.js
    ,subtitle_translation_enabled: 'Η μετάφραση υποτίτλων σε πραγματικό χρόνο ενεργοποιήθηκε.'
    ,subtitle_translation_disabled: 'Η μετάφραση υποτίτλων σε πραγματικό χρόνο απενεργοποιήθηκε.'
    ,subtitle_translation_button: 'Μετάφραση υποτίτλων σε πραγματικό χρόνο'
    ,runtime_not_initialized: 'Το Chrome runtime δεν έχει αρχικοποιηθεί.'
    ,message_send_error: 'Σφάλμα κατά την αποστολή μηνύματος:'
    ,translation_response_missing: 'Δεν υπάρχει απάντηση μετάφρασης.'
    ,translation_error: 'Σφάλμα μετάφρασης υποτίτλων:'
};

export default el; 