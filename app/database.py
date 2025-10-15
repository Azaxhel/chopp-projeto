import os
from sqlmodel import create_engine, SQLModel, Session

# Lê a URL do banco de dados da variável de ambiente
# Se não existir, usa o SQLite local como padrão
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# O `connect_args` é específico do SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Engine é criado aqui, mas a sessão será gerenciada pela aplicação
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def init_db():
    """Cria as tabelas do banco de dados se não existirem."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Função de dependência para obter uma sessão do banco de dados."""
    with Session(engine) as session:
        yield session
    