import json
import os

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

# Para compatibilidade, carrega as tags se executado diretamente
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    catalogo_path = os.path.join(current_dir, '..', '..', 'catalogo.json')
    tags_unicas = extrai_tags(catalogo_path)
    print(f"Tags encontradas: {sorted(list(tags_unicas))}")

