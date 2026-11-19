"""Coleta a população dos municípios de Minas Gerais via API do IBGE."""

from pathlib import Path

import pandas as pd
import requests

IBGE_POP_URL = (
    "https://servicodados.ibge.gov.br/api/v1/pesquisas/indicadores/97907/resultados/31xxxxx"
)
OUTPUT_PATH = Path("dados_input/populacao-minas-ibge.csv")


def fetch_ibge_population(url: str = IBGE_POP_URL, timeout: int = 30) -> pd.DataFrame:
    """Consulta a API de indicadores do IBGE e retorna DataFrame com localidade e populacao."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    resultados = payload[0]["res"]
    rows = []
    for item in resultados:
        localidade = item["localidade"]
        res_dict = item["res"]
        # Pega o primeiro valor do dicionário de anos retornado pelo indicador
        populacao = next(iter(res_dict.values()))
        rows.append({"localidade": localidade, "populacao": populacao})

    return pd.DataFrame(rows)


def main() -> None:
    """Executa a raspagem e salva o arquivo CSV em dados_input/."""
    df = fetch_ibge_population()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Arquivo salvo com sucesso: {OUTPUT_PATH} ({len(df)} municípios)")


if __name__ == "__main__":
    main()
