"""
Projeto: Telco Customer Churn (tratamento + features para Power BI)
Autor: Fabrício Miranda Carvalho
Objetivo: Ler o CSV, limpar dados (principalmente TotalCharges),
criar variáveis úteis (features) e exportar um CSV pronto para o Power BI.

Como usar:
1) Coloque este .py na MESMA pasta do CSV (recomendado).
2) Rode: python CustomerChurn.py
3) Ele vai gerar: telco_cleaned_for_powerbi.csv na mesma pasta.

"""

import os
import pandas as pd
import numpy as np


# ============================================================
# 1) Definindo caminhos (pra não dar erro de path no Windows)
# ============================================================

# Pego a pasta onde ESTE arquivo .py está salvo
base_dir = os.path.dirname(__file__)

# Monto o caminho completo do CSV (assumindo que ele está na mesma pasta)
csv_name = "WA_Fn-UseC_-Telco-Customer-Churn.csv"
path = os.path.join(base_dir, csv_name)

# (Só pra eu ter certeza de onde estou lendo)
print(f"Lendo arquivo em: {path}")


# ============================================================
# 2) Lendo o dataset
# ============================================================

# Leio o CSV com pandas
df = pd.read_csv(path)

# Olho o tamanho pra confirmar que carregou
print("Dataset carregado!")
print("Linhas e colunas:", df.shape)

# Vejo um resumo rápido (primeiras linhas)
print("\nPrévia do dataset:")
print(df.head())

# ============================================================
# 3) Ajustes iniciais de limpeza (strings e tipos)
# ============================================================

# Faço uma cópia pra evitar modificar o df original sem querer
df = df.copy()

# Pego todas as colunas do tipo texto (object)
obj_cols = df.select_dtypes(include="object").columns

# Removo espaços extras das strings (tipo " Yes " -> "Yes")
df[obj_cols] = df[obj_cols].apply(lambda s: s.str.strip())

# Agora, o grande ponto do dataset:
# TotalCharges normalmente vem como texto, às vezes com espaço em branco.
# Converto pra número e forço erros virarem NaN
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

# Eu conto quantos NaNs apareceram depois da conversão
n_nans_totalcharges = df["TotalCharges"].isna().sum()
print(f"\nTotalCharges virou numérico. NaNs gerados: {n_nans_totalcharges}")

# Geralmente esses NaNs são clientes com tenure = 0 (cliente novinho).
# Faz sentido total dele ser 0.
df["TotalCharges"] = df["TotalCharges"].fillna(0)

# ============================================================
# 4) Criando alvo (target) para churn e variáveis binárias
# ============================================================

# Crio uma versão numérica do churn: Yes = 1, No = 0
df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)

# Algumas colunas são Yes/No bem diretas
yes_no_cols = ["Partner", "Dependents", "PhoneService", "PaperlessBilling"]

# Eu crio versões numéricas dessas colunas para ajudar nas análises
for c in yes_no_cols:
    df[c + "_bin"] = df[c].map({"Yes": 1, "No": 0}).astype("Int64")

print("\nChurn rate (média do ChurnFlag):", df["ChurnFlag"].mean())


# ============================================================
# 5) Feature engineering (o que ajuda MUITO no Power BI)
# ============================================================

# 5.1) Faixas de tempo como cliente (tenure)
# Crio "bandas" para facilitar gráfico e segmentação no BI
bins_tenure = [-1, 0, 6, 12, 24, 48, 72, 10**9]
labels_tenure = ["0", "1-6", "7-12", "13-24", "25-48", "49-72", "73+"]

df["tenure_band"] = pd.cut(df["tenure"], bins=bins_tenure, labels=labels_tenure)

# 5.2) Faixas de MonthlyCharges (quintis)
# Isso divide em 5 grupos com quantidades semelhantes de clientes
df["monthly_band"] = pd.qcut(df["MonthlyCharges"], q=5, duplicates="drop")

# 5.3) Valor do cliente (proxy simples): quanto ele "gera" ao longo do tempo
# Não é o valor real da vida inteira, mas ajuda a enxergar impacto
df["customer_value"] = df["tenure"] * df["MonthlyCharges"]

# 5.4) Contagem de serviços ativos (bom pra entender churn)
service_cols = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies", "MultipleLines"
]

# Defino uma função simples: só "Yes" conta como serviço ativo
def is_active_service(x: str) -> int:
    return 1 if x == "Yes" else 0

# Crio colunas auxiliares _active e depois somo tudo
for c in service_cols:
    df[c + "_active"] = df[c].apply(is_active_service)

df["services_count"] = df[[c + "_active" for c in service_cols]].sum(axis=1)


# ============================================================
# 6) Checagens rápidas (sanity checks)
# ============================================================

print("\nChecagem rápida - tipos e resumo numérico:")
print(df[["tenure", "MonthlyCharges", "TotalCharges", "customer_value", "services_count"]].describe())

print("\nChurn por Contract (média do churn):")
print(df.groupby("Contract")["ChurnFlag"].mean().sort_values(ascending=False))

print("\nChurn por tenure_band:")
print(df.groupby("tenure_band")["ChurnFlag"].mean())


# ============================================================
# 7) Preparando dataframe final para o Power BI
# ============================================================

# Garantindo que o customerID é texto (bom pra chave)
df["customerID"] = df["customerID"].astype(str)

# Organizo algumas colunas importantes no começo (fica mais fácil no BI)
front_cols = [
    "customerID", "Churn", "ChurnFlag",
    "tenure", "tenure_band",
    "MonthlyCharges", "monthly_band",
    "TotalCharges", "customer_value",
    "services_count"
]

# Adiciono todas as outras colunas depois
other_cols = [c for c in df.columns if c not in front_cols]
df_bi = df[front_cols + other_cols]


# ============================================================
# 8) Exportando CSV final (pronto para Power BI)
# ============================================================

out_name = "telco_limpo_para_powerbi.csv"
out_path = os.path.join(base_dir, out_name)

df_bi.to_csv(out_path, index=False)

print(f"\n✅ Arquivo exportado com sucesso: {out_path}")
print("Agora eu posso importar esse CSV no Power BI e montar o dashboard.")