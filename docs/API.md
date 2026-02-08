# API (rascunho)

Base URL: `/api`

## Upload
### `POST /api/documents`
- Multipart: `file` (application/pdf)
- Resposta: `{ id, filename, pageCount }`

## Obter metadados
### `GET /api/documents/{id}`
- Resposta: `{ id, filename, pageCount, createdAt }`

## Baixar original
### `GET /api/documents/{id}/original`
- Resposta: PDF

## Aplicar edições e gerar PDF
### `POST /api/documents/{id}/export`
Body (JSON):
```json
{
  "edits": [
    {
      "type": "replaceTextOverlay",
      "page": 1,
      "rect": {"x": 100, "y": 200, "width": 250, "height": 18},
      "background": "#FFFFFF",
      "text": "Novo texto",
      "font": "Roboto-Regular",
      "fontSize": 11,
      "color": "#111111",
      "align": "left",
      "wrap": false
    }
  ]
}
```
Resposta: PDF (arquivo gerado)

## Fontes
### `GET /api/fonts`
- Lista fontes disponíveis no servidor: `[{"name": "Roboto-Regular"}]`

### `POST /api/fonts`
- Upload de fonte TTF/OTF para registro

## Observações
- Coordenadas: definir padrão único (PDF points). Frontend deve converter de pixels → points.
- Validação: retângulos fora da página devem ser rejeitados.
