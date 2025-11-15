import os
import requests
import re
import time
import nltk
import random
from typing import Tuple, List, Dict, Optional
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from src.utils.config import Config

class AIService:
    def __init__(self):
        self.config = Config()
        self.headers = {
            "Authorization": f"Bearer {self.config.HF_API_KEY}",
            "Content-Type": "application/json"
        }
        self.classification_history = []
        self._setup_nltk()
        
        self.stop_words_pt = set(stopwords.words('portuguese'))
        self.stemmer = PorterStemmer()
        
        self.priority_models = [
            "facebook/bart-large-mnli",  
            "joeddav/xlm-roberta-large-xnli",  
            "typeform/distilbert-base-uncased-mnli"  
        ]
        
        self.generation_model = "microsoft/DialoGPT-medium"  
        
        print("🚀 AIService inicializado com modelos avançados")

    def _setup_nltk(self):
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            print("✅ NLTK pré-configurado")
        except LookupError:
            print("📥 Baixando recursos NLTK...")
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                print("✅ Recursos NLTK baixados")
            except Exception as e:
                print(f"⚠️  Fallback para NLTK básico: {e}")

    def classificar_com_huggingface(self, texto: str) -> Tuple[str, float]:
        modelos = [
            "facebook/bart-large-mnli",
            "joeddav/xlm-roberta-large-xnli", 
            "typeform/distilbert-base-uncased-mnli"
        ]
        
        for modelo in modelos:
            try:
                API_URL = f"https://api-inference.huggingface.co/models/{modelo}"
                
                payload = {
                    "inputs": texto[:400],
                    "parameters": {
                        "candidate_labels": ["produtivo", "improdutivo"],
                        "multi_label": False
                    }
                }
                
                print(f"🤖 Tentando modelo: {modelo}")
                response = requests.post(API_URL, headers=self.headers, json=payload, timeout=25)
                
                if response.status_code == 503:
                    print(f"⏳ Modelo {modelo} carregando...")
                    time.sleep(12)
                    response = requests.post(API_URL, headers=self.headers, json=payload, timeout=25)
                
                response.raise_for_status()
                result = response.json()
                
                if 'labels' in result and 'scores' in result:
                    best_idx = result['scores'].index(max(result['scores']))
                    categoria = result['labels'][best_idx]
                    confianca = result['scores'][best_idx]
                    
                    categoria_final = "Produtivo" if categoria == "produtivo" else "Improdutivo"
                    print(f"✅ {modelo}: {categoria_final} ({confianca:.3f})")
                    
                    if "distilbert" in modelo:
                        confianca = confianca * 0.95 
                    
                    return categoria_final, round(confianca, 3)
                    
            except Exception as e:
                print(f"❌ {modelo} falhou: {e}")
                continue
        
        raise Exception("Todos os modelos Hugging Face falharam")

    def classificar_localmente(self, texto: str) -> Tuple[str, float]:
        print("🔄 Iniciando análise local avançada...")
        
        texto_lower = texto.lower()
        texto_limpo = self.preprocessar_texto_avancado(texto)
        
        contexto_geral = self._analisar_contexto_geral(texto_lower)
        
        if contexto_geral == "social_forte":
            return self._classificar_contexto_social(texto_limpo, texto_lower)
        
        score_produtivo, score_improdutivo = self._analise_palavras_chave_contextual(texto_limpo, texto_lower)
        
        padroes_produtivo, padroes_improdutivo = self._analise_padroes_linguisticos(texto_lower)
        
        total_produtivo = score_produtivo + padroes_produtivo
        total_improdutivo = score_improdutivo + padroes_improdutivo
        
        total_produtivo, total_improdutivo = self._ajuste_final_contextual(
            texto_lower, total_produtivo, total_improdutivo
        )
        
        confianca = self._calcular_confianca_avancada(total_produtivo, total_improdutivo)
        
        if total_produtivo > total_improdutivo:
            categoria = "Produtivo"
            confianca_final = max(0.55, min(0.98, confianca))
        else:
            categoria = "Improdutivo" 
            confianca_final = max(0.55, min(0.98, confianca))
        
        print(f"🎯 Análise Final: {categoria} (P:{total_produtivo:.2f}, I:{total_improdutivo:.2f}, Conf:{confianca_final:.3f})")
        
        return categoria, round(confianca_final, 3)

    def _analisar_contexto_geral(self, texto_lower: str) -> str:
        padroes_sociais_fortes = [
            'parabenizar', 'parabéns', 'excelente', 'maravilhoso', 'perfeito',
            'feliz natal', 'ano novo', 'boas festas', 'agradeço pelo', 'obrigado pelo',
            'gostaria de parabenizar', 'quero parabenizar', 'muito obrigado', 'muito obrigada'
        ]
        
        for padrao in padroes_sociais_fortes:
            if padrao in texto_lower:
                print(f"🎉 Contexto social forte detectado: '{padrao}'")
                return "social_forte"
        
        padroes_urgentes = [
            'urgente', 'crítico', 'emergência', 'fora do ar', 'não funciona',
            'erro 500', 'erro 503', 'sistema parou', 'prioridade', 'imediato'
        ]
        
        for padrao in padroes_urgentes:
            if padrao in texto_lower:
                print(f"🚨 Contexto urgente detectado: '{padrao}'")
                return "urgente"
        
        return "neutro"

    def _classificar_contexto_social(self, texto_limpo: str, texto_lower: str) -> Tuple[str, float]:
        print("💬 Analisando contexto social...")
        
        palavras_solicitacao = ['preciso', 'necessito', 'ajuda', 'problema', 'erro', 'bug', 'falha']
        tem_solicitacao = any(palavra in texto_limpo for palavra in palavras_solicitacao)
        
        if tem_solicitacao:
            print("⚠️  Contexto social com solicitação detectado")
            return "Improdutivo", 0.7
        else:
            print("🎊 Contexto social puro detectado")
            return "Improdutivo", 0.9

    def _analise_palavras_chave_contextual(self, texto_limpo: str, texto_lower: str) -> Tuple[float, float]:
        palavras_produtivas = {
            'erro 500': 3.0, 'erro 503': 3.0, 'não funciona': 2.8, 'fora do ar': 2.8,
            'bug': 2.5, 'falha': 2.5, 'quebrado': 2.5, 'parou': 2.5,
            
            'preciso de ajuda': 2.5, 'necessito de ajuda': 2.5, 'problema': 2.0,
            'não consigo': 2.0, 'como configurar': 1.8, 'dúvida': 1.5,
            'solicitação': 1.8, 'requisição': 1.8, 'chamado': 1.5,
            
            'configurar': 1.2, 'instalar': 1.2, 'integrar': 1.2, 'atualizar': 1.0
        }
        
        palavras_improdutivas = {
            'obrigado': 2.5, 'obrigada': 2.5, 'agradeço': 2.5, 'agradecimento': 2.0,
            'muito obrigado': 3.0, 'muito obrigada': 3.0,
            
            'parabéns': 3.0, 'parabenizar': 3.0, 'excelente': 2.5, 'maravilhoso': 2.5,
            'perfeito': 2.5, 'incrível': 2.0, 'fantástico': 2.0, 'ótimo': 2.0,
            
            'feliz natal': 3.0, 'ano novo': 2.8, 'boas festas': 2.5,
            'cumprimentos': 1.5, 'saudações': 1.5, 'saudação': 1.2,
            
            'gostei': 2.0, 'satisfeito': 2.0, 'content': 1.8, 'feliz': 1.5
        }
        
        score_produtivo = 0
        score_improdutivo = 0
        
        for palavra, peso in palavras_produtivas.items():
            if palavra in texto_limpo:
                if not self._esta_em_contexto_agradecimento(palavra, texto_lower):
                    score_produtivo += peso
                    print(f"🔴 Produtivo: '{palavra}' (+{peso})")
        
        for palavra, peso in palavras_improdutivas.items():
            if palavra in texto_limpo:
                score_improdutivo += peso
                print(f"🟢 Improdutivo: '{palavra}' (+{peso})")
    
        return score_produtivo, score_improdutivo

    def _esta_em_contexto_agradecimento(self, palavra: str, texto_lower: str) -> bool:
        contextos_agradecimento = [
            'obrigado', 'agradeço', 'parabéns', 'gostaria de agradecer',
            'quero agradecer', 'excelente', 'maravilhoso', 'muito obrigado'
        ]
        
        palavras_vizinhas = texto_lower.split()
        if palavra in palavras_vizinhas:
            idx = palavras_vizinhas.index(palavra)
            contexto_proximo = ' '.join(palavras_vizinhas[max(0, idx-3):min(len(palavras_vizinhas), idx+4)])
            
            for contexto in contextos_agradecimento:
                if contexto in contexto_proximo and contexto != palavra:
                    print(f"🔄 Palavra '{palavra}' em contexto de agradecimento - peso reduzido")
                    return True
    
        return False

    def _analise_padroes_linguisticos(self, texto: str) -> Tuple[float, float]:
        padroes_produtivo = 0
        padroes_improdutivo = 0
        
        texto_lower = texto.lower()
        
        if any(pergunta in texto_lower for pergunta in ['?', 'como', 'por que', 'porque', 'quando']):
            padroes_produtivo += 1.5
            print("❓ Padrão de pergunta detectado")
        
        if any(imperativo in texto_lower for imperativo in ['preciso', 'necessito', 'urgente', 'por favor']):
            padroes_produtivo += 1.2
            print("🎯 Padrão de solicitação detectado")
        
        if any(tecnico in texto_lower for tecnico in ['código', 'log', 'erro', 'exceção', 'configuração']):
            padroes_produtivo += 1.3
            print("💻 Padrão técnico detectado")
        
        if any(saudacao in texto_lower for saudacao in ['olá', 'oi ', 'bom dia', 'boa tarde', 'boa noite']):
            padroes_improdutivo += 0.5
        
        if len(re.findall(r'!', texto)) > 2: 
            padroes_improdutivo += 0.8
            print("❗ Muitas exclamações - padrão social")
        
        if any(elogio in texto_lower for elogio in ['excelente', 'maravilhoso', 'perfeito', 'incrível']):
            padroes_improdutivo += 1.0
            print("⭐ Padrão de elogio detectado")
        
        return padroes_produtivo, padroes_improdutivo

    def _ajuste_final_contextual(self, texto_lower: str, score_p: float, score_i: float) -> Tuple[float, float]:
        if 'obrigado' in texto_lower and 'suporte' in texto_lower:
            print("🔄 Padrão: Agradecimento por suporte - favorecendo improdutivo")
            score_i += 2.0
        
        if any(elogio in texto_lower for elogio in ['parabéns', 'excelente']) and 'problema' in texto_lower:
            print("🔄 Padrão: Elogio sobre problema resolvido - favorecendo improdutivo")
            score_i += 1.5
        
        palavras_positivas = ['obrigado', 'parabéns', 'excelente', 'maravilhoso', 'perfeito']
        count_positivas = sum(1 for palavra in palavras_positivas if palavra in texto_lower)
        
        if count_positivas >= 2:
            print(f"🔄 Múltiplas palavras positivas ({count_positivas}) - favorecendo improdutivo")
            score_i += 1.0
        
        return score_p, score_i

    def _calcular_confianca_avancada(self, score_p: float, score_i: float) -> float:
        diferenca = abs(score_p - score_i)
        soma = score_p + score_i
        
        if soma == 0:
            return 0.6 
        
        confianca_base = min(0.95, diferenca / soma)
        
        fatores = []
        
        if diferenca > 3:
            fatores.append(0.15)  
        elif diferenca > 1.5:
            fatores.append(0.08)  
        else:
            fatores.append(-0.1)  
        
        confianca_ajustada = confianca_base + sum(fatores)
        
        return max(0.5, min(0.98, confianca_ajustada))

    def preprocessar_texto_avancado(self, texto: str) -> str:
        if not texto:
            return ""
        
        print("🔧 Aplicando pré-processamento NLP...")
        
        texto = texto.lower()
        
        texto = re.sub(r'[^\w\sáàâãéèêíïóôõöúçñ]', ' ', texto)
        
        try:
            tokens = word_tokenize(texto, language='portuguese')
        except:
            tokens = texto.split()
        
        tokens = [token for token in tokens if token not in self.stop_words_pt]
        
        tokens = [self.stemmer.stem(token) for token in tokens]
        
        texto_processado = ' '.join(tokens)
        
        texto_processado = re.sub(r'\s+', ' ', texto_processado).strip()
        
        print(f"🔧 Texto processado ({len(tokens)} tokens): {texto_processado[:100]}...")
        return texto_processado

    def preprocessar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        
        texto_limpo = re.sub(r'[^\w\s]', ' ', texto.lower())
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
        
        return texto_limpo

    def processar_arquivo(self, arquivo_path: str) -> str:
        try:
            if arquivo_path.endswith('.txt'):
                with open(arquivo_path, 'r', encoding='utf-8') as file:
                    conteudo = file.read()
                    print(f"📄 Arquivo TXT processado: {len(conteudo)} caracteres")
                    return conteudo
            
            elif arquivo_path.endswith('.pdf'):
                conteudo = self.extrair_texto_pdf(arquivo_path)
                print(f"📄 Arquivo PDF processado: {len(conteudo)} caracteres")
                return conteudo
                
            else:
                raise ValueError("Formato de arquivo não suportado")
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivo: {e}")
            raise

    def extrair_texto_pdf(self, arquivo_path: str) -> str:
        try:
            try:
                import PyPDF2
            except ImportError:
                print("⚠️  PyPDF2 não instalado. Instale com: pip install PyPDF2")
                return "[ERRO: Biblioteca PyPDF2 não instalada. Use: pip install PyPDF2]"
            
            texto = ""
            with open(arquivo_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_paginas = len(reader.pages)
                
                for i, pagina in enumerate(reader.pages):
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto += f"--- Página {i+1} ---\n{texto_pagina}\n\n"
            
            if not texto.strip():
                return "[AVISO: Nenhum texto extraído do PDF. O arquivo pode ser digitalizado.]"
            
            return texto.strip()
            
        except Exception as e:
            print(f"❌ Erro ao extrair texto PDF: {e}")
            return f"[ERRO ao processar PDF: {str(e)}]"

    def gerar_resposta_com_ai(self, categoria: str, texto_original: str) -> str:
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
        
        if categoria == "Produtivo":
            prompt = f"""
            Como assistente de suporte técnico, responda este email de forma profissional e útil:
            
            Email: "{texto_original[:300]}"
            
            Gere uma resposta curta que:
            - Agradece o contato
            - Indica que a solicitação será analisada
            - Oferece um prazo aproximado
            - Seja profissional e direta
            
            Resposta:
            """
        else:
            prompt = f"""
            Como assistente de relacionamento, responda este email de forma educada e amigável:
            
            Email: "{texto_original[:300]}"
            
            Gere uma resposta curta que:
            - Agradece a mensagem
            - Retribui a gentileza
            - Seja breve e cordial
            
            Resposta:
            """
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 80,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            print("🤖 Chamando Hugging Face API para geração de resposta...")
            response = requests.post(API_URL, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 503:
                time.sleep(8)
                response = requests.post(API_URL, headers=self.headers, json=payload, timeout=30)
            
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
                resposta = self._limpar_resposta_gerada(generated_text, prompt)
                if len(resposta) > 15:
                    print("✅ Resposta gerada com Hugging Face")
                    return resposta
                else:
                    raise Exception("Resposta muito curta")
            else:
                raise Exception("Resposta vazia da API")
                
        except Exception as e:
            print(f"❌ Erro na geração: {e}")
            return self.gerar_resposta_local(categoria, texto_original)

    def _limpar_resposta_gerada(self, generated_text: str, prompt: str) -> str:
        if prompt in generated_text:
            resposta = generated_text.replace(prompt, "").strip()
        else:
            resposta = generated_text.strip()
        
        linhas = resposta.split('\n')
        linhas_limpas = []
        
        for linha in linhas:
            linha_limpa = linha.strip()
            if len(linha_limpa) > 10 and not linha_limpa.startswith('Email:'):
                linhas_limpas.append(linha_limpa)
        
        resposta_final = ' '.join(linhas_limpas[:2])  
        resposta_final = resposta_final.replace('"', '')  
        
        if resposta_final and not resposta_final[-1] in ['.', '!', '?']:
            resposta_final += '.'
            
        return resposta_final

    def gerar_resposta_avancada(self, categoria: str, texto_original: str, confianca: float) -> str:
        texto_lower = texto_original.lower()
        
        if categoria == "Produtivo":
            if confianca > 0.85:
                if any(word in texto_lower for word in ['erro', 'bug', 'falha']):
                    return "🔧 Identificamos o problema técnico relatado. Nossa equipe priorizou a análise e retornará com a solução em até 1 hora útil."
                elif any(word in texto_lower for word in ['dúvida', 'como fazer']):
                    return "💡 Agradecemos sua consulta. Nossa equipe especializada está preparando uma resposta detalhada para orientá-lo no processo."
                else:
                    return "✅ Recebemos sua solicitação. Um ticket foi criado com prioridade e você receberá atualizações em breve."
            else:
                return "📨 Agradecemos seu contato. Nossa equipe analisará a mensagem e retornará dentro do prazo de 24 horas úteis."
        
        else:  
            if confianca > 0.85:
                if any(word in texto_lower for word in ['natal', 'ano novo']):
                    return "🎄 Agradecemos as felicitações! Retribuímos os votos de um feliz natal e um próspero ano novo para você e toda equipe!"
                elif any(word in texto_lower for word in ['parabéns', 'elogio']):
                    return "⭐ Muito obrigado pelo reconhecimento! Ficamos felizes em saber que nosso trabalho está fazendo a diferença."
                else:
                    return "🙏 Agradecemos sua mensagem! Valorizamos muito o contato e desejamos um excelente dia."
            else:
                return "💌 Obrigado pelo contato! Sua mensagem foi recebida e apreciamos sua interação conosco."

    def gerar_resposta_local(self, categoria: str, texto_original: str) -> str:
        print("🔄 Usando resposta local...")
        
        texto_lower = texto_original.lower()
        
        if categoria == "Produtivo":
            if any(word in texto_lower for word in ['erro', 'bug', 'não funciona']):
                respostas = [
                    "Agradecemos o reporte do problema. Nossa equipe técnica já está analisando o caso e retornará em breve.",
                    "Identificamos o problema relatado. Um ticket de prioridade foi criado e você receberá atualizações em até 2 horas.",
                    "Obrigado por reportar esta falha. Nossos desenvolvedores estão trabalhando na correção.",
                    "Confirmamos o recebimento do seu reporte de problema. Estamos investigando e retornaremos com uma solução."
                ]
            elif any(word in texto_lower for word in ['dúvida', 'como', 'configurar']):
                respostas = [
                    "Agradecemos sua dúvida. Nossa equipe de suporte responderá com as orientações necessárias em breve.",
                    "Obrigado pela pergunta. Estamos preparando uma resposta detalhada para auxiliá-lo.",
                    "Recebemos sua consulta. Nossa equipe especializada retornará com as informações solicitadas.",
                    "Agradecemos seu questionamento. Em até 1 hora útil você receberá nossa resposta completa."
                ]
            else:
                respostas = [
                    "Agradecemos seu contato. Nossa equipe analisará sua solicitação e retornará em breve.",
                    "Recebemos sua requisição. Um ticket foi criado e você receberá atualizações em breve.",
                    "Confirmamos o recebimento de sua solicitação. Retornaremos dentro de 24 horas úteis.",
                    "Sua solicitação foi registrada em nosso sistema. Em breve entraremos em contato."
                ]
        else:
            if any(word in texto_lower for word in ['natal', 'ano novo', 'festas']):
                respostas = [
                    "Agradecemos suas felicitações! Desejamos um feliz natal e um próspero ano novo para você e toda sua equipe!",
                    "Muito obrigado pelas mensagens de festas! Retribuímos os votos de um excelente natal e ano novo!",
                    "Agradecemos seus cumprimentos! Que as festas sejam repletas de alegria e que o novo ano traga ainda mais sucesso!",
                    "Obrigado pelas felicitações! Desejamos a você e sua equipe um natal abençoado e um ano novo cheio de conquistas!"
                ]
            elif any(word in texto_lower for word in ['parabéns', 'elogio']):
                respostas = [
                    "Agradecemos muito pelos elogios! Ficamos felizes em saber que nosso trabalho está atendendo suas expectativas.",
                    "Muito obrigado pelo reconhecimento! Sua satisfação é nossa maior motivação para continuar evoluindo.",
                    "Agradecemos suas palavras! É um prazer poder contribuir com o sucesso do seu negócio.",
                    "Obrigado pelo feedback positivo! Estamos sempre buscando oferecer o melhor serviço possível."
                ]
            else:
                respostas = [
                    "Agradecemos sua mensagem! Desejamos um ótimo dia.",
                    "Obrigado pelo contato! Ficamos felizes com sua mensagem.",
                    "Agradecemos suas palavras! Estamos sempre à disposição.",
                    "Muito obrigado! Sua mensagem foi recebida com alegria."
                ]
        
        index = hash(texto_original) % len(respostas)
        return respostas[index]
    
    def gerar_resposta_inteligente(self, categoria: str, texto_original: str, confianca: float) -> str:
        """
        Gera respostas contextuais baseadas na categoria e confiança
        """
        texto_lower = texto_original.lower()
        
        if categoria == "Produtivo":
            return self._gerar_resposta_produtiva(texto_lower, confianca)
        else:
            return self._gerar_resposta_improdutiva(texto_lower, confianca)
    
    def _gerar_resposta_produtiva(self, texto_lower: str, confianca: float) -> str:
        if confianca > 0.8:
            if any(word in texto_lower for word in ['erro', 'bug', 'não funciona', 'fora do ar']):
                return "🔧 **Problema identificado** - Nossa equipe técnica já está analisando esta falha. Você receberá uma atualização em até 1 hora útil."
            
            elif any(word in texto_lower for word in ['dúvida', 'como fazer', 'configurar']):
                return "💡 **Consulta recebida** - Nossa equipe especializada está preparando um guia detalhado para sua dúvida. Retornaremos em breve."
            
            elif any(word in texto_lower for word in ['urgente', 'prioridade', 'crítico']):
                return "🚨 **Caso prioritário** - Sua solicitação foi marcada como urgente. Atualizações em até 30 minutos."
        
        respostas = [
            "✅ **Solicitação recebida** - Confirmamos o recebimento de sua requisição. Ticket #{} criado com sucesso.",
            "📋 **Em análise** - Sua solicitação está sendo processada por nossa equipe. Retornaremos em até 2 horas úteis.",
            "👨‍💻 **Em atendimento** - Já iniciamos a análise do seu caso. Você receberá atualizações em breve."
        ]
        
        
        ticket_id = random.randint(1000, 9999)
        return respostas[hash(texto_lower) % len(respostas)].format(ticket_id)
    
    def _gerar_resposta_improdutiva(self, texto_lower: str, confianca: float) -> str:
        if confianca > 0.85:
            if any(word in texto_lower for word in ['natal', 'ano novo', 'festas']):
                return "🎄 **Agradecemos as felicitações!** Retribuímos os votos de um feliz natal e um ano novo repleto de conquistas para você e toda equipe!"
            
            elif any(word in texto_lower for word in ['parabéns', 'elogio', 'excelente']):
                return "⭐ **Muito obrigado pelo reconhecimento!** Sua satisfação é nossa maior motivação para continuar evoluindo."
        
        respostas = [
            "💌 **Mensagem recebida** - Agradecemos seu contato! Desejamos um excelente dia.",
            "🙏 **Agradecemos** - Sua mensagem foi recebida com alegria. Estamos sempre à disposição!",
            "😊 **Obrigado!** - Valorizamos muito sua interação conosco. Tenha um ótimo dia!"
        ]
        
        return respostas[hash(texto_lower) % len(respostas)]

    def classificar_email(self, texto: str) -> Tuple[str, float]:
        if not texto or len(texto.strip()) < 10:
            return "Improdutivo", 0.6
            
        print(f"📊 Analisando texto de {len(texto)} caracteres...")
        
        try:
            categoria, confianca = self.classificar_com_huggingface(texto)
            self._registrar_classificacao("huggingface", categoria, confianca)
            return categoria, confianca
        except Exception as e:
            print(f"🔁 Fallback para análise local: {e}")
            
        return self.classificar_localmente_aprimorado(texto)

    def _registrar_classificacao(self, metodo: str, categoria: str, confianca: float):
        self.classification_history.append({
            'timestamp': time.time(),
            'metodo': metodo,
            'categoria': categoria,
            'confianca': confianca
        })
        
        if len(self.classification_history) > 100:
            self.classification_history.pop(0)

    def gerar_resposta(self, categoria: str, texto_original: str) -> str:
        try:
            return self.gerar_resposta_com_ai(categoria, texto_original)
        except Exception as e:
            print(f"❌ Falha na geração com Hugging Face: {e}")
            _, confianca_estimada = self.classificar_localmente(texto_original)
            return self.gerar_resposta_avancada(categoria, texto_original, confianca_estimada)
        
    def classificar_localmente_aprimorado(self, texto: str) -> Tuple[str, float]:
        texto_lower = texto.lower()
        
        contexto = self._analisar_contexto_rapido(texto_lower)
        
        if contexto == "social_forte":
            return "Improdutivo", 0.92
        elif contexto == "urgente":
            return "Produtivo", 0.88
            
        score_produtivo = self._calcular_score_produtivo(texto_lower)
        score_improdutivo = self._calcular_score_improdutivo(texto_lower)
        
        diferenca = score_produtivo - score_improdutivo
        
        if diferenca > 1.0:
            confianca = min(0.95, 0.7 + (diferenca * 0.1))
            return "Produtivo", round(confianca, 3)
        elif diferenca < -1.0:
            confianca = min(0.95, 0.7 + (abs(diferenca) * 0.1))
            return "Improdutivo", round(confianca, 3)
        else:
            return "Produtivo", 0.65
    
    def _calcular_score_produtivo(self, texto_lower: str) -> float:
        score = 0
        
        problemas = {
            r'erro\s+\d{3}': 3.0, r'n[aã]o\s+funciona': 2.8, r'fora\s+do\s+ar': 2.8,
            r'bug': 2.5, r'falha': 2.5, r'quebrado': 2.5, r'parou': 2.5,
            r'travando': 2.0, r'lento': 1.8, r'problema': 2.0
        }
        
        for padrao, peso in problemas.items():
            if re.search(padrao, texto_lower):
                score += peso
                
        solicitacoes = {
            r'preciso\s+de': 2.0, r'necessito\s+de': 2.0, r'como\s+faço': 1.8,
            r'como\s+configurar': 1.8, r'd[uú]vida': 1.5, r'ajuda': 1.5,
            r'solicita[cç][aã]o': 1.8, r'requisi[cç][aã]o': 1.8
        }
        
        for padrao, peso in solicitacoes.items():
            if re.search(padrao, texto_lower):
                score += peso
                
        if '?' in texto_lower:
            score += 1.0
        if any(palavra in texto_lower for palavra in ['por favor', 'urgente', 'prioridade']):
            score += 1.2
            
        return score

    def _calcular_score_improdutivo(self, texto_lower: str) -> float:
        score = 0
        
        agradecimentos = {
            r'muito\s+obrigad[ao]': 3.0, r'agradeço\s+pelo': 2.8,
            r'obrigad[ao]\s+pelo': 2.5, r'agradecimento': 2.0
        }
        
        for padrao, peso in agradecimentos.items():
            if re.search(padrao, texto_lower):
                score += peso
                
        elogios = {
            r'parab[ée]ns': 3.0, r'excelente': 2.5, r'maravilhoso': 2.5,
            r'perfeito': 2.5, r'incr[ií]vel': 2.0, r'fant[aá]stico': 2.0
        }
        
        for padrao, peso in elogios.items():
            if re.search(padrao, texto_lower):
                score += peso
                
        festas = {
            r'feliz\s+natal': 3.0, r'ano\s+novo': 2.8, r'boas\s+festas': 2.5,
            r'felicidades': 1.5, r'sa[uú]de\s+e\s+paz': 1.5
        }
        
        for padrao, peso in festas.items():
            if re.search(padrao, texto_lower):
                score += peso
                
        return score
    
    def _analisar_contexto_rapido(self, texto_lower: str) -> str:
        sociais_fortes = [
            r'feliz\s+natal', r'ano\s+novo', r'boas\s+festas', 
            r'parab[ée]ns\s+pelo', r'agradeço\s+pelo', r'muito\s+obrigad[ao]',
            r'desejo.*feliz', r'felicidades'
        ]
        
        for padrao in sociais_fortes:
            if re.search(padrao, texto_lower):
                return "social_forte"
                
        urgentes = [
            r'urgente', r'cr[ií]tico', r'emerg[êe]ncia', r'fora\s+do\s+ar',
            r'n[aã]o\s+funciona', r'erro\s+\d+', r'sistema\s+parou',
            r'prioridade', r'imediato', r'bloqueado'
        ]
        
        for padrao in urgentes:
            if re.search(padrao, texto_lower):
                return "urgente"
                
        return "neutro"