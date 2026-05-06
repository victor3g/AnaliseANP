import os
import requests

URLS_ANP = {
    "postos": "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/arquivos-dados-cadastrais-dos-revendedores-varejistas-de-combustiveis-automotivos/dados-cadastrais-revendedores-varejistas-combustiveis-automoveis.csv", 
    "distribuidoras": "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/dcl/planilha-aea-filiais.csv",
    "tanques": "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/arquivos-tancagem-do-abastecimento-nacional-de-combustiveis/dados-abertos/2026/abril.csv"
}

RAW_DIR = "../data/raw"

def criar_pasta(caminho):
    if not os.path.exists(caminho):
        os.makedirs(caminho)
        print(f"Pasta criada: {caminho}")

def baixar_arquivo(nome, url, pasta_destino):
    try:
        print(f"Iniciando download de: {nome}...")
        resposta = requests.get(url, stream=True)
        resposta.raise_for_status()
        
        extensao = url.split('.')[-1]
        caminho_arquivo = os.path.join(pasta_destino, f"{nome}_bruto.{extensao}")
        
        with open(caminho_arquivo, 'wb') as arquivo:
            for chunk in resposta.iter_content(chunk_size=8192):
                arquivo.write(chunk)
                
        print(f"Sucesso! {nome} salvo em: {caminho_arquivo}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar {nome}: {e}\n")


if __name__ == "__main__":
    print("=== Iniciando Pipeline de Extração ===")
    criar_pasta(RAW_DIR)
    
    for nome_entidade, link in URLS_ANP.items():
        baixar_arquivo(nome_entidade, link, RAW_DIR)
        
    print("=== Extração Concluída ===")