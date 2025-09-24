if(!require('dplyr'))install.packages("dplyr");library(dplyr)

# listing files in the directory
lf <- list.files("dados_input")

# start with cv string
cv_files <- lf[grep("cv", lf)]

# Dados

dados_totais_tratados <- data.frame()

# for each file, read and treat the data

for(file in cv_files) {
  dados <- read.csv(paste0("dados_input/", file), sep = ";", check.names = FALSE, fileEncoding = "Latin1")
  dados$RISP <- as.character(dados$RISP) # Transforma em caracter para padronizar com os novos arquivos (a partir de agosto/25)
  dados_totais_tratados <- bind_rows(dados_totais_tratados, dados)
}
rm(dados)

# Funções
## Seleciona apenas as colunas necessárias
remove_colunas <- function(df) {
  df <- df |>
    rename(registros = Registros, natureza = Natureza, municipio = Município, cod_municipio = `Cod IBGE`, mes = Mês, ano = Ano) |>
    select(registros, natureza, municipio, cod_municipio, mes, ano)
  
  df
}

dados_totais_tratados <- remove_colunas(dados_totais_tratados)


## Cria uma coluna com as 5 grandes categorias "Estupro", "Sequestro", "Extorsão", "Roubo" e "Homicídio"
cria_categorias <- function(df) {
  df$categoria <- ""
  categorias_crimes <- c("Estupro", "Sequestro", "Extorsão", "Roubo", "Homicídio") 
  
  # Existe a natureza 'Extorsão Mediante Sequestro Consumado'. 
  # Como Extorsão está depois de Sequestro no vetor acima, não haverá problema.
  
  for(cat in categorias_crimes) {
    df$categoria <- ifelse(grepl(cat, df$natureza), yes = cat, no = df$categoria)
  }
  
  df
}

dados_totais_tratados <- cria_categorias(dados_totais_tratados)


## Cria uma coluna com o tipo "Consumado" ou "Tentado"
cria_tipo <- function(df) {
  df$tipo <- ""
  tipos <- c("Consumado", "Tentado")
  
  for(tp in tipos) {
    df$tipo <- ifelse(grepl(tp, df$natureza), yes = tp, no = df$tipo)
  }
  
  df
}

dados_totais_tratados <- cria_tipo(dados_totais_tratados)


write.csv(dados_totais_tratados, 
          gzfile("dados_dash/dados_totais_tratados.csv.gz"), 
          row.names = FALSE)
