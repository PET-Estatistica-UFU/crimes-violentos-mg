"""Funções de geração de gráficos (Plotly) e mapas (Plotly / GeoPandas)."""

import json
import textwrap

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import shapely

from src.data_loader import COR_AZUL_ESCURO, COR_VERMELHO, PALETA_CORES, format_pt_float, format_pt_int


def grafico_barras_natureza(tabela: pd.DataFrame, categ: str | None = None) -> go.Figure:
    """Gráfico de barras horizontais por categoria ou natureza do crime."""
    col = "categoria" if categ is None else "natureza"
    labels_wrapped = ["<br>".join(textwrap.wrap(str(val), width=18)) for val in tabela[col]]
    valores = tabela["registros"].tolist()
    textos = [format_pt_int(v) for v in valores]

    max_val = max(valores) if valores else 1
    fig = go.Figure(
        go.Bar(
            x=valores,
            y=labels_wrapped,
            orientation="h",
            marker_color=COR_VERMELHO,
            text=textos,
            textposition="outside",
            textfont=dict(size=14, color="#fdfefe"),
            hovertemplate="%{y}: %{text} registros<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fdfefe"),
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            range=[0, max_val * 1.22],
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=13, color="#fdfefe"),
        ),
        height=420,
    )
    return fig


def grafico_linhas_historico(tabela: pd.DataFrame, categ: str | None = None) -> go.Figure:
    """Gráfico de linhas histórico em Plotly com apenas 'Total' visível inicialmente."""
    col = "categoria" if categ is None else "natureza"
    label_tipo = "Categoria" if categ is None else "Natureza"
    unico_ano = int(tabela["ano"].min()) == int(tabela["ano"].max())

    series_names = tabela[col].unique().tolist()
    # Garante 'Total' ao final ou na ordem padrão com cor consistente
    ordered_names = [s for s in series_names if s != "Total"] + (
        ["Total"] if "Total" in series_names else []
    )

    fig = go.Figure()
    for idx, name in enumerate(ordered_names):
        sub = tabela[tabela[col] == name].sort_values("data")
        color = PALETA_CORES[idx % len(PALETA_CORES)]
        visible = True if name == "Total" else "legendonly"
        custom_dates = sub["data"].dt.strftime("%m/%y").tolist()
        hover_text = [
            f"Registros: {format_pt_int(reg)}<br>Data: {dt}<br>{label_tipo}: {name}"
            for reg, dt in zip(sub["registros"], custom_dates)
        ]

        fig.add_trace(
            go.Scatter(
                x=sub["data"],
                y=sub["registros"],
                mode="lines+markers" if len(sub) <= 12 else "lines",
                name=name,
                line=dict(color=color, width=2.5),
                visible=visible,
                text=hover_text,
                hoverinfo="text",
            )
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fdfefe"),
        margin=dict(l=10, r=10, t=10, b=80),
        xaxis=dict(
            title="Mês" if unico_ano else "Ano",
            dtick="M1" if unico_ano else "M12",
            tickformat="%m" if unico_ano else "%y",
            gridcolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            title=None,
            rangemode="tozero",
            gridcolor="rgba(255,255,255,0.1)",
        ),
        legend=dict(
            orientation="h",
            x=0.5,
            y=-0.22,
            xanchor="center",
            yanchor="top",
        ),
        showlegend=True,
        height=420,
    )
    return fig


def grafico_mapa_violencia(gdf: gpd.GeoDataFrame) -> go.Figure:
    """Mapa coroplético de crimes violentos por mil habitantes em Minas Gerais."""
    gdf_plot = gdf[["cod_municipio", "geometry"]].copy()
    # Plotly (D3-geo) exige anéis exteriores no sentido horário (CW)
    gdf_plot["geometry"] = shapely.orient_polygons(gdf_plot.geometry, exterior_cw=True)
    geojson_data = json.loads(gdf_plot.to_json())
    taxa = gdf["registros_rel_habitantes"].fillna(0.0)
    hover_text = [
        f"{muni if pd.notna(muni) else cod}<br>Crimes por mil hab.: {format_pt_float(val, 2)}"
        for muni, cod, val in zip(gdf["municipio"], gdf["cod_municipio"], taxa)
    ]

    fig = go.Figure(
        go.Choropleth(
            geojson=geojson_data,
            locations=gdf["cod_municipio"],
            featureidkey="properties.cod_municipio",
            z=taxa,
            colorscale=[[0.0, "#FFFFFF"], [1.0, "#492627"]],
            colorbar=dict(title="Crimes<br>por mil hab.", tickfont=dict(color="#fdfefe")),
            marker_line_color="rgba(120,120,120,0.35)",
            marker_line_width=0.4,
            text=hover_text,
            hoverinfo="text",
        )
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fdfefe"),
        margin=dict(l=0, r=0, t=10, b=10),
        height=580,
    )
    return fig


def grafico_mapa_localizacao(gdf: gpd.GeoDataFrame, nome_municipio: str) -> plt.Figure:
    """Mapa de localização destacando o município selecionado em azul."""
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=COR_AZUL_ESCURO)
    ax.set_facecolor(COR_AZUL_ESCURO)

    gdf.plot(ax=ax, color="#E5E5E5", edgecolor="#BFBFBF", linewidth=0.35)
    selecionado = gdf[gdf["municipio"] == nome_municipio]
    if not selecionado.empty:
        selecionado.plot(ax=ax, color="blue", edgecolor="none")

    ax.set_title(
        "A cidade selecionada foi preenchida com a cor azul",
        fontsize=11,
        color="#fdfefe",
        loc="left",
        pad=10,
    )
    ax.axis("off")
    plt.tight_layout()
    return fig
