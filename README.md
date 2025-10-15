# Bot de Relatórios - Trailer de Chopp 

Este projeto é um bot em Python + FastAPI que processa dados de vendas e responde automaticamente via WhatsApp com relatórios financeiros, ideal para pequenos negócios. Além disso, oferece um formulário web seguro para registro manual de vendas.

## Status Atual
**O projeto está totalmente funcional e online!** Foi feito o deploy na nuvem e está disponível 24/7 para registro de vendas e consulta de relatórios.

## Tecnologias Usadas
- Python
- FastAPI
- Twilio (WhatsApp)
- Pandas (ETL dos dados)
- **PostgreSQL (armazenamento em nuvem)**
- **SQLModel (ORM para banco de dados)**
- **Railway (Plataforma de Deploy)**
- python-dotenv (gerenciamento de variáveis de ambiente)
- openpyxl (leitura de arquivos Excel)
- python-multipart (processamento de formulários web)

## Como Funciona?

### Registro de Vendas
1.  Acesse o formulário web seguro (URL fornecida após o deploy).
2.  Faça login com usuário e senha.
3.  Preencha os dados da venda (data, total, cartão, dinheiro, pix, custos de funcionário, copos e boleto).
4.  O lucro é calculado automaticamente e salvo no banco de dados.

### Geração de Relatórios (via WhatsApp)
1.  O usuário envia uma mensagem para o bot no WhatsApp (ex: `relatorio 5 2025`).
2.  O bot processa os dados de vendas daquele mês/ano.
3.  Ele responde automaticamente com lucros, gastos e outras métricas financeiras.

## Segurança:
- Dados sensíveis (tokens, senhas, dados de vendas) são gerenciados via variáveis de ambiente e **não são expostos no repositório GitHub**.
- O formulário web é protegido por autenticação de usuário e senha.
- A comunicação com o Twilio é validada para garantir a autenticidade das requisições.

## Como Rodar (Desenvolvimento Local)
1.  Clone o repositório.
2.  Crie e ative um ambiente virtual:
    ```bash
    # Crie o ambiente virtual
    python -m venv venv
    # Ative no Windows
    .\venv\Scripts\activate
    # Ative no macOS/Linux
    # source venv/bin/activate
    ```
3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
4.  Crie um arquivo `.env` na raiz do projeto com suas variáveis de ambiente (veja o arquivo `.env.example` se existir, ou use `DATABASE_URL="sqlite:///./database.db"` para começar).
5.  Aplique as migrações do banco de dados:
    ```bash
    alembic upgrade head
    ```
6.  Execute o ETL para carregar dados iniciais (opcional, se for usar dados de planilha):
    ```bash
    python run_etl.py
    ```
7.  Inicie o servidor FastAPI:
    ```bash
    uvicorn app.main:app --reload
    ```

## Gerenciamento do Banco de Dados (Alembic)

Este projeto usa o Alembic para gerenciar as migrações do banco de dados. Quando você alterar os modelos em `app/models.py` (por exemplo, adicionar uma nova coluna), siga estes passos para gerar e aplicar uma nova migração:

1.  **Gerar a migração automaticamente:**
    ```bash
    # Substitua a mensagem por uma descrição da sua alteração
    alembic revision --autogenerate -m "Descreve a alteração feita"
    ```
2.  **Aplicar a migração ao banco de dados:**
    ```bash
    alembic upgrade head
    ```

## Deploy (Produção)
O deploy é feito na plataforma Railway, garantindo que a aplicação esteja online 24/7. O banco de dados PostgreSQL também é hospedado no Railway.

---

**Este projeto foi desenvolvido para automatizar os relatórios de vendas do trailer de chopp da minha família.**
