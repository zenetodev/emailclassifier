class EmailClassifier {
    constructor() {
        this.apiUrl = '/api/classificar';
        this.uploadApiUrl = '/api/upload';
        this.isProcessing = false;
        this.classificationHistory = [];
        this.settings = {
            autoClassify: false,
            responseStyle: 'professional',
            apiUrl: this.apiUrl
        };
        
        this.init();
    }

    init() {
        console.log('🚀 Inicializando EmailClassifier AI...');
        
        this.detectEnvironment();
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupApplication();
            });
        } else {
            this.setupApplication();
        }
    }

    detectEnvironment() {
        const isLocalhost = window.location.hostname === 'localhost' || 
                           window.location.hostname === '127.0.0.1';
        
        if (isLocalhost) {
            this.apiUrl = 'http://localhost:5000/api/classificar';
            this.uploadApiUrl = 'http://localhost:5000/api/upload';
            console.log('🔧 Modo: Desenvolvimento Local');
        } else {
            this.apiUrl = '/api/classificar';
            this.uploadApiUrl = '/api/upload';
            console.log('🌐 Modo: Produção');
        }
        
        this.settings.apiUrl = this.apiUrl;
    }

    setupApplication() {
        try {
            this.bindEvents();
            this.setupFileUpload();
            this.loadSettings();
            this.setupExamples();
            this.updateCharCount(0);
            
            console.log('✅ Aplicação inicializada com sucesso');
            console.log('📡 API URL:', this.apiUrl);
        } catch (error) {
            console.error('❌ Erro na inicialização:', error);
            this.showNotification('Erro na inicialização da aplicação', 'error');
        }
    }

    bindEvents() {
        this.safeAddEventListener('classifyBtn', 'click', () => this.classifyMessage());
        
        this.safeAddEventListener('clearBtn', 'click', () => this.clearForm());
        
        this.safeAddEventListener('copyResponseBtn', 'click', () => this.copyResponse());
        
        const textarea = document.getElementById('emailText');
        if (textarea) {
            textarea.addEventListener('input', (e) => {
                this.updateCharCount(e.target.value.length);
                if (this.settings.autoClassify && e.target.value.length > 50) {
                    this.debouncedClassify();
                }
            });
            
            textarea.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    this.classifyMessage();
                }
            });
            
            textarea.addEventListener('paste', (e) => {
                setTimeout(() => {
                    this.updateCharCount(e.target.value.length);
                }, 100);
            });
        }
        
        this.debouncedClassify = this.debounce(() => {
            if (!this.isProcessing) {
                this.classifyMessage();
            }
        }, 1000);
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileTab = document.querySelector('[data-tab="file"]');
        const textTab = document.querySelector('[data-tab="text"]');

        if (fileTab && textTab) {
            fileTab.addEventListener('click', () => this.switchTab('file'));
            textTab.addEventListener('click', () => this.switchTab('text'));
        }

        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('active');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('active');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('active');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });

            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0]);
                }
            });
        }
    }

    switchTab(tabName) {
        document.querySelectorAll('.upload-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}Tab`);
        });

        if (tabName === 'text') {
            const textarea = document.getElementById('emailText');
            if (textarea) {
                textarea.focus();
            }
        }
    }

    async handleFileSelect(file) {
        console.log('📁 Arquivo selecionado:', file.name);
        
        const validTypes = ['text/plain', 'application/pdf'];
        const validExtensions = ['.txt', '.pdf'];
        const fileExtension = file.name.toLowerCase().slice(-4);
        
        if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
            this.showNotification('Formato não suportado. Use .txt ou .pdf', 'error');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            this.showNotification('Arquivo muito grande. Máximo: 5MB', 'error');
            return;
        }

        try {
            this.showNotification('Processando arquivo...', 'info');
            
            if (file.size < 102400) { 
                const content = await this.readFileContent(file);
                this.displayFilePreview(file, content);
                
                const textarea = document.getElementById('emailText');
                if (textarea) {
                    textarea.value = content;
                    this.updateCharCount(content.length);
                }
                
                this.showNotification('Arquivo carregado com sucesso!', 'success');
            } else {
                await this.uploadFileToServer(file);
            }
            
        } catch (error) {
            console.error('❌ Erro ao processar arquivo:', error);
            this.showNotification('Erro ao processar arquivo: ' + error.message, 'error');
        }
    }

    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                resolve(e.target.result);
            };
            
            reader.onerror = () => {
                reject(new Error('Falha ao ler arquivo'));
            };
            
            if (file.type === 'application/pdf') {
                this.showNotification('PDF detectado. Use o upload para processamento completo.', 'info');
                resolve(`[Arquivo PDF: ${file.name}]\n\nPara melhor processamento de PDF, use o upload diretamente para o servidor.`);
            } else {
                reader.readAsText(file, 'UTF-8');
            }
        });
    }

    async uploadFileToServer(file) {
        this.showLoading(true);
        
        try {
            const formData = new FormData();
            formData.append('file', file);

            console.log('📤 Enviando arquivo para:', this.uploadApiUrl);

            const response = await fetch(this.uploadApiUrl, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Erro ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            this.displayResults(data, 0);
            this.showNotification('Arquivo processado com sucesso!', 'success');
            
        } catch (error) {
            console.error('❌ Erro no upload:', error);
            
            let userMessage = error.message;
            if (error.message.includes('Failed to fetch')) {
                userMessage = 'Serviço de upload indisponível. Tente colar o texto diretamente.';
            }
            
            this.showNotification(`Erro no upload: ${userMessage}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayFilePreview(file, content) {
        const filePreview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const fileContentPreview = document.getElementById('fileContentPreview');
        
        if (filePreview && fileName && fileSize && fileContentPreview) {
            fileName.textContent = file.name;
            fileSize.textContent = this.formatFileSize(file.size);
            
            const previewContent = content.length > 1000 
                ? content.substring(0, 1000) + '...' 
                : content;
            fileContentPreview.textContent = previewContent;
            
            filePreview.style.display = 'block';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    clearFile() {
        const filePreview = document.getElementById('filePreview');
        const fileInput = document.getElementById('fileInput');
        const textarea = document.getElementById('emailText');
        
        if (filePreview) filePreview.style.display = 'none';
        if (fileInput) fileInput.value = '';
        if (textarea) textarea.value = '';
        
        this.updateCharCount(0);
        this.showNotification('Arquivo removido', 'info');
    }

    async classifyMessage() {
        if (this.isProcessing) {
            this.showNotification('Já existe uma análise em andamento...', 'warning');
            return;
        }

        const text = this.getTextareaValue();
        
        if (!this.validateInput(text)) {
            return;
        }

        this.setProcessingState(true);
        this.showLoading(true);
        const startTime = performance.now();

        try {
            console.log('📨 Enviando mensagem para análise...');
            console.log('🔗 Usando endpoint:', this.settings.apiUrl);
            
            const response = await fetch(this.settings.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    texto: text
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Erro HTTP:', response.status, errorText);
                throw new Error(`Erro ${response.status} no servidor: ${errorText}`);
            }

            const data = await response.json();
            const processingTime = Math.round(performance.now() - startTime);

            this.addToHistory(data, text, processingTime);
            this.displayResults(data, processingTime);
            this.showNotification('Mensagem classificada com sucesso!', 'success');
            
            console.log('✅ Análise concluída:', data);

        } catch (error) {
            console.error('❌ Erro na classificação:', error);
            
            let userMessage = error.message;
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                userMessage = 'Erro de conexão. Verifique se o servidor está rodando.';
            }
            
            this.showNotification(`Erro: ${userMessage}`, 'error');
            this.displayError(error.message);
        } finally {
            this.setProcessingState(false);
            this.showLoading(false);
        }
    }

    validateInput(text) {
        if (!text || text.trim().length === 0) {
            this.showNotification('Por favor, insira o conteúdo da mensagem', 'warning');
            return false;
        }

        if (text.trim().length < 10) {
            this.showNotification('A mensagem parece muito curta. Insira pelo menos 10 caracteres.', 'warning');
            return false;
        }

        if (text.trim().length > 10000) {
            this.showNotification('A mensagem é muito longa. Limite: 10.000 caracteres.', 'warning');
            return false;
        }

        return true;
    }

    setProcessingState(processing) {
        this.isProcessing = processing;
        const button = document.getElementById('classifyBtn');

        if (button) {
            if (processing) {
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analisando...';
                button.disabled = true;
                button.classList.add('processing');
            } else {
                button.innerHTML = '<i class="fas fa-rocket"></i> Classificar Mensagem';
                button.disabled = false;
                button.classList.remove('processing');
            }
        }
    }

    showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    displayResults(data, processingTime) {
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) {
            console.error('❌ Seção de resultados não encontrada');
            return;
        }

        try {
            this.updateCategoryBadge(data);
            this.updateResponse(data);
            this.updateDetails(data, processingTime);
            
            resultsSection.classList.add('active');
            
            setTimeout(() => {
                resultsSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start',
                    inline: 'nearest'
                });
            }, 300);
            
        } catch (error) {
            console.error('❌ Erro ao exibir resultados:', error);
            this.showNotification('Erro ao processar resultados', 'error');
        }
    }

    updateCategoryBadge(data) {
        const categoryBadge = document.getElementById('categoryBadge');
        if (!categoryBadge) return;

        const isProductive = data.categoria === 'Produtivo';
        const confidence = data.confianca || 0.5;
        
        let confidenceClass = 'confidence-medium';
        if (confidence > 0.85) confidenceClass = 'confidence-high';
        if (confidence < 0.65) confidenceClass = 'confidence-low';
        
        let badgeClass = 'medium-confidence';
        if (confidence > 0.85) badgeClass = 'high-confidence';
        if (confidence < 0.65) badgeClass = 'low-confidence';

        categoryBadge.innerHTML = `
            <div class="category-icon ${isProductive ? 'productive' : 'unproductive'}">
                <i class="fas ${isProductive ? 'fa-bolt' : 'fa-heart'}"></i>
            </div>
            <div class="category-info">
                <span class="category-label">${this.escapeHtml(data.categoria)}</span>
                <span class="confidence ${confidenceClass}">
                    ${Math.round((data.confianca || 0.5) * 100)}% de confiança
                </span>
            </div>
        `;
        
        categoryBadge.className = `category-badge ${badgeClass}`;
    }

    updateResponse(data) {
        const responseText = document.getElementById('responseText');
        const copyButton = document.getElementById('copyResponseBtn');
        
        if (responseText) {
            responseText.textContent = data.resposta_sugerida || 'Não foi possível gerar uma resposta.';
        }
        
        if (copyButton) {
            copyButton.disabled = false;
            copyButton.innerHTML = '<i class="fas fa-copy"></i> Copiar Resposta';
        }
    }

    updateDetails(data, processingTime) {
        const processedText = document.getElementById('processedText');
        const processingTimeEl = document.getElementById('processingTime');
        const analysisMethod = document.getElementById('analysisMethod');
        
        if (processedText) {
            processedText.textContent = data.texto_processado || 'Texto processado com sucesso';
        }
        
        if (processingTimeEl) {
            const serverTime = data.tempo_processamento;
            processingTimeEl.textContent = serverTime ? 
                `${serverTime} (servidor)` : 
                `${processingTime}ms (local)`;
        }

        if (analysisMethod) {
            analysisMethod.textContent = data.modelo_utilizado || 'IA Avançada';
        }
    }

    displayError(errorMessage) {
        const resultsSection = document.getElementById('resultsSection');
        const categoryBadge = document.getElementById('categoryBadge');
        const responseText = document.getElementById('responseText');
        
        if (categoryBadge) {
            categoryBadge.innerHTML = `
                <div class="category-icon" style="background: #6b7280;">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="category-info">
                    <span class="category-label">Erro na Análise</span>
                    <span class="confidence confidence-low">Falha no processamento</span>
                </div>
            `;
            categoryBadge.className = 'category-badge low-confidence';
        }
        
        if (responseText) {
            responseText.textContent = `Não foi possível analisar a mensagem. Erro: ${errorMessage}`;
        }
        
        if (resultsSection) {
            resultsSection.classList.add('active');
        }
    }

    clearForm() {
        const textarea = document.getElementById('emailText');
        const resultsSection = document.getElementById('resultsSection');
        const copyButton = document.getElementById('copyResponseBtn');
        
        if (textarea) {
            textarea.value = '';
            textarea.focus();
        }
        
        if (resultsSection) {
            resultsSection.classList.remove('active');
        }
        
        if (copyButton) {
            copyButton.disabled = true;
        }
        
        this.clearFile();
        this.updateCharCount(0);
        this.showNotification('Formulário limpo com sucesso!', 'info');
    }

    async copyResponse() {
        const responseText = document.getElementById('responseText');
        const copyButton = document.getElementById('copyResponseBtn');
        
        if (!responseText || !responseText.textContent) {
            this.showNotification('Nenhuma resposta disponível para copiar', 'warning');
            return;
        }

        try {
            await navigator.clipboard.writeText(responseText.textContent);
            
            if (copyButton) {
                const originalHTML = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check"></i> Copiado!';
                copyButton.style.background = 'var(--deepseek-green)';
                
                setTimeout(() => {
                    copyButton.innerHTML = originalHTML;
                    copyButton.style.background = '';
                }, 2000);
            }
            
            this.showNotification('Resposta copiada para a área de transferência!', 'success');
        } catch (error) {
            console.error('❌ Erro ao copiar:', error);
            this.showNotification('Erro ao copiar resposta', 'error');
        }
    }

    setupExamples() {
        const examples = [
            {
                title: "Problema Técnico",
                icon: "bug",
                type: "productive",
                text: `URGENTE: Sistema de pagamentos fora do ar!

Prezados, nosso sistema de pagamentos está completamente inoperante desde às 14h. Os clientes não conseguem finalizar compras e estamos perdendo vendas a cada minuto. O erro retornado é "503 Service Unavailable". 

Podem priorizar este caso? Precisamos de uma solução imediata.

Atenciosamente,
João Silva
Gerente de E-commerce`
            },
            {
                title: "Mensagem Social",
                icon: "gift",
                type: "unproductive", 
                text: `Feliz Natal e Próspero Ano Novo!

Gostaria de desejar um feliz natal e um ano novo repleto de realizações para toda a equipe! Que 2024 traga ainda mais sucesso e parcerias duradouras.

Agradeço pelo excelente trabalho ao longo deste ano e pela parceria de sempre.

Com os melhores cumprimentos,
Carlos Eduardo`
            },
            {
                title: "Dúvida Operacional",
                icon: "question-circle",
                type: "productive",
                text: `Como configurar permissões de usuário?

Olá equipe, gostaria de saber como posso configurar diferentes níveis de permissão para os usuários do nosso sistema. Preciso criar perfis de administrador, editor e visualizador com acesso a funcionalidades específicas.

Existe algum tutorial ou documentação sobre isso? Preciso implementar até sexta-feira.

Obrigado,
Maria Santos`
            },
            {
                title: "Feedback Positivo", 
                icon: "heart",
                type: "unproductive",
                text: `Parabéns pelo lançamento!

Quero parabenizar toda a equipe pelo lançamento da nova versão do sistema. A interface está fantástica e as novas funcionalidades são exatamente o que precisávamos.

Estamos muito satisfeitos com o trabalho de vocês!

Grande abraço,
Patrícia Lima`
            }
        ];

        const examplesGrid = document.querySelector('.examples-grid');
        if (!examplesGrid) return;

        examplesGrid.innerHTML = examples.map((example, index) => `
            <div class="example-card" data-example="${index}">
                <div class="example-header">
                    <div class="example-icon ${example.type}">
                        <i class="fas fa-${example.icon}"></i>
                    </div>
                    <h3>${example.title}</h3>
                </div>
                <p class="example-text">${example.text.substring(0, 120)}...</p>
                <button class="btn btn-outline btn-block example-btn">
                    <i class="fas fa-play"></i>
                    Testar Este Exemplo
                </button>
            </div>
        `).join('');

        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const card = e.target.closest('.example-card');
                if (card) {
                    const exampleIndex = parseInt(card.dataset.example);
                    this.loadExample(examples[exampleIndex].text);
                }
            });
        });
    }

    loadExample(text) {
        const textarea = document.getElementById('emailText');
        if (!textarea) return;

        this.switchTab('text');
        
        textarea.value = text;
        this.updateCharCount(text.length);
        
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.classList.remove('active');
        }
        
        this.showNotification('Exemplo carregado! Clique em "Classificar Mensagem" para testar.', 'info');

        setTimeout(() => {
            textarea.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
            textarea.focus();
        }, 100);
    }

    updateCharCount(count) {
        const charCount = document.getElementById('charCount');
        if (charCount) {
            charCount.textContent = `${count.toLocaleString('pt-BR')} caracteres`;
            
            if (count > 5000) {
                charCount.style.color = 'var(--deepseek-orange)';
                charCount.style.fontWeight = '600';
            } else {
                charCount.style.color = '';
                charCount.style.fontWeight = '';
            }
        }
    }

    showNotification(message, type = 'info') {
        let container = document.getElementById('notificationContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notificationContainer';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${this.escapeHtml(message)}</span>
        `;

        container.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('hiding');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getTextareaValue() {
        const textarea = document.getElementById('emailText');
        return textarea ? textarea.value.trim() : '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    addToHistory(data, originalText, processingTime) {
        this.classificationHistory.unshift({
            timestamp: new Date().toISOString(),
            data: data,
            originalText: originalText.substring(0, 200),
            processingTime: processingTime
        });
        
        if (this.classificationHistory.length > 50) {
            this.classificationHistory.pop();
        }
    }

    loadSettings() {
        const saved = localStorage.getItem('emailClassifierSettings');
        if (saved) {
            try {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            } catch (error) {
                console.warn('❌ Erro ao carregar configurações:', error);
            }
        }
    }

    saveSettings() {
        try {
            localStorage.setItem('emailClassifierSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('❌ Erro ao salvar configurações:', error);
        }
    }

    safeAddEventListener(elementId, event, handler) {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener(event, handler);
        } else {
            console.warn(`⚠️ Elemento #${elementId} não encontrado para evento ${event}`);
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Inicializando EmailClassifier AI...');
    console.log('📍 Host:', window.location.hostname);
    
    try {
        window.emailClassifier = new EmailClassifier();
        console.log('✅ EmailClassifier AI carregado com sucesso!');
        
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('💻 Ambiente: Desenvolvimento Local');
        } else {
            console.log('🚀 Ambiente: Produção');
        }
        
    } catch (error) {
        console.error('💥 Erro crítico na inicialização:', error);
        
        const errorMessage = document.createElement('div');
        errorMessage.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            padding: 1.5rem;
            text-align: center;
            z-index: 10000;
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-bottom: 1px solid #fecaca;
        `;
        errorMessage.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Erro ao carregar o classificador. <strong>Recarregue a página</strong>.</span>
            </div>
        `;
        document.body.appendChild(errorMessage);
    }
});

window.addEventListener('error', function(e) {
    console.error('💥 Erro global:', e.error);
    console.error('📄 Em:', e.filename, 'linha:', e.lineno);
});

if ('serviceWorker' in navigator && !window.location.hostname.includes('localhost')) {
    window.addEventListener('load', function() {
        console.log('⚡ Service Worker disponível (não implementado)');
    });
}