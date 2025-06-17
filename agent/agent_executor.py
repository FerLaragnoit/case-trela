import os
import json
from openai import OpenAI
from typing import Dict, List, Optional

from .tools.procura_catalogo import search_catalog, get_cheapest_item, get_most_expensive_item, get_price_range

class MealRecommendationAgent:
    """
    Agente de recomendação de refeições usando GPT-4o com Responses API
    """
    
    def __init__(self, api_key: str = None):
        """
        Inicializa o agente com a API da OpenAI
        
        Args:
            api_key (str): Chave da API da OpenAI. Se não fornecida, busca na variável de ambiente.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("API key da OpenAI não encontrada. Configure OPENAI_API_KEY ou passe como parâmetro.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
        
        self.response_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "meal_recommendation_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "action_taken": {
                            "type": "string",
                            "enum": ["search_catalog", "get_cheapest_item", "get_most_expensive_item", "get_price_range"],
                            "description": "Ação que será executada baseada na solicitação do usuário"
                        },
                        "search_params": {
                            "type": "object",
                            "properties": {
                                "budget": {"type": ["number", "null"]},
                                "incluir_tags": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "excluir_tags": {
                                    "type": "array", 
                                    "items": {"type": "string"}
                                },
                                "ingredientes_obrigatorios": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "additionalProperties": False
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explicação de por que esta ação foi escolhida"
                        },
                        "user_intent": {
                            "type": "string",
                            "description": "Interpretação da intenção do usuário"
                        }
                    },
                    "required": ["action_taken", "reasoning", "user_intent"],
                    "additionalProperties": False
                }
            }
        }
        
        self.system_prompt = """
Você é um assistente especializado em recomendação de refeições. Sua resposta deve seguir EXATAMENTE o schema JSON fornecido.

ANÁLISE E DECISÃO:
1. Analise a solicitação do usuário
2. Determine qual ação tomar baseada nas regras
3. Prepare os parâmetros necessários (se aplicável)
4. Forneça uma explicação clara

MAPEAMENTO DE AÇÕES:
- "mais barato", "econômico", "menor preço", "mais em conta" → action_taken: "get_cheapest_item"
- "mais caro", "premium", "maior preço" → action_taken: "get_most_expensive_item"  
- "faixa de preço", "preços disponíveis" → action_taken: "get_price_range"
- Qualquer outra busca por comida → action_taken: "search_catalog"

TAGS DISPONÍVEIS (use exatamente):
- "vegano", "sem lactose", "picante", "sem gluten", "sem açucar"

INTERPRETAÇÃO INTELIGENTE:
- "proteína" → ingredientes_obrigatorios: ["frango", "carne", "peixe", "ovo", "tofu", "camarão"]
- "arroz" → ingredientes_obrigatorios: ["arroz"]
- "legumes" → ingredientes_obrigatorios: ["legumes", "brócolis", "cenoura"]
- "saudável" → IGNORE (todos os pratos são saudáveis)
- "apimentado"/"picante" → incluir_tags: ["picante"]

EXEMPLOS DE RESPOSTA:
1. "Quero o prato mais barato" →
   {
     "action_taken": "get_cheapest_item",
     "reasoning": "Usuário pediu especificamente pelo prato mais barato",
     "user_intent": "Encontrar a opção mais econômica do cardápio"
   }

2. "Prato vegano com proteína até R$40" →
   {
     "action_taken": "search_catalog",
     "search_params": {
       "budget": 40,
       "incluir_tags": ["vegano"],
       "ingredientes_obrigatorios": ["frango", "carne", "peixe", "ovo", "tofu", "camarão"]
     },
     "reasoning": "Busca por prato vegano com proteína dentro do orçamento especificado",
     "user_intent": "Encontrar refeição vegana com fonte de proteína respeitando limite de preço"
   }

IMPORTANTE: Sempre preencha action_taken, reasoning e user_intent. Use search_params apenas para search_catalog.
"""

    def _execute_function(self, function_name: str, arguments: dict):
        """
        Executa uma função baseada na resposta estruturada da Responses API
        
        Args:
            function_name (str): Nome da função
            arguments (dict): Argumentos da função
            
        Returns:
            dict: Resultado da execução da função
        """
        if function_name == "search_catalog":
            try:
                results = search_catalog(arguments)
                return {
                    "success": True,
                    "results": results,
                    "count": len(results)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "count": 0
                }
        elif function_name == "get_cheapest_item":
            try:
                result = get_cheapest_item()
                return {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        elif function_name == "get_most_expensive_item":
            try:
                result = get_most_expensive_item()
                return {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        elif function_name == "get_price_range":
            try:
                result = get_price_range()
                return {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "error": f"Função '{function_name}' não encontrada"
            }

    def _relax_search_filters(self, original_args: dict) -> dict:
        """
        Relaxa os filtros de busca para tentar encontrar resultados
        
        Args:
            original_args (dict): Argumentos originais
            
        Returns:
            dict: Argumentos relaxados
        """
        relaxed = original_args.copy()
        
        if "ingredientes_obrigatorios" in relaxed and len(relaxed["ingredientes_obrigatorios"]) > 1:
            relaxed["ingredientes_obrigatorios"] = relaxed["ingredientes_obrigatorios"][:1]
        
        if "excluir_tags" in relaxed:
            del relaxed["excluir_tags"]
            
        if "budget" in relaxed:
            relaxed["budget"] = relaxed["budget"] * 1.2
        
        return relaxed

    def chat(self, user_message: str) -> str:
        """
        Processa uma mensagem do usuário usando Responses API
        
        Args:
            user_message (str): Mensagem do usuário
            
        Returns:
            str: Resposta do agente
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=self.response_schema
            )
            try:
                response_content = response.choices[0].message.content
                if isinstance(response_content, str):
                    decision_json = json.loads(response_content)
                else:
                    decision_json = json.loads(str(response_content))
            except (json.JSONDecodeError, AttributeError) as e:
                return f"Erro ao processar resposta estruturada: {str(e)}. Tente novamente!"
            
            action = decision_json["action_taken"]
            reasoning = decision_json["reasoning"]
            user_intent = decision_json["user_intent"]
            
            if action == "search_catalog":
                search_params = decision_json.get("search_params", {})
                clean_params = {k: v for k, v in search_params.items() if v is not None and v != []}
                function_result = self._execute_function(action, clean_params)
                
                if function_result.get("count", 0) == 0 and clean_params:
                    relaxed_params = self._relax_search_filters(clean_params)
                    if relaxed_params != clean_params:
                        function_result = self._execute_function(action, relaxed_params)
                        
            else:
                function_result = self._execute_function(action, {})
            
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um assistente de recomendação de refeições. Formate uma resposta amigável e útil baseada nos resultados fornecidos."
                    },
                    {
                        "role": "user", 
                        "content": f"""
Solicitação do usuário: {user_message}
Intenção identificada: {user_intent}
Ação tomada: {action}
Raciocínio: {reasoning}
Resultado da busca: {json.dumps(function_result, ensure_ascii=False, indent=2)}

Formate uma resposta amigável e útil para o usuário, incluindo os pratos encontrados (se houver) com nome, preço e descrição.
"""
                    }
                ]
            )
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            return f"Desculpe, ocorreu um erro: {str(e)}. Tente novamente!"

    def get_recommendation(self, user_request: str) -> str:
        """
        Método simplificado para obter recomendações
        
        Args:
            user_request (str): Solicitação do usuário
            
        Returns:
            str: Recomendação formatada
        """
        return self.chat(user_request)
