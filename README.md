# Tendências do Warframe Market

Painel para entender preços e tendências dos conjuntos (sets) do
[warframe.market](https://warframe.market/) no PC, com 90 dias de histórico.

**[Abrir o dashboard](https://claude.ai/artifact/PBvyrxNh5UxiRA6JX1VcU5)**

Os dados são um retrato de 1º de novembro de 2026 e não atualizam sozinhos.

## O que tem aqui

| Caminho | Conteúdo |
|---|---|
| `scripts/collect.py` | Baixa da API pública o histórico e as melhores ofertas de cada conjunto |
| `scripts/build.py` | Transforma a coleta nos dois CSVs usados pelo dashboard |
| `data/historico.csv` | Vendas e preços por dia e por conjunto |
| `data/itens.csv` | Os 234 conjuntos, com categoria e melhores ofertas |
| `dashboard/index.html` | Código da página do dashboard |

`dashboard/index.html` não abre sozinho no navegador nem no GitHub Pages. Ele
depende do ambiente de dashboards dos Artifacts do Claude, que fornece o objeto
`dash`, o d3 e os dados. Ele está aqui como código-fonte.

## Como atualizar os dados

Não precisa de conta nem de token. A coleta faz no máximo 2,5 requisições por
segundo e leva alguns minutos.

```sh
mkdir -p raw
python3 scripts/collect.py raw
python3 scripts/build.py raw data
```

Depois, envie os novos CSVs para o dashboard, porque ele usa cópias próprias.

## Como os números são calculados

- **Preço atual:** média das medianas diárias dos últimos 7 dias, ponderada por
  vendas.
- **Variação:** preço atual comparado à mesma média de 7 dias, calculada há 7
  dias, há 30 dias ou no início do período.
- **Índice de preços:** mediana, entre os itens, do preço médio de 7 dias
  dividido pelo do início do período, vezes 100.
- **Tendência:** Alta ou Queda quando a variação em 30 dias passa de 5%. Com
  menos de 30 vendas no mês, o item aparece como Pouco negociado.
- **Spread:** diferença entre a melhor venda e a melhor compra, em % do preço de
  venda.

## Dias excluídos

A coluna `suspeito` de `historico.csv` marca os dias com preço 10 vezes acima do
típico do item ou vendas 20 vezes acima. Esses dias ficam no arquivo, mas fora de
todos os cálculos.

Na coleta atual, a regra marcou 3 dias de Xiphos Set, um item que vende cerca de
1 unidade por dia:

| Dia | Vendas | Preço mediano |
|---|---|---|
| 2026-09-03 | 199 | 99.999 p |
| 2026-09-21 | 50 | 9.999 p |
| 2026-10-01 | 151 | 50 p |

## Limitações

- Só conjuntos no PC. Mods, arcanes e rivens ficaram de fora.
- As vendas são as registradas no site, então o volume real pode ser maior.
- As melhores ofertas vêm de usuários online no momento da coleta.
- O histórico usa `/v1/items/{slug}/statistics`. A API v1 está sendo desativada
  e não encontrei um equivalente na v2, então essa rota pode parar de funcionar.
