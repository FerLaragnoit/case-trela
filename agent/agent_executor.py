import os
import json
from openai import OpenAI
from typing import Dict, List, Optional

from .tools.procura_catalogo import search_catalog, get_cheapest_item, get_most_expensive_item, get_price_range
from .tools.extrai_filtro import extrai_tags

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
        
        # Carrega as tags únicas do catálogo
        try:
            catalogo_path = os.path.join(os.path.dirname(__file__), '..', 'catalogo.json')
            self.tags_disponiveis = list(extrai_tags(catalogo_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar tags do catálogo: {e}")
            self.tags_disponiveis = []
        
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
                        },                        "search_params": {
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
                            "required": ["budget", "incluir_tags", "excluir_tags", "ingredientes_obrigatorios"],
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
                    "required": ["action_taken", "search_params", "reasoning", "user_intent"],
                    "additionalProperties": False
                }            }        }
        
        self.system_prompt = f"""
Assistente de recomendação de refeições. Responda EXATAMENTE no formato JSON.

TAGS DISPONÍVEIS: {', '.join(self.tags_disponiveis)}

AÇÕES:
- "mais barato" → "get_cheapest_item"
- "mais caro" → "get_most_expensive_item"  
- "faixa de preço" → "get_price_range"
- Qualquer busca → "search_catalog"

MAPEAMENTO TAGS:
- "sem lactose" → ["sem lactose"]
- "vegano" → ["vegano"]
- "picante/apimentado" → ["picante"]
- "sem gluten" → ["sem gluten"]
- "sem açúcar" → ["sem açucar"]

INGREDIENTES:
- "proteína" → ["frango", "carne", "peixe", "ovo", "tofu", "camarão"]
- "arroz" → ["arroz"]
- "legumes" → ["legumes", "brócolis", "cenoura"]

FORMATO:
{{
  "action_taken": "search_catalog",
  "search_params": {{
    "budget": null,
    "incluir_tags": [],
    "excluir_tags": [],
    "ingredientes_obrigatorios": []
  }},
  "reasoning": "explicação breve",
  "user_intent": "intenção do usuário"
}}

IMPORTANTE: SEMPRE inclua search_params com TODOS os campos, mesmo vazios.
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

    def _map_user_text_to_tags(self, user_text: str) -> List[str]:
        """
        Mapeia o texto do usuário para as tags disponíveis no catálogo
        
        Args:
            user_text (str): Texto do usuário
            
        Returns:
            List[str]: Lista de tags encontradas
        """
        user_text_lower = user_text.lower()
        tags_encontradas = []
        
        # Mapeamento de termos comuns para tags
        mapeamentos = {
            'sem lactose': ['sem lactose'],
            'intolerante a lactose': ['sem lactose'],
            'lactose': ['sem lactose'],
            'vegano': ['vegano'],
            'vegan': ['vegano'],
            'apimentado': ['picante'],
            'picante': ['picante'],
            'sem gluten': ['sem gluten'],
            'sem açucar': ['sem açucar'],
            'sem açúcar': ['sem açucar'],
        }
        
        # Busca por mapeamentos diretos
        for termo, tags in mapeamentos.items():
            if termo in user_text_lower:
                for tag in tags:
                    if tag in self.tags_disponiveis:
                        tags_encontradas.append(tag)
        
        # Busca direta nas tags disponíveis
        for tag in self.tags_disponiveis:
            if tag.lower() in user_text_lower:
                tags_encontradas.append(tag)
        
        return list(set(tags_encontradas))  # Remove duplicatas

    def _optimize_search_params(self, user_text: str, search_params: dict) -> dict:
        """
        Otimiza os parâmetros de busca usando as tags reais do catálogo
        
        Args:
            user_text (str): Texto original do usuário
            search_params (dict): Parâmetros originais
            
        Returns:
            dict: Parâmetros otimizados
        """
        optimized_params = search_params.copy()
        
        # Mapeia o texto do usuário para tags reais
        tags_encontradas = self._map_user_text_to_tags(user_text)
        
        # Se encontrou tags específicas, use-as
        if tags_encontradas:
            current_tags = set(optimized_params.get('incluir_tags', []))
            current_tags.update(tags_encontradas)
            optimized_params['incluir_tags'] = list(current_tags)
        
        return optimized_params

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
                # Otimiza os parâmetros usando as tags reais do catálogo
                optimized_params = self._optimize_search_params(user_message, search_params)
                clean_params = {k: v for k, v in optimized_params.items() if v is not None and v != []}
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
