import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

TRUSTED_DIR = './data/trusted'

load_dotenv()

DATABASE_URI = os.getenv('DATABASE_URI')
if not DATABASE_URI:
    raise ValueError("A variável DATABASE_URI não foi encontrada.")

def carregar_modelar_dados():
    try:
        #Conexão com o banco de dados
        engine = create_engine(DATABASE_URI)

        #Limpeza prévia
        print("Limpando tabelas existentes...")
        with engine.connect() as conn:
            conn.execute(text('''
                              DROP TABLE IF EXISTS tb_tancagem, tb_distribuicao, tb_revendedores, tb_populacao CASCADE;
                              '''))
            conn.commit()
        print("Tabelas limpas com sucesso!")

        #Configuração das tabelas
        tabelas = {
            "populacao.csv": {"nome": "tb_populacao", "sep": ";", "tipo_string": ["uf"]},
            "revendedores.csv": {"nome": "tb_revendedores", "sep": ";", "tipo_string": ["cnpj", "uf"]},
            "distribuicao.csv": {"nome": "tb_distribuicao", "sep": ";", "tipo_string": ["cnpj", "uf"]},
            "tancagem.csv": {"nome": "tb_tancagem", "sep": ",", "tipo_string": ["uf"]}
        }

        #Ciclo de Carga
        for arquivo, config in tabelas.items():
            caminho_arquivo = os.path.join(TRUSTED_DIR, arquivo)
            
            if os.path.exists(caminho_arquivo):
                print(f"Enviando {config['nome']} para o banco...")

                tipo = {col: str for col in config['tipo_string']}
                
                df = pd.read_csv(caminho_arquivo, sep=config['sep'], encoding='utf-8', dtype=tipo)
                
                #Envia para o PostgreSQL
                df.to_sql(config['nome'], engine, if_exists='replace', index=False)
                print(f"Tabela {config['nome']} carregada com sucesso!")
            else:
                print(f"Aviso: {caminho_arquivo} não encontrado.")

        #Modelagem Relacional
        print("\nAplicando PKs e FKs...")
        with engine.connect() as conn:

            conn.execute(text('ALTER TABLE tb_populacao ADD PRIMARY KEY ("uf");'))
            conn.execute(text('ALTER TABLE tb_revendedores ADD PRIMARY KEY ("cnpj");'))
            conn.execute(text('ALTER TABLE tb_distribuicao ADD PRIMARY KEY ("cnpj");'))
            
            conn.execute(text('''
                ALTER TABLE tb_distribuicao
                ADD CONSTRAINT fk_dist_uf FOREIGN KEY ("uf") REFERENCES tb_populacao ("uf");
            '''))
            
            conn.execute(text('''
                ALTER TABLE tb_revendedores
                ADD CONSTRAINT fk_rev_uf FOREIGN KEY ("uf") REFERENCES tb_populacao ("uf");
            '''))
            
            conn.commit()
            print("Modelagem concluída!")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    print("Iniciando...")
    carregar_modelar_dados()