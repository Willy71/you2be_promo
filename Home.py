import streamlit as st
import pandas as pd
import re
import gspread
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup
import requests

# Configuración de la página
st.set_page_config(
    page_title="You 2 be",
    page_icon="▶️",
)

# Reducir espacio en la parte superior
reduce_space ="""
            <style type="text/css">
            div[data-testid="stAppViewBlockContainer"]{
                padding-top:30px;
            }
            </style>
            """
st.markdown(reduce_space, unsafe_allow_html=True)

# Conexión con Google Sheets
SERVICE_ACCOUNT_INFO = st.secrets["gsheets"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(credentials)
SPREADSHEET_KEY = '11IRRawCTs9uevO3muLz0EUp8iRFQLzJy8BjXhnzIaxk'
SHEET_NAME = 'youtube_videos'

try:
    sheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
except gspread.exceptions.SpreadsheetNotFound:
    st.error(f"A planilha com a chave não foi encontrada '{SPREADSHEET_KEY}'.")

# Funciones auxiliares
def centrar_texto(texto, tamanho, color):
    st.markdown(f"<h{tamanho} style='text-align: center; color: {color}'>{texto}</h{tamanho}>", unsafe_allow_html=True)

def load_videos():
    rows = sheet.get_all_records()
    df = pd.DataFrame(rows)
    return df

def extract_video_id(url):
    regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    match = re.match(regex, url)
    if match:
        return match.group(1)
    return None

def get_video_title(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('meta', property='og:title')
        if title_tag and 'content' in title_tag.attrs:
            return title_tag['content']
        else:
            st.error("No se encontró la etiqueta de título en el video.")
            return None
    except Exception as e:
        st.error(f"Error al obtener el título del video: {e}")
        return None

def delete_video(url):
    cell = sheet.find(url)
    if cell:
        sheet.delete_rows(cell.row)

def add_video(category, url, title):
    sheet.append_row([category, url, title])

def main():
    df = load_videos()

    if df.empty:
        st.warning("Nenhum vídeo encontrado no banco de dados.")
        return

    with st.sidebar:
        df_1 = df["Category"].unique()
        df_1_1 = sorted(df_1)
        slb_1 = st.selectbox('Categoria', df_1_1)

        df_filtered = df[df["Category"] == slb_1]

        if not df_filtered.empty:
            df_titles = df_filtered["Title"].unique()
            df_titles = sorted(df_titles)
            
            # Guardamos el índice inicial para saber cuál video está seleccionado
            initial_index = 0
            slb_2 = st.radio("Selecione um vídeo para reproduzir", df_titles, index=initial_index)
            
            df_video = df_filtered[df_filtered["Title"] == slb_2].iloc[0]

    # Reproductor principal de video
    video_id = extract_video_id(df_video['Url'])
    
    st.markdown(f"""
    <div style="display: flex; justify-content: center;">
        <iframe id="player" type="text/html" width="832" height="507"
        src="https://www.youtube.com/embed/{video_id}?autoplay=1&controls=1&loop=1"
        frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>
    """, unsafe_allow_html=True)
    
    # JavaScript para avanzar automáticamente al siguiente video cuando uno termina
    st.markdown(f"""
    <script>
    var player;
    function onYouTubeIframeAPIReady() {{
        player = new YT.Player('player', {{
            events: {{
                'onStateChange': onPlayerStateChange
            }}
        }});
    }}

    function onPlayerStateChange(event) {{
        if (event.data === YT.PlayerState.ENDED) {{
            var currentIndex = {df_titles.index(slb_2)};
            var nextIndex = (currentIndex + 1) % {len(df_titles)};
            var nextTitle = {df_titles}[nextIndex];
            document.querySelector('input[value="' + nextTitle + '"]').click();
        }}
    }}
    </script>
    <script src="https://www.youtube.com/iframe_api"></script>
    """, unsafe_allow_html=True)

    # Botón para eliminar el video
    with st.container():
        col15, col16, col17, col18, col19 = st.columns([3,1,1,1,2])
        with col15:         
            if st.button("Excluir vídeo"):
                delete_video(df_video['Url'])
                st.success("Vídeo excluído")
                st.rerun()

    with st.sidebar:
        st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#1717dc;" /> """, unsafe_allow_html=True)
        centrar_texto("Adicionar vídeo", 2, "white")
        
        video_url = st.text_input("URL do video de YouTube:")
        category = st.text_input("Insira a categoria do vídeo:")

        if st.button("Adicionar vídeo"):
            if video_url and category:
                video_id = extract_video_id(video_url)
                if video_id:
                    video_title = get_video_title(video_url)
                    if video_title:
                        add_video(category, video_url, video_title)
                        st.success(f"Video '{video_title}' adicionado à categoria '{category}'")
                        st.rerun()
                    else:
                        st.error("Não foi possível obter o título do vídeo.")
                else:
                    st.error("Insira um URL válido do YouTube.")
            else:
                st.error("Insira um URL e uma categoria.")

if __name__ == "__main__":
    main()
