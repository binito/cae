from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from typing import Optional, Tuple

class EInformaScraper:
    def __init__(self):
        self.base_url_template = "https://www.einforma.pt/servlet/app/portal/ENTP/prod/ETIQUETA_EMPRESA/nif/{nif}/source/search/campaign/fichaemp/"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_company_info(self, nif: str) -> Optional[Tuple[str, str]]:
        try:
            time.sleep(2)
            url = self.base_url_template.format(nif=nif)
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar Denominação
            denominacao_row = soup.find('td', text='Denominação:')
            if denominacao_row:
                nome_empresa = denominacao_row.find_next('td').text.strip()
            else:
                nome_empresa = "Nome não encontrado"
            
            # Buscar Atividade (CAE)
            cae_row = soup.find('td', text='Atividade (CAE):')
            if cae_row:
                cae = cae_row.find_next('td').text.strip()
            else:
                cae = "CAE não encontrado"
            
            return nome_empresa, cae
            
        except Exception as e:
            print(f"Erro ao processar NIF {nif}: {str(e)}")
            return None

def process_csv(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    
    if 'NIF' not in df.columns:
        raise ValueError("O CSV deve conter uma coluna 'NIF'")
    
    scraper = EInformaScraper()
    
    df['Nome_Empresa'] = None
    df['CAE'] = None
    
    for idx, row in df.iterrows():
        nif = str(row['NIF'])
        print(f"Processando NIF {nif}...")
        result = scraper.fetch_company_info(nif)
        if result:
            nome_empresa, cae = result
            df.at[idx, 'Nome_Empresa'] = nome_empresa
            df.at[idx, 'CAE'] = cae
        else:
            df.at[idx, 'Nome_Empresa'] = "Não encontrado"
            df.at[idx, 'CAE'] = "Não encontrado"
    
    df.to_csv(output_path, index=False)
    print(f"Resultados salvos em {output_path}")

if __name__ == "__main__":
    input_csv = r"C:\Users\jorge\Downloads\CAE.csv"
    output_csv = r"C:\Users\jorge\Downloads\resultados_cae.csv"
    process_csv(input_csv, output_csv)