from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from typing import Optional, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

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
            
            denominacao_row = soup.find('td', text='Denominação:')
            if denominacao_row:
                nome_empresa = denominacao_row.find_next('td').text.strip()
            else:
                nome_empresa = "Nome não encontrado"
            
            cae_row = soup.find('td', text='Atividade (CAE):')
            if cae_row:
                cae = cae_row.find_next('td').text.strip()
            else:
                cae = "CAE não encontrado"
            
            return nome_empresa, cae
            
        except Exception as e:
            print(f"Erro ao processar NIF {nif}: {str(e)}")
            return None

class ScraperGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("EInforma Scraper")
        self.window.geometry("600x400")
        
        # Variáveis para armazenar os caminhos dos arquivos
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Seleção do arquivo de entrada
        ttk.Label(main_frame, text="Arquivo CSV de entrada:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_path, width=50).grid(row=1, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Procurar", command=self.browse_input).grid(row=1, column=1, padx=5)
        
        # Seleção do arquivo de saída
        ttk.Label(main_frame, text="Arquivo CSV de saída:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(row=3, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Procurar", command=self.browse_output).grid(row=3, column=1, padx=5)
        
        # Barra de progresso
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Log de status
        self.log_text = tk.Text(main_frame, height=10, width=60)
        self.log_text.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Botão de início
        ttk.Button(main_frame, text="Iniciar Processamento", command=self.start_processing).grid(row=6, column=0, columnspan=2, pady=10)
        
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo CSV de entrada",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar arquivo CSV como",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        
    def process_csv(self):
        try:
            input_path = self.input_path.get()
            output_path = self.output_path.get()
            
            df = pd.read_csv(input_path)
            
            if 'NIF' not in df.columns:
                messagebox.showerror("Erro", "O CSV deve conter uma coluna 'NIF'")
                return
            
            scraper = EInformaScraper()
            total_rows = len(df)
            
            df['Nome_Empresa'] = None
            df['CAE'] = None
            
            self.progress['maximum'] = total_rows
            
            for idx, row in df.iterrows():
                nif = str(row['NIF'])
                self.log(f"Processando NIF {nif}...")
                result = scraper.fetch_company_info(nif)
                if result:
                    nome_empresa, cae = result
                    df.at[idx, 'Nome_Empresa'] = nome_empresa
                    df.at[idx, 'CAE'] = cae
                else:
                    df.at[idx, 'Nome_Empresa'] = "Não encontrado"
                    df.at[idx, 'CAE'] = "Não encontrado"
                
                self.progress['value'] = idx + 1
                self.window.update_idletasks()
            
            df.to_csv(output_path, index=False)
            self.log(f"Processamento concluído! Resultados salvos em {output_path}")
            messagebox.showinfo("Sucesso", "Processamento concluído com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante o processamento: {str(e)}")
            
    def start_processing(self):
        if not self.input_path.get() or not self.output_path.get():
            messagebox.showerror("Erro", "Por favor, selecione os arquivos de entrada e saída.")
            return
            
        # Inicia o processamento em uma thread separada para não travar a interface
        threading.Thread(target=self.process_csv, daemon=True).start()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = ScraperGUI()
    app.run()