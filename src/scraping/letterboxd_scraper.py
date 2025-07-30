import pandas as pd
from collections import Counter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

def get_favorite_movies(nickname):
    url = f"https://letterboxd.com/{nickname}"

    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "favourites"))
        )
        html = driver.page_source
    except Exception as e:
        print("Erro ao carregar favoritos:", e)
        driver.quit()
        return []
    
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    favorites_list = soup.find("ul", class_="poster-list -p150 -horizontal")
    if not favorites_list:
        print("Lista de favoritos não encontrada.")
        return []

    favorite_titles = []
    movie_items = favorites_list.find_all("li", class_="poster-container favourite-film-poster-container")

    for item in movie_items[:4]:
        poster_div = item.find("div", class_="react-component poster film-poster")
        if poster_div and poster_div.has_attr("data-film-name"):
            title = poster_div["data-film-name"]
            favorite_titles.append(title)
        else:
            frame_title = item.select_one("span.frame-title")
            if frame_title:
                clean_title = re.sub(r"\s*\(\d{4}\)", "", frame_title.text)
                favorite_titles.append(clean_title)

    return favorite_titles


if __name__ == "__main__":
    filmes=[]
    filmes= get_favorite_movies('dudis1990')
    print(filmes)