import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class Config:
    def __init__(self):
        self._validate_environment()
        self._setup_logging()
        
        self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
        self.PORT = int(os.getenv('PORT', '5000'))
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        
        self.HF_API_KEY = os.getenv('HF_API_KEY', '')
        self._validate_api_keys()
        
        self.MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '15000'))
        self.MIN_TEXT_LENGTH = int(os.getenv('MIN_TEXT_LENGTH', '10'))
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
        
        self.MODEL_CONFIDENCE_THRESHOLD = float(os.getenv('MODEL_CONFIDENCE_THRESHOLD', '0.6'))
        self.ENABLE_HUGGINGFACE = os.getenv('ENABLE_HUGGINGFACE', 'True').lower() == 'true'
        self.FALLBACK_TO_LOCAL = os.getenv('FALLBACK_TO_LOCAL', 'True').lower() == 'true'
        
        self.PALAVRAS_PRODUTIVAS = self._load_productive_words()
        self.PALAVRAS_IMPRODUTIVAS = self._load_unproductive_words()
        self.PADROES_CONTEXTO = self._load_context_patterns()
        
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
        self.RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
        
        self.logger.info(f"✅ Configuração carregada para ambiente: {self.ENVIRONMENT}")

    def _validate_environment(self):
        """Valida variáveis de ambiente críticas"""
        required_vars = []
        
        if self._get_env('ENABLE_HUGGINGFACE', 'True').lower() == 'true':
            required_vars.append('HF_API_KEY')
        
        missing_vars = [var for var in required_vars if not self._get_env(var)]
        
        if missing_vars:
            warning_msg = f"⚠️ Variáveis de ambiente ausentes: {', '.join(missing_vars)}"
            print(warning_msg)

    def _validate_api_keys(self):
        if self.HF_API_KEY and self.HF_API_KEY.startswith('hf_'):
            self.logger.info("✅ HuggingFace API Key formatada corretamente")
        elif self.HF_API_KEY:
            self.logger.warning("⚠️  HuggingFace API Key pode estar em formato incorreto")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG if self._get_env('DEBUG') == 'True' else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
            ]
        )
        self.logger = logging.getLogger('Config')

    def _get_env(self, key: str, default: str = '') -> str:
        return os.getenv(key, default).strip()

    def _load_productive_words(self) -> List[str]:
        base_words = [
            'problema', 'erro', 'ajuda', 'suporte', 'solicitação', 'requisição',
            'urgente', 'importante', 'atualização', 'status', 'como fazer',
            'não funciona', 'conserto', 'reparo', 'assistência', 'dúvida',
            'suporte técnico', 'atendimento', 'chamado', 'ticket', 'bug',
            'defeito', 'falha', 'incidente', 'contrato', 'proposta', 'sistema',
            'aplicação', 'software', 'hardware', 'rede', 'servidor', 'banco de dados',
            'configuração', 'instalação', 'integração', 'migração', 'backup',
            'restauração', 'performance', 'lentidão', 'travamento', 'crash',
            'exception', 'timeout', 'erro 500', 'erro 503', 'service unavailable',
            'monitoramento', 'dashboard', 'relatório', 'analytics', 'métrica'
        ]
        
        custom_words = self._get_env('CUSTOM_PRODUTIVE_WORDS', '').split(',')
        custom_words = [word.strip().lower() for word in custom_words if word.strip()]
        
        return base_words + custom_words

    def _load_unproductive_words(self) -> List[str]:
        base_words = [
            'obrigado', 'obrigada', 'agradeço', 'parabéns', 'feliz natal',
            'feliz ano novo', 'boas festas', 'cumprimentos', 'saudações',
            'agradecimento', 'felicitações', 'comemoração', 'festas',
            'natal', 'ano novo', 'feriado', 'final de semana', 'cumprimento',
            'saudação', 'felicidades', 'comemorações', 'comemorar',
            'elogio', 'reconhecimento', 'feedback positivo', 'excelente',
            'maravilhoso', 'perfeito', 'incrível', 'fantástico', 'ótimo',
            'bom trabalho', 'parabéns pela', 'agradeço pelo', 'muito obrigado',
            'muito obrigada', 'grato', 'grata', 'agradecimentos', 'reconheço'
        ]
        
        custom_words = self._get_env('CUSTOM_IMPRODUTIVE_WORDS', '').split(',')
        custom_words = [word.strip().lower() for word in custom_words if word.strip()]
        
        return base_words + custom_words

    def _load_context_patterns(self) -> Dict[str, List[str]]:
        return {
            'social_forte': [
                r'feliz\s+natal', r'ano\s+novo', r'boas\s+festas',
                r'parab[ée]ns\s+pelo', r'muito\s+obrigad[ao]',
                r'desejo.*feliz', r'felicidades.*para'
            ],
            'urgente': [
                r'urgente', r'cr[ií]tico', r'emerg[êe]ncia',
                r'fora\s+do\s+ar', r'n[aã]o\s+funciona',
                r'erro\s+\d{3}', r'sistema\s+parou'
            ],
            'tecnico': [
                r'bug', r'falha', r'exception', r'stack\s+trace',
                r'log', r'debug', r'troubleshoot'
            ]
        }

    def get_model_config(self) -> Dict[str, Any]:
        return {
            'huggingface': {
                'enabled': self.ENABLE_HUGGINGFACE,
                'api_key': self.HF_API_KEY,
                'timeout': self.REQUEST_TIMEOUT,
                'max_retries': 2
            },
            'local_fallback': {
                'enabled': self.FALLBACK_TO_LOCAL,
                'confidence_threshold': self.MODEL_CONFIDENCE_THRESHOLD
            },
            'performance': {
                'max_text_length': self.MAX_TEXT_LENGTH,
                'min_text_length': self.MIN_TEXT_LENGTH
            }
        }

    def get_security_config(self) -> Dict[str, Any]:
        return {
            'cors': {
                'origins': self.CORS_ORIGINS,
                'methods': ['GET', 'POST', 'OPTIONS'],
                'allow_headers': ['Content-Type', 'Authorization']
            },
            'rate_limiting': {
                'enabled': self.RATE_LIMIT_ENABLED,
                'requests_per_minute': 60
            }
        }

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == 'production'

    def validate_text_length(self, texto: str) -> bool:
        return self.MIN_TEXT_LENGTH <= len(texto) <= self.MAX_TEXT_LENGTH

    def __repr__(self) -> str:
        return (f"Config(environment={self.ENVIRONMENT}, "
                f"debug={self.DEBUG}, "
                f"huggingface_enabled={self.ENABLE_HUGGINGFACE})")


config = Config()