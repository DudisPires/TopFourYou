import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def recommend_movies_with_diversity(fav_matches, imdb_df, embeddings, top_n=10, candidate_pool_size=50, diversity_threshold=0.85):
    """
    Gera recomendações de filmes com um algoritmo de diversidade para evitar
    resultados muito repetitivos.

    Args:
        fav_matches (dict): Dicionário com os filmes favoritos mapeados para o dataset.
        imdb_df (pd.DataFrame): O DataFrame completo com os dados dos filmes.
        embeddings (np.array): O array de embeddings para todos os filmes.
        top_n (int): O número final de recomendações a serem retornadas.
        candidate_pool_size (int): O tamanho do grupo inicial de candidatos a partir do qual
                                   as recomendações serão selecionadas. Um número maior
                                   aumenta a chance de diversidade.
        diversity_threshold (float): Limiar de similaridade (entre 0 e 1) para considerar
                                     dois filmes "parecidos demais". Um valor mais alto
                                     resultará em maior diversidade. 0.85 é um bom começo.

    Returns:
        pd.DataFrame: Um DataFrame com os filmes recomendados.
    """
    # 1. Calcular o vetor de gosto médio do usuário a partir dos seus favoritos
    try:
        indices = [imdb_df[imdb_df['title'] == match].index[0] for match in fav_matches.values()]
    except IndexError:
        print("Erro: Não foi possível encontrar os índices para um ou mais filmes favoritos no DataFrame.")
        # Retorna um DataFrame vazio se houver erro
        return pd.DataFrame()

    fav_vecs = embeddings[indices]
    mean_vector = np.mean(fav_vecs, axis=0).reshape(1, -1)

    # 2. Calcular a similaridade do gosto do usuário com TODOS os filmes
    similarities = cosine_similarity(mean_vector, embeddings)[0]

    # 3. Criar um pool inicial de candidatos
    # Adicionamos o tamanho dos favoritos para garantir que teremos candidatos suficientes
    # mesmo depois de filtrar os próprios favoritos.
    total_candidates = candidate_pool_size + len(indices)
    
    # Pega os N candidatos com maior similaridade, ignorando os filmes que o usuário já favoritou
    top_indices_pool = [i for i in similarities.argsort()[::-1] if i not in indices][:total_candidates]

    # 4. Algoritmo de Diversidade (Maximum Marginal Relevance - MMR simplificado)
    final_recommendations_indices = []
    
    # Conjunto para rastrear índices que já foram escolhidos ou descartados
    indices_to_skip = set()

    while len(final_recommendations_indices) < top_n and top_indices_pool:
        # Encontra o próximo melhor candidato que ainda não foi pulado
        best_candidate_idx = -1
        for idx in top_indices_pool:
            if idx not in indices_to_skip:
                best_candidate_idx = idx
                break
        
        # Se não houver mais candidatos, para o loop
        if best_candidate_idx == -1:
            break
            
        # Adiciona o melhor candidato à lista final
        final_recommendations_indices.append(best_candidate_idx)
        indices_to_skip.add(best_candidate_idx)
        
        # Agora, penaliza filmes que são muito similares ao que acabamos de adicionar
        newly_added_vec = embeddings[best_candidate_idx].reshape(1, -1)
        
        # Calcula a similaridade do novo filme com todos os outros do pool de candidatos
        candidate_embeddings = embeddings[top_indices_pool]
        similarity_to_new_movie = cosine_similarity(newly_added_vec, candidate_embeddings)[0]

        # Descarta (adiciona à lista de pulos) todos os candidatos "parecidos demais"
        for i, candidate_idx in enumerate(top_indices_pool):
            if similarity_to_new_movie[i] > diversity_threshold:
                indices_to_skip.add(candidate_idx)

    # 5. Retornar o DataFrame final com as recomendações
    return imdb_df.iloc[final_recommendations_indices][['title', 'year', 'director', 'rating_imdb']]