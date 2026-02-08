# ADR-0001 — Estratégia de edição via overlay

## Status
Aceito

## Contexto
Editar PDF “de verdade” (reflow) é complexo e tende a quebrar fidelidade. O objetivo inicial é permitir edições pontuais mantendo layout.

## Decisão
A primeira versão aplicará edições via **overlay**:
- Cobrir o texto original com um retângulo do fundo
- Escrever o novo texto por cima dentro de uma caixa

## Consequências
- Excelente preservação de layout em documentos complexos
- Limitações: não reordena parágrafos, pode exigir fallback de fonte

## Mitigações
- Registro de fontes TTF/OTF no backend
- Auto-fit de fonte para caber na caixa
- Fallback configurável por família
