from flask import jsonify, request
from src.services.email_service import EmailService
from src.models.email_model import EmailRequest
import logging
from datetime import datetime

class EmailController:
    def __init__(self):
        self.email_service = EmailService()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('EmailController')
        logger.setLevel(logging.INFO)
        return logger
    
    def classificar_email(self):
        """
        Endpoint principal para classificação de emails
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"📨 Nova requisição de classificação recebida")
            
            if not request.is_json:
                return jsonify({
                    'erro': 'Content-Type deve ser application/json',
                    'codigo': 'INVALID_CONTENT_TYPE'
                }), 400
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'erro': 'Corpo da requisição vazio',
                    'codigo': 'EMPTY_BODY'
                }), 400
            
            if 'texto' not in data:
                return jsonify({
                    'erro': 'Campo "texto" é obrigatório',
                    'codigo': 'MISSING_TEXT_FIELD'
                }), 400
            
            texto = data['texto'].strip()
            
            if not texto:
                return jsonify({
                    'erro': 'Texto do email não pode estar vazio',
                    'codigo': 'EMPTY_TEXT'
                }), 400
            
            if len(texto) < 10:
                return jsonify({
                    'erro': 'Texto do email muito curto (mínimo 10 caracteres)',
                    'codigo': 'TEXT_TOO_SHORT',
                    'tamanho_atual': len(texto)
                }), 400
            
            if len(texto) > 10000:
                return jsonify({
                    'erro': 'Texto do email muito longo (máximo 10.000 caracteres)',
                    'codigo': 'TEXT_TOO_LONG',
                    'tamanho_atual': len(texto)
                }), 400
            
            email_request = EmailRequest(
                texto=texto,
                formato=data.get('formato', 'texto'),
                metadata={
                    'timestamp': start_time.isoformat(),
                    'tamanho_texto': len(texto),
                    'user_agent': request.headers.get('User-Agent', 'Desconhecido')
                }
            )
            
            self.logger.info(f"🔍 Processando email de {len(texto)} caracteres...")
            resultado = self.email_service.processar_email(email_request)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"✅ Email classificado como '{resultado.categoria}' "
                           f"com {resultado.confianca*100:.1f}% de confiança "
                           f"em {processing_time:.2f}s")
            
            response_data = resultado.to_dict()
            response_data.update({
                'tempo_processamento': f"{processing_time:.3f}s",
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify(response_data), 200
            
        except ValueError as e:
            self.logger.warning(f"⚠️ Erro de validação: {str(e)}")
            return jsonify({
                'erro': str(e),
                'codigo': 'VALIDATION_ERROR'
            }), 400
            
        except Exception as e:
            self.logger.error(f"❌ Erro interno no servidor: {str(e)}", exc_info=True)
            
            return jsonify({
                'erro': 'Erro interno no processamento do email',
                'codigo': 'INTERNAL_SERVER_ERROR',
                'detalhes': 'Nossa equipe foi notificada'
            }), 500
    
    def health_check(self):
        """
        Endpoint de health check para monitoramento
        """
        try:
            health_status = {
                'status': 'healthy',
                'service': 'Email Classifier AI API',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'dependencies': {
                    'email_service': 'operational',
                    'ai_service': 'operational'
                }
            }
            
            test_text = "Teste de saúde do sistema"
            test_request = EmailRequest(texto=test_text, formato="texto")
            
            test_result = self.email_service.processar_email(test_request)
            health_status['dependencies']['classification'] = 'operational'
            health_status['last_test'] = {
                'categoria': test_result.categoria,
                'confianca': test_result.confianca
            }
            
            return jsonify(health_status), 200
            
        except Exception as e:
            self.logger.error(f"🚨 Health check falhou: {str(e)}")
            
            return jsonify({
                'status': 'unhealthy',
                'service': 'Email Classifier AI API',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'erro': str(e),
                'dependencies': {
                    'email_service': 'failed',
                    'ai_service': 'failed'
                }
            }), 503
    
    def get_stats(self):
        """
        Endpoint para estatísticas do serviço (opcional)
        """
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'uptime': 'ativo',
                'total_classificacoes': len(getattr(self.email_service.ai_service, 'classification_history', [])),
                'versao_api': '1.0.0'
            }
            
            return jsonify(stats), 200
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return jsonify({'erro': 'Não foi possível obter estatísticas'}), 500