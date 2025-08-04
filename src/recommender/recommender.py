import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
# O FAISS é uma biblioteca da Meta para busca de similaridade eficiente.
# Para instalar, use: pip install faiss-cpu
import faiss

def recommend_items_advanced(
    fav_matches,
    items_df,
    embeddings,
    ratings=None,
    top_n=10,
    candidate_pool_size=100,
    lambda_=0.7
):
    """
    Gera recomendações de itens com diversidade usando uma implementação clássica de
    Maximal Marginal Relevance (MMR) e preparada para escalabilidade com FAISS.

    Parâmetros:
    - fav_matches (dict): Dicionário com os itens favoritos do usuário.
    - items_df (pd.DataFrame): DataFrame com os dados dos itens (filmes, séries, etc.).
    - embeddings (np.ndarray): Matriz de embeddings de todos os itens.
    - ratings (dict, opcional): Dicionário de {title: rating} para ponderar o perfil do usuário.
    - top_n (int): O número de recomendações a serem retornadas.
    - candidate_pool_size (int): O tamanho do pool inicial de candidatos a serem considerados.
    - lambda_ (float): Parâmetro para o MMR. Controla o trade-off entre relevância e diversidade.
                       lambda_ = 1 -> Apenas relevância.
                       lambda_ = 0 -> Apenas diversidade.
    """
    # --- 1. Obter Índices e Criar Perfil de Usuário (Simples ou Ponderado) ---
    try:
        # Procura os índices dos itens favoritos no DataFrame
        indices = [items_df[items_df['title'] == match].index[0] for match in fav_matches.values()]
    except IndexError:
        print("Erro: Não foi possível encontrar os índices para um ou mais itens favoritos.")
        return pd.DataFrame()

    fav_vecs = embeddings[indices]

    if ratings:
        # Perfil Ponderado: itens com maior nota têm mais peso.
        weights = np.array([ratings.get(title, 1.0) for title in fav_matches.values()]).reshape(-1, 1)
        mean_vector = np.sum(fav_vecs * weights, axis=0) / np.sum(weights)
    else:
        # Perfil Simples: média dos vetores.
        mean_vector = np.mean(fav_vecs, axis=0)

    user_profile_vec = mean_vector.reshape(1, -1)

    # --- 2. Gerar Pool de Candidatos (Otimizado com FAISS) ---
    # Normalizar embeddings para busca com produto interno (equivalente à similaridade de cosseno)
    faiss.normalize_L2(embeddings)
    
    d = embeddings.shape[1]  # Dimensão dos vetores
    index = faiss.IndexFlatIP(d) # IndexFlatIP é para produto interno (Inner Product)
    index.add(embeddings)

    # Busca os `candidate_pool_size` vizinhos mais próximos do perfil do usuário
    k = candidate_pool_size + len(indices)
    distances, candidate_indices = index.search(user_profile_vec, k)

    # Filtra os candidatos, removendo os itens que o usuário já favoritou
    candidate_indices = [idx for idx in candidate_indices[0] if idx not in indices]
    candidate_indices = candidate_indices[:candidate_pool_size]

    # --- 3. Algoritmo Maximal Marginal Relevance (MMR) ---
    if not candidate_indices:
        print("Não foram encontrados candidatos suficientes para gerar recomendações.")
        return pd.DataFrame()
        
    candidate_embeddings = embeddings[candidate_indices]
    relevance_scores = cosine_similarity(user_profile_vec, candidate_embeddings)[0]
    candidate_relevance = {idx: score for idx, score in zip(candidate_indices, relevance_scores)}

    # Inicia a lista de recomendações com o item mais relevante
    initial_best_idx = np.argmax(relevance_scores)
    recommendations_indices = [candidate_indices[initial_best_idx]]
    candidate_indices.pop(initial_best_idx)

    while len(recommendations_indices) < top_n and candidate_indices:
        mmr_scores = []
        recommended_vecs = embeddings[recommendations_indices]

        for candidate_idx in candidate_indices:
            candidate_vec = embeddings[candidate_idx].reshape(1, -1)
            relevance = candidate_relevance[candidate_idx]
            max_similarity = np.max(cosine_similarity(candidate_vec, recommended_vecs))
            
            mmr_score = lambda_ * relevance - (1 - lambda_) * max_similarity
            mmr_scores.append((mmr_score, candidate_idx))

        if not mmr_scores:
            break

        best_candidate_idx = max(mmr_scores, key=lambda x: x[0])[1]
        recommendations_indices.append(best_candidate_idx)
        candidate_indices.remove(best_candidate_idx)

    # --- 4. Retornar Itens Recomendados com as Colunas Corretas ---
    return items_df.iloc[recommendations_indices][['type', 'title', 'release_date', 'genre', 'director']]

# --- Exemplo de Uso com a Nova Estrutura de Dados ---
if __name__ == '__main__':
    # Criando dados de exemplo para demonstração
    num_items = 1000
    embedding_dim = 32
    
    np.random.seed(42)
    sample_embeddings = np.random.rand(num_items, embedding_dim).astype('float32')

    # Criando um DataFrame de exemplo com a nova estrutura de colunas
    item_types = [np.random.choice(['Filme', 'Série de TV']) for _ in range(num_items)]
    titles = [f'Obra de Arte {i}' for i in range(num_items)]
    genres = [np.random.choice(['Ação', 'Comédia', 'Drama', 'Ficção Científica']) for _ in range(num_items)]
    dates = [f'20{np.random.randint(10, 24)}-01-01' for _ in range(num_items)]
    directors = [f'Diretor {chr(65 + np.random.randint(0,10))}' for _ in range(num_items)]
    
    sample_df = pd.DataFrame({
        'type': item_types,
        'title': titles,
        'release_date': dates,
        'genre': genres,
        'director': directors
    })

    # Itens favoritos do usuário e suas notas
    user_favorites = {
        '1': 'Obra de Arte 10',
        '2': 'Obra de Arte 11',
        '3': 'Obra de Arte 500'
    }
    user_ratings = {
        'Obra de Arte 10': 5.0,
        'Obra de Arte 11': 4.8,
        'Obra de Arte 500': 3.5
    }

    print("--- Recomendações com a Nova Base de Dados (lambda=0.7) ---")
    recommendations = recommend_items_advanced(
        fav_matches=user_favorites,
        items_df=sample_df,
        embeddings=sample_embeddings,
        ratings=user_ratings,
        top_n=10,
        lambda_=0.7
    )
    print(recommendations)
