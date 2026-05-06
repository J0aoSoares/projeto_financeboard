<div align="center">

# 💰 Financeiro PRO

Dashboard web para controle financeiro empresarial — registre entradas e saídas e acompanhe o saldo mensal em tempo real.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

</div>

---

## Sobre o projeto

Sistema web desenvolvido para controle financeiro de pequenas empresas. Permite registrar transações de entrada e saída, filtrar por mês e visualizar o saldo em tempo real através de uma interface limpa e responsiva.

Projeto construído com foco em aprendizado — cada camada da aplicação (rotas, banco de dados, frontend) foi desenvolvida de forma separada e bem documentada.

---

## Funcionalidades

- Registro de entradas e saídas com descrição, valor e data
- Filtro por mês
- Cards com total de entradas, saídas e saldo calculado
- Exclusão de transações

---

## Stack

| Camada   | Tecnologia          |
|----------|---------------------|
| Backend  | Python 3.12 + Flask |
| Banco    | SQLite              |
| Frontend | HTML + CSS + JS     |

---

## Como rodar

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/financeiro-pro.git
cd financeiro-pro

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode o servidor
python app.py
```

Acesse **http://localhost:5000**

---

## Estrutura

```
financeiro-pro/
├── app.py              # Rotas e endpoints da API
├── database.py         # Queries SQL
├── static/
│   ├── css/style.css   # Estilos
│   └── js/app.js       # Lógica do frontend
└── templates/
    └── index.html      # Interface
```

---

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.