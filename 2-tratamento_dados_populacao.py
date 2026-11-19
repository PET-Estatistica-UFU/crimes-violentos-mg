"""Tratamento e consolidação dos dados populacionais dos municípios de MG (2012-2026)."""

from pathlib import Path

import pandas as pd

INPUT_DIR = Path("dados_input")
OUTPUT_PATH = Path("dados_dash/dados_populacao_completo.csv")


def _extract_ibge_excel(path: Path, sheet_name: str, ano: int) -> pd.DataFrame:
    """Lê planilha de estimativa populacional do IBGE e padroniza código de 6 dígitos."""
    df = pd.read_excel(path, sheet_name=sheet_name, dtype={"COD. MUNIC": str})
    cod_munic = df["COD. MUNIC"].astype(str).str.strip().str.zfill(5)
    localidade = ("31" + cod_munic).str[:6].astype(int)
    populacao = pd.to_numeric(df["POPULAÇÃO ESTIMADA"], errors="raise").astype(int)
    return pd.DataFrame({"localidade": localidade, "populacao": populacao, "ano": ano})


def build_population_dataset() -> pd.DataFrame:
    """Consolida séries populacionais de MG de 2012 até 2026."""
    # De 2012 a 2021 (Base dos Dados / IBGE)
    dados_novo = pd.read_csv(INPUT_DIR / "ibge_populacao_municipio.csv", encoding="utf-8")
    dados_novo = dados_novo.loc[
        (dados_novo["sigla_uf"] == "MG")
        & (dados_novo["ano"] >= 2012)
        & (dados_novo["ano"] < 2022),
        ["id_municipio", "populacao", "ano"],
    ].copy()
    dados_novo["localidade"] = dados_novo["id_municipio"].astype(str).str[:6].astype(int)
    dados_novo["populacao"] = dados_novo["populacao"].astype(int)
    dados_novo["ano"] = dados_novo["ano"].astype(int)
    dados_novo = dados_novo[["localidade", "populacao", "ano"]]

    # 2022 (API IBGE) e 2023 (repete 2022 conforme regra do projeto)
    dados_antigo = pd.read_csv(INPUT_DIR / "populacao-minas-ibge.csv", encoding="utf-8")
    dados_antigo = dados_antigo[["localidade", "populacao"]].copy()
    dados_antigo["localidade"] = dados_antigo["localidade"].astype(int)
    dados_antigo["populacao"] = dados_antigo["populacao"].astype(int)
    dados_antigo["ano"] = 2022

    dados_2023 = dados_antigo.copy()
    dados_2023["ano"] = 2023

    # 2024, 2025 e 2026 (planilhas oficiais do IBGE)
    dados_2024 = _extract_ibge_excel(INPUT_DIR / "POP2024.xlsx", "Página1", 2024)
    dados_2025 = _extract_ibge_excel(INPUT_DIR / "POP2025.xlsx", "Página2", 2025)
    dados_2026 = _extract_ibge_excel(INPUT_DIR / "POP2026.xlsx", "MG-2026", 2026)

    completo = pd.concat(
        [dados_novo, dados_antigo, dados_2023, dados_2024, dados_2025, dados_2026],
        ignore_index=True,
    )
    completo = (
        completo.loc[completo["ano"] >= 2012, ["localidade", "populacao", "ano"]]
        .sort_values(["localidade", "ano"])
        .reset_index(drop=True)
    )
    return completo


def main() -> None:
    """Executa o tratamento populacional e exporta para dados_dash/."""
    df = build_population_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Arquivo gerado: {OUTPUT_PATH} ({len(df)} linhas)")


if __name__ == "__main__":
    main()
