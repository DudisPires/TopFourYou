from rapidfuzz import process
from tqdm import tqdm

def match_titles(favorite_titles, imdb_titles, threshold=80, show_scores=False):
    matches = {}
    for fav in tqdm(favorite_titles, desc="Matching titles"):
        match, score, _ = process.extractOne(fav, imdb_titles)
        if score >= threshold:
            matches[fav] = (match, score) if show_scores else match
        else:
            matches[fav] = None
    return matches
