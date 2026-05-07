import os
import glob
import pandas as pd
import re
import csv
import unicodedata

RAW_DIR = './data/raw/'
TRUSTED_DIR = './data/trusted/'

os.makedirs(TRUSTED_DIR, exist_ok=True)

def analyze_file_structure(file_path):
    
    encoding = 'utf-8'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.readline()
    except UnicodeDecodeError:
        encoding = 'latin1'

    #verifica as primeiras 100 linhas
    with open(file_path, 'r', encoding=encoding) as f:
        lines = [line.strip() for line in f.readlines()[:100] if line.strip()]
        
    if not lines:
        return encoding, ';', 0
        
    sep_counts = {';': sum(l.count(';') for l in lines), ',': sum(l.count(',') for l in lines)}
    delimiter = ';' if sep_counts[';'] >= sep_counts[','] else ','

    #Encontra a linha do cabeçalho baseada no seu padrão estrito
    header_idx = 0
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.reader(f, delimiter=delimiter)
        for i, row in enumerate(reader):
            row = [cell.strip() for cell in row]
            
            if not row or any(cell == '' for cell in row):
                continue
            
            if len(set(row)) != len(row):
                continue
            
            text_cells = sum(1 for cell in row if not cell.replace('.', '').replace('-', '').isdigit())
            if text_cells >= len(row) / 2:
                header_idx = i
                break

    return encoding, delimiter, header_idx

def safe_clean_cnpj(val):
    val_str = str(val).strip()
    
    if not val_str:
        return val
        
    # Remove pontuações
    val_clean = re.sub(r'\D', '', val_str)
    
    if not val_clean:
        return val
        
    return val_clean.zfill(14)

#Remove espaços invisíveis nas pontas, retira acentos e converte para minúsculas.
def padronizar_texto(texto):

    if not isinstance(texto, str):
        return texto
    
    texto_sem_acento = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    
    return texto_sem_acento.lower().strip()

def processar_arquivos():
    csv_files = glob.glob(os.path.join(RAW_DIR, '*.csv'))
    
    if not csv_files:
        print(f"Nenhum arquivo CSV encontrado em: {RAW_DIR}")
        return

    for file in csv_files:
        filename = os.path.basename(file)
        print(f"\nIniciando processamento seguro: {filename}")
        
        # Inspeção detalhada
        encoding, delimiter, header_idx = analyze_file_structure(file)
        print(f"Separador: '{delimiter}' | Cabeçalho na linha: {header_idx}")
        
        df = pd.read_csv(
            file, 
            sep=delimiter, 
            skiprows=header_idx, 
            dtype=str, 
            encoding=encoding, 
            na_filter=False 
        )

        #Padronização dos Nomes das Colunas
        df.columns = [padronizar_texto(col).replace(' ', '') for col in df.columns]

        #Limpeza de dados
        for col in df.columns:
            df[col] = df[col].apply(padronizar_texto)

        #Limpeza de CNPJ
        cnpj_columns = [col for col in df.columns if 'cnpj' in str(col).lower()]
        if not cnpj_columns:
            print("Sem CNPJs neste arquivo.")
        
        for cnpj_col in cnpj_columns:
            print(f"Limpando coluna: {cnpj_col}")
            df[cnpj_col] = df[cnpj_col].apply(safe_clean_cnpj)

        output_path = os.path.join(TRUSTED_DIR, filename)
        df.to_csv(output_path, sep=delimiter, index=False, encoding='utf-8')
        print("Salvo com sucesso!")

if __name__ == "__main__":
    processar_arquivos()