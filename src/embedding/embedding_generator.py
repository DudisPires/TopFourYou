from sentence_transformers import SentenceTransformer

def generate_descriptions(df):
    return df.apply(lambda row: f"{row['title']} ({row['year']}), directed by {row['director']}, starring {row['star']}. Genre: {row['genre']}. Language: {row['language']}", axis=1)

def generate_description_nova_base(df):
        return df.apply(lambda row: f"{row['title']} ({row['release_date']}), Genre: {row['genre']}. Language: {row['language']}", axis=1)

def embed_descriptions(descriptions, model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    return model.encode(descriptions.tolist(), show_progress_bar=True)

