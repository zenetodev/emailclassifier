from src.models.email_model import EmailRequest, EmailResponse, CategoriaEmail
from src.services.ai_service import AIService
import logging
from datetime import datetime
from typing import List, Dict, Any
import time

class EmailService:
    def __init__(self):
        self.ai_service = AIService()
        self.logger = self._setup_logger()
        self.metrics = {
            'total_emails_processados': 0,
            'emails_produtivos': 0,
            'emails_improdutivos': 0,
            'tempo_medio_processamento': 0
        }
    
    def _setup_logger(self):
        logger = logging.getLogger('EmailService')
        logger.setLevel(logging.INFO)
        return logger

    def processar_email(self, email_request: EmailRequest) -> EmailResponse:
        """
        Processa um único email através do serviço de IA
        """
        start_time = time.time()
        
        try:
            self._validar_email_request(email_request)
            
            self.logger.info(f"📧 Iniciando processamento de email ({len(email_request.texto)} caracteres)")
            
            categoria_str, confianca = self.ai_service.classificar_email(email_request.texto)
            categoria = CategoriaEmail(categoria_str)
            
            resposta_sugerida = self.ai_service.gerar_resposta_inteligente(
                categoria.value, 
                email_request.texto, 
                confianca
            )
            
            texto_processado = self._processar_e_resumir_texto(email_request.texto)
            
            self._atualizar_metricas(categoria, time.time() - start_time)
            
            self.logger.info(f"✅ Email processado: {categoria.value} "
                           f"(confiança: {confianca*100:.1f}%) "
                           f"em {(time.time() - start_time):.2f}s")
            
            return EmailResponse(
                categoria=categoria,
                resposta_sugerida=resposta_sugerida,
                texto_processado=texto_processado,
                confianca=confianca,
                modelo_utilizado="HuggingFace Transformers + Análise Contextual",
                tempo_processamento=f"{(time.time() - start_time):.3f}s"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar email: {str(e)}", exc_info=True)
            raise

    def _validar_email_request(self, email_request: EmailRequest):
        if not email_request or not email_request.texto:
            raise ValueError("Requisição de email inválida: texto ausente")
        
        texto_limpo = email_request.texto.strip()
        
        if len(texto_limpo) < 10:
            raise ValueError(f"Texto do email muito curto: {len(texto_limpo)} caracteres (mínimo: 10)")
        
        if len(texto_limpo) > 15000:
            raise ValueError(f"Texto do email muito longo: {len(texto_limpo)} caracteres (máximo: 15.000)")
        
        caracteres_validos = sum(1 for char in texto_limpo if char.isalnum() or char.isspace())
        if caracteres_validos < 5:
            raise ValueError("Texto do email contém poucos caracteres válidos")

    def _processar_e_resumir_texto(self, texto: str, max_length: int = 200) -> str:
        if len(texto) <= max_length:
            return texto
        
        paragrafos = texto.split('\n\n')
        if paragrafos and len(paragrafos[0]) <= max_length:
            return paragrafos[0]
        
        frases = texto.split('. ')
        texto_resumido = ""
        
        for frase in frases:
            if len(texto_resumido + frase) < max_length - 3:  
                texto_resumido += frase + '. '
            else:
                break
        
        texto_resumido = texto_resumido.strip()
        
        if len(texto_resumido) < len(texto):
            texto_resumido = texto_resumido.rstrip('.,!?') + '...'
        
        return texto_resumido if texto_resumido else texto[:max_length].rsplit(' ', 1)[0] + '...'

    def _atualizar_metricas(self, categoria: CategoriaEmail, tempo_processamento: float):
        self.metrics['total_emails_processados'] += 1
        
        if categoria == CategoriaEmail.PRODUTIVO:
            self.metrics['emails_produtivos'] += 1
        else:
            self.metrics['emails_improdutivos'] += 1
        
        total_tempo = self.metrics['tempo_medio_processamento'] * (self.metrics['total_emails_processados'] - 1)
        self.metrics['tempo_medio_processamento'] = (total_tempo + tempo_processamento) / self.metrics['total_emails_processados']

    def processar_lote(self, emails: List[str]) -> List[Dict[str, Any]]:
        start_time = time.time()
        resultados = []
        processados_com_sucesso = 0
        
        self.logger.info(f"📦 Iniciando processamento em lote de {len(emails)} emails")
        
        for i, email_texto in enumerate(emails, 1):
            try:
                email_request = EmailRequest(texto=email_texto)
                resultado = self.processar_email(email_request)
                resultados.append(resultado.to_dict())
                processados_com_sucesso += 1
                
                self.logger.debug(f"✅ Email {i}/{len(emails)} processado com sucesso")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Erro no email {i}/{len(emails)}: {str(e)}")
                
                resultados.append({
                    'erro': str(e),
                    'texto_processado': email_texto[:150] + '...' if len(email_texto) > 150 else email_texto,
                    'categoria': 'ERRO',
                    'confianca': 0.0,
                    'resposta_sugerida': 'Não foi possível processar este email.'
                })
        
        tempo_total = time.time() - start_time
        self.logger.info(f"🎯 Lote concluído: {processados_com_sucesso}/{len(emails)} sucessos "
                       f"em {tempo_total:.2f}s ({tempo_total/len(emails):.2f}s por email)")
        
        return resultados

    def obter_metricas(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            'timestamp': datetime.now().isoformat(),
            'taxa_sucesso_produtivo': (
                self.metrics['emails_produtivos'] / self.metrics['total_emails_processados'] 
                if self.metrics['total_emails_processados'] > 0 else 0
            ),
            'uptime': 'ativo'
        }

    def processar_arquivo(self, caminho_arquivo: str, formato: str = 'auto') -> EmailResponse:
        try:
            self.logger.info(f"📁 Processando arquivo: {caminho_arquivo}")
            
            texto = self.ai_service.processar_arquivo(caminho_arquivo)
            
            if not texto or len(texto.strip()) < 10:
                raise ValueError(f"Arquivo vazio ou conteúdo insuficiente: {caminho_arquivo}")
            
            email_request = EmailRequest(texto=texto, formato=formato)
            return self.processar_email(email_request)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar arquivo {caminho_arquivo}: {str(e)}")
            raise ValueError(f"Erro ao processar arquivo: {str(e)}")