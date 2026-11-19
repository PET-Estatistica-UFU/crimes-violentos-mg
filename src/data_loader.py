"""Carregamento em cache das bases tratadas e utilitários de formatação pt-BR."""

from pathlib import Path
import unicodedata

import geopandas as gpd
import pandas as pd
import streamlit as st

CRIMES_PATH = Path("dados_dash/dados_totais_tratados.csv.gz")
POP_PATH = Path("dados_dash/dados_populacao_completo.csv")
MAPA_PATH = Path("dados_dash/mapa_minas.geojson")

GRUPO_HABITANTES = 1000
QTD_RANKING = 10

COR_AZUL_ESCURO = "#172C3C"
COR_AZUL_SIDEBAR = "#203C52"
COR_AZUL = "#274862"
COR_VERMELHO = "#995052"
COR_LARANJA = "#D96831"
COR_AMARELO = "#E6B33D"

PALETA_CORES = [
    "#274862",
    "#48C837",
    "#3791C8",
    "#B737C8",
    "#E6B33D",
    "#D96831",
    "#995052",
]


def format_pt_int(value: int | float) -> str:
    """Formata número inteiro com separador de milhar '.' (padrão pt-BR)."""
    return f"{int(round(value)):,}".replace(",", ".")


def format_pt_float(value: float, decimals: int = 2) -> str:
    """Formata número decimal com '.' para milhar e ',' para decimal (padrão pt-BR)."""
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def sort_pt(values: list[str]) -> list[str]:
    """Ordena strings em ordem alfabética ignorando acentuação (aproximação locale pt)."""
    def _key(text: str) -> tuple[str, str]:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_base = "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()
        return (ascii_base, text.lower())

    return sorted(values, key=_key)


@st.cache_data(show_spinner="Carregando dados de criminalidade...")
def load_crimes_data() -> pd.DataFrame:
    """Carrega os registros tratados de criminalidade violenta em MG."""
    df = pd.read_csv(CRIMES_PATH, encoding="utf-8")
    df["registros"] = df["registros"].astype(int)
    df["cod_municipio"] = df["cod_municipio"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["ano"] = df["ano"].astype(int)
    return df


@st.cache_data(show_spinner="Carregando dados populacionais...")
def load_population_data() -> pd.DataFrame:
    """Carrega a série populacional dos municípios de MG."""
    df = pd.read_csv(POP_PATH, encoding="utf-8")
    df = df.rename(columns={"localidade": "cod_municipio"})
    df["cod_municipio"] = df["cod_municipio"].astype(int)
    df["populacao"] = df["populacao"].astype(int)
    df["ano"] = df["ano"].astype(int)
    return df


@st.cache_data(show_spinner="Carregando malha municipal de MG...")
def load_map_data() -> gpd.GeoDataFrame:
    """Carrega o GeoJSON dos municípios de Minas Gerais."""
    gdf = gpd.read_file(MAPA_PATH)
    gdf["cod_municipio"] = gdf["cod_municipio"].astype(int)
    return gdf[["cod_municipio", "geometry"]]
