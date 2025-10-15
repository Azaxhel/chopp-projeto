import sys
import os
from datetime import date
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

# Adiciona o diretório raiz do projeto ao path para permitir importações de 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, calculate_report_metrics
from app.database import get_session
from app.models import MovimentoEstoque, Venda

# --- Configuração do Banco de Dados de Teste ---
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

# --- Testes de Lógica Pura ---


def test_calculate_report_metrics_com_dados():
    vendas_exemplo = [
        Venda(
            data=date(2025, 10, 1),
            total=100.0,
            cartao=100.0,
            dinheiro=0.0,
            pix=0.0,
            custo_func=10.0,
            custo_copos=5.0,
            custo_boleto=0.0,
            lucro=85.0,
            dia_semana="",
            tipo_venda="",
        ),
        Venda(
            data=date(2025, 10, 2),
            total=250.50,
            cartao=250.50,
            dinheiro=0.0,
            pix=0.0,
            custo_func=10.0,
            custo_copos=12.5,
            custo_boleto=2.0,
            lucro=226.0,
            dia_semana="",
            tipo_venda="",
        ),
        Venda(
            data=date(2025, 10, 3),
            total=50.0,
            cartao=50.0,
            dinheiro=0.0,
            pix=0.0,
            custo_func=10.0,
            custo_copos=2.5,
            custo_boleto=0.0,
            lucro=37.5,
            dia_semana="",
            tipo_venda="",
        ),
    ]
    resultado = calculate_report_metrics(vendas_exemplo)
    assert resultado["receita_bruta"] == 400.50
    assert resultado["receita_liquida"] == 348.50


def test_calculate_report_metrics_sem_dados():
    resultado = calculate_report_metrics([])
    assert resultado["receita_bruta"] == 0.0


# --- Testes de Endpoint (Webhook) ---


@patch("app.main.validator.validate", return_value=True)
def test_webhook_comando_ajuda(mock_validate):
    response = client.post("/whatsapp/webhook", data={"Body": "ajuda"})
    assert response.status_code == 200
    assert "Comandos disponíveis:" in response.text


@patch("app.main.validator.validate", return_value=True)
@patch("app.main.get_report_data")
def test_webhook_comando_relatorio_sucesso(mock_get_report, mock_validate):
    report_atual = {
        "receita_bruta": 1500.0,
        "receita_liquida": 1200.50,
        "media_vendas": 1500.0,
        "gasto_funcionarios": 100.0,
        "gasto_copos": 100.0,
        "gasto_boleto": 99.50,
        "dias_registrados": 1,
    }
    report_anterior = {
        "receita_bruta": 1200.0,
        "receita_liquida": 900.0,
        "media_vendas": 1200.0,
        "gasto_funcionarios": 100.0,
        "gasto_copos": 100.0,
        "gasto_boleto": 100.0,
        "dias_registrados": 1,
    }
    mock_get_report.side_effect = [report_atual, report_anterior]
    response = client.post("/whatsapp/webhook", data={"Body": "relatorio 10 2025"})
    assert response.status_code == 200
    assert "Receita líquida: R$ 1200.50" in response.text
    assert "Tendência: 33.39%" in response.text


@patch("app.main.validator.validate", return_value=True)
@patch("app.main.get_report_data", return_value=None)
def test_webhook_comando_relatorio_sem_dados(mock_get_report, mock_validate):
    response = client.post("/whatsapp/webhook", data={"Body": "relatorio 11 2025"})
    assert response.status_code == 200
    assert "Nenhum registro de vendas encontrado" in response.text


@patch("app.main.validator.validate", return_value=False)
def test_webhook_falha_validacao_twilio(mock_validate):
    response = client.post("/whatsapp/webhook", data={"Body": "qualquer coisa"})
    assert response.status_code == 403


# --- Testes de Endpoints (Formulário Web) ---


def test_criar_e_listar_produtos():
    client.auth = ("admin", "admin")
    response_get1 = client.get("/produtos")
    assert response_get1.status_code == 200
    assert response_get1.json() == []

    client.post(
        "/produtos", data={"nome": "Chopp IPA", "preco_venda_barril_fechado": 750.0}
    )

    response_get2 = client.get("/produtos")
    data = response_get2.json()
    assert len(data) == 1
    assert data[0]["nome"] == "Chopp IPA"


def test_registrar_venda_feira():
    client.auth = ("admin", "admin")
    # Cria um produto primeiro
    response_produto = client.post(
        "/produtos",
        data={
            "nome": "Pilsen",
            "preco_venda_barril_fechado": 600.0,
            "volume_litros": 50,
            "preco_venda_litro": 20.0,
        },
    )
    assert response_produto.status_code == 200

    venda_data = {
        "data": "2025-10-10",
        "produto_id": 1,
        "tipo_venda": "feira",
        "total": 500.0,
        "cartao": 500.0,
        "dinheiro": 0.0,
        "pix": 0.0,
        "custo_func": 50.0,
        "custo_copos": 25.0,
        "custo_boleto": 0.0,
    }
    response = client.post("/registrar_venda", data=venda_data)
    assert response.status_code == 200

    # Agora, verifica diretamente no banco de dados
    with Session(engine) as session:
        venda_registrada = session.exec(
            select(Venda).where(Venda.data == date(2025, 10, 10))
        ).first()
        assert venda_registrada is not None
        assert venda_registrada.total == 500.0
        # Lucro = 500 - 50 - 25 - 0 = 425
        assert venda_registrada.lucro == 425.0

        movimento_estoque = session.exec(
            select(MovimentoEstoque).where(
                MovimentoEstoque.tipo_movimento == "saida_venda"
            )
        ).first()
        assert movimento_estoque is not None
        # Litros vendidos = 500 / 20 = 25
        # Barris baixados = 25 / 50 = 0.5
        assert movimento_estoque.quantidade == pytest.approx(0.5)


def test_registrar_venda_barril_festas():
    client.auth = ("admin", "admin")
    # Cria um produto e uma entrada de estoque
    client.post(
        "/produtos",
        data={
            "nome": "IPA",
            "preco_venda_barril_fechado": 750.0,
            "volume_litros": 50,
            "preco_venda_litro": 22.0,
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

    venda_data = {
        "data": "2025-10-11",
        "produto_id": 1,
        "tipo_venda": "barril_festas",
        "quantidade_barris_vendidos": 2,
        "cartao": 1500.0,
        "dinheiro": 0.0,
        "pix": 0.0,
    }
    response = client.post("/registrar_venda", data=venda_data)
    assert response.status_code == 200

    # Agora, verifica diretamente no banco de dados
    with Session(engine) as session:
        venda_registrada = session.exec(
            select(Venda).where(Venda.data == date(2025, 10, 11))
        ).first()
        assert venda_registrada is not None
        # Total = 2 barris * 750.0 = 1500.0
        assert venda_registrada.total == 1500.0
        # Custo = 2 barris * 400.0 (custo médio) = 800.0
        # Lucro = 1500.0 - 800.0 = 700.0
        assert venda_registrada.lucro == 700.0

        movimento_estoque = session.exec(
            select(MovimentoEstoque).where(
                MovimentoEstoque.tipo_movimento == "saida_venda_barril"
            )
        ).first()
        assert movimento_estoque is not None
        assert movimento_estoque.quantidade == 2
