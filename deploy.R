if (!require('rsconnect'))install.packages("rsconnect");library(rsconnect)

rsconnect::setAccountInfo(name=Sys.getenv("NAME"), 
                          token=Sys.getenv("TOKEN"), 
                          secret=Sys.getenv("SECRET"))

rsconnect::forgetDeployment("crimes-mg")

rsconnect::deployApp(
  appName = "crimes-mg",
  appFiles = c(
    "dash.qmd",
    "dash.html",
    "dados_dash/dados_populacao_completo.csv",
    "dados_dash/dados_totais_tratados.csv.gz",
    "dash_files/"
  ),
  forceUpdate = TRUE
)
