# Roadmap

## Fase 0 — Documentação e base
- Estrutura do projeto e decisões iniciais (ADRs)
- Definição de contratos de API e modelo de edição

## Fase 1 — MVP Overlay (1 usuário)
- Upload + visualização do PDF
- Seleção de texto/área
- Criar edição `replaceTextOverlay`
- Exportar PDF com overlay
- Registro de fontes TTF/OTF no backend

## Fase 2 — Melhorias de fidelidade
- Ajuste automático de `fontSize` para caber na caixa
- Quebra de linha opcional e alinhamento
- Fallback de fontes e mapeamento por família

## Fase 3 — Escalabilidade / Produto
- Autenticação
- Armazenamento (S3/Blob)
- Jobs assíncronos (fila)
- Auditoria e histórico de versões

## Fase 4 — OCR (opcional)
- Detectar PDFs escaneados
- OCR para camada pesquisável / edição assistida
