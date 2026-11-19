"""Baixa e padroniza a malha municipal de Minas Gerais via API do IBGE."""

import io
from pathlib import Path

import geopandas as gpd
import requests

IBGE_MALHA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/31"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
)
OUTPUT_PATH = Path("dados_dash/mapa_minas.geojson")


def download_mg_geojson(url: str = IBGE_MALHA_URL, timeout: int = 60) -> gpd.GeoDataFrame:
    """Obtém malha municipal de MG pela API do IBGE e padroniza cod_municipio (6 dígitos)."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    gdf = gpd.read_file(io.BytesIO(response.content))
    gdf["cod_municipio"] = gdf["codarea"].astype(str).str[:6].astype(int)
    return gdf[["cod_municipio", "geometry"]]


def main() -> None:
    """Salva o GeoJSON padronizado em dados_dash/mapa_minas.geojson."""
    gdf = download_mg_geojson()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUTPUT_PATH, driver="GeoJSON")
    print(f"Arquivo gerado: {OUTPUT_PATH} ({len(gdf)} municípios)")


if __name__ == "__main__":
    main()
