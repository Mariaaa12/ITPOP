import streamlit as st
import requests
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(layout="wide")

#Para pegar os dados do firebase colocar essa flag como False, para testar localmente coloque como True
isTest = False

#Funcao de consulta ao firebase que pega todos os registros da tabela movies; transforma os dados recebidos em um dataframe
def get_all_movies():
    db = firestore.client()
    movies_ref = list(db.collection(u'movies').stream())
    movies_dict = list(map(lambda x: x.to_dict(), movies_ref))
    movies = pd.DataFrame(movies_dict)
    movies.to_csv('movies.csv', index=False)

#Funcao de conexao ao firebase, pega as credenciais e inicializa o firebase. Depois chama a funcao de consulta aos filmes
@st.cache
def connection_db():
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    get_all_movies()

#Trata os dados recebidos pelo banco, transformando as string literais em array de strings
def convert(text):
    L = []
    N = []
    for i in text:
        if i != '[' and i != ']' and i != ',' and i != "'":
          N.append(i)
    L = [''.join(N)]
    return L

#Faz o mesmo da funcao de cima, nesse caso trata de arrays com mais de um elemento
def convert_array(text):
    L = []
    N = []
    for i in text:
        if i != '[' and i != ']' and i != ',' and i != "'":
          N.append(i)
        if i == ',' or i == ']':
          L.append(''.join(N))
          N = []
    return L

#Adiciona espaco em nomes compostos para exibir na tela
def add_space(text):
    result = ""
    upper_count = 0
    for character in text:
        if character.isupper() and upper_count == 1:
            result = result + ' ' + character
        elif character.isupper():
            upper_count = upper_count + 1
            result = result + character
        else:
            result = result + character
    return result

#Funcao que faz o tratamento dos dados recebidos pelo firebase e aplica as funcoes anteriores para ajustar os dados
#Apos isso eh aplicada a geracao do modelo de recomendacao
def data_optimization():
    global movies
    global recommendation

    movies = pd.read_csv('movies.csv')

    # Trata os dados recebidos como string
    movies['crew'] = movies['crew'].apply(convert)
    movies['genres'] = movies['genres'].apply(convert_array)
    movies['keywords'] = movies['keywords'].apply(convert_array)
    movies['cast'] = movies['cast'].apply(convert_array)

    # eh criada uma nova coluna chamada tags, sendo a juncao das colunas genres, keywords, cast e crew.
    # essa nova coluna ira servir de base para o algoritmo de recomendacao, pois eh como se as informacoes de cada filme tivessem contidas na coluna tags
    # sendo essa a ideia principal dessa estrategia de recomendacao, tags de conteudo
    movies['tags'] = movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']
    movies['tags'] = movies['tags'].apply(lambda x: " ".join(x))

    # aqui que eh aplicada a inteligencia e a geracao do modelo de recomendacao

    # lib usada: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html
    # ex: https://www.geeksforgeeks.org/using-countvectorizer-to-extracting-features-from-text/

    # inicializa o CountVectorizer do scikit-learn com os parametros passados
    cv = CountVectorizer(max_features=5000, stop_words='english')

    # o algoritmo eh entao aplicado na coluna tags, a que foi preparada no processo anterior
    vector_list = cv.fit_transform(movies['tags']).toarray()

    # agora que foi gerada a lista de vetores eh possivel fazer uma relacao matematica entre eles
    # quanto mais proximo um vetor estiver do outro, significa que eles tem uma maior relacao de similaridade
    # para cada filme eh entao calculada sua relacao de similaridade com todos os outros
    similarity = cosine_similarity(vector_list)
    recommendation = similarity

#Funcao que verifica se deve se conectar ao firebase ou nao e inicializa a chamada das funcoes que carregam os dados
def initialization():

    if not isTest:
        connection_db()

    data_optimization()

initialization()

#Botao que recarrega as informacoes vindas do firebase, so funciona se a flag isTest for False
if st.button('Reload'):
    if not isTest:
        get_all_movies()
        data_optimization()
        movie_list = movies['title'].values

col_00, col_01, col_02 = st.columns([2,4,1])

with col_00:
    st.title('')
with col_01:
    st.title('ItPop-Recomendador de filmes')
    st.title('')
with col_02:
    st.title('')

#Funcao que pega as imagens dos filmes de uma api externa de acordo com o id do filme, caso nao exista eh atribuido uma imagem placeholder
def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    if "success" in data:
        full_path = "https://pedagoflix.com.br/view/img/notfound_portrait.jpg"
    else:
        poster_path = data['poster_path']
        if poster_path != None:
            full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            full_path = "https://pedagoflix.com.br/view/img/notfound_portrait.jpg"
    return full_path

#Quando o filme eh selecionado sao carregados os 10 filmes recomendados com base nele, conforme modelo ja feito anteriormente
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(recommendation[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:11]:
        # fetch the movie poster
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names,recommended_movie_posters

#Pega os titulos dos filmes para exibir na lista
movie_list = movies['title'].values

col_select, col_image, col_info_image = st.columns([4,1.5,1])

with col_select:
    selected_movie = st.selectbox(
        "Selecione um filme",
        movie_list
    )

    position = movies[movies['title'] == selected_movie]

    st.markdown("**Sinopse:**")
    st.write(position.overview[position.index[0]])
with col_image:
    st.image(fetch_poster(position.movie_id[position.index[0]]), width=200)

with col_info_image:

    st.text(" ")
    st.markdown('**Diretor:**')
    st.text(add_space(position.crew[position.index[0]][0]))

    st.text(" ")
    st.markdown("**Elenco:**")
    st.text(add_space(position.cast[position.index[0]][0]))
    st.text(add_space(position.cast[position.index[0]][1]))
    st.text(add_space(position.cast[position.index[0]][2]))


recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

st.markdown("**Filmes Recomendados:**")
with st.spinner('Aguarde...'):
    st.success('Pronto!')

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.image(recommended_movie_posters[0])
    st.text(recommended_movie_names[0])
with col2:
    st.image(recommended_movie_posters[1])
    st.text(recommended_movie_names[1])
with col3:
    st.image(recommended_movie_posters[2])
    st.text(recommended_movie_names[2])
with col4:
    st.image(recommended_movie_posters[3])
    st.text(recommended_movie_names[3])
with col5:
    st.image(recommended_movie_posters[4])
    st.text(recommended_movie_names[4])

col11, col21, col31, col41, col51 = st.columns(5)
with col11:
    st.image(recommended_movie_posters[5])
    st.text(recommended_movie_names[5])
with col21:
    st.image(recommended_movie_posters[6])
    st.text(recommended_movie_names[6])
with col31:
    st.image(recommended_movie_posters[7])
    st.text(recommended_movie_names[7])
with col41:
    st.image(recommended_movie_posters[8])
    st.text(recommended_movie_names[8])
with col51:
    st.image(recommended_movie_posters[9])
    st.text(recommended_movie_names[9])