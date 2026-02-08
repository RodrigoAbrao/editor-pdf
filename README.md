# editor-pdf

Editor de PDF estilo iLovePDF (focado em **edição via overlay**), com **frontend + backend**.

## Objetivo
- Upload de PDF
- Visualização no navegador
- Selecionar texto e editar
- Exportar um novo PDF mantendo o layout do original o máximo possível

## Estratégia de edição (MVP)
PDF não é um formato “de texto fluido”. O MVP aqui usa **overlay**:
1. Detectar o trecho/caixa selecionada no viewer.
2. Cobrir o texto original com um retângulo (fundo) no PDF final.
3. Desenhar o novo texto por cima, com fonte/tamanho alinhados.

Isso preserva layout e funciona bem para edições pontuais.

## O que NÃO é objetivo (por enquanto)
- Reflow de parágrafos “como Word”
- Reconstrução completa do layout
- Edição perfeita em PDFs com fontes não disponíveis

## Stack planejado
- Frontend: React + Vite + TypeScript + PDF.js
- Backend: Python (FastAPI)
- Geração/edição do PDF no backend: overlay com ReportLab + PyPDF (ou biblioteca equivalente)
- Persistência (dev): disco local (diretório `data/` ignorado pelo Git)

## Documentação
- Arquitetura: docs/ARCHITECTURE.md
- API: docs/API.md
- Roadmap: docs/ROADMAP.md
- Setup local: docs/DEV_SETUP.md
- Decisões (ADRs): docs/DECISIONS/

## Status
Somente documentação inicial (sem código ainda).
