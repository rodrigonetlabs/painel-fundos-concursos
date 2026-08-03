# Fundos & Concursos — site com deteção automática diária

Site estático e gratuito que se atualiza sozinho todos os dias, indo buscar
concursos e fundos a **fontes oficiais** (API pública da TED, feeds RSS
oficiais) — sem scraping de páginas que não o permitem.

## Como funciona

1. Uma GitHub Action corre `scripts/coletar.py` todos os dias às 07:00 UTC.
2. O script consulta a API da TED e os feeds RSS que configurares em `config.json`.
3. Escreve o resultado em `data/oportunidades.json`.
4. O `index.html` (o site) lê esse ficheiro e mostra tudo, com as novidades do dia marcadas.
5. O GitHub Pages serve o `index.html` — é o teu site, com um link fixo.

Não precisas de servidor, base de dados nem custos — tudo corre nos
runners gratuitos do GitHub Actions.

## Passo a passo (± 15 minutos, só se faz uma vez)

1. **Cria uma conta no GitHub** (se ainda não tiveres): github.com
2. **Cria um repositório novo**, público ou privado, ex: `fundos-startup`.
3. **Envia estes ficheiros** para esse repositório (arrasta a pasta toda
   para a página do repositório no browser, ou usa `git push` se preferires
   linha de comandos).
4. **Ativa o GitHub Pages**: no repositório, vai a
   `Settings → Pages → Source` e escolhe a branch `main`, pasta `/ (root)`.
   Ao fim de 1-2 minutos o site fica disponível num link tipo
   `https://o-teu-user.github.io/fundos-startup/`.
5. **Corre a Action pela primeira vez à mão**: vai a `Actions →
   Atualizar oportunidades → Run workflow`. Isto preenche o
   `data/oportunidades.json` logo, sem esperares pelo dia seguinte.
6. Depois disto, tudo é automático — todos os dias o site atualiza-se sozinho.

## Como calibrar para a tua startup

Edita `config.json` diretamente no GitHub (botão do lápis no ficheiro):

- `palavras_chave`: os termos que definem o vosso setor. Quanto mais
  específicos, melhor a sinalização (evita termos demasiado genéricos
  tipo "empresa").
- `paises_ted`: por omissão só Portugal (`PRT`). Podes adicionar outros
  códigos de país se fizer sentido para o vosso mercado.
- `rss_feeds`: aqui adicionas o feed RSS do Funding & Tenders Portal.
  Vai a
  `https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search`,
  faz a pesquisa com os filtros do vosso setor/programa e clica no ícone
  de RSS da página — cola esse link no campo `url`.

Depois de guardares o `config.json`, corre a Action manualmente uma vez
(`Actions → Run workflow`) para ver logo o efeito.

## Limitações a saber

- A API da TED cobre **concursos públicos acima dos limiares da UE**
  (tipicamente > 140 mil € consoante o tipo de contrato). Concursos
  municipais pequenos abaixo desse valor não aparecem ali — para esses,
  o Portal BASE continua a ser a referência manual.
- Os avisos do Portugal 2030 / Compete2030 não têm feed oficial no
  momento em que isto foi escrito — não estão incluídos automaticamente.
  Se quiseres, posso mais tarde adicionar uma verificação diária leve e
  respeitosa a essas páginas (é um passo extra, não incluído aqui para
  já manter tudo 100% baseado em fontes com feed oficial).
- Isto é um ponto de partida sólido, não um produto acabado — o código
  está todo aberto para ajustares à medida que forem aparecendo
  necessidades novas.
