import os
import logging
from etl.clean_data import clean_master
from etl.load_to_db import load

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Garante que os caminhos sejam relativos ao script
# Isso é importante para rodar em diferentes ambientes
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    logging.info("Iniciando processo de ETL...")

    # 1. Limpa os dados e gera o master.csv
    logging.info("Passo 1: Limpando dados e gerando master.csv")
    try:
        clean_master()
        logging.info("Passo 1 concluído com sucesso.")
    except Exception as e:
        logging.error(f"Erro na execução do clean_master: {e}", exc_info=True)
        exit(1)  # Encerra o script se houver um erro crítico

    # 2. Carrega os dados do master.csv para o banco de dados
    logging.info("Passo 2: Carregando dados para o banco de dados")
    try:
        load()
        logging.info("Passo 2 concluído com sucesso.")
    except Exception as e:
        logging.error(f"Erro na execução do load: {e}", exc_info=True)
        exit(1)  # Encerra o script se houver um erro crítico

    logging.info("Processo de ETL concluído com sucesso!")
