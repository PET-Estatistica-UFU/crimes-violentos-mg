"""Tratamento e padronização dos dados de criminalidade violenta em MG (Sejusp)."""

from pathlib import Path

import pandas as pd

INPUT_DIR = Path("dados_input")
OUTPUT_PATH = Path("dados_dash/dados_totais_tratados.csv.gz")

NATUREZA_MAP = {
    "ESTUPRO CONSUMADO": "Estupro Consumado",
    "ESTUPRO DE VULNERAVEL CONSUMADO": "Estupro de Vulnerável Consumado",
    "ESTUPRO DE VULNERAVEL TENTADO": "Estupro de Vulnerável Tentado",
    "ESTUPRO TENTADO": "Estupro Tentado",
    "EXTORSAO CONSUMADO": "Extorsão Consumado",
    "EXTORSAO MEDIANTE SEQUESTRO CONSUMADO": "Extorsão Mediante Sequestro Consumado",
    "EXTORSAO TENTADO": "Extorsão Tentado",
    "FEMINICIDIO TENTADO": "Feminicídio Tentado",
    "HOMICIDIO TENTADO": "Homicídio Tentado",
    "ROUBO CONSUMADO": "Roubo Consumado",
    "ROUBO TENTADO": "Roubo Tentado",
    "SEQUESTRO E CARCERE PRIVADO CONSUMADO": "Sequestro e Cárcere Privado Consumado",
    "SEQUESTRO E CARCERE PRIVADO TENTADO": "Sequestro e Cárcere Privado Tentado",
    "FEMINICIDIO CONSUMADO (REGISTROS)": "Feminicídio Consumado (Registros)",
    "HOMICIDIO CONSUMADO (REGISTROS)": "Homicídio Consumado (Registros)",
    "HOMICIDIO CONSUMADO (Registros)": "Homicídio Consumado (Registros)",
    "FEMINICIDIO CONSUMADO": "Feminicídio Consumado",
}

# Ordem preservada: "Extorsão" após "Sequestro" para classificar
# "Extorsão Mediante Sequestro Consumado" como "Extorsão".
CATEGORIAS_CRIMES = ["Estupro", "Sequestro", "Extorsão", "Roubo", "Homicídio", "Feminicídio"]
TIPOS_CRIMES = ["Consumado", "Tentado"]


def _assign_match(series: pd.Series, candidates: list[str]) -> pd.Series:
    """Atribui o último candidato encontrado via substring na série informada."""
    result = pd.Series("", index=series.index, dtype="object")
    for candidate in candidates:
        mask = series.str.contains(candidate, case=True, na=False, regex=False)
        result = result.where(~mask, candidate)
    return result


def standardize_municipalities(
    df: pd.DataFrame,
    ibge_path: Path = INPUT_DIR / "POP2026.xlsx",
    sheet_name: str = "MG-2026",
) -> pd.DataFrame:
    """Substitui nomes de municípios da Sejusp pela grafia oficial do IBGE."""
    ibge = pd.read_excel(ibge_path, sheet_name=sheet_name, dtype={"COD. MUNIC": str})
    cod_munic = ibge["COD. MUNIC"].astype(str).str.strip().str.zfill(5)
    ibge_ref = pd.DataFrame(
        {
            "cod_municipio": ("31" + cod_munic).str[:6].astype(int),
            "municipio_ibge": ibge["NOME DO MUNICÍPIO"].astype(str),
        }
    ).drop_duplicates(subset=["cod_municipio"], keep="first")

    merged = df.merge(ibge_ref, on="cod_municipio", how="left")
    merged["municipio"] = merged["municipio_ibge"].fillna(merged["municipio"])
    return merged.drop(columns=["municipio_ibge"])


def build_criminality_dataset() -> pd.DataFrame:
    """Lê todos os CSVs *cv*.csv em dados_input/, normaliza e padroniza os registros."""
    cv_files = sorted(p for p in INPUT_DIR.glob("*cv*.csv") if p.is_file())
    if not cv_files:
        raise FileNotFoundError("Nenhum arquivo *cv*.csv encontrado em dados_input/.")

    frames = []
    for file_path in cv_files:
        chunk = pd.read_csv(file_path, sep=";", encoding="utf-8")
        frames.append(chunk)

    df = pd.concat(frames, ignore_index=True)
    df = df.rename(
        columns={
            "Registros": "registros",
            "Natureza": "natureza",
            "Município": "municipio",
            "Cód. IBGE": "cod_municipio",
            "Mês": "mes",
            "Ano Fato": "ano",
        }
    )[["registros", "natureza", "municipio", "cod_municipio", "mes", "ano"]].copy()

    df["natureza"] = df["natureza"].map(NATUREZA_MAP)
    df["categoria"] = _assign_match(df["natureza"], CATEGORIAS_CRIMES)
    df["tipo"] = _assign_match(df["natureza"], TIPOS_CRIMES)

    df["registros"] = df["registros"].astype(int)
    df["cod_municipio"] = df["cod_municipio"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["ano"] = df["ano"].astype(int)

    df = standardize_municipalities(df)
    return df


def main() -> None:
    """Executa o tratamento de criminalidade e exporta para CSV compactado em UTF-8."""
    df = build_criminality_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8", compression="gzip")
    print(f"Arquivo gerado: {OUTPUT_PATH} ({len(df)} linhas)")


if __name__ == "__main__":
    main()
