import requests
import csv
import time
import os

RAW_DIR = "./data/raw"

def criar_csv_populacao():
    url_base = "https://brasilapi.com.br/api/ibge/uf/v1"
    
    print("Consultando a lista geral de estados na Brasil API...")
    
    try:
        response = requests.get(url_base)
        response.raise_for_status() 
        dados_estados = response.json()
        
        nome_arquivo = os.path.join(RAW_DIR, "populacao.csv")
        
        with open(nome_arquivo, mode='w', newline='', encoding='utf-8-sig') as arquivo_csv:
            colunas = ['id', 'uf', 'nome', 'regiao_sigla', 'regiao_nome', 'populacao_estimada', 'periodo']
            escritor = csv.DictWriter(arquivo_csv, fieldnames=colunas, delimiter=';')
            escritor.writeheader()
            
            for estado in dados_estados:
                sigla = estado.get('sigla', '')
                populacao = estado.get('populacao_estimada')
                periodo = estado.get('periodo')
                
                # Regra para verificar se a população é inválida (None, 0 ou vazia)
                if not populacao:
                    try:
                        # Chama a rota individual do estado, ativando os provedores alternativos
                        url_especifica = f"{url_base}/{sigla}?providers=dados-abertos-br,gov,wikipedia"
                        res_estado = requests.get(url_especifica)
                        
                        if res_estado.status_code == 200:
                            dados_especificos = res_estado.json()
                            populacao = dados_especificos.get('populacao_estimada')
                            periodo = dados_especificos.get('periodo')
                            
                        # Pequena pausa para não sobrecarregar a API com muitas requisições seguidas
                        time.sleep(0.5) 
                    except requests.exceptions.RequestException:
                        print(f"Falha ao buscar dados extras para {sigla}.")
                
                # Monta a linha tratando os valores finais para que não fiquem em branco no CSV
                linha = {
                    'id': estado.get('id', ''),
                    'uf': sigla,
                    'nome': estado.get('nome', ''),
                    'regiao_sigla': estado.get('regiao', {}).get('sigla', ''),
                    'regiao_nome': estado.get('regiao', {}).get('nome', ''),
                    'populacao_estimada': populacao if populacao else 'Dados Indisponíveis',
                    'periodo': periodo if periodo else 'Dados Indisponíveis'
                }
                
                escritor.writerow(linha)
                
        print(f"\nOperação concluída com sucesso!")
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    criar_csv_populacao()