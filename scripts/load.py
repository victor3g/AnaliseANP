import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

TRUSTED_DIR = "./data/trusted"

load_dotenv()

DATABASE_URI = os.getenv("DATABASE_URI")

if not DATABASE_URI:
    raise ValueError("A variável DATABASE_URI não foi encontrada.")


def carregar_modelar_dados():

    try:

        engine = create_engine(DATABASE_URI)

        print("Limpeza preventiva...")

        with engine.connect() as conn:

            conn.execute(text("""
                DROP TABLE IF EXISTS
                    fato_tancagem,
                    fato_distribuidoras,
                    fato_postos,
                    fato_populacao,
                    dim_uf,
                    tb_tancagem,
                    tb_distribuicao,
                    tb_revendedores,
                    tb_populacao
                CASCADE;
            """))

            conn.commit()

        print("Tabelas antigas removidas com sucesso!")

        tabelas = {
            "populacao.csv": {
                "nome": "tb_populacao",
                "sep": ";"
            },

            "revendedores.csv": {
                "nome": "tb_revendedores",
                "sep": ";"
            },

            "distribuicao.csv": {
                "nome": "tb_distribuicao",
                "sep": ";"
            },

            "tancagem.csv": {
                "nome": "tb_tancagem",
                "sep": ","
            }
        }

        #Carga dos dados para o banco
        for arquivo, config in tabelas.items():

            caminho = os.path.join(TRUSTED_DIR, arquivo)

            if not os.path.exists(caminho):
                print(f"Arquivo não encontrado: {caminho}")
                continue

            print(f"Carregando {arquivo}...")

            df = pd.read_csv(
                caminho,
                sep=config["sep"],
                encoding="utf-8"
            )

            df.to_sql(
                config["nome"],
                engine,
                if_exists="replace",
                index=False
            )

            print(f"{config['nome']} carregada com sucesso.")

        print("Criando modelo analítico...")

        with engine.connect() as conn:

            #Dimensão UF
            conn.execute(text("""
                CREATE TABLE dim_uf AS
                SELECT DISTINCT
                    LOWER(uf) AS uf,
                    INITCAP(nome) AS nome_uf,
                    UPPER(regiao_sigla) AS regiao_sigla,
                    INITCAP(regiao_nome) AS regiao_nome
                FROM tb_populacao;
            """))

            conn.execute(text("""
                ALTER TABLE dim_uf
                ADD CONSTRAINT pk_dim_uf PRIMARY KEY (uf);
            """))

            #Fato população
            conn.execute(text("""
                CREATE TABLE fato_populacao AS
                SELECT
                    LOWER(uf) AS uf,
                    periodo,
                    populacao_estimada
                FROM tb_populacao;
            """))

            #Fato postos
            conn.execute(text("""
                CREATE TABLE fato_postos AS
                SELECT
                    ROW_NUMBER() OVER () AS id_posto,
                    codigoisimp,
                    autorizacao,
                    datapublicacao,
                    razaosocial,
                    cnpj,
                    endereco,
                    complemento,
                    bairro,
                    cep,
                    LOWER(uf) AS uf,
                    INITCAP(municipio) AS municipio,
                    INITCAP(bandeira) AS bandeira,
                    datavinculacao
                FROM tb_revendedores;
            """))

            conn.execute(text("""
                ALTER TABLE fato_postos
                ADD CONSTRAINT pk_fato_postos PRIMARY KEY (id_posto);
            """))

            #Fato distribuidoras
            conn.execute(text("""
                CREATE TABLE fato_distribuidoras AS
                SELECT
                    ROW_NUMBER() OVER () AS id_distribuidora,
                    codigoagente,
                    "codigoagentei-simp" AS codigoagentei_simp,
                    cnpj,
                    INITCAP(nomereduzido) AS nome_reduzido,
                    INITCAP(razaosocial) AS razao_social,
                    INITCAP(enderecodamatriz) AS endereco_matriz,
                    INITCAP(bairro) AS bairro,
                    INITCAP(municipio) AS municipio,
                    LOWER(uf) AS uf,
                    cep,
                    INITCAP(situacao) AS situacao,
                    iniciodasituacao,
                    datapublicacao,
                    INITCAP(tipodeato) AS tipo_ato,
                    INITCAP(tipodeautorizacao) AS tipo_autorizacao,
                    numerodaautorizacao
                FROM tb_distribuicao;
            """))

            conn.execute(text("""
                ALTER TABLE fato_distribuidoras
                ADD CONSTRAINT pk_fato_distribuidoras PRIMARY KEY (id_distribuidora);
            """))

            #Fato Tancagem
            conn.execute(text("""
                CREATE TABLE fato_tancagem AS
                SELECT
                    ROW_NUMBER() OVER () AS id_tancagem,
                    data,
                    INITCAP(nomeempresarial) AS nome_empresarial,
                    LOWER(uf) AS uf,
                    INITCAP(municipio) AS municipio,
                    cnpj,
                    codinstalacao,
                    INITCAP(segmento) AS segmento,
                    INITCAP(detalheinstalacao) AS detalhe_instalacao,
                    tag,
                    INITCAP(tipodaunidade) AS tipo_unidade,
                    INITCAP(grupodeprodutos) AS grupo_produtos,
                    tancagemm3
                FROM tb_tancagem;
            """))

            conn.execute(text("""
                ALTER TABLE fato_tancagem
                ADD CONSTRAINT pk_fato_tancagem PRIMARY KEY (id_tancagem);
            """))

            #Relacionamentos
            conn.execute(text("""
                ALTER TABLE fato_postos
                ADD CONSTRAINT fk_postos_uf
                FOREIGN KEY (uf)
                REFERENCES dim_uf(uf);
            """))

            conn.execute(text("""
                ALTER TABLE fato_distribuidoras
                ADD CONSTRAINT fk_distribuidoras_uf
                FOREIGN KEY (uf)
                REFERENCES dim_uf(uf);
            """))

            conn.execute(text("""
                ALTER TABLE fato_tancagem
                ADD CONSTRAINT fk_tancagem_uf
                FOREIGN KEY (uf)
                REFERENCES dim_uf(uf);
            """))

            conn.execute(text("""
                ALTER TABLE fato_populacao
                ADD CONSTRAINT fk_populacao_uf
                FOREIGN KEY (uf)
                REFERENCES dim_uf(uf);
            """))

            conn.commit()

        print("Modelo analítico criado com sucesso!")

    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":

    print("Iniciando processo de carga...")

    carregar_modelar_dados()