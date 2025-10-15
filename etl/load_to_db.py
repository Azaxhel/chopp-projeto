import os
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import delete, exc
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import Venda, Produto
from dotenv import load_dotenv

# Configura um logger para este módulo
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente do .env
load_dotenv()

# Caminho para o CSV mestre
BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_CSV = BASE_DIR / "master.csv"

# Usa variável de ambiente para o nome do produto, com um padrão
ETL_PRODUCT_NAME = os.getenv("ETL_PRODUCT_NAME", "Chopp Pilsen 50L")


def load():
    try:
        # Inicializa o banco (cria tabelas se não existirem)
        init_db()
    except Exception as e:
        logger.error(f"Falha ao inicializar o banco de dados: {e}", exc_info=True)
        raise

    # Busca o ID do produto a partir da variável de ambiente
    product_id = None
    with Session(engine) as sess:
        produto = sess.exec(
            select(Produto).where(Produto.nome == ETL_PRODUCT_NAME)
        ).first()
        if produto:
            product_id = produto.id
            logger.info(
                f"Produto '{ETL_PRODUCT_NAME}' encontrado com ID: {product_id}."
            )
        else:
            logger.error(
                f"Produto '{ETL_PRODUCT_NAME}' não encontrado no banco de dados. Por favor, cadastre-o primeiro."
            )
            raise ValueError(f"Produto '{ETL_PRODUCT_NAME}' não encontrado.")

    if not MASTER_CSV.exists():
        logger.error(f"Arquivo master não encontrado em: {MASTER_CSV}")
        raise FileNotFoundError(f"Arquivo master não encontrado em: {MASTER_CSV}")

    # Lê o CSV mestre com parse de datas
    logger.info(f"Lendo arquivo de dados de {MASTER_CSV}")
    df = pd.read_csv(MASTER_CSV, parse_dates=["data"])
    df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.date

    # --- Apaga todas as vendas para as datas deste CSV ---
    datas = df["data"].dropna().unique().tolist()
    if not datas:
        logger.warning(
            "Nenhuma data válida encontrada no arquivo CSV. Nenhum dado será carregado."
        )
        return

    logger.info(f"Apagando registros existentes para {len(datas)} datas.")
    with Session(engine) as sess:
        try:
            stmt = delete(Venda).where(
                Venda.data.in_(datas), Venda.produto_id == product_id
            )
            result = sess.exec(stmt)
            sess.commit()
            logger.info(f"{result.rowcount} registros foram apagados.")
        except exc.SQLAlchemyError as e:
            logger.error(
                f"Erro no banco de dados ao apagar registros: {e}", exc_info=True
            )
            sess.rollback()
            raise

    # --- Insere tudo de novo ---
    logger.info(f"Inserindo {len(df)} novos registros...")
    with Session(engine) as sess:
        try:
            for _, row in df.iterrows():
                venda = Venda(
                    data=row["data"],
                    dia_semana=row.get("dia_da_semana"),
                    total=row.get("total", 0.0),
                    cartao=row.get("cartao", 0.0),
                    dinheiro=row.get("dinheiro", 0.0),
                    pix=row.get("pix", 0.0),
                    custo_func=row.get("custo_func", 0.0),
                    custo_copos=row.get("custo_copos", 0.0),
                    custo_boleto=row.get("custo_boleto", 0.0),
                    lucro=row.get("lucro", 0.0),
                    observacoes=row.get("observacoes"),
                    produto_id=product_id,  # Associa ao produto correto
                )
                sess.add(venda)
            sess.commit()
        except exc.SQLAlchemyError as e:
            logger.error(
                f"Erro no banco de dados ao inserir registros: {e}", exc_info=True
            )
            sess.rollback()
            raise

    logger.info(f"{len(df)} registros recarregados para {len(datas)} dias.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    load()
