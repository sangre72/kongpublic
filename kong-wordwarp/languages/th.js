// 태국어 (Thai) 언어 파일

const th = {
    // 메뉴 및 UI 관련
    translate: 'แปล',
    summarize: 'สรุป',
    lookup: 'ค้นหาคำศัพท์',
    cancel: 'ยกเลิก',
    copy: 'คัดลอก',
    copied: 'คัดลอกแล้ว',
    close: 'ปิด',
    translating: 'กำลังแปล...',
    summarizing: 'กำลังสรุป...',
    looking_up: 'กำลังค้นหา...',
    cancel_with_esc: '(ESC เพื่อยกเลิก)',
    image_text_recognition: 'การรู้จำตัวอักษรจากภาพ',
    menu_addition_error: 'ข้อผิดพลาดในการเพิ่มเมนู:',
    summary_result: 'ผลการสรุป',
    copy_term_definition: 'คัดลอกคำจำกัดความของคำ',
    
    //options.js
    deepl_free_api_key_error: 'คีย์ API ไม่ถูกต้อง กรุณาตรวจสอบคีย์ API',
    deepl_free_api_key_warning: 'คำเตือน: ดูเหมือนว่านี่ไม่ใช่คีย์ API DeepL กรุณาป้อนคีย์ API DeepL แบบฟรีที่ถูกต้อง',
    deepl_pro_api_key_warning: 'คำเตือน: ดูเหมือนว่านี่ไม่ใช่คีย์ API DeepL กรุณาป้อนคีย์ API DeepL แบบเสียเงินที่ถูกต้อง',
    settings_save_error: 'เกิดข้อผิดพลาดในการบันทึกการตั้งค่า กรุณาลองอีกครั้ง',
    saved_all_settings: 'การตั้งค่าทั้งหมดที่บันทึกไว้:',
    
    // 옵션 페이지 관련
    options_title: 'การตั้งค่าส่วนขยายการแปล',
    service_selection: 'เลือกบริการแปล',
    api_key: 'คีย์ API',
    model_selection: 'เลือกโมเดล',
    api_url: 'URL API (ไม่บังคับ)',
    api_key_free: 'คีย์ API (ฟรี)',
    api_key_pro: 'คีย์ API (เสียเงิน)',
    interface_language: 'ภาษาส่วนติดต่อผู้ใช้',
    interface_language_desc: 'เมนูและข้อความของส่วนขยายจะแสดงในภาษาที่เลือก',
    preferred_languages: 'ภาษาที่ต้องการ (เลือกได้เพียงหนึ่งภาษา)',
    save: 'บันทึก',
    settings_saved: 'บันทึกการตั้งค่าแล้ว',
    
    // 디버그 모드
    debug_mode: 'เปิดใช้งานโหมดดีบัก (สำหรับการแก้ไขปัญหา)',
    debug_mode_desc: 'เมื่อเปิดใช้งานโหมดดีบัก ข้อความแสดงข้อผิดพลาดและข้อมูลการสื่อสาร API จะแสดงในคอนโซลของเบราว์เซอร์',
    api_guide_title: 'คู่มือการลงทะเบียน API',
    claude_api_guide_title: 'การลงทะเบียนและสร้างคีย์ Claude API',
    chatgpt_api_guide_title: 'การลงทะเบียนและสร้างคีย์ ChatGPT API',
    grok_api_guide_title: 'การลงทะเบียนและสร้างคีย์ Grok API',
    deepl_api_guide_title: 'การลงทะเบียนและสร้างคีย์ DeepL API',
    deepl_api_help_title: 'หมายเหตุเกี่ยวกับการใช้ DeepL API',
    
    // Claude API 가이드
    claude_guide_step1: 'เยี่ยมชมเว็บไซต์ Anthropic (https://www.anthropic.com/api)',
    claude_guide_step2: 'คลิกปุ่ม "Sign up" ที่มุมขวาบน',
    claude_guide_step3: 'ป้อนอีเมลและรหัสผ่านของคุณเพื่อสร้างบัญชี',
    claude_guide_step4: 'หลังจากเข้าสู่ระบบ ไปที่แท็บ "API Keys"',
    claude_guide_step5: 'คลิกปุ่ม "Create API Key"',
    claude_guide_step6: 'ตั้งชื่อคีย์และสร้าง',
    claude_guide_step7: 'คัดลอกคีย์ API ที่สร้างขึ้นและวางในช่องคีย์ Claude API ด้านบน',
    claude_guide_note1: '※ Claude API ต้องการการลงทะเบียนบัตรเครดิต การใช้งานมีค่าใช้จ่าย',
    claude_guide_note2: '※ คีย์ API จะขึ้นต้นด้วยรูปแบบ sk-ant-api03-...',
    
    // ChatGPT API 가이드
    chatgpt_guide_step1: 'เยี่ยมชมเว็บไซต์ OpenAI (https://platform.openai.com/signup)',
    chatgpt_guide_step2: 'คลิกปุ่ม "Sign up" เพื่อสร้างบัญชี',
    chatgpt_guide_step3: 'ยืนยันที่อยู่อีเมลของคุณ',
    chatgpt_guide_step4: 'หลังจากเข้าสู่ระบบ คลิก Dashboard ข้างรูปโปรไฟล์ของคุณและเลือก "API keys" จากเมนูด้านซ้าย',
    chatgpt_guide_step5: 'คลิกปุ่ม "Create new secret key"',
    chatgpt_guide_step6: 'ตั้งชื่อคีย์และสร้าง',
    chatgpt_guide_step7: 'คัดลอกคีย์ API ที่สร้างขึ้นและวางในช่องคีย์ ChatGPT API ด้านบน',
    chatgpt_guide_note1: '※ OpenAI API ต้องการการลงทะเบียนบัตรเครดิต การใช้งานมีค่าใช้จ่าย',
    chatgpt_guide_note2: '※ คีย์ API จะขึ้นต้นด้วยรูปแบบ sk-...',
    
    // Grok API 가이드
    grok_guide_step1: 'เยี่ยมชมเว็บไซต์ X.AI (https://x.ai)',
    grok_guide_step2: 'เข้าสู่ระบบบัญชีของคุณ',
    grok_guide_step3: 'คลิกเมนู API ที่ด้านบน',
    grok_guide_step4: 'คลิกปุ่ม "Start building now"',
    grok_guide_step5: 'คลิกเมนู API Keys ที่ด้านซ้าย',
    grok_guide_step6: 'สร้างคีย์ API ของคุณ',
    grok_guide_step7: 'คัดลอกคีย์ API ที่สร้างขึ้นและวางในช่องคีย์ Grok API ด้านบน',
    grok_guide_note1: '※ คีย์ API จะขึ้นต้นด้วยรูปแบบ xai-...',
    
    // DeepL API 가이드
    deepl_guide_step1: 'เยี่ยมชมเว็บไซต์ DeepL API (https://www.deepl.com/pro-api)',
    deepl_guide_step2: 'คลิกปุ่ม "Sign up for free"',
    deepl_guide_step3: 'ป้อนอีเมลและรหัสผ่านของคุณเพื่อสร้างบัญชี',
    deepl_guide_step4: 'ยืนยันที่อยู่อีเมลของคุณเพื่อเปิดใช้งานบัญชี',
    deepl_guide_step5: 'หลังจากเข้าสู่ระบบ ไปที่ https://www.deepl.com/account/subscription',
    deepl_guide_step6: 'ไปที่เมนู API keys (https://www.deepl.com/account/keys)',
    deepl_guide_step7: 'วางคีย์ API สำหรับเวอร์ชันฟรีในช่อง DeepL API Key (ฟรี) ด้านบน',
    deepl_guide_step8: 'วางคีย์ API สำหรับเวอร์ชันเสียเงินในช่อง DeepL API Key (เสียเงิน) ด้านบน',
    deepl_guide_note1: '※ เวอร์ชันฟรีของ DeepL API อนุญาตให้แปลได้สูงสุด 500,000 ตัวอักษรต่อเดือน',
    deepl_guide_note2: '※ เมื่ออัพเกรดเป็นเวอร์ชันเสียเงิน คุณสามารถแปลข้อความได้มากขึ้น',
    deepl_guide_note3: '※ หมายเหตุ: หลังจากอัพเกรดเป็นเวอร์ชันเสียเงิน ฉันไม่สามารถใช้ API ฟรีได้ โปรดทราบเรื่องนี้',
    
    // DeepL API 도움말
    deepl_api_help_free: 'สำหรับคีย์ API ฟรี ใช้ endpoint https://api-free.deepl.com',
    deepl_api_help_pro: 'สำหรับคีย์ API เสียเงิน ใช้ endpoint https://api.deepl.com',
    deepl_api_help_error: 'หากคุณได้รับข้อผิดพลาด "Wrong endpoint. Use https://api.deepl.com" เมื่อใช้คีย์ API ฟรี:',
    deepl_api_help_check1: '1. ตรวจสอบว่าคุณได้เลือกตัวเลือก DeepL API (ฟรี)',
    deepl_api_help_check2: '2. ตรวจสอบว่าคุณกำลังใช้คีย์ API ฟรีจริงๆ',
    
    // 영역 및 결과 관련
    original_text: 'ข้อความต้นฉบับ',
    translation: 'การแปล',
    summary: 'สรุป',
    definition: 'คำจำกัดความ',
    copy_original: 'คัดลอกต้นฉบับ',
    copy_translation: 'คัดลอกการแปล',
    copy_summary: 'คัดลอกสรุป',
    copy_both: 'คัดลอกทั้งคู่',
    summarize_translation_result: 'สรุปผลการแปล',
    debug_info: 'ข้อมูลการดีบัก',
    page_url: 'URL ของหน้า',
    page_title: 'ชื่อหน้า',
    target_language: 'ภาษาเป้าหมาย',
    request_prompt: 'คำขอ prompt',
    api_response: 'การตอบสนอง API',
    clipboard_copy_failed: 'ไม่สามารถคัดลอกไปยังคลิปบอร์ด',
    
    // 알림 및 오류 메시지
    canceled: 'ยกเลิกแล้ว',
    translation_canceled: 'ยกเลิกการแปลแล้ว',
    summary_canceled: 'ยกเลิกการสรุปแล้ว',
    lookup_canceled: 'ยกเลิกการค้นหาแล้ว',
    operation_canceled: 'ยกเลิกการดำเนินการแล้ว',
    api_key_error: 'ข้อผิดพลาดคีย์ API',
    api_key_missing: 'ไม่ได้กำหนดค่าคีย์ API โปรดกำหนดค่าคีย์ API ในการตั้งค่าส่วนขยาย',
    goto_settings: 'ไปที่การตั้งค่า',
    error: 'ข้อผิดพลาด',
    translation_failed: 'การแปลล้มเหลว:',
    summary_failed: 'การสรุปล้มเหลว:',
    lookup_failed: 'การค้นหาล้มเหลว:',
    no_response: 'ไม่มีการตอบสนอง',
    
    // 로그 메시지
    menu_added: 'เพิ่มเมนูแล้ว',
    menu_add_error: 'ข้อผิดพลาดในการเพิ่มเมนู:',
    menu_removed: 'ลบเมนูการแปลแล้ว:',
    operation_applied: 'พื้นที่นี้มี {operation} อยู่แล้ว แสดงเมนูบริบทเริ่มต้น',
    already_has_operation: 'พื้นที่นี้มี {operation} อยู่แล้ว ข้ามการดำเนินการ',
    rightclick_text: 'ข้อความที่เลือกด้วยคลิกขวา:',
    ctrl_rightclick: 'ตรวจพบ Ctrl + คลิกขวา: กำลังทำการสรุป',
    normal_rightclick: 'ตรวจพบคลิกขวาปกติ: กำลังทำการแปล',
    doubleclick_text: 'ข้อความที่เลือกด้วยดับเบิลคลิก:',
    hovered_element: 'องค์ประกอบที่เมาส์ชี้:',
    summary_response: 'การตอบสนองการสรุป:',
    range_undefined: 'ช่วงไม่ได้กำหนด',
    inline_translation_insertion_error: 'ข้อผิดพลาดในการแทรกการแปลแบบอินไลน์:',
    inline_summary_insertion_error: 'ข้อผิดพลาดในการแทรกสรุปแบบอินไลน์:',
    fallback_insertion_error: 'ข้อผิดพลาดในการแทรกการสำรอง:',
    copy_failed: 'การคัดลอกล้มเหลว:',
    
    // 도메인 컨텍스트
    domain_programming: 'การเขียนโปรแกรม/การพัฒนาซอฟต์แวร์',
    domain_blog: 'บล็อก/บทความทางเทคนิค',
    domain_qa: 'คำถามและคำตอบเกี่ยวกับการเขียนโปรแกรม',
    domain_docs: 'เอกสารทางเทคนิค/เอกสาร API',
    domain_academic: 'วิชาการ/การวิจัย',
    domain_news: 'ข่าว/เหตุการณ์ปัจจุบัน',
    domain_finance: 'การเงิน/การลงทุน',
    domain_medical: 'การแพทย์/สุขภาพ',
    domain_legal: 'กฎหมาย',
    domain_webpage: 'ชื่อหน้าเว็บ:',
    
    // 초기화 메시지
    extension_init: 'กำลังเริ่มต้นส่วนขยายการแปล...',
    listeners_registered: 'ลงทะเบียนตัวรับฟังเหตุการณ์แล้ว',
    doubleclick_registered: 'ลงทะเบียนตัวรับฟังดับเบิลคลิกแล้ว',
    extension_ready: 'ส่วนขยายการแปลพร้อมใช้งานแล้ว'

    //filePanel.js
    ,fileListWillBeShownHere: 'รายการไฟล์จะแสดงที่นี่'

    //subtitleService.js
    ,subtitle_translation_enabled: 'เปิดใช้งานการแปลคำบรรยายแบบเรียลไทม์แล้ว'
    ,subtitle_translation_disabled: 'ปิดใช้งานการแปลคำบรรยายแบบเรียลไทม์แล้ว'
    ,subtitle_translation_button: 'การแปลคำบรรยายแบบเรียลไทม์'
    ,runtime_not_initialized: 'ยังไม่ได้เริ่มต้น Chrome Runtime'
    ,message_send_error: 'เกิดข้อผิดพลาดในการส่งข้อความ:'
    ,translation_response_missing: 'ไม่มีการตอบสนองการแปล'
    ,translation_error: 'ข้อผิดพลาดในการแปลคำบรรยาย:'
};

export default th;