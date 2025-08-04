import pandas as pd

# Carregar a nova base
df = pd.read_csv("/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/netflix_titles.csv")


# --- Pré-processamento ---

# title: já está pronto
df['type'] = df['type'] 

df['title'] = df['title']

# year: extrai o ano da release_date
df['release_date'] = df['release_year']

df['genre'] = df['listed_in']

df['director'] = df['director']


# --- Selecionar e salvar colunas finais ---
df_final = df[['type','title', 'release_date', 'genre', 'director']]
df_final.to_csv("/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/pre-processing/nova-NETFLIX.csv", index=False)
