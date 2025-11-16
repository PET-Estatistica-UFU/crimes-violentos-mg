if(!require('dplyr'))install.packages("dplyr");library(dplyr)
if(!require('readxl'))install.packages("readxl");library(readxl)

# De 2012 a 2023 foi baixado desse link: https://basedosdados.org/dataset/d30222ad-7a5c-4778-a1ec-f0785371d1ca?raw_data_source=522f2745-3e1f-43b8-a64e-5d6c9162979a

dados_populacao_antigo <- read.csv("dados_input/populacao-minas-ibge.csv")
dados_populacao_novo <- read.csv("dados_input/ibge_populacao_municipio.csv")
POP2024 <- read_excel("dados_input/POP2024.xlsx", sheet = "Página1")
POP2025 <- read_excel("dados_input/POP2025.xlsx", sheet = "Página2")

dados_populacao_novo <- dados_populacao_novo |>
  filter(sigla_uf == "MG") |>
  filter(ano < 2022) |>
  select(-sigla_uf) |>
  mutate(id_municipio = as.numeric(substr(id_municipio, start = 1, stop = 6))) |>
  rename(localidade = id_municipio)


dados_populacao_antigo$ano <- 2022

dados_populacao_2023 <- dados_populacao_antigo |>
  mutate(ano = 2023)

dados_populacao_2024 <- POP2024 |>
  mutate(ano = 2024,
         localidade = paste0("31", `COD. MUNIC`)) |>
  mutate(localidade = as.numeric(substr(localidade, start = 1, stop = 6)),
         populacao = `POPULAÇÃO ESTIMADA`) |>
  select(localidade, ano, populacao)

dados_populacao_2025 <- POP2025 |>
  mutate(ano = 2025,
         localidade = paste0("31", `COD. MUNIC`)) |>
  mutate(localidade = as.numeric(substr(localidade, start = 1, stop = 6)),
         populacao = `POPULAÇÃO ESTIMADA`) |>
  select(localidade, ano, populacao)

dados_populacao_antigo <- bind_rows(dados_populacao_antigo, dados_populacao_2023, dados_populacao_2024, dados_populacao_2025)

dados_populacao_antigo <- dados_populacao_antigo |>
  arrange(localidade, ano) |>
  select(-X)


dados_populacao_completo <- bind_rows(dados_populacao_antigo, dados_populacao_novo) |>
  filter(ano >= 2012) |>
  arrange(localidade, ano)



write.csv(dados_populacao_completo, "dados_dash/dados_populacao_completo.csv", row.names = FALSE)

