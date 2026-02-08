# Arquitetura

## Visão geral
O sistema é dividido em:
- **Frontend** (web): renderiza PDF, permite seleção e criação de edições (intenção do usuário).
- **Backend** (API): gerencia arquivos, validações e **gera o PDF final** aplicando overlays.

A renderização/seleção acontece no browser (PDF.js) para uma UX rápida e precisa.

## Fluxo principal (MVP)
1. Usuário faz upload do PDF.
2. Frontend exibe o PDF com PDF.js.
3. Usuário seleciona um trecho/área e informa o novo texto.
4. Frontend envia ao backend uma lista de operações de edição (ex.: “substituir texto nessa caixa”).
5. Backend aplica overlays e retorna um novo PDF para download.

## Modelo de edição (conceitual)
Operação `replaceTextOverlay`:
- `page`: número da página (1-based)
- `rect`: {x, y, width, height} em coordenadas do PDF
- `background`: cor (ex.: branco) para cobrir o texto antigo
- `text`: string nova
- `font`: nome lógico (ex.: "Roboto-Regular")
- `fontSize`: número
- `color`: cor do texto
- `align`: left|center|right
- `wrap`: true|false

## Fontes (ponto crítico)
### Premissas realistas
- O PDF frequentemente contém fontes subsetadas. Extrair e reusar automaticamente a fonte original nem sempre é simples.
- Para "manter a fonte" com confiabilidade, o MVP assume **fontes fornecidas/registradas** no backend (TTF/OTF).

### Estratégia proposta
- Frontend tenta identificar o nome da fonte via PDF.js (quando disponível) e envia como sugestão.
- Backend mapeia `fontName` → arquivo TTF/OTF instalado no servidor.
- Se a fonte não existir, aplica fallback e ajusta tamanho/spacing para aproximar.

## Componentes
- Frontend
  - Viewer (PDF.js)
  - Camada de seleção
  - Editor inline/modal
  - Lista de edições (timeline/undo)
- Backend
  - Armazenamento temporário de PDFs
  - Endpoint para aplicar edições e gerar PDF
  - Validações (tamanho, páginas, limites)

## Não-funcionais
- Segurança: PDFs são entrada não confiável.
- Performance: limitar tamanho e páginas; processar em background se necessário.
- Observabilidade: logs estruturados e IDs de correlação.
