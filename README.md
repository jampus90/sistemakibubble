# KiBubble — Sistema de Vendas para Eventos

Sistema de PDV (Ponto de Venda) desenvolvido para gerenciar vendas de um restaurante de comida japonesa e Bubble Tea em eventos. O projeto foi construído com foco em boas práticas de desenvolvimento, incluindo TDD, autenticação segura e arquitetura limpa.

---

## Funcionalidades

- **PDV (Ponto de Venda)** — registro de vendas com carrinho de compras por sessão, geração automática de senha do pedido (1–999, reiniciando diariamente) e coleta opcional do WhatsApp do cliente
- **Painel de Pedidos** — acompanhamento em tempo real dos pedidos do dia; ao marcar um pedido como pronto, gera automaticamente um link WhatsApp pré-preenchido para notificar o cliente
- **Gestão de Estoque** — CRUD completo de produtos com alerta visual de estoque baixo
- **Resumo / Dashboard** — métricas de vendas (total arrecadado, número de vendas, produtos mais vendidos) com filtro por período
- **Autenticação** — login/logout com sessão Django + emissão de JWT para uso na API; cadastro de usuários restrito a administradores (`is_staff`)

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3 · Django 6 · Django REST Framework |
| Autenticação | Django Sessions + SimpleJWT |
| Banco de dados | PostgreSQL |
| Frontend | Bootstrap 5 (CDN) · Django Templates |
| Testes | Django TestCase (TDD) |
| Configuração | python-dotenv |

---

## Arquitetura

```
sistemadevenda/
├── mysite/          # Configuração do projeto Django (settings, urls, wsgi)
└── vendas/          # App principal com toda a lógica de negócio
    ├── models.py    # Cliente, Produto, Venda, ItemVenda
    ├── views.py     # Views baseadas em funções
    ├── urls.py      # Rotas da aplicação
    ├── tests.py     # Suíte de testes (TDD)
    └── templates/   # HTML com Django Template Language
```

### Modelos principais

- **Produto** — nome, preço unitário, quantidade em estoque
- **Venda** — funcionário, data/hora, total, senha do pedido, status, WhatsApp do cliente
- **ItemVenda** — produto, quantidade e `preco_na_hora` (preço no momento da venda, imutável)

---

## Como rodar localmente

### Pré-requisitos

- Python 3.11+
- PostgreSQL rodando localmente

### Instalação

```bash
# Clone o repositório
git clone https://github.com/jampus90/sistemakibubble

# Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Instale as dependências
pip install -r sistemadevenda/requirements.txt

# Configure as variáveis de ambiente
cp sistemadevenda/.env.example sistemadevenda/.env
# Edite o .env com suas credenciais
```

### Banco de dados

```bash
cd sistemadevenda
python manage.py migrate
python manage.py createsuperuser
```

### Rodando o servidor

```bash
python manage.py runserver
```

Acesse [http://localhost:8000](http://localhost:8000) — será redirecionado automaticamente para o login.

---

## Testes

O projeto foi desenvolvido com **TDD (Test-Driven Development)**. Os testes cobrem autenticação, CRUD de estoque, PDV, geração de senha, painel de pedidos e dashboard.

```bash
cd sistemadevenda
python manage.py test vendas
```

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
SECRET_KEY=sua-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=kibubble
DB_USER=postgres
DB_PASSWORD=sua-senha
DB_HOST=localhost
DB_PORT=5432
```

---

## Rotas

| Rota | Descrição | Acesso |
|---|---|---|
| `/vendas/login/` | Login | Público |
| `/vendas/pdv/` | Ponto de venda | Autenticado |
| `/vendas/pedidos/` | Painel de pedidos do dia | Autenticado |
| `/vendas/estoque/` | Gestão de estoque | Autenticado |
| `/vendas/resumo/` | Dashboard de vendas | Autenticado |
| `/vendas/register/` | Cadastro de usuários | Admin |
| `/api/token/` | Obter token JWT | Público |
