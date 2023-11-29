import os
import streamlit as st # importação da bilioteca para construir a interface web
import cv2 # biblioteca para processamento de imagem
import numpy as np # para realizar calculos
from moviepy.editor import VideoFileClip #lib de codecs de video

# remover a imagem de fundo
def remove_background(frame, background_image, lower_bound, upper_bound):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # convertendo a imagem do espaço de cor BGR para HSV

    mask = cv2.inRange(hsv, lower_bound, upper_bound) # cria uma mascara pro chromakey, com tolerancias
    mask = cv2.erode(mask, None, iterations=2) # aplico filtro de erosao
    mask = cv2.dilate(mask, None, iterations=2) # aplico filtro de dilatação

    foreground = cv2.bitwise_and(frame, frame, mask=~mask)#extrair tudo que não é "verde", que não é ChromaKey

    background = cv2.resize(background_image, (frame.shape[1], frame.shape[0])) # redimensiono a nova imagem de fundo
    background = cv2.bitwise_and(background, background, mask=mask) # aplico uma mascara pro fundo da imagem

    combined = cv2.add(foreground, background) # junto o que não é o chromakey com a imagem de fundo

    return combined # retorno o frame criado

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
    bgr_color = rgb_color[::-1] # "conversao" RGB -> BGR: (43, 177, 9)
    hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0] # Conversão de BGR para HSV
    lower_bound = np.array([max(hsv_color[0] - tolerance, 0), 50, 50]) # limite minimo para o filtro HSV
    upper_bound = np.array([min(hsv_color[0] + tolerance, 255), 255, 255]) # lmite maximo para o filtro HSV
    return lower_bound, upper_bound # Retorno uma tupla

chroma_key_rgb = (9, 117, 43) # é a cor em RGB do ChromaKey
lower_bound, upper_bound = convert_to_hsv_with_tolerance(chroma_key_rgb, 10) # Converter a cor HEX-RGB para HSV com tolerancia

st.title("Aplicação de Chroma Key") # titulo da aplicação
st.subheader("Utilizando Streamlit e OpenCV") # subtitulo da aplicação

# envio da nova imagem de fundo
uploaded_file = st.file_uploader("Escolha uma imagem de fundo", type=['png', 'jpg', 'jpeg'])

# Envio do vídeo de fundo pelo usuário
uploaded_video = st.file_uploader("Escolha um vídeo de fundo", type=['mp4'])
background_video = None

if uploaded_video is not None:
    # Salvando o vídeo de fundo em um arquivo temporário na pasta "temp"
    video_dir = 'temp'
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, 'video_temp.mp4')

    with open(video_path, 'wb') as video_file:
        video_file.write(uploaded_video.read())

    # Inicializando a leitura do vídeo de fundo
    background_video = cv2.VideoCapture(video_path)

background_image = None # inicializo a variavel de imagem de fundo, como vazio

# verifico se a imagem enviada não esta vazia
if uploaded_file is not None:
    # decodificar a imagem e carregar a imagem de fundo
    background_image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_COLOR)

name = st.text_input("Nome: ") # pede o nome
phone_input = st.text_input("Numero de telefone:") # pede o numero
# crio um botao de salvar imagem
save_image = st.button("Salvar Foto")

# configuro a camera (0, é camera nativa, notebook), (1, camera usb, notebook)
cap = cv2.VideoCapture(0)
frameST = st.empty()

frameST = st.empty() # configura espaço vazio para a transmissão da camera

while True:
    ret, frame = cap.read() # ler e carregar os dados da camera
    if not ret: # se a camera não ligou:
        st.warning("Camera nao iniciada") # exibe uma mensagem caso a camera nao seja iniciada
        break # saia do laço de de repetição

    if background_image is not None: # verifico se a nova imagem de fundo foi enviada

        # enquanto estiver dentro do laço, vai capturar todos os frames da camera
        # e substituir o chromakey pela imagem de fundo enviada
        frame = remove_background(frame, background_image, lower_bound, upper_bound)

    # Aplicando a substituição do chroma key ao frame
    if background_video is not None:
        frame = remove_background_and_add_video(frame, background_video, lower_bound, upper_bound)
    # seta/configura o Streaming da camera
    frameST.image(frame, channels='BGR', use_column_width=True)

    # verifico se o botao de tirar foto foi clicado
    if save_image:
        # Garante que o diretório já exista, ou vai criá-lo
        save_dir = os.path.join(os.getcwd(), name)
        os.makedirs(save_dir, exist_ok=True)

        # Caminho completo para a imagem com o número do telefone
        image_path = os.path.join(save_dir, f'{phone_input}.jpg')

        # Salva a imagem
        cv2.imwrite(image_path, frame)

        # Exibe na tela uma mensagem que a imagem foi salva
        st.write(f"Imagem salva como '{image_path}'")

        # Reseta o botão de salvar para evitar looping de salvamentos
        save_image = False

cap.release() # liberar a camera
background_video.release() # libera os recursos da camera e do video de fundo
