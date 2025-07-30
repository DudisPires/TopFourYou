import pandas as pd
import numpy as np
import os
import sys

from src.scraping.letterboxd_scraper import get_favorite_movies
from src.matching.fuzzy_matcher import match_titles
from src.embedding.embedding_generator import generate_descriptions, embed_descriptions
from src.recommender.recommender import recommend_movies_with_diversity

# --- CONFIGURAÇÕES ---
# Nome do arquivo do seu dataset de filmes
DATASET_PATH = '/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/world_imdb_movies_preprocessed.csv' # IMPORTANTE: Adapte para o nome do seu arquivo CSV
# Nome do arquivo para salvar/carregar os embeddings pré-calculados
EMBEDDINGS_PATH = '/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/embeddings/movie_embeddings.npy'
# Nickname do usuário do Letterboxd
LETTERBOXD_NICKNAME = 'ceciliamonteiro' # Altere aqui ou peça como input

def main():
    """
    Função principal que orquestra todo o processo de recomendação de filmes.
    """
    print("--- Sistema de Recomendação de Filmes Baseado no Letterboxd ---")

    # --- ETAPA 1: Obter os filmes favoritos do usuário ---
    print(f"\n[1/5] Buscando os 4 favoritos de '{LETTERBOXD_NICKNAME}' no Letterboxd...")
    favorite_titles = get_favorite_movies(LETTERBOXD_NICKNAME)
    
    if not favorite_titles:
        print("Não foi possível continuar. Encerrando o programa.")
        sys.exit()
    
    print("Favoritos encontrados:", favorite_titles)

    # --- ETAPA 2: Carregar o dataset de filmes ---
    print(f"\n[2/5] Carregando o dataset de filmes de '{DATASET_PATH}'...")
    if not os.path.exists(DATASET_PATH):
        print(f"Erro: O arquivo do dataset '{DATASET_PATH}' não foi encontrado.")
        sys.exit()
    
    try:
        imdb_df = pd.read_csv(DATASET_PATH)
        
        # COLUNAS ESPERADAS: ['title', 'year', 'genre', 'director', 'star', 'language', 'rating_imdb']
        colunas_necessarias = ['title', 'year', 'genre', 'director', 'star', 'language', 'rating_imdb']
        
        # Verifica se todas as colunas necessárias existem no DataFrame
        if not all(coluna in imdb_df.columns for coluna in colunas_necessarias):
            print("Erro: O dataset não contém todas as colunas necessárias.")
            print(f"Verifique se seu arquivo CSV possui as colunas: {colunas_necessarias}")
            sys.exit()

        # Garante que não haja valores nulos nas colunas principais para evitar erros
        imdb_df.dropna(subset=['title', 'year', 'director', 'star', 'genre'], inplace=True)

    except FileNotFoundError:
        print(f"Erro fatal: O arquivo do dataset '{DATASET_PATH}' não foi encontrado.")
        sys.exit()
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao carregar o CSV: {e}")
        sys.exit()

    # --- ETAPA 3: Combinar títulos dos favoritos com o dataset ---
    print("\n[3/5] Combinando títulos dos favoritos com o dataset usando fuzzy matching...")
    imdb_titles = imdb_df['title'].tolist()
    matched_titles = match_titles(favorite_titles, imdb_titles, threshold=85)

    if not matched_titles:
        print("Não foi possível encontrar correspondências para os filmes favoritos no dataset.")
        sys.exit()
        
    print("Filmes correspondentes no dataset:", list(matched_titles.values()))

    # --- ETAPA 4: Gerar ou carregar os embeddings ---
    if os.path.exists(EMBEDDINGS_PATH):
        print(f"\n[4/5] Carregando embeddings pré-calculados de '{EMBEDDINGS_PATH}'...")
        embeddings = np.load(EMBEDDINGS_PATH)
    else:
        print("\n[4/5] Gerando embeddings para o dataset (isso pode levar alguns minutos)...")
        descriptions = generate_descriptions(imdb_df)
        embeddings = embed_descriptions(descriptions)
        print(f"Salvando embeddings em '{EMBEDDINGS_PATH}' para uso futuro.")
        np.save(EMBEDDINGS_PATH, embeddings)

    # --- ETAPA 5: Gerar e exibir as recomendações ---
    print("\n[5/5] Gerando recomendações com base nos seus favoritos...")
    # Chame a nova função, você pode experimentar os valores de `diversity_threshold`
    recommendations = recommend_movies_with_diversity(
        fav_matches=matched_titles,
        imdb_df=imdb_df,
        embeddings=embeddings,
        top_n=10,
        candidate_pool_size=50,
        diversity_threshold=0.85 # Tente valores entre 0.8 (mais diverso) e 0.95 (menos diverso)
    )

    print("\n--- RECOMENDAÇÕES PARA VOCÊ ---")
    # Verifica se o dataframe de recomendações não está vazio
    if not recommendations.empty:
        print(recommendations.to_string(index=False))
    else:
        print("Não foi possível gerar recomendações.")


if __name__ == "__main__":
    main()