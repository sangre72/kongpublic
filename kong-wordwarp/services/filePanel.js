// filePanel.js
// 전역 변수로 FilePanel 클래스 노출
window.FilePanel = class {
    constructor() {
        this.isPanelOpen = false;
        this.isEnabled = false;
        this.init();
    }

    init() {
        // ★a_3772 fix: document.body 미준비 시점에 init 되면 createFileButton의
        //   document.body.appendChild가 "Cannot read properties of undefined" throw("오류" 배지 원인).
        //   body 준비될 때까지 대기 후 초기화.
        if (!document.body) {
            document.addEventListener('DOMContentLoaded', () => this.init(), { once: true });
            return;
        }
        this.addStyles();
        this.createFileButton();
        this.createSidePanel();
        this.setupEventListeners();
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .file-button {
                display: none; /* 파일 버튼 숨기기 */
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999998;
                padding: 12px 24px;
                background-color: #6B4EFF;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }

            .file-button:hover {
                background-color: #5B3EEF;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }

            .side-panel {
                position: fixed;
                top: 0;
                right: -200px;
                width: 200px;
                height: 100vh;
                background-color: white;
                box-shadow: -2px 0 8px rgba(0,0,0,0.1);
                z-index: 9999999;
                transition: right 0.3s ease;
                padding: 20px;
                box-sizing: border-box;
            }

            .side-panel.open {
                right: 0;
            }

            .side-panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }

            .close-button {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #666;
                padding: 4px;
            }

            .close-button:hover {
                color: #333;
            }
        `;
        document.head.appendChild(style);
    }

    createFileButton() {
        this.fileButton = document.createElement('button');
        this.fileButton.className = 'file-button';
        this.fileButton.textContent = 'File';
        document.body.appendChild(this.fileButton);
    }

    createSidePanel() {
        this.sidePanel = document.createElement('div');
        this.sidePanel.className = 'side-panel';
        
        // 패널 헤더
        const header = document.createElement('div');
        header.className = 'side-panel-header';
        
        const title = document.createElement('h3');
        title.textContent = '파일';
        title.style.margin = '0';
        title.style.color = '#333';
        
        this.closeButton = document.createElement('button');
        this.closeButton.className = 'close-button';
        this.closeButton.innerHTML = '×';
        
        header.appendChild(title);
        header.appendChild(this.closeButton);
        this.sidePanel.appendChild(header);

        // 활성화 상태 체크박스 추가
        const { container: checkboxContainer } = this.addCheckbox(
            '번역 기능 활성화',
            this.isEnabled,
            (checked) => {
                this.isEnabled = checked;
                this.updateMouseWheelHandler();
                // 번역 서비스 상태 업데이트
                if (window.translationService) {
                    window.translationService.setEnabled(checked);
                }
                // 자막 서비스 상태 업데이트
                if (window.subtitleService) {
                    window.subtitleService.setEnabled(checked);
                }
            },
            {
                margin: '15px 0',
                padding: '0 15px'
            }
        );
        this.sidePanel.appendChild(checkboxContainer);

        // 패널 컨텐츠 컨테이너
        this.contentContainer = document.createElement('div');
        this.contentContainer.className = 'panel-content';
        this.contentContainer.innerHTML = `
            <div style="color: #666;">
                <p data-i18n="fileListWillBeShownHere">파일 목록이 여기에 표시됩니다.</p>
            </div>
        `;
        this.sidePanel.appendChild(this.contentContainer);

        document.body.appendChild(this.sidePanel);
    }

    setupEventListeners() {
        // 파일 버튼 클릭 이벤트
        this.fileButton.addEventListener('click', () => {
            this.togglePanel();
        });

        // 닫기 버튼 이벤트
        this.closeButton.addEventListener('click', () => {
            this.closePanel();
        });

        // ESC 키 이벤트
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isPanelOpen) {
                this.closePanel();
            }
        });

        // 패널 외부 클릭 이벤트
        document.addEventListener('click', (e) => {
            if (this.isPanelOpen && 
                !this.sidePanel.contains(e.target) && 
                !this.fileButton.contains(e.target)) {
                this.closePanel();
            }
        });
    }

    togglePanel() {
        this.isPanelOpen = !this.isPanelOpen;
        this.sidePanel.classList.toggle('open');
    }

    closePanel() {
        this.isPanelOpen = false;
        this.sidePanel.classList.remove('open');
    }

    // 패널 내용 업데이트 메서드
    updateContent(content) {
        if (this.contentContainer) {
            this.contentContainer.innerHTML = content;
        }
    }

    // 패널 내용 초기화 메서드
    clearContent() {
        if (this.contentContainer) {
            this.contentContainer.innerHTML = '';
        }
    }

    // 일반 엘리먼트 추가 메서드
    addElement(tagName, attributes = {}, innerHTML = '', styles = {}) {
        const element = document.createElement(tagName);
        
        // 속성 설정
        for (const [key, value] of Object.entries(attributes)) {
            element.setAttribute(key, value);
        }
        
        // 내용 설정
        if (innerHTML) {
            element.innerHTML = innerHTML;
        }
        
        // 스타일 설정
        for (const [key, value] of Object.entries(styles)) {
            element.style[key] = value;
        }
        
        this.contentContainer.appendChild(element);
        return element;
    }

    // 버튼 추가 메서드
    addButton(text, onClick, styles = {}) {
        const defaultStyles = {
            margin: '5px 0',
            padding: '8px 16px',
            backgroundColor: '#6B4EFF',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
            width: '100%',
            textAlign: 'center'
        };
        
        const mergedStyles = {...defaultStyles, ...styles};
        
        const button = this.addElement('button', {}, text, mergedStyles);
        button.addEventListener('click', onClick);
        
        return button;
    }

    // 목록 추가 메서드
    addList(items = [], onClick = null, styles = {}) {
        const ul = this.addElement('ul', {}, '', {
            listStyleType: 'none',
            padding: '0',
            margin: '10px 0',
            ...styles
        });
        
        items.forEach((item, index) => {
            const li = document.createElement('li');
            li.innerHTML = item;
            li.style.padding = '8px 0';
            li.style.borderBottom = index < items.length - 1 ? '1px solid #eee' : 'none';
            li.style.cursor = onClick ? 'pointer' : 'default';
            
            if (onClick) {
                li.addEventListener('click', () => onClick(item, index));
            }
            
            ul.appendChild(li);
        });
        
        return ul;
    }

    // 입력 필드 추가 메서드
    addInput(placeholder = '', onChange = null, styles = {}) {
        const input = this.addElement('input', {
            type: 'text',
            placeholder
        }, '', {
            width: '100%',
            padding: '8px',
            margin: '5px 0',
            boxSizing: 'border-box',
            border: '1px solid #ddd',
            borderRadius: '4px',
            ...styles
        });
        
        if (onChange) {
            input.addEventListener('input', (e) => onChange(e.target.value));
        }
        
        return input;
    }

    // 구분선 추가 메서드
    addDivider(styles = {}) {
        if (this.contentContainer) {
            const divider = document.createElement('div');
            divider.style.borderTop = '1px solid #eee';
            divider.style.margin = '10px 0';
            Object.assign(divider.style, styles);
            this.contentContainer.appendChild(divider);
        }
    }
    
    // 제목 추가 메서드
    addTitle(text) {
        if (this.contentContainer) {
            const title = document.createElement('h4');
            title.textContent = text;
            title.style.margin = '10px 0';
            title.style.color = '#333';
            this.contentContainer.appendChild(title);
        }
    }

    // 텍스트 추가 메서드
    addText(text) {
        if (this.contentContainer) {
            const textElement = document.createElement('p');
            textElement.textContent = text;
            textElement.style.margin = '5px 0';
            textElement.style.color = '#666';
            this.contentContainer.appendChild(textElement);
        }
    }
    
    // 체크박스 추가 메서드
    addCheckbox(label, checked = false, onChange = null, styles = {}) {
        const container = this.addElement('div', {}, '', {
            display: 'flex',
            alignItems: 'center',
            margin: '8px 0',
            ...styles
        });
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = checked;
        checkbox.style.margin = '0 8px 0 0';
        
        if (onChange) {
            checkbox.addEventListener('change', (e) => onChange(e.target.checked));
        }
        
        const labelElement = document.createElement('label');
        labelElement.textContent = label;
        labelElement.style.cursor = 'pointer';
        labelElement.style.fontSize = '14px';
        
        labelElement.addEventListener('click', () => {
            checkbox.checked = !checkbox.checked;
            if (onChange) {
                onChange(checkbox.checked);
            }
        });
        
        container.appendChild(checkbox);
        container.appendChild(labelElement);
        
        return { container, checkbox, label: labelElement };
    }

    updateMouseWheelHandler() {
        // 체크박스 상태 업데이트
        const checkbox = this.sidePanel.querySelector('input[type="checkbox"]');
        if (checkbox) {
            checkbox.checked = this.isEnabled;
        }
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'translate-ui notification';
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '10%';
        notification.style.left = '50%';
        notification.style.transform = 'translateX(-50%)';
        notification.style.background = 'rgba(0, 0, 0, 0.8)';
        notification.style.color = 'white';
        notification.style.padding = '10px 20px';
        notification.style.borderRadius = '5px';
        notification.style.zIndex = '9999999';
        notification.style.fontSize = '16px';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
};