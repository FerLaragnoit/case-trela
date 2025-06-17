Assistente de Recomendação de Refeições
Um assistente conversacional que recomenda refeições baseado em preferências do usuário. Utiliza GPT-4o com Responses API da OpenAI para interpretar pedidos naturais como "quero um prato vegano barato" e retorna sugestões do catálogo.

Como usar
Instale as dependências: pip install -r requirements.txt Configure sua API key da OpenAI no arquivo .env: OPENAI_API_KEY=sua-chave Execute: streamlit run app.py

Funcionalidades
O sistema responde a pedidos como "prato sem lactose até R$55", "quero o mais barato", "refeição com proteína e arroz". Usa um catálogo JSON local com pratos que incluem preço, tags dietéticas e descrições. O agente analisa a intenção do usuário via Responses API, executa buscas no catálogo e formata respostas amigáveis.

Arquivos principais
agent_executor.py: Agente principal com Responses API
procura_catalogo.py: Funções de busca no catálogo
catalogo.json: Base de dados das refeições
app.py: Interface web Streamlit
O sistema não mantém memória entre conversas e funciona com structured outputs para garantir respostas consistentes.
