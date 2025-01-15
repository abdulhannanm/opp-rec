import streamlit as st
import pickle
import pandas as pd
import requests
from collections import Counter
import random
import numpy as np
import re

st.title("Hey TTE 👋")


def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path


def removeChoice(sim_list, choiceIndex):
    ret_list = [tup for tup in sim_list if tup[0] not in choiceIndex]
    return ret_list

def recommendMovies(choiceList):
    #need index of candidate movie and indexd of each movie in choiceList
    #then i can find the cosine sim using similarity[index of candMovie][index of element in choiceList in movies]
    similarity = load_similarity()
    choiceIndex = []
    for choice in choiceList:
        choiceIndex.append(int(movies[movies['title'] == choice].index[0]))
    sim_list = []
    for i in range(4809):
        sim_sum = 0
        for index in choiceIndex:
            sim_sum = sim_sum + similarity[i][index]
        sim_list.append(sim_sum)
    sim_list = list(enumerate(sim_list))
    rec_list = sorted(sim_list, reverse = True, key = lambda x: x[1])
    rec_list = removeChoice(rec_list, choiceIndex)
    rec_names = []
    rec_name_posters = []
    for movie in rec_list[0:10]:
        rec_names.append(movies.iloc[movie[0]].title)
        rec_name_posters.append(fetch_poster(movies.iloc[movie[0]].movie_id))
    return rec_names, rec_name_posters

@st.cache_data
def load_sentiments():
    with open("sentiments.pkl", "rb") as f:
        return pickle.load(f)


@st.cache_data
def load_similarity():
    with open("similarity.pkl", "rb") as f:
        return pickle.load(f)

def findOpposites(selectionList):
    new_sentiment_df = load_sentiments()
    print(type(new_sentiment_df))
    print(type(movies))
    print(movies.head())
    print(new_sentiment_df.head())
    seen_movies = set()
    most_sentimental = []
    final_opposite = set()
    for selection in selectionList:
        movie_ident = movies[movies['title'] == selection].movie_id.values[0]
        top_10_opposites = new_sentiment_df.loc[movie_ident]
        top_10_list = list(zip(top_10_opposites.index, top_10_opposites.values))
        

        top_10_list = sorted(top_10_list, key=lambda x: x[1], reverse=True)[:10]

        top_opp_names = [movie[0] for movie in top_10_list]


        top_opposite_movies = movies[movies["title"].isin(top_opp_names)]
        top_opp_names = top_10_opposites.index.tolist()
        top_clusters = []
        for name in top_opp_names:
            clean_name = re.sub(r'_\d+$', '', name)  # Removes '_1234' at the end of the title
        
            # Find the cluster using the cleaned movie name
            cluster_values = movies.loc[movies["title"] == clean_name, "cluster"].values[0]
            top_clusters.append(cluster_values)
            # if cluster_values.any(): 
            #     top_clusters.append(cluster_values[0])
            # else:
            #     print(f"Warning: No cluster found for '{clean_name}' (original: '{name}')")
        most_common_cluster = Counter(top_clusters).most_common(1)[0][0]
        reference_sentiment = movies.loc[movies.movie_id == movie_ident, 'sentiments'].values[0]
        cluster_movies = movies[movies['cluster'] == most_common_cluster][['title', 'sentiments']]
        cluster_movies['sentiment_difference'] = np.abs(cluster_movies['sentiments'] - reference_sentiment)
        top_10_movies = cluster_movies.nlargest(10, 'sentiment_difference')[['title', 'sentiment_difference']]
        for movie_tuple in top_10_movies.itertuples(index=False, name=None):
            movie_title = movie_tuple[0]
            if movie_title not in seen_movies:
                seen_movies.add(movie_title) 
                most_sentimental.append(movie_tuple)  
        if most_sentimental:
            random_top_movie = random.choice(most_sentimental)
            while random_top_movie[0] in final_opposite:
                random_top_movie = random.choice(most_sentimental)  
            
            final_opposite.add(random_top_movie[0]) 
    return list(final_opposite)



#data for recc
movies_dict = pickle.load(open('oppmovies.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
movie_list = movies['title'].values 
# similarity = pickle.load(open('similarity.pkl', 'rb'))

# data for opp
# with open("oppmovies.pkl", "rb") as f:
#     opp_movies_dict = pickle.load(f)
# movies = pd.DataFrame(opp_movies_dict)

# with open("sentiments.pkl", "rb") as f:
#     sentiment_dict = pickle.load(f)
# new_sentiment_df = pd.DataFrame(sentiment_dict)




selected_movies = st.multiselect("Pick up to 5 favorites, and we'll find movies you'll love!", movie_list)
selected_movies = selected_movies[0:5]
if st.button('Recommend'):
    recommended_movies, recommended_movie_posters = recommendMovies(selected_movies)
    num_movies = len(recommended_movies)
    num_cols = min(5, num_movies)  
    cols = st.columns(num_cols)

    # Inject CSS for hover effect
    st.markdown(
        """
        <style>
        .movie-container {
            position: relative;
            display: inline-block;
            text-align: center;
            margin-bottom: 20px;
        }
        .movie-container img {
            width: 150px;
            transition: transform 0.2s ease-in-out;
        }
        .movie-container img:hover {
            transform: scale(1.1);
        }
        .movie-title {
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
            width: 100%;
            text-align: center;
        }
        .movie-container:hover .movie-title {
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    for i, movie in enumerate(recommended_movies):
        with cols[i % num_cols]:  # Distribute across columns
            st.markdown(
                f"""
                <div class="movie-container">
                    <img src="{recommended_movie_posters[i]}" alt="{movie}">
                    <div class="movie-title">{movie}</div>
                </div>
                """,
                unsafe_allow_html=True
            )