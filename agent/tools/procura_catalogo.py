import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
catalogo_path = os.path.join(current_dir, '..', '..', 'catalogo.json')

try:
    with open(catalogo_path, 'r', encoding='utf-8') as file:
        catalogo = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    catalogo = []

def search_catalog(filters: dict) -> list:
    """
    Busca no catálogo de refeições baseado nos filtros fornecidos.
    
    Args:
        filters (dict): Dicionário com os filtros:
            - budget (float): Preço máximo
            - incluir_tags (list): Tags que devem estar presentes
            - excluir_tags (list): Tags que devem ser excluídas
            - ingredientes_obrigatorios (list): Ingredientes/palavras que devem estar no nome ou descrição
    
    Returns:
        list: Lista de até 10 refeições ordenadas por preço
    """
    if not catalogo:
        return []
    
    budget = filters.get('budget')
    incluir = set(filters.get('incluir_tags', []))
    excluir = set(filters.get('excluir_tags', []))
    requisitos = filters.get('ingredientes_obrigatorios', [])

    resultados = []
    
    for item in catalogo:
        if budget is not None and item['preco'] > budget:
            continue
        
        item_tags = set(item['tags'])
        if incluir and not incluir.issubset(item_tags):
            continue
        
        if excluir and excluir.intersection(item_tags):
            continue
        
        if requisitos:
            text = (item['nome'] + ' ' + item['descricao']).lower()
            # Verifica se ALGUMAS das palavras requisitadas estão no texto
            if not any(requisito.lower() in text for requisito in requisitos):
                continue

        resultados.append(item)

    resultados.sort(key=lambda x: x['preco'])
    
    return resultados[:10]

def get_cheapest_item() -> dict:
    """
    Retorna o prato mais barato do catálogo.
    
    Returns:
        dict: Prato mais barato ou None se catálogo vazio
    """
    if not catalogo:
        return None
    
    return min(catalogo, key=lambda x: x['preco'])


def get_most_expensive_item() -> dict:
    """
    Retorna o prato mais caro do catálogo.
    
    Returns:
        dict: Prato mais caro ou None se catálogo vazio
    """
    if not catalogo:
        return None
    
    return max(catalogo, key=lambda x: x['preco'])


def get_price_range() -> dict:
    """
    Retorna informações sobre a faixa de preços do catálogo.
    
    Returns:
        dict: Informações de preços (min, max, média)
    """
    if not catalogo:
        return {"min_price": 0, "max_price": 0, "avg_price": 0, "total_items": 0}
    
    precos = [item['preco'] for item in catalogo]
    
    return {
        "min_price": min(precos),
        "max_price": max(precos),
        "avg_price": round(sum(precos) / len(precos), 2),
        "total_items": len(catalogo)
    }

