import json

catalogo_path = 'catalogo.json'

def extrai_tags(arquivo_json):
    """
    Extrai tags únicas de um arquivo JSON.
    
    :arquivo_json: Caminho para o arquivo JSON.
    :return: Conjunto de tags únicas.
    """
    with open(arquivo_json, 'r', encoding='utf-8') as file:
        catalogo = json.load(file)

    tags_unicas = set()

    for item in catalogo:
        for tag in item.get('tags', []):
            tags_unicas.add(tag)

    return tags_unicas

tags_unicas = extrai_tags(catalogo_path)

