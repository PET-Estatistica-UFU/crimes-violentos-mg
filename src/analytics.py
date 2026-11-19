"""Regras de negócio, filtragem, métricas e agregações do dashboard."""

import geopandas as gpd
import pandas as pd

from src.data_loader import (
    GRUPO_HABITANTES,
    QTD_RANKING,
    format_pt_float,
    format_pt_int,
)


def filtra_dataframe(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str | None = None,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tamanho_cidade: str | None = None,
    manter_muni: str | None = None,
    tipo_crime: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica filtros de município, tipo de crime, categoria, período e porte populacional."""
    df = dados_totais

    if nome_municipio is not None:
        df = df[df["municipio"] == nome_municipio]

    if tipo_crime is not None and set(tipo_crime) != {"Consumado", "Tentado"}:
        df = df[df["tipo"].isin(tipo_crime)]

    if categ is not None:
        df = df[df["categoria"] == categ]

    if ano_intervalo is not None:
        df = df[(df["ano"] >= ano_intervalo[0]) & (df["ano"] <= ano_intervalo[1])]

    if tamanho_cidade is not None and tamanho_cidade != "Todas":
        ano_ref = ano_intervalo[1] if ano_intervalo is not None else int(dados_populacao["ano"].max())
        pop_ref = dados_populacao[dados_populacao["ano"] == ano_ref]

        if tamanho_cidade == "Grandes":
            pop_ref = pop_ref[pop_ref["populacao"] > 500_000]
        elif tamanho_cidade == "Médias":
            pop_ref = pop_ref[(pop_ref["populacao"] >= 100_000) & (pop_ref["populacao"] <= 500_000)]
        elif tamanho_cidade == "Pequenas":
            pop_ref = pop_ref[pop_ref["populacao"] < 100_000]
        elif tamanho_cidade == "Grandes e médias":
            pop_ref = pop_ref[pop_ref["populacao"] >= 100_000]
        elif tamanho_cidade == "Médias e pequenas":
            pop_ref = pop_ref[pop_ref["populacao"] <= 500_000]

        cod_muni = set(pop_ref["cod_municipio"].tolist())

        if manter_muni is not None:
            manter_cod = dados_totais.loc[
                dados_totais["municipio"] == manter_muni, "cod_municipio"
            ].iloc[0]
            cod_muni.add(int(manter_cod))

        df = df[df["cod_municipio"].isin(cod_muni)]

    return df


def _get_cod_municipio(dados_totais: pd.DataFrame, nome_municipio: str) -> int:
    """Obtém o código IBGE (6 dígitos) de um município."""
    return int(
        dados_totais.loc[dados_totais["municipio"] == nome_municipio, "cod_municipio"].iloc[0]
    )


def populacao_cidade(
    dados_totais: pd.DataFrame, dados_populacao: pd.DataFrame, nome_municipio: str
) -> str:
    """Retorna a população mais recente do município formatada em pt-BR."""
    cod_muni = _get_cod_municipio(dados_totais, nome_municipio)
    ano_max = int(dados_populacao["ano"].max())
    pop = dados_populacao.loc[
        (dados_populacao["ano"] == ano_max) & (dados_populacao["cod_municipio"] == cod_muni),
        "populacao",
    ].iloc[0]
    return format_pt_int(pop)


def ranking_populacao(
    dados_totais: pd.DataFrame, dados_populacao: pd.DataFrame, nome_municipio: str
) -> str:
    """Retorna a posição do município no ranking populacional de MG."""
    cod_muni = _get_cod_municipio(dados_totais, nome_municipio)
    ano_max = int(dados_populacao["ano"].max())
    df = (
        dados_populacao[dados_populacao["ano"] == ano_max]
        .sort_values("populacao", ascending=False)
        .reset_index(drop=True)
    )
    pos = int(df.index[df["cod_municipio"] == cod_muni][0]) + 1
    return f"{pos}ª"


def texto_informativo(
    dados_totais: pd.DataFrame, dados_populacao: pd.DataFrame, nome_municipio: str
) -> str:
    """Gera o texto informativo exibido na barra lateral."""
    pop = populacao_cidade(dados_totais, dados_populacao, nome_municipio)
    pos = ranking_populacao(dados_totais, dados_populacao, nome_municipio)
    ano_max = int(dados_populacao["ano"].max())
    return (
        f"{nome_municipio} possui {pop} hab. e é a {pos} cidade mineira "
        f"com maior população, em {ano_max}."
    )


def total_crimes(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> str:
    """Calcula o número total de crimes para os filtros selecionados."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        nome_municipio=nome_municipio,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    return format_pt_int(df["registros"].sum())


def crimes_rel_habitantes(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> str:
    """Calcula a taxa acumulada de crimes por mil habitantes no período."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        nome_municipio=nome_municipio,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    if df.empty:
        return format_pt_float(0.0, 2)

    por_ano = df.groupby("ano", as_index=False)["registros"].sum()
    cod_muni = int(df["cod_municipio"].iloc[0])

    pop = dados_populacao[dados_populacao["cod_municipio"] == cod_muni]
    if ano_intervalo is not None:
        pop = pop[(pop["ano"] >= ano_intervalo[0]) & (pop["ano"] <= ano_intervalo[1])]

    merged = por_ano.merge(pop[["ano", "populacao"]], on="ano", how="inner")
    resultado = (merged["registros"] * GRUPO_HABITANTES / merged["populacao"]).sum()
    return format_pt_float(round(float(resultado), 2), 2)


def media_crimes(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> str:
    """Calcula a média mensal de crimes no período."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        nome_municipio=nome_municipio,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    if df.empty:
        return format_pt_float(0.0, 2)

    media = df.groupby(["ano", "mes"], as_index=False)["registros"].sum()["registros"].mean()
    return format_pt_float(round(float(media), 2), 2)


def porc_alteracao_crimes(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    ano_maximo: int,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> str:
    """Calcula a variação percentual entre os dois últimos meses disponíveis."""
    intervalo = ano_intervalo
    if (
        intervalo is not None
        and intervalo[0] == intervalo[1] == ano_maximo
        and (dados_totais.loc[dados_totais["ano"] == ano_maximo, "mes"] == 1).all()
    ):
        intervalo = (ano_maximo - 1, ano_maximo)

    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        nome_municipio=nome_municipio,
        categ=categ,
        ano_intervalo=intervalo,
        tipo_crime=tipo_crime,
    )
    mensal = (
        df.groupby(["ano", "mes"], as_index=False)["registros"]
        .sum()
        .sort_values(["ano", "mes"])
    )
    if len(mensal) < 2:
        return "Indefinida"

    valores = mensal["registros"].tail(2).tolist()
    if valores[0] == 0:
        return "Indefinida"

    alteracao = round(((valores[1] - valores[0]) / valores[0]) * 100, 2)
    return f"{format_pt_float(alteracao, 2)}%"


def posicao_abs_municipio(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> str:
    """Retorna a posição do município em MG pelo total absoluto de crimes."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    ranking = (
        df.groupby("municipio", as_index=False)["registros"]
        .sum()
        .sort_values("registros", ascending=False)
        .reset_index(drop=True)
    )
    pos = int(ranking.index[ranking["municipio"] == nome_municipio][0]) + 1
    return f"{pos}º"


def posicao_rel_municipio(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> str:
    """Retorna a posição do município em MG pela taxa de crimes por mil habitantes."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    por_ano = df.groupby(["municipio", "cod_municipio", "ano"], as_index=False)["registros"].sum()
    merged = por_ano.merge(dados_populacao, on=["cod_municipio", "ano"], how="left")
    merged["registros_rel_habitantes"] = (
        merged["registros"] / merged["populacao"]
    ) * GRUPO_HABITANTES

    ranking = (
        merged.groupby("municipio", as_index=False)["registros_rel_habitantes"]
        .sum()
        .sort_values("registros_rel_habitantes", ascending=False)
        .reset_index(drop=True)
    )
    pos = int(ranking.index[ranking["municipio"] == nome_municipio][0]) + 1
    return f"{pos}º"


def df_total(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> pd.DataFrame:
    """Agrega registros por categoria (ou natureza) + linha Total para o gráfico de barras."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        nome_municipio=nome_municipio,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    col = "categoria" if categ is None else "natureza"
    grouped = df.groupby(col, as_index=False)["registros"].sum()
    total_row = pd.DataFrame({col: ["Total"], "registros": [int(grouped["registros"].sum())]})
    combined = pd.concat([grouped, total_row], ignore_index=True)
    return combined.sort_values("registros", ascending=True).reset_index(drop=True)


def df_temporal(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    dados_mensais: bool = False,
    tipo_crime: list[str] | None = None,
) -> pd.DataFrame:
    """Agrega série histórica anual ou mensal por categoria (ou natureza) + Total."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        nome_municipio=nome_municipio,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    col = "categoria" if categ is None else "natureza"
    time_cols = ["ano", "mes"] if dados_mensais else ["ano"]

    grouped = df.groupby([col, *time_cols], as_index=False)["registros"].sum()
    totais = df.groupby(time_cols, as_index=False)["registros"].sum()
    totais[col] = "Total"

    combined = pd.concat([grouped, totais[[col, *time_cols, "registros"]]], ignore_index=True)
    combined = combined.sort_values(time_cols).reset_index(drop=True)

    if dados_mensais:
        combined["data"] = pd.to_datetime(
            dict(year=combined["ano"], month=combined["mes"], day=1)
        )
    else:
        combined["data"] = pd.to_datetime(dict(year=combined["ano"], month=1, day=1))

    return combined


def _apply_ranking_ties(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Atribui a mesma posição para valores empatados na tabela de ranking."""
    df = df.reset_index(drop=True)
    for i in range(1, len(df)):
        if df.loc[i, value_col] == df.loc[i - 1, value_col]:
            df.loc[i, "pos"] = df.loc[i - 1, "pos"]
    return df


def df_ranking_crime(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
    tamanho_cidade: str | None = None,
    ordem: str = "Decrescente",
) -> pd.DataFrame:
    """Monta tabela de ranking de criminalidade por mil habitantes (top 10 + cidade selecionada)."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
        tamanho_cidade=tamanho_cidade,
        manter_muni=None,
    )
    por_ano = df.groupby(["municipio", "cod_municipio", "ano"], as_index=False)["registros"].sum()

    pop_filtrada = dados_populacao
    if ano_intervalo is not None:
        pop_filtrada = pop_filtrada[
            (pop_filtrada["ano"] >= ano_intervalo[0]) & (pop_filtrada["ano"] <= ano_intervalo[1])
        ]

    merged = por_ano.merge(pop_filtrada, on=["cod_municipio", "ano"], how="left")
    merged["registros_rel_habitantes"] = (
        merged["registros"] / merged["populacao"]
    ) * GRUPO_HABITANTES

    ranking = merged.groupby(["municipio", "cod_municipio"], as_index=False).agg(
        registros_rel_habitantes=("registros_rel_habitantes", "sum"),
        registros=("registros", "sum"),
    )

    ascending = ordem == "Crescente"
    ranking = ranking.sort_values("registros_rel_habitantes", ascending=ascending).reset_index(
        drop=True
    )

    qtd_linhas = min(len(ranking), QTD_RANKING)
    df_atualizado = ranking.head(qtd_linhas).copy()
    df_atualizado["pos"] = list(range(1, qtd_linhas + 1))

    if nome_municipio in ranking["municipio"].values:
        pos_municipio = int(ranking.index[ranking["municipio"] == nome_municipio][0]) + 1
        if pos_municipio > qtd_linhas:
            extra = ranking.iloc[[pos_municipio - 1]].copy()
            extra["pos"] = pos_municipio
            df_atualizado = pd.concat([df_atualizado, extra], ignore_index=True)

    df_atualizado["registros_rel_habitantes"] = df_atualizado["registros_rel_habitantes"].round(2)
    df_atualizado = _apply_ranking_ties(df_atualizado, "registros_rel_habitantes")

    coluna_taxa = "Crimes violentos por mil hab." if categ is None else f"{categ} por mil hab."
    df_atualizado[coluna_taxa] = df_atualizado["registros_rel_habitantes"].apply(
        lambda v: format_pt_float(v, 2)
    )
    return df_atualizado[["pos", "municipio", coluna_taxa]].rename(
        columns={"pos": "#", "municipio": "Município"}
    )


def df_ranking_populacao(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    nome_municipio: str,
    ano_intervalo: tuple[int, int] | None = None,
    tamanho_cidade: str | None = None,
    ordem: str = "Decrescente",
) -> pd.DataFrame:
    """Monta tabela de ranking populacional (top 10 + cidade selecionada)."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        ano_intervalo=ano_intervalo,
        tamanho_cidade=tamanho_cidade,
        manter_muni=None,
    )

    pop_filtrada = dados_populacao
    if ano_intervalo is not None:
        pop_filtrada = pop_filtrada[
            (pop_filtrada["ano"] >= ano_intervalo[0]) & (pop_filtrada["ano"] <= ano_intervalo[1])
        ]

    merged = df.merge(pop_filtrada, on=["cod_municipio", "ano"], how="left")
    ranking = merged.groupby(
        ["municipio", "cod_municipio", "populacao", "ano"], as_index=False
    )["registros"].sum()

    ano_max = int(ranking["ano"].max())
    ranking = ranking[ranking["ano"] == ano_max]

    ascending = ordem == "Crescente"
    ranking = ranking.sort_values("populacao", ascending=ascending).reset_index(drop=True)

    qtd_linhas = min(len(ranking), QTD_RANKING)
    df_atualizado = ranking.head(qtd_linhas).copy()
    df_atualizado["pos"] = list(range(1, qtd_linhas + 1))

    if nome_municipio in ranking["municipio"].values:
        pos_municipio = int(ranking.index[ranking["municipio"] == nome_municipio][0]) + 1
        if pos_municipio > qtd_linhas:
            extra = ranking.iloc[[pos_municipio - 1]].copy()
            extra["pos"] = pos_municipio
            df_atualizado = pd.concat([df_atualizado, extra], ignore_index=True)

    df_atualizado = _apply_ranking_ties(df_atualizado, "populacao")

    coluna_populacao = f"População em {ano_max}"
    df_atualizado[coluna_populacao] = df_atualizado["populacao"].apply(format_pt_int)
    return df_atualizado[["pos", "municipio", coluna_populacao]].rename(
        columns={"pos": "#", "municipio": "Município"}
    )


def df_mapa(
    dados_totais: pd.DataFrame,
    dados_populacao: pd.DataFrame,
    mapa_minas: gpd.GeoDataFrame,
    categ: str | None = None,
    ano_intervalo: tuple[int, int] | None = None,
    tipo_crime: list[str] | None = None,
) -> gpd.GeoDataFrame:
    """Prepara GeoDataFrame com taxa de crimes por mil habitantes por município."""
    df = filtra_dataframe(
        dados_totais,
        dados_populacao,
        categ=categ,
        ano_intervalo=ano_intervalo,
        tipo_crime=tipo_crime,
    )
    por_ano = df.groupby(["municipio", "cod_municipio", "ano"], as_index=False)["registros"].sum()
    merged = por_ano.merge(dados_populacao, on=["cod_municipio", "ano"], how="left")
    merged["registros_rel_habitantes"] = (
        merged["registros"] / merged["populacao"]
    ) * GRUPO_HABITANTES

    agg = merged.groupby(["municipio", "cod_municipio"], as_index=False)[
        "registros_rel_habitantes"
    ].sum()
    return mapa_minas.merge(agg, on="cod_municipio", how="left")
