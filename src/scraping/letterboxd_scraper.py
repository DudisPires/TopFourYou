import os
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_favorite_movies(nickname):
    url = f"https://letterboxd.com/{nickname}"

    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "poster-list"))
        )
        html = driver.page_source
    except Exception as e:
        print("Erro ao carregar favoritos:", e)
        driver.quit()
        return []
    
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    favorites_list = soup.find("ul", class_="poster-list")
    if not favorites_list:
        print("Lista de favoritos não encontrada.")
        return []

    favorite_titles = []
    movie_items = favorites_list.find_all("li", class_="poster-container")

    for item in movie_items[:4]:
        poster_div = item.find("div", class_="film-poster")
        if poster_div and poster_div.has_attr("data-film-name"):
            title = poster_div["data-film-name"]
            favorite_titles.append(title)
        else:
            frame_title = item.select_one("span.frame-title")
            if frame_title:
                clean_title = re.sub(r"\s*\(\d{4}\)", "", frame_title.text)
                favorite_titles.append(clean_title)

    return favorite_titles

def scrape_watchlist(nickname):
    base_url = f"https://letterboxd.com/{nickname}/watchlist/"
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    watchlist_titles = []
    page = 1

    try:
        while True:
            url = f"{base_url}page/{page}/"
            driver.get(url)

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".poster-list li.poster-container"))
                )
            except TimeoutException:
                print(f"Fim da watchlist. Nenhum filme carregado na página {page}.")
                break

            soup = BeautifulSoup(driver.page_source, "html.parser")
            movies = soup.select("ul.poster-list li.poster-container")

            for item in movies:
                poster_div = item.find("div", class_="film-poster")
                if poster_div:
                    img_tag = poster_div.find("img")
                    if img_tag and img_tag.has_attr("alt"):
                        title = img_tag["alt"].strip()
                        watchlist_titles.append(title)

            print(f"Página {page} processada com {len(movies)} filmes.")
            page += 1

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o scraping de {nickname}: {e}")
    finally:
        print("Fechando o navegador.")
        driver.quit()

    return watchlist_titles

def save_watchlists_to_json(nickname1, nickname2, output_file="data/watchlist/watchlist_filmes.json"):
    print(f"\nColetando watchlist de '{nickname1}'...")
    watchlist1 = scrape_watchlist(nickname1)

    print(f"\nColetando watchlist de '{nickname2}'...")
    watchlist2 = scrape_watchlist(nickname2)

    data = {
        nickname1: watchlist1,
        nickname2: watchlist2
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\nArquivo JSON criado com sucesso em: {output_file}")

def find_common_movies(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    users = list(data.keys())
    if len(users) < 2:
        print("O JSON deve conter dois usuários.")
        return []

    lista1 = set(data[users[0]])
    lista2 = set(data[users[1]])

    comuns = sorted(lista1 & lista2)
    print(f"\nFilmes em comum entre {users[0]} e {users[1]}:")
    for filme in comuns:
        print("-", filme)

    return comuns

def get_user_avatar(nickname):
    url = f"https://letterboxd.com/{nickname}/"
    options = Options()
    options.headless = True
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        
        avatar_div = soup.find("div", class_="profile-avatar")
        if avatar_div:
            img_tag = avatar_div.find("img")
            if img_tag and img_tag.has_attr("src"):
                return img_tag["src"] 

    except Exception as e:
        print(f"Erro ao buscar o avatar de {nickname}: {e}")
    
    return None 
def get_movie_poster_by_slug(slug):
    
    movie_url = f"https://letterboxd.com/film/{slug}/"
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(movie_url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "film-poster"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        poster_div = soup.find("div", class_="film-poster")
        if poster_div:
            img_tag = poster_div.find("img")
            if img_tag and img_tag.has_attr("src"):
                return img_tag["src"]

    except TimeoutException:
        print(f"Timeout ao buscar pôster para {slug}")
    except Exception as e:
        print(f"Erro ao buscar pôster de {slug}: {e}")
    finally:
        driver.quit()

    return None

if __name__ == "__main__":
    nickname1 = 'trevorrussi'
    nickname2 = 'dudis1990'  

    json_path = "data/watchlist/watchlist_filmes.json"

    print("\nIniciando scraping das duas watchlists...")
    save_watchlists_to_json(nickname1, nickname2, output_file=json_path)

    print("\nAnalisando filmes em comum...")
    find_common_movies(json_path)
