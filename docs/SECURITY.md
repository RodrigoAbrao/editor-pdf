# Segurança

PDF é um formato complexo e deve ser tratado como **entrada não confiável**.

## Recomendações (MVP)
- Limitar tamanho de upload e número de páginas
- Validar MIME type e assinatura do arquivo (quando possível)
- Processar PDFs em diretório temporário isolado
- Evitar executar ferramentas externas sem sandbox
- Logar ações com IDs de correlação

## Dados
- Não versionar PDFs no Git
- Armazenamento em `data/` no ambiente de desenvolvimento

## Futuro
- Antivírus/scan
- Quarentena e expiração de arquivos
- Rate limiting por IP/usuário
