if(!require('httr'))install.packages("httr");library(httr)

## Raspagem pela API
requisicao <- GET(url = "https://servicodados.ibge.gov.br/api/v1/pesquisas/indicadores/97907/resultados/31xxxxx")
requisicao

content_api_ibge <- content(requisicao)
content_api_ibge

lista <- content_api_ibge[[1]]$res

localidade <- c()
populacao <- c()

for(i in 1:length(lista)) {
  localidade <- c(localidade, lista[[i]]$localidade)
  populacao <- c(populacao, lista[[i]]$res[[1]])
}

df_minas_pop_ibge <- data.frame(localidade, populacao)

write.csv(df_minas_pop_ibge, "dados_input/populacao-minas-ibge.csv")
