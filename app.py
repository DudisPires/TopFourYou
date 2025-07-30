import pandas as pd
import numpy as np
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Adiciona o diretório raiz do projeto ao path para que o Python encontre a pasta 'src'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from src.scraping.letterboxd_scraper import get_favorite_movies
    from src.matching.fuzzy_matcher import match_titles
    from src.embedding.embedding_generator import generate_descriptions, embed_descriptions
    from src.recommender.recommender import recommend_movies_with_diversity
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    print("Verifique se você está executando 'python app.py' do diretório raiz do projeto e se a pasta 'src' está no lugar certo.")
    sys.exit()

# --- INICIALIZAÇÃO DO APP FLASK ---
app = Flask(__name__)
CORS(app)

# --- CAMINHOS DOS ARQUIVOS ---
DATASET_PATH = '/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/world_imdb_movies_preprocessed.csv'
EMBEDDINGS_PATH = '/home/eduardo-monteiro/projetos/letterboxd/TopFourYou/data/embeddings/movie_embeddings.npy'

# --- CARREGAMENTO DOS DADOS ---
print("Iniciando o servidor e carregando os recursos...")
imdb_df = None
embeddings = None

try:
    print(f"Carregando dataset de '{DATASET_PATH}'...")
    imdb_df = pd.read_csv(DATASET_PATH)
    colunas_necessarias = ['title', 'year', 'genre', 'director', 'star', 'language', 'rating_imdb']
    if not all(coluna in imdb_df.columns for coluna in colunas_necessarias):
        raise ValueError(f"O dataset não contém todas as colunas necessárias: {colunas_necessarias}")
    imdb_df.dropna(subset=['title', 'year', 'director', 'star', 'genre'], inplace=True)
    print("Dataset de filmes carregado com sucesso.")

    if os.path.exists(EMBEDDINGS_PATH):
        print(f"Carregando embeddings de '{EMBEDDINGS_PATH}'...")
        embeddings = np.load(EMBEDDINGS_PATH)
        print("Embeddings carregados de arquivo.")
    else:
        print("Embeddings não encontrados. Gerando novos embeddings...")
        os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
        descriptions = generate_descriptions(imdb_df)
        embeddings = embed_descriptions(descriptions)
        np.save(EMBEDDINGS_PATH, embeddings)
        print(f"Embeddings gerados e salvos em '{EMBEDDINGS_PATH}'.")
except (FileNotFoundError, ValueError, NameError) as e:
    print(f"ERRO CRÍTICO DURANTE A INICIALIZAÇÃO: {e}")
    
print("Servidor pronto para receber requisições.")


# --- DEFINIÇÃO DAS ROTAS DA API ---

# NOVA ROTA: Rota raiz para confirmar que o servidor está funcionando
@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Bem-vindo à API do Recomendador de Filmes! O servidor está no ar. Use o endpoint /recommend."})


@app.route('/recommend', methods=['GET'])
def recommend():
    nickname = request.args.get('nickname')
    if not nickname:
        return jsonify({"error": "O parâmetro 'nickname' é obrigatório."}), 400

    if imdb_df is None or embeddings is None:
        return jsonify({"error": "O servidor não foi inicializado corretamente devido a um erro de arquivo. Verifique os logs."}), 500

    print(f"Recebida requisição para o nickname: {nickname}")
    try:
        favorite_titles = get_favorite_movies(nickname)
        if not favorite_titles:
            return jsonify({"error": f"Não foi possível encontrar favoritos para o usuário '{nickname}'. Verifique o perfil."}), 404

        imdb_titles = imdb_df['title'].tolist()
        matched_titles = match_titles(favorite_titles, imdb_titles, threshold=85)
        if not matched_titles:
            return jsonify({"error": "Não foi possível encontrar os filmes favoritos no nosso banco de dados."}), 404

        recommendations = recommend_movies_with_diversity(
            fav_matches=matched_titles,
            imdb_df=imdb_df,
            embeddings=embeddings
        )
        result = recommendations.to_json(orient="records")
        return result
    except Exception as e:
        print(f"Ocorreu um erro durante a recomendação: {e}")
        return jsonify({"error": "Ocorreu um erro interno ao processar sua solicitação."}), 500


# --- PONTO DE ENTRADA PARA RODAR O SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)