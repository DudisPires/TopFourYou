import pandas as pd

# Carregar a nova base
df = pd.read_csv("/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/TMDB_movie_dataset_v11.csv")

# --- Pré-processamento ---

# title: já está pronto
df['title'] = df['title']

# year: extrai o ano da release_date
df['release_date'] = df['release_date']

# rating_imdb: usar vote_average
df['rating_imdb'] = df['vote_average']

# genre: já está como string separada por vírgula
df['genre'] = df['genres']

# language: usar original_language
df['language'] = df['original_language']

# --- Filtrar filmes com rating_imdb > 0 ---
df = df[df['rating_imdb'] >= 6]

# --- Selecionar e salvar colunas finais ---
df_final = df[['title', 'release_date', 'rating_imdb', 'genre', 'language']]
df_final.to_csv("/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/pre-processing/base_transformada.csv", index=False)
