// content.js
// FilePanel, TranslationService, SubtitleService 클래스는 각각 별도 파일로 정의되어 전역 변수로 노출됨

// 전역 변수
let translationService = null;
let subtitleService = null;
let filePanel = null;

// 초기화 함수
function initializeExtension() {
    console.log('번역 확장 프로그램 초기화 중...');
    
    // TranslationService 인스턴스 생성
    try {
        if (window.TranslationService) {
            translationService = new window.TranslationService();
            console.log('번역 서비스가 초기화되었습니다.');
        } else {
            console.error('TranslationService 클래스를 찾을 수 없습니다.');
        }
    } catch (error) {
        console.error('번역 서비스 초기화 중 오류 발생:', error);
    }
    
    // SubtitleService 인스턴스 생성
    try {
        if (window.SubtitleService) {
            subtitleService = new window.SubtitleService();
            console.log('자막 서비스가 초기화되었습니다.');
        } else {
            console.error('SubtitleService 클래스를 찾을 수 없습니다.');
        }
    } catch (error) {
        console.error('자막 서비스 초기화 중 오류 발생:', error);
    }
    
    // FilePanel 인스턴스 생성
    try {
        if (window.FilePanel) {
            filePanel = new window.FilePanel();
            console.log('파일 패널이 초기화되었습니다.');
            
            // 상태 정보 업데이트를 약간 지연시킴
            setTimeout(() => {
                // 상태 정보 업데이트
                filePanel.addTitle('번역 확장 기능 상태');
                filePanel.addDivider();
                filePanel.addText('번역 서비스: ' + (translationService ? '활성화' : '비활성화'));
                filePanel.addText('자막 서비스: ' + (subtitleService ? '활성화' : '비활성화'));
            }, 100);
        } else {
            console.error('FilePanel 클래스를 찾을 수 없습니다.');
        }
    } catch (error) {
        console.error('파일 패널 초기화 중 오류 발생:', error);
    }
    
    console.log('번역 확장 프로그램이 준비되었습니다.');
}

// 페이지 로드 시 초기화
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    initializeExtension();
} else {
    document.addEventListener('DOMContentLoaded', initializeExtension);
}

// 번역 메뉴 확장을 위한 원본 함수 재정의
if (window.TranslationService && window.TranslationService.prototype) {
    const originalShowTranslateMenu = window.TranslationService.prototype.showTranslateMenu;
    
    if (originalShowTranslateMenu) {
        window.TranslationService.prototype.showTranslateMenu = async function(event, hasImages) {
            // 원래 함수 호출
            await originalShowTranslateMenu.call(this, event, hasImages);
            
            // 메뉴 컨테이너 찾기
            const menuContainer = document.querySelector('.translate-ui.translate-menu');
            if (menuContainer && subtitleService) {
                const divider = document.createElement('div');
                divider.style.borderTop = '1px solid #ddd';
                divider.style.margin = '10px 0';
                menuContainer.appendChild(divider);
                
                // 자막 번역 버튼 추가
                subtitleService.addSubtitleTranslationButton(menuContainer);
            }
        };
    }
}