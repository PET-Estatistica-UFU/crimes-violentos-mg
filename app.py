"""Aplicação Streamlit: Crimes violentos em Minas Gerais."""

import streamlit as st

from src.analytics import (
    crimes_rel_habitantes,
    df_mapa,
    df_ranking_crime,
    df_ranking_populacao,
    df_temporal,
    df_total,
    media_crimes,
    porc_alteracao_crimes,
    posicao_abs_municipio,
    posicao_rel_municipio,
    texto_informativo,
    total_crimes,
)
from src.charts import (
    grafico_barras_natureza,
    grafico_linhas_historico,
    grafico_mapa_localizacao,
    grafico_mapa_violencia,
)
from src.data_loader import (
    COR_AZUL,
    COR_AZUL_ESCURO,
    COR_AZUL_SIDEBAR,
    COR_VERMELHO,
    load_crimes_data,
    load_map_data,
    load_population_data,
    sort_pt,
)

st.set_page_config(
    page_title="Crimes violentos em Minas Gerais",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = f"""
<style>
    .stApp {{
        background-color: {COR_AZUL_ESCURO};
        color: #fdfefe;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {COR_AZUL_SIDEBAR};
        color: #fdfefe;
    }}
    .pop-cidade-box {{
        background-color: #335A7A;
        border-radius: 4px;
        padding: 8px 10px;
        font-size: 0.85rem;
        margin-bottom: 1rem;
        color: #fdfefe;
    }}
    .value-box {{
        background-color: {COR_VERMELHO};
        border-radius: 6px;
        padding: 12px 14px;
        color: #fdfefe;
        min-height: 92px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .value-box-title {{
        font-size: 0.8rem;
        opacity: 0.95;
        margin-bottom: 4px;
    }}
    .value-box-value {{
        font-size: 1.55rem;
        font-weight: 700;
        line-height: 1.2;
    }}
    .card-title {{
        background-color: {COR_AZUL_SIDEBAR};
        padding: 8px 14px;
        border-radius: 6px 6px 0 0;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }}
    div[data-baseweb="tab-list"] {{
        background-color: {COR_AZUL};
        padding: 4px 8px 0 8px;
        border-radius: 6px;
    }}
    button[data-baseweb="tab"] {{
        color: #fdfefe !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        border-bottom: 3px solid #fdfefe !important;
        font-weight: 600;
    }}
    div[data-testid="stSliderTickBarMin"],
    div[data-testid="stSliderTickBarMax"] {{
        color: #fdfefe !important;
        opacity: 0.9 !important;
        font-weight: 500;
    }}
    div[data-testid="stSliderThumbValue"] {{
        color: #fdfefe !important;
        background-color: #335A7A;
        padding: 1px 6px;
        border-radius: 3px;
        font-weight: 600;
    }}
</style>
"""


def _render_value_box(title: str, value: str) -> None:
    """Renderiza um card métrico estilizado."""
    st.markdown(
        f"""
        <div class="value-box">
            <div class="value-box-title">{title}</div>
            <div class="value-box-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _protect_tipo_crime() -> None:
    """Impede que ambos os checkboxes de tipo de crime fiquem desmarcados."""
    if not st.session_state.get("chk_consumado", True) and not st.session_state.get(
        "chk_tentado", True
    ):
        st.session_state["chk_consumado"] = True
        st.session_state["chk_tentado"] = True


def main() -> None:
    """Inicializa dados, barra lateral e visões do dashboard."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    dados_totais = load_crimes_data()
    dados_populacao = load_population_data()
    mapa_minas = load_map_data()

    ano_minimo = int(dados_totais["ano"].min())
    ano_maximo = int(dados_totais["ano"].max())
    cidades = sort_pt(dados_totais["municipio"].dropna().unique().tolist())
    categorias = ["Todas"] + dados_totais["categoria"].dropna().unique().tolist()

    # Inicialização de estado para proteção de seleção vazia e toggle automático
    if "chk_consumado" not in st.session_state:
        st.session_state["chk_consumado"] = True
    if "chk_tentado" not in st.session_state:
        st.session_state["chk_tentado"] = True
    if "prev_single_year" not in st.session_state:
        st.session_state["prev_single_year"] = False
    if "dados_mensais" not in st.session_state:
        st.session_state["dados_mensais"] = False

    with st.sidebar:
        default_city_idx = cidades.index("Uberlândia") if "Uberlândia" in cidades else 0
        cidade_escolhida = st.selectbox("Cidade:", options=cidades, index=default_city_idx)

        info_txt = texto_informativo(dados_totais, dados_populacao, cidade_escolhida)
        st.markdown(f'<div class="pop-cidade-box">{info_txt}</div>', unsafe_allow_html=True)

        categoria_sel = st.selectbox("Categoria:", options=categorias, index=0)
        categ = None if categoria_sel == "Todas" else categoria_sel

        ano_sel = st.slider(
            "Ano:",
            min_value=ano_minimo,
            max_value=ano_maximo,
            value=(ano_minimo, ano_maximo),
            step=1,
        )
        ano_intervalo = None if ano_sel == (ano_minimo, ano_maximo) else ano_sel

        st.markdown("**Crime:**")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.checkbox("Consumado", key="chk_consumado", on_change=_protect_tipo_crime)
        with col_c2:
            st.checkbox("Tentado", key="chk_tentado", on_change=_protect_tipo_crime)

        tipo_crime: list[str] = []
        if st.session_state["chk_consumado"]:
            tipo_crime.append("Consumado")
        if st.session_state["chk_tentado"]:
            tipo_crime.append("Tentado")

        st.markdown("---")
        with st.expander("Avisos", expanded=False):
            st.markdown(
                """
Fonte dos dados: [Sejusp](https://www.seguranca.mg.gov.br/index.php/transparencia/dados-abertos)

Os dados são reportados mensalmente e se referem aos registros, e não à quantidade de vítimas.

Os dados de feminicídio passaram a ser reportados separadamente de homicídio a partir de 2025. Porém, em outubro de 2026, todos os dados de feminicídio voltaram a ser contabilizados na categoria de homicídio.

São consideradas:
- Cidades pequenas: menos de 100 mil hab.
- Cidades médias: com 100 mil a 500 mil hab.
- Cidades grandes: mais de 500 mil hab.

A cidade é classificada de acordo com a população do último ano do intervalo de tempo escolhido.

Caso o intervalo de tempo escolhido seja de um ano, a opção de 'Dados mensais' será automaticamente selecionada e a escala do gráfico mudará de 'ano' para 'mês'.

Os dados da população de 2023 são iguais ao da população de 2022.

Dúvidas ou sugestões: petestatisticaufu@gmail.com
                """
            )

    # Toggle automático de "Dados mensais" ao escolher intervalo de 1 ano
    is_single_year = ano_sel[0] == ano_sel[1]
    if is_single_year and not st.session_state["prev_single_year"]:
        st.session_state["dados_mensais"] = True
    st.session_state["prev_single_year"] = is_single_year

    st.title("Crimes violentos em Minas Gerais")
    tab_est, tab_rank, tab_map = st.tabs(["Estatísticas", "Rankings", "Mapas"])

    with tab_est:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            _render_value_box(
                "Número total de crimes",
                total_crimes(
                    dados_totais, dados_populacao, cidade_escolhida, categ, ano_intervalo, tipo_crime
                ),
            )
        with c2:
            _render_value_box(
                "Crimes por mil habitantes",
                crimes_rel_habitantes(
                    dados_totais, dados_populacao, cidade_escolhida, categ, ano_intervalo, tipo_crime
                ),
            )
        with c3:
            _render_value_box(
                "Média mensal de crimes",
                media_crimes(
                    dados_totais, dados_populacao, cidade_escolhida, categ, ano_intervalo, tipo_crime
                ),
            )
        with c4:
            _render_value_box(
                "Variação no último mês",
                porc_alteracao_crimes(
                    dados_totais,
                    dados_populacao,
                    cidade_escolhida,
                    ano_maximo,
                    categ,
                    ano_intervalo,
                    tipo_crime,
                ),
            )
        with c5:
            _render_value_box(
                "Posição absoluta em MG",
                posicao_abs_municipio(
                    dados_totais, dados_populacao, cidade_escolhida, categ, ano_intervalo, tipo_crime
                ),
            )
        with c6:
            _render_value_box(
                "Posição relativa em MG",
                posicao_rel_municipio(
                    dados_totais, dados_populacao, cidade_escolhida, categ, ano_intervalo, tipo_crime
                ),
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown('<div class="card-title">Natureza do crime</div>', unsafe_allow_html=True)
            tab_tot = df_total(
                dados_totais, dados_populacao, cidade_escolhida, categ, ano_intervalo, tipo_crime
            )
            st.plotly_chart(
                grafico_barras_natureza(tab_tot, categ=categ),
                use_container_width=True,
            )

        with col_right:
            header_col, chk_col = st.columns([3, 1])
            with header_col:
                st.markdown('<div class="card-title">Dados históricos</div>', unsafe_allow_html=True)
            with chk_col:
                dados_mensais = st.checkbox("Dados mensais", key="dados_mensais")

            tab_temp = df_temporal(
                dados_totais,
                dados_populacao,
                cidade_escolhida,
                categ,
                ano_intervalo,
                dados_mensais=dados_mensais,
                tipo_crime=tipo_crime,
            )
            st.plotly_chart(
                grafico_linhas_historico(tab_temp, categ=categ),
                use_container_width=True,
            )

    with tab_rank:
        f_col1, f_col2, _ = st.columns([2, 2, 4])
        with f_col1:
            tamanho_cidade = st.selectbox(
                "Cidades:",
                options=[
                    "Todas",
                    "Grandes",
                    "Médias",
                    "Pequenas",
                    "Grandes e médias",
                    "Médias e pequenas",
                ],
                index=0,
            )
        with f_col2:
            ordem_ranking = st.selectbox(
                "Ordem:",
                options=["Decrescente", "Crescente"],
                index=0,
            )

        sub_crim, sub_pop = st.tabs(["Criminalidade", "População"])
        with sub_crim:
            tb_rank = df_ranking_crime(
                dados_totais,
                dados_populacao,
                cidade_escolhida,
                categ=categ,
                ano_intervalo=ano_intervalo,
                tipo_crime=tipo_crime,
                tamanho_cidade=tamanho_cidade,
                ordem=ordem_ranking,
            )
            st.dataframe(tb_rank, hide_index=True, use_container_width=True)

        with sub_pop:
            tb_pop = df_ranking_populacao(
                dados_totais,
                dados_populacao,
                cidade_escolhida,
                ano_intervalo=ano_intervalo,
                tamanho_cidade=tamanho_cidade,
                ordem=ordem_ranking,
            )
            st.dataframe(tb_pop, hide_index=True, use_container_width=True)

    with tab_map:
        sub_viol, sub_loc = st.tabs(["Mapa da violência", "Localização"])
        gdf_mapa = df_mapa(
            dados_totais,
            dados_populacao,
            mapa_minas,
            categ=categ,
            ano_intervalo=ano_intervalo,
            tipo_crime=tipo_crime,
        )
        with sub_viol:
            st.plotly_chart(grafico_mapa_violencia(gdf_mapa), use_container_width=True)
        with sub_loc:
            fig_loc = grafico_mapa_localizacao(gdf_mapa, cidade_escolhida)
            st.pyplot(fig_loc, use_container_width=True)


if __name__ == "__main__":
    main()
