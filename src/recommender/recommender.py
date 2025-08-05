import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
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
    try:
        indices = [imdb_df[imdb_df['title'] == match].index[0] for match in fav_matches.values()]
    except IndexError:
        print("Erro: Não foi possível encontrar os índices para um ou mais filmes favoritos.")
        return pd.DataFrame()

    fav_vecs = embeddings[indices]

    if ratings:
        weights = np.array([ratings.get(title, 1.0) for title in fav_matches.values()]).reshape(-1, 1)
        mean_vector = np.sum(fav_vecs * weights, axis=0) / np.sum(weights)
    else:
        mean_vector = np.mean(fav_vecs, axis=0)

    user_profile_vec = mean_vector.reshape(1, -1)

    faiss.normalize_L2(embeddings)
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)

    k = candidate_pool_size + len(indices)
    distances, candidate_indices = index.search(user_profile_vec, k)

    candidate_indices = [idx for idx in candidate_indices[0] if idx not in indices]
    candidate_indices = candidate_indices[:candidate_pool_size]

    candidate_embeddings = embeddings[candidate_indices]
    relevance_scores = cosine_similarity(user_profile_vec, candidate_embeddings)[0]
    candidate_relevance = {idx: score for idx, score in zip(candidate_indices, relevance_scores)}

    recommendations_indices = [candidate_indices[np.argmax(relevance_scores)]]
    candidate_indices.pop(np.argmax(relevance_scores))

    while len(recommendations_indices) < top_n and candidate_indices:
        mmr_scores = []
        recommended_vecs = embeddings[recommendations_indices]

        for candidate_idx in candidate_indices:
            candidate_vec = embeddings[candidate_idx].reshape(1, -1)
            relevance = candidate_relevance[candidate_idx]
            similarity_with_selected = cosine_similarity(candidate_vec, recommended_vecs)
            max_similarity = np.max(similarity_with_selected)
            mmr_score = lambda_ * relevance - (1 - lambda_) * max_similarity
            mmr_scores.append((mmr_score, candidate_idx))

        if not mmr_scores:
            break

        best_candidate_idx = max(mmr_scores, key=lambda x: x[0])[1]
        recommendations_indices.append(best_candidate_idx)
        candidate_indices.remove(best_candidate_idx)

    return imdb_df.iloc[recommendations_indices][['title', 'genre', 'release_date', 'language', 'rating_imdb']]\
             .sort_values(by='rating_imdb', ascending=False)\
             .reset_index(drop=True)

if __name__ == '__main__':
    num_movies = 1000
    embedding_dim = 32
    np.random.seed(42)
    sample_embeddings = np.random.rand(num_movies, embedding_dim).astype('float32')
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
    user_favorites = {
        '1': 'Filme 10',
        '2': 'Filme 11',
        '3': 'Filme 500'
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
        lambda_=0.95
    )
    print(recommendations_relevance)
    print("\n--- Recomendações Focadas em Diversidade (lambda=0.2) ---")
    recommendations_diversity = recommend_movies_advanced(
        fav_matches=user_favorites,
        imdb_df=sample_imdb_df,
        embeddings=sample_embeddings,
        ratings=user_ratings,
        top_n=10,
        lambda_=0.2
    )