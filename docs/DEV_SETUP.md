# Setup local (somente documentação por enquanto)

## Pré-requisitos
- Git
- Python (o projeto usa um `venv` em `.venv/`)
- Node.js (para o frontend quando começarmos a codar)

## Ambiente Python
Este workspace já está configurado para usar o interpretador em:
- `.venv/Scripts/python.exe`

Comandos úteis (PowerShell):
- Verificar Python: `./.venv/Scripts/python.exe --version`
- Instalar dependências (quando existirem): `./.venv/Scripts/python.exe -m pip install -r requirements.txt`

## Convenções
- PDFs e saídas geradas localmente devem ficar em `data/` (ignorado pelo Git)
- Variáveis de ambiente em `.env` (ignorado pelo Git)

## Próximos passos (quando for começar o código)
- Definir o projeto do backend (FastAPI) e do frontend (Vite/React)
- Implementar endpoints do rascunho em docs/API.md
- Implementar o viewer com PDF.js
