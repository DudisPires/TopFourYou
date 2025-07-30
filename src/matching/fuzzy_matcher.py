from rapidfuzz import process

def match_titles(favorite_titles, imdb_titles, threshold=80):
    matches = {}
    for fav in favorite_titles:
        match, score, _ = process.extractOne(fav, imdb_titles)
        if score >= threshold:
            matches[fav] = match
    return matches
