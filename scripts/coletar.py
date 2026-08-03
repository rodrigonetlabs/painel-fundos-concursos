"""
Recolhe oportunidades de financiamento (TED + RSS oficiais) e escreve
data/oportunidades.json para o site estático ler.

Não faz scraping de páginas — usa apenas fontes que disponibilizam
os dados de propósito para consumo automático (API pública da TED,
feeds RSS oficiais). Corre uma vez por dia via GitHub Actions.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests
import feedparser

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(RAIZ, "config.json")
DADOS_PATH = os.path.join(RAIZ, "data", "oportunidades.json")

TED_ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"


def carregar_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_dados_anteriores():
    if not os.path.exists(DADOS_PATH):
        return []
    try:
        with open(DADOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("oportunidades", [])
    except (json.JSONDecodeError, OSError):
        return []


def texto_multilingue(valor, preferencia=("por", "eng")):
    """Campos da TED vêm por vezes como {"eng": "...", "fra": "..."}; escolhe o melhor idioma disponível."""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, dict):
        for idioma in preferencia:
            if idioma in valor and valor[idioma]:
                v = valor[idioma]
                return v[0] if isinstance(v, list) else v
        for v in valor.values():
            return v[0] if isinstance(v, list) else v
    if isinstance(valor, list) and valor:
        return valor[0]
    return ""


def obter_ted(config):
    """Consulta a API pública e gratuita da TED (Tenders Electronic Daily)."""
    palavras = config.get("palavras_chave", [])
    paises = config.get("paises_ted", ["PRT"])
    limite = config.get("max_resultados_ted", 40)

    if not palavras:
        return []

    clausula_palavras = " OR ".join(f'FT~"{p}"' for p in palavras)
    clausula_paises = " OR ".join(f"buyer-country={p}" for p in paises)
    query = f"({clausula_palavras}) AND ({clausula_paises})"

    corpo = {
        "query": query,
        "fields": [
            "publication-number",
            "notice-title",
            "buyer-name",
            "buyer-country",
            "deadline-receipt-request",
            "publication-date",
        ],
        "limit": limite,
        "scope": "ACTIVE",
        "paginationMode": "ITERATION",
    }

    try:
        resp = requests.post(TED_ENDPOINT, json=corpo, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[aviso] Falha ao consultar a TED: {e}", file=sys.stderr)
        return []

    agora = datetime.now(timezone.utc)
    notices = resp.json().get("notices", [])
    resultado = []
    for n in notices:
        num = n.get("publication-number", "")
        prazo = texto_multilingue(n.get("deadline-receipt-request")) or None

        if prazo:
            try:
                if datetime.fromisoformat(prazo) < agora:
                    continue
            except ValueError:
                pass

        resultado.append({
            "id": f"ted-{num}",
            "titulo": texto_multilingue(n.get("notice-title")),
            "entidade": texto_multilingue(n.get("buyer-name")),
            "tipo": "Concurso Público",
            "prazo": prazo,
            "link": f"https://ted.europa.eu/en/notice/-/detail/{num}" if num else "",
            "fonte": "TED (Tenders Electronic Daily)",
        })
    return resultado


def obter_rss(config):
    """Lê feeds RSS oficiais configurados (ex: Funding & Tenders Portal)."""
    resultado = []
    for feed_cfg in config.get("rss_feeds", []):
        url = feed_cfg.get("url", "").strip()
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[aviso] Falha ao ler feed '{feed_cfg.get('nome')}': {e}", file=sys.stderr)
            continue

        for entrada in feed.entries:
            resultado.append({
                "id": f"rss-{entrada.get('id', entrada.get('link', ''))}",
                "titulo": entrada.get("title", "Sem título"),
                "entidade": feed_cfg.get("nome", ""),
                "tipo": feed_cfg.get("tipo", "Fundo UE"),
                "prazo": None,
                "link": entrada.get("link", ""),
                "fonte": feed_cfg.get("nome", "RSS"),
            })
    return resultado


def main():
    config = carregar_config()
    anteriores = carregar_dados_anteriores()
    ids_anteriores = {item["id"] for item in anteriores}

    atuais = obter_ted(config) + obter_rss(config)

    agora = datetime.now(timezone.utc).isoformat()
    for item in atuais:
        item["novo"] = item["id"] not in ids_anteriores
        item["detetado_em"] = agora if item["novo"] else next(
            (a["detetado_em"] for a in anteriores if a["id"] == item["id"]), agora
        )

    atuais.sort(key=lambda x: (x["prazo"] is None, x["prazo"] or ""))

    saida = {
        "atualizado_em": agora,
        "total": len(atuais),
        "oportunidades": atuais,
    }

    os.makedirs(os.path.dirname(DADOS_PATH), exist_ok=True)
    with open(DADOS_PATH, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"Escrevi {len(atuais)} oportunidades em {DADOS_PATH}")


if __name__ == "__main__":
    main()
