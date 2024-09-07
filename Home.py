import streamlit as st
import pandas as pd
import re
import gspread
from google.oauth2.service_account import Credentials
import yt_dlp

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

#=============================================================================================================================
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
    regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+\?v=([^&=%\?]{11})'
    match = re.match(regex, url)
    if match:
        return match.group(5)  # Aseguramos que se extrae el video_id correctamente
    return None

def get_video_title(url):
    try:
        ydl = yt_dlp.YoutubeDL()
        info_dict = ydl.extract_info(url, download=False)
        return info_dict.get('title', None)
    except Exception as e:
        st.error(f"Error al obtener el título del video: {e}")
        return None

# Eliminar un video de Google Sheets
def delete_video(url):
    cell = sheet.find(url)
    if cell:
        sheet.delete_rows(cell.row)

def add_video(category, url, title):
    sheet.append_row([category, title, url])

def main():
    # Cargar los videos desde Google Sheets
    df = load_videos()

    if df.empty:
        st.warning("Nenhum vídeo encontrado no banco de dados.")
        return

    # Sidebar para seleccionar videos
    with st.sidebar:
        #centrar_texto("Videos", 2, 'white')

        # Mostrar las categorías
        df_1 = df["Category"].unique()
        df_1_1 = sorted(df_1)
        slb_1 = st.selectbox('Categoria', df_1_1)

        # Filtrar videos por categoría
        df_filtered = df[df["Category"] == slb_1]

        # Mostrar los títulos en radio buttons
        if not df_filtered.empty:
            df_titles = df_filtered["Title"].unique()
            df_titles = sorted(df_titles)
            slb_2 = st.radio("Selecione um vídeo para reproduzir", df_titles)
            
            # Filtrar el DataFrame por el título seleccionado
            df_video = df_filtered[df_filtered["Title"] == slb_2].iloc[0]

    # Reproductor principal de video
    st.markdown(f"""
    <div style="display: flex; justify-content: center;">
        <iframe id="player" type="text/html" width="832" height="507"
        src="https://www.youtube.com/embed/{extract_video_id(df_video['Url'])}?autoplay=1&controls=1"
        frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>
    """, unsafe_allow_html=True)
    
    st.text("")
    
    # Botón para eliminar el video
    with st.container():
        col15, col16, col17, col18, col19 = st.columns([3,1,1,1,2])
        with col15:         
            if st.button("Excluir vídeo"):
                delete_video(df_video['Url'])
                st.success("Vídeo excluído")
                st.rerun()

    # Sección para agregar videos
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
