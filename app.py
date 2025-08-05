import pandas as pd
import numpy as np
import os
import sys
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from src.scraping.letterboxd_scraper import get_favorite_movies
    from src.matching.fuzzy_matcher import match_titles
    from src.embedding.embedding_generator import generate_description_nova_base, embed_descriptions
    from src.recommender.recommender import recommend_movies_advanced
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    sys.exit()

app = Flask(__name__)
CORS(app)

DATASET_PATH = './data/pre-processing/base_transformada.csv'
EMBEDDINGS_PATH = './data/embeddings/movie_embeddings.npy'

print("Iniciando o servidor e carregando os recursos...")
imdb_df = None
embeddings = None

try:
    print(f"Carregando dataset de '{DATASET_PATH}'...")
    imdb_df = pd.read_csv(DATASET_PATH)
    imdb_df.dropna(subset=['title', 'release_date', 'rating_imdb', 'genre', 'language'], inplace=True)
    print("Dataset carregado com sucesso.")

    if os.path.exists(EMBEDDINGS_PATH):
        print(f"Carregando embeddings de '{EMBEDDINGS_PATH}'...")
        embeddings = np.load(EMBEDDINGS_PATH)
    else:
        print("Embeddings não encontrados. Gerando novos...")
        os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
        descriptions = generate_description_nova_base(imdb_df)
        embeddings = embed_descriptions(descriptions)
        np.save(EMBEDDINGS_PATH, embeddings)
    print("Servidor pronto.")
except Exception as e:
    print(f"Erro durante a inicialização: {e}")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/app')
def frontend():
    return render_template('index.html')

@app.route('/recommend', methods=['GET'])
def recommend():
    nickname = request.args.get('nickname')
    if not nickname:
        return jsonify({"error": "O parâmetro 'nickname' é obrigatório."}), 400

    if imdb_df is None or embeddings is None:
        return jsonify({"error": "Erro interno: dataset ou embeddings não carregados."}), 500

    try:
        favorite_titles = get_favorite_movies(nickname)
        if not favorite_titles:
            return jsonify({"error": f"Não foi possível encontrar favoritos para '{nickname}'."}), 404

        imdb_titles = imdb_df['title'].tolist()
        matched_titles = match_titles(favorite_titles, imdb_titles, threshold=85)
        if not matched_titles:
            return jsonify({"error": "Nenhum filme favorito foi encontrado no nosso banco de dados."}), 404

        recommendations = recommend_movies_advanced(
            fav_matches=matched_titles,
            imdb_df=imdb_df,
            embeddings=embeddings
        )
        return recommendations.to_json(orient="records")
    except Exception as e:
        print(f"Erro ao gerar recomendações: {e}")
        return jsonify({"error": "Erro interno durante a recomendação."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
