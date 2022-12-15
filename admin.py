import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

st.set_page_config(layout="wide")

genres_sort = ['Action', 'Comedy', 'Crime', 'Adventure', 'Terror', 'Mistery', 'Romance', 'Horror', 'ScienceFiction', 'Family']
keywords_sort = ['ambush', 'alcohol', 'shotgun', 'tea', 'fun', 'plot',
                 'rain', 'ghost', 'cavern', 'killing', 'sheriff', 'police', 'murder']
#Dados para conexao ao firebase
@st.cache
def connection_db():
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

connection_db()

def get_info(text):
    result = []
    word = ''
    for char in text:
        if char != '[' and char != ']' and char !="'" and char != ',' and char != ' ':
            word = word + char
        if char == ',' or char == ']':
            result.append(word)
            word = ''
    return result

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

def remove_space(text):
    result = ""
    for character in text:
        if character != ' ':
            result = result + character
    return result

#Funcao que adiciona um filme ao banco, eh possivel passa o id do filme que voce vai criar como parametro
def add_movie(movie_id, title, director, overview, actor1, actor2, actor3, genres, keywords):
    db = firestore.client()
    data = {
        u'cast': f"['{actor1}', '{actor2}', '{actor3}']",
        u'crew': f"['{director}']",
        u'genres': f"{genres}",
        u'keywords': f"{keywords}",
        u'movie_id': 99363452,
        u'overview': f'{overview}',
        u'title': f'{title}'
    }

    db.collection(u'movies').document(f'{movie_id}').set(data)
    #db.collection(u'movies').add(data)

def is_movie_available(movie_id):
    db = firestore.client()
    movie_ref = db.collection(u'movies').document(f'{movie_id}')
    movie = movie_ref.get()
    if movie.exists:
        return True
    else:
        return False

#Tras o filme correspondente ao id passado; caso o filme exista eh dado um print em suas informacoes
def get_movie(movie_id):
    db = firestore.client()
    movie_ref = db.collection(u'movies').document(f'{movie_id}')
    movie = movie_ref.get()
    return movie.to_dict()

#Atualiza as informacoes do filme de id correspondente
def update_movie(movie_id, title, director, overview, actor1, actor2, actor3, genres, keywords):
    db = firestore.client()

    data = {
        u'cast': f"['{actor1}', '{actor2}', '{actor3}']",
        u'crew': f"['{director}']",
        u'genres': f"{genres}",
        u'keywords': f"{keywords}",
        u'overview': f'{overview}',
        u'title': f'{title}'
    }

    db.collection(u'movies').document(f'{movie_id}').update(data)

#Exclui o filme que pertence ao id passado
def delete_movie(movie_id):
    db = firestore.client()
    db.collection(u'movies').document(f'{movie_id}').delete()

#Eh bom usar id: #movie pois o filme fica listado como primeiro na lista e mais facil de visualizar
#Para fazer as operacoes descomente o metodo que deseja usar e execute: python admin.py

col_00, col_01, col_02 = st.columns([3,4,1])

with col_00:
    st.title('')
with col_01:
    st.title('Administrador')
    st.title('')
with col_02:
    st.title('')

with st.expander("Adicionar"):
    col_form, col_view = st.columns([2, 2])
    with col_form:
        title = st.text_input('Titulo do Filme', 'Filme Arretado')
        overview = st.text_input('Sinopse', 'Um filme muito bacana')
        genres = st.multiselect(
            'Generos',
            genres_sort,
            ['Action', 'Crime'])
        keywords = st.multiselect(
            'Palavras-chave',
            keywords_sort,
            ['shotgun', 'fun'])
        movie_id = st.text_input('ID', '#movie')
    with col_view:
        director = st.text_input('Diretor', 'Sam Mendes')
        actor1 = st.text_input('Ator/Atriz Principal', 'Daniel Craig')
        actor2 = st.text_input('Ator/Atriz Coadjuvante 1', 'Selton Melo')
        actor3 = st.text_input('Ator/Atriz Coadjuvante 2', 'Tom Hanks')
        st.write(' ')
        st.write(' ')
        if st.button('Adicionar Filme'):
            with st.spinner('Aguarde...'):
                add_movie(movie_id, title, remove_space(director), overview, remove_space(actor1),
                          remove_space(actor2), remove_space(actor3), genres, keywords)
                st.success('Pronto!')

with st.expander("Atualizar/Deletar"):
    movie_id_add = st.text_input('Digite o ID do Filme que deseja atualizar ou deletar', '#id_filme')
    col_form_up, col_view_up = st.columns([2, 2])

    movie_exist = is_movie_available(movie_id_add)
    if movie_exist:
        movie_ref = get_movie(movie_id_add)
        with col_form_up:
            st.write(' ')
            title = st.text_input('Titulo do Filme ', movie_ref['title'])
            overview = st.text_input('Sinopse ', movie_ref['overview'])
            genres = st.multiselect(
                'Generos ',
                genres_sort + list(set(get_info(movie_ref['genres'])) - set(genres_sort)),
                get_info(movie_ref['genres']))
            keywords = st.multiselect(
                'Palavras-chave ',
                keywords_sort + list(set(get_info(movie_ref['keywords'])) - set(keywords_sort)),
                get_info(movie_ref['keywords']))
        with col_view_up:
            st.write(' ')
            director = st.text_input('Diretor ', add_space(get_info(movie_ref['crew'])[0]))
            actor1 = st.text_input('Ator/Atriz Principal ', add_space(get_info(movie_ref['cast'])[0]))
            actor2 = st.text_input('Ator/Atriz Coadjuvante 1 ', add_space(get_info(movie_ref['cast'])[1]))
            actor3 = st.text_input('Ator/Atriz Coadjuvante 2 ', add_space(get_info(movie_ref['cast'])[2]))

            st.write(' ')
            if st.button('Atualizar Filme'):
                with st.spinner('Aguarde...'):
                    update_movie(movie_id_add, title, remove_space(director), overview,
                                 remove_space(actor1), remove_space(actor2), remove_space(actor3),
                                 genres, keywords)
                    st.success('Pronto!')
            if st.button('Deletar Filme'):
                with st.spinner('Aguarde...'):
                    delete_movie(movie_id_add)
                    st.success('Pronto!')
    else:
        st.write('O filme nao existe')