
import sys
import os
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import get_session
from app.models import MovimentoEstoque, Produto

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)


def get_session_override():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = get_session_override


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Cria e limpa o banco de dados para cada função de teste."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


client = TestClient(app)


def test_register_entrada_estoque():
    client.auth = ("admin", "admin")
    client.post(
        "/produtos",
        data={
            "nome": "Pilsen",
            "preco_venda_barril_fechado": 600.0,
            "volume_litros": 50,
            "preco_venda_litro": 20.0,
        },
    )

    response = client.post(
        "/estoque/entrada",
        data={
            "produto_id": 1,
            "quantidade": 10,
            "custo_unitario": 400.0,
            "data_movimento": "2025-10-01",
        },
    )
    assert response.status_code == 200
    assert "Entrada de 10 barril(is) registrada com sucesso!" in response.text

    with Session(engine) as session:
        movimento = session.exec(select(MovimentoEstoque)).first()
        assert movimento is not None
        assert movimento.tipo_movimento == "entrada"
        assert movimento.quantidade == 10
        assert movimento.custo_unitario == 400.0


def test_register_saida_manual_estoque():
    client.auth = ("admin", "admin")
    client.post(
        "/produtos",
        data={
            "nome": "Pilsen",
            "preco_venda_barril_fechado": 600.0,
            "volume_litros": 50,
            "preco_venda_litro": 20.0,
        },
    )

    response = client.post(
        "/estoque/saida_manual",
        data={"produto_id": 1, "quantidade": 2, "data_movimento": "2025-10-02"},
    )
    assert response.status_code == 200
    assert "Saída manual de 2 barril(is) registrada com sucesso!" in response.text

    with Session(engine) as session:
        movimento = session.exec(select(MovimentoEstoque)).first()
        assert movimento is not None
        assert movimento.tipo_movimento == "saida_manual"
        assert movimento.quantidade == 2


def test_get_estoque_atual():
    client.auth = ("admin", "admin")
    client.post(
        "/produtos",
        data={
            "nome": "Pilsen",
            "preco_venda_barril_fechado": 600.0,
            "volume_litros": 50,
            "preco_venda_litro": 20.0,
        },
    )
    client.post(
        "/estoque/entrada",
        data={
            "produto_id": 1,
            "quantidade": 10,
            "custo_unitario": 400.0,
            "data_movimento": "2025-10-01",
        },
    )
    client.post(
        "/estoque/saida_manual",
        data={"produto_id": 1, "quantidade": 2, "data_movimento": "2025-10-02"},
    )

    response = client.get("/estoque")
    assert response.status_code == 200
    estoque = response.json()
    assert "Pilsen" in estoque
    assert estoque["Pilsen"]["quantidade_barris"] == 8
    assert estoque["Pilsen"]["volume_litros_total"] == 400
