import os
import streamlit as st  # importação da bilioteca para construir a interface web
import cv2  # biblioteca para processamento de imagem
import numpy as np  # para realizar calculos
from moviepy.editor import VideoFileClip  # lib de codecs de video


# remover a imagem de fundo
def remove_background(frame, background_image, lower_bound, upper_bound):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # convertendo a imagem do espaço de cor BGR para HSV

    mask = cv2.inRange(hsv, lower_bound, upper_bound)  # cria uma mascara pro chromakey, com tolerancias
    mask = cv2.erode(mask, None, iterations=2)  # aplico filtro de erosao
    mask = cv2.dilate(mask, None, iterations=2)  # aplico filtro de dilatação

    foreground = cv2.bitwise_and(frame, frame, mask=~mask)  # extrair tudo que não é "verde", que não é ChromaKey

    background = cv2.resize(background_image, (frame.shape[1], frame.shape[0]))  # redimensiono a nova imagem de fundo
    background = cv2.bitwise_and(background, background, mask=mask)  # aplico uma mascara pro fundo da imagem

    combined = cv2.add(foreground, background)  # junto o que não é o chromakey com a imagem de fundo

    return combined  # retorno o frame criado


# Função para remover o fundo verde e substituir por um vídeo MP4
def remove_background_and_add_video(frame, background_video, lower_bound, upper_bound):
    # Convertendo o frame para o espaço de cores HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Criando uma máscara para a região de fundo verde (Chroma Key)
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Aplicando a máscara para obter a região de primeiro plano (pessoa)
    foreground = cv2.bitwise_and(frame, frame, mask=~mask)

    # Lendo o próximo frame do vídeo de fundo
    ret, background_frame = background_video.read()
    if not ret:
        # Se atingir o final do vídeo, reinicia do início
        background_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        _, background_frame = background_video.read()

    # Redimensionando o frame de fundo para o tamanho do frame da câmera
    background_frame = cv2.resize(background_frame, (frame.shape[1], frame.shape[0]))

    # Aplicando a máscara para obter a região de fundo substituída
    background = cv2.bitwise_and(background_frame, background_frame, mask=mask)

    # Combinando a região de primeiro plano e a região de fundo substituída
    combined = cv2.add(foreground, background)

    return combined


# converte uma cor RGB para HSV com tolerancia
def convert_to_hsv_with_tolerance(rgb_color, tolerance=40):
    bgr_color = rgb_color[::-1]  # "conversao" RGB -> BGR: (43, 177, 9)
    hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]  # Conversão de BGR para HSV
    lower_bound = np.array([max(hsv_color[0] - tolerance, 0), 50, 50])  # limite minimo para o filtro HSV
    upper_bound = np.array([min(hsv_color[0] + tolerance, 255), 255, 255])  # lmite maximo para o filtro HSV
    return lower_bound, upper_bound  # Retorno uma tupla


chroma_key_rgb = (9, 117, 43)  # é a cor em RGB do ChromaKey
lower_bound, upper_bound = convert_to_hsv_with_tolerance(chroma_key_rgb,
                                                         10)  # Converter a cor HEX-RGB para HSV com tolerancia

st.title("Aplicação de Chroma Key")  # titulo da aplicação
st.subheader("Utilizando Streamlit e OpenCV")  # subtitulo da aplicação

# Envio do arquivo de imagem ou vídeo
uploaded_file = st.file_uploader("Escolha uma imagem ou vídeo de fundo", type=['png', 'jpg', 'jpeg', 'mp4', 'gif'])
background_image = None
background_video = None

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension in ['png', 'jpg', 'jpeg']:
        # Decodificar a imagem
        background_image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_COLOR)
    elif file_extension in ['mp4', 'gif'] :
        # Salvar o vídeo em um arquivo temporário
        video_dir = 'temp'
        os.makedirs(video_dir, exist_ok=True)
        video_path = os.path.join(video_dir, 'video_temp.mp4')

        with open(video_path, 'wb') as video_file:
            video_file.write(uploaded_file.read())

        # Inicializar a leitura do vídeo
        background_video = cv2.VideoCapture(video_path)

# Inicialização de variáveis
name = st.text_input("Nome:")
phone_input = st.text_input("Número de telefone:")
save_image = st.button("Salvar Foto")

# Configurar a câmera (0 para câmera nativa, notebook)
cap = cv2.VideoCapture(1)
frameST = st.empty()

while True:
    ret, frame = cap.read()
    if not ret:
        st.warning("Câmera não iniciada")
        break

    if background_image is not None:
        frame = remove_background(frame, background_image, lower_bound, upper_bound)

    if background_video is not None:
        frame = remove_background_and_add_video(frame, background_video, lower_bound, upper_bound)

    frameST.image(frame, channels='BGR', use_column_width=True)

    if save_image:
        # Garantir que o diretório exista ou criá-lo
        save_dir = os.path.join(os.getcwd(), name)
        os.makedirs(save_dir, exist_ok=True)

        # Caminho completo para a imagem com o número do telefone
        image_path = os.path.join(save_dir, f'{phone_input}.jpg')

        # Salvar a imagem
        cv2.imwrite(image_path, frame)

        # Exibir mensagem na tela que a imagem foi salva
        st.write(f"Imagem salva como '{image_path}'")

        # Resetar o botão de salvar para evitar salvamentos repetidos
        save_image = False

cap.release()  # Liberar a câmera
if background_video is not None:
    background_video.release()  # Liberar os recursos da câmera e do vídeo de fundo
