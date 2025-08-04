import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
# O FAISS é uma biblioteca da Meta para busca de similaridade eficiente.
# Para instalar, use: pip install faiss-cpu
import faiss

def recommend_movies_advanced(
    fav_matches,
    imdb_df,
    embeddings,
    ratings=None,
    top_n=10,
    candidate_pool_size=100,
    lambda_=0.7
):
    """
    Gera recomendações de filmes com diversidade usando uma implementação clássica de
    Maximal Marginal Relevance (MMR) e preparada para escalabilidade com FAISS.

    Parâmetros:
    - fav_matches (dict): Dicionário com os filmes favoritos do usuário.
    - imdb_df (pd.DataFrame): DataFrame com os dados dos filmes.
    - embeddings (np.ndarray): Matriz de embeddings de todos os filmes.
    - ratings (dict, opcional): Dicionário de {title: rating} para ponderar o perfil do usuário.
    - top_n (int): O número de recomendações a serem retornadas.
    - candidate_pool_size (int): O tamanho do pool inicial de candidatos a serem considerados.
    - lambda_ (float): Parâmetro para o MMR. Controla o trade-off entre relevância e diversidade.
                       lambda_ = 1 -> Apenas relevância.
                       lambda_ = 0 -> Apenas diversidade.
    """
    # --- 1. Obter Índices e Criar Perfil de Usuário (Simples ou Ponderado) ---
    try:
        indices = [imdb_df[imdb_df['title'] == match].index[0] for match in fav_matches.values()]
    except IndexError:
        print("Erro: Não foi possível encontrar os índices para um ou mais filmes favoritos.")
        return pd.DataFrame()

    fav_vecs = embeddings[indices]

    if ratings:
        # Perfil Ponderado: filmes com maior nota têm mais peso.
        weights = np.array([ratings.get(title, 1.0) for title in fav_matches.values()]).reshape(-1, 1)
        mean_vector = np.sum(fav_vecs * weights, axis=0) / np.sum(weights)
    else:
        # Perfil Simples: média dos vetores.
        mean_vector = np.mean(fav_vecs, axis=0)

    user_profile_vec = mean_vector.reshape(1, -1)

    # --- 2. Gerar Pool de Candidatos (Otimizado com FAISS) ---
    # Para datasets muito grandes, a busca por similaridade em todo o catálogo é lenta.
    # O FAISS cria um índice que torna essa busca ordens de magnitude mais rápida.

    # Normalizar embeddings para busca com produto interno (equivalente à similaridade de cosseno)
    faiss.normalize_L2(embeddings)
    
    d = embeddings.shape[1]  # Dimensão dos vetores
    index = faiss.IndexFlatIP(d) # IndexFlatIP é para produto interno (Inner Product)
    index.add(embeddings)

    # Busca os `candidate_pool_size` vizinhos mais próximos do perfil do usuário
    # Adicionamos len(indices) para garantir que teremos candidatos suficientes após remover os favoritos.
    k = candidate_pool_size + len(indices)
    distances, candidate_indices = index.search(user_profile_vec, k)

    # Filtra os candidatos, removendo os filmes que o usuário já favoritou
    candidate_indices = [idx for idx in candidate_indices[0] if idx not in indices]
    candidate_indices = candidate_indices[:candidate_pool_size]

    # --- 3. Algoritmo Maximal Marginal Relevance (MMR) ---
    # Seleciona iterativamente os itens que maximizam a relevância e a diversidade.

    # Calcula a relevância (similaridade com o perfil do usuário) para cada candidato
    candidate_embeddings = embeddings[candidate_indices]
    relevance_scores = cosine_similarity(user_profile_vec, candidate_embeddings)[0]

    # Dicionário para fácil acesso: {indice_filme: score_relevancia}
    candidate_relevance = {idx: score for idx, score in zip(candidate_indices, relevance_scores)}

    # Inicia a lista de recomendações com o item mais relevante
    recommendations_indices = [candidate_indices[np.argmax(relevance_scores)]]
    candidate_indices.pop(np.argmax(relevance_scores))

    while len(recommendations_indices) < top_n and candidate_indices:
        mmr_scores = []
        
        # Vetores dos filmes já recomendados
        recommended_vecs = embeddings[recommendations_indices]

        for candidate_idx in candidate_indices:
            candidate_vec = embeddings[candidate_idx].reshape(1, -1)
            
            # Relevância do candidato (já calculada)
            relevance = candidate_relevance[candidate_idx]
            
            # Similaridade com os itens já selecionados
            similarity_with_selected = cosine_similarity(candidate_vec, recommended_vecs)
            max_similarity = np.max(similarity_with_selected)
            
            # Cálculo do MMR Score
            mmr_score = lambda_ * relevance - (1 - lambda_) * max_similarity
            mmr_scores.append((mmr_score, candidate_idx))

        if not mmr_scores:
            break

        # Seleciona o candidato com o maior MMR score
        best_candidate_idx = max(mmr_scores, key=lambda x: x[0])[1]
        
        recommendations_indices.append(best_candidate_idx)
        candidate_indices.remove(best_candidate_idx)

    # --- 4. Retornar Filmes Recomendados ---
    return imdb_df.iloc[recommendations_indices][['title', 'genre', 'release_date', 'language', 'rating_imdb']]\
             .sort_values(by='rating_imdb', ascending=False)\
             .reset_index(drop=True)

# --- Exemplo de Uso ---
if __name__ == '__main__':
    # Criando dados de exemplo para demonstração
    num_movies = 1000
    embedding_dim = 32
    
    # Gerando embeddings aleatórios
    np.random.seed(42)
    sample_embeddings = np.random.rand(num_movies, embedding_dim).astype('float32')

    # Criando um DataFrame de exemplo
    titles = [f'Filme {i}' for i in range(num_movies)]
    genres = [np.random.choice(['Ação', 'Comédia', 'Drama', 'Ficção Científica']) for _ in range(num_movies)]
    dates = [f'20{np.random.randint(10, 24)}-01-01' for _ in range(num_movies)]
    languages = ['Inglês'] * num_movies
    ratings_imdb = np.round(np.random.uniform(5.0, 9.5, num_movies), 1)
    
    sample_imdb_df = pd.DataFrame({
        'title': titles,
        'genre': genres,
        'release_date': dates,
        'language': languages,
        'rating_imdb': ratings_imdb
    })

    # Filmes favoritos do usuário e suas notas
    user_favorites = {
        '1': 'Filme 10', # Gosta muito
        '2': 'Filme 11', # Gosta muito
        '3': 'Filme 500' # Gosta, mas é bem diferente dos outros
    }
    
    user_ratings = {
        'Filme 10': 5.0,
        'Filme 11': 4.5,
        'Filme 500': 3.0
    }

    print("--- Recomendações com Perfil Ponderado e MMR (lambda=0.7) ---")
    recommendations = recommend_movies_advanced(
        fav_matches=user_favorites,
        imdb_df=sample_imdb_df,
        embeddings=sample_embeddings,
        ratings=user_ratings,
        top_n=10,
        lambda_=0.7
    )
    print(recommendations)
    
    print("\n--- Recomendações Focadas em Relevância (lambda=0.95) ---")
    recommendations_relevance = recommend_movies_advanced(
        fav_matches=user_favorites,
        imdb_df=sample_imdb_df,
        embeddings=sample_embeddings,
        ratings=user_ratings,
        top_n=10,
        lambda_=0.95 # Valor alto para priorizar relevância
    )
    print(recommendations_relevance)

    print("\n--- Recomendações Focadas em Diversidade (lambda=0.2) ---")
    recommendations_diversity = recommend_movies_advanced(
        fav_matches=user_favorites,
        imdb_df=sample_imdb_df,
        embeddings=sample_embeddings,
        ratings=user_ratings,
        top_n=10,
        lambda_=0.2 # Valor baixo para priorizar diversidade
    )
    print(recommendations_diversity)
