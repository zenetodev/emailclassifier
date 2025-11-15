from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class CategoriaEmail(Enum):
    PRODUTIVO = "Produtivo"
    IMPRODUTIVO = "Improdutivo"
    
    @classmethod
    def from_string(cls, value: str):
        value_lower = value.lower().strip()
        for member in cls:
            if member.value.lower() == value_lower:
                return member
        raise ValueError(f"Categoria inválida: {value}")

@dataclass
class EmailRequest:
    texto: str
    formato: Optional[str] = "texto"
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.texto or not self.texto.strip():
            raise ValueError("Texto do email não pode estar vazio")
        
        if len(self.texto.strip()) < 10:
            raise ValueError("Texto do email muito curto (mínimo 10 caracteres)")
            
        self.texto = self.texto.strip()
        
        if not self.request_id:
            self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        if self.metadata is None:
            self.metadata = {}

@dataclass
class EmailResponse:
    categoria: CategoriaEmail
    resposta_sugerida: str
    texto_processado: str
    confianca: float
    modelo_utilizado: Optional[str] = "Sistema de IA"
    tempo_processamento: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if not 0 <= self.confianca <= 1:
            raise ValueError(f"Confiança deve estar entre 0 e 1, recebido: {self.confianca}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'categoria': self.categoria.value,
            'resposta_sugerida': self.resposta_sugerida,
            'texto_processado': self.texto_processado,
            'confianca': round(self.confianca, 4), 
            'modelo_utilizado': self.modelo_utilizado,
            'tempo_processamento': self.tempo_processamento,
            'timestamp': self.timestamp,
            'request_id': self.request_id,
            'nivel_confianca': self._get_nivel_confianca()
        }
    
    def _get_nivel_confianca(self) -> str:
        """Retorna nível textual da confiança"""
        if self.confianca >= 0.9:
            return "Muito Alta"
        elif self.confianca >= 0.7:
            return "Alta"
        elif self.confianca >= 0.5:
            return "Média"
        else:
            return "Baixa"
    
    def is_confiante(self, threshold: float = 0.7) -> bool:
        return self.confianca >= threshold
    
    def get_resumo(self) -> Dict[str, Any]:
        return {
            'categoria': self.categoria.value,
            'confianca': round(self.confianca, 3),
            'resposta_sugerida': self.resposta_sugerida[:100] + '...' if len(self.resposta_sugerida) > 100 else self.resposta_sugerida
        }

@dataclass
class BatchEmailRequest:
    emails: list[EmailRequest]
    batch_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.batch_id:
            self.batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'batch_id': self.batch_id,
            'total_emails': len(self.emails),
            'emails': [asdict(email) for email in self.emails]
        }

@dataclass
class BatchEmailResponse:
    resultados: list[EmailResponse]
    batch_id: str
    total_processados: int
    sucessos: int
    falhas: int
    tempo_total_processamento: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'batch_id': self.batch_id,
            'total_processados': self.total_processados,
            'sucessos': self.sucessos,
            'falhas': self.falhas,
            'taxa_sucesso': round(self.sucessos / self.total_processados, 3) if self.total_processados > 0 else 0,
            'tempo_total_processamento': self.tempo_total_processamento,
            'resultados': [resultado.to_dict() for resultado in self.resultados]
        }

@dataclass 
class ErrorResponse:
    erro: str
    codigo: str
    detalhes: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'erro': self.erro,
            'codigo': self.codigo,
            'detalhes': self.detalhes,
            'request_id': self.request_id,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_exception(cls, exception: Exception, request_id: str = None):
        return cls(
            erro=str(exception),
            codigo=exception.__class__.__name__,
            detalhes=getattr(exception, 'details', None),
            request_id=request_id
        )