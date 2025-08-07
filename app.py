import pandas as pd
import numpy as np
import os
import sys
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from src.scraping.letterboxd_scraper import get_favorite_movies, scrape_watchlist, get_user_avatar
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
    imdb_df.dropna(subset=['title', 'release_date', 'rating_imdb', 'genre', 'language'], inplace=True) #
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

@app.route('/common')
def common_page():
    return render_template('common.html')

@app.route('/recommend', methods=['GET'])
def recommend():
    nickname = request.args.get('nickname')
    if not nickname:
        return jsonify({"error": "O parâmetro 'nickname' é obrigatório."}), 400

    if imdb_df is None or embeddings is None:
        return jsonify({"error": "Erro interno: dataset ou embeddings não carregados."}), 500

    try:
        print(f"Buscando avatar para {nickname}...")
        avatar_url = get_user_avatar(nickname) 
        
        print(f"Buscando filmes favoritos para {nickname}...")
        favorite_titles = get_favorite_movies(nickname) 
        
        if not favorite_titles:
            return jsonify({"error": f"Não foi possível encontrar favoritos para '{nickname}'."}), 404

        imdb_titles = imdb_df['title'].tolist()
        matched_titles = match_titles(favorite_titles, imdb_titles, threshold=85)
        if not matched_titles:
            return jsonify({"error": "Nenhum filme favorito foi encontrado no nosso banco de dados."}), 404

        recommendations_df = recommend_movies_advanced(
            fav_matches=matched_titles,
            imdb_df=imdb_df,
            embeddings=embeddings
        )

        response_data = {
            "avatar_url": avatar_url,
            "recommendations": recommendations_df.to_dict(orient="records")
        }
        
        return jsonify(response_data) 

    except Exception as e:
        print(f"Erro ao gerar recomendações: {e}")
        return jsonify({"error": "Erro interno durante a recomendação."}), 500

@app.route('/find_common', methods=['GET'])
def find_common():
    nickname1 = request.args.get('nickname1') 
    nickname2 = request.args.get('nickname2') 

    if not nickname1 or not nickname2:
        return jsonify({"error": "Os dois nicknames são obrigatórios."}), 400 

    try:
        print(f"Coletando watchlist de '{nickname1}'...")
        watchlist1 = scrape_watchlist(nickname1)

        print(f"\nColetando watchlist de '{nickname2}'...")
        watchlist2 = scrape_watchlist(nickname2)

        common_movies = sorted(list(set(watchlist1) & set(watchlist2)))

        if not common_movies:
            print("Nenhum filme em comum encontrado.")
        else:
            print(f"Filmes em comum: {common_movies}")
            
        return jsonify(common_movies)

    except Exception as e:
        print(f"Erro ao buscar filmes em comum: {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 