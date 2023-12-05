import os
import streamlit as st  # importação da bilioteca para construir a interface web
import cv2  # biblioteca para processamento de imagem
import numpy as np  # para realizar calculos
import imutils
from moviepy.editor import VideoFileClip  # lib de codecs de video
from PIL import Image

img_ext = ['png', 'jpg', 'jpeg']
video_ext = ['mp4', 'gif']

file_ext = img_ext + video_ext



# remover a imagem de fundo
def __remove_background(frame, background_image, lower_bound, upper_bound):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    foreground = cv2.bitwise_and(frame, frame, mask=~mask)

    # Calcular a proporção do frame e do background
    frame_height, frame_width = frame.shape[:2]
    background_height, background_width = background_image.shape[:2]
    scale = max(frame_width / background_width, frame_height / background_height)

    # Redimensionar o background
    resized_background = cv2.resize(background_image, (int(background_width * scale), int(background_height * scale)))

    # Cortar o excesso do background
    start_x = (resized_background.shape[1] - frame_width) // 2
    start_y = (resized_background.shape[0] - frame_height) // 2
    cropped_background = resized_background[start_y:start_y + frame_height, start_x:start_x + frame_width]

    # Aplicar a máscara e combinar foreground e background
    background = cv2.bitwise_and(cropped_background, cropped_background, mask=mask)
    combined = cv2.add(foreground, background)

    return combined


# Função para remover o fundo verde e substituir por um vídeo MP4
def __remove_background_and_add_video(frame, background_video, lower_bound, upper_bound):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    foreground = cv2.bitwise_and(frame, frame, mask=~mask)

    ret, background_frame = background_video.read()
    if not ret:
        background_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        _, background_frame = background_video.read()

    # Calcular a proporção do frame e do background_frame
    frame_height, frame_width = frame.shape[:2]
    background_height, background_width = background_frame.shape[:2]
    scale = max(frame_width / background_width, frame_height / background_height)

    # Redimensionar o background_frame
    resized_background_frame = cv2.resize(background_frame, (int(background_width * scale), int(background_height * scale)))

    # Cortar o excesso do background_frame
    start_x = (resized_background_frame.shape[1] - frame_width) // 2
    start_y = (resized_background_frame.shape[0] - frame_height) // 2
    cropped_background_frame = resized_background_frame[start_y:start_y + frame_height, start_x:start_x + frame_width]

    # Aplicar a máscara e combinar foreground e background
    background = cv2.bitwise_and(cropped_background_frame, cropped_background_frame, mask=mask)
    combined = cv2.add(foreground, background)

    return combined


# converte uma cor RGB para HSV com tolerancia
def __convert_to_hsv_with_tolerance(rgb_color, tolerance=40):
    bgr_color = rgb_color[::-1]  # "conversao" RGB -> BGR: (43, 177, 9)
    hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]  # Conversão de BGR para HSV
    lower_bound = np.array([max(hsv_color[0] - tolerance, 0), 50, 50])  # limite minimo para o filtro HSV
    upper_bound = np.array([min(hsv_color[0] + tolerance, 255), 255, 255])  # lmite maximo para o filtro HSV
    return lower_bound, upper_bound  # Retorno uma tupla


chroma_key_rgb = (9, 117, 43)  # é a cor em RGB do ChromaKey
lower_bound, upper_bound = __convert_to_hsv_with_tolerance(
    chroma_key_rgb,
    10
)  # Converter a cor HEX-RGB para HSV com tolerancia

st.title("Aplicação de Chroma Key")  # titulo da aplicação
st.subheader("Utilizando Streamlit e OpenCV")  # subtitulo da aplicação

# Envio do arquivo de imagem ou vídeo
uploaded_file = st.file_uploader(
    "Escolha uma imagem ou vídeo de fundo",
    type=file_ext
)
background_image = None
background_video = None

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension in img_ext:
        # Decodificar a imagem
        background_image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_COLOR)

    elif file_extension in video_ext:
        # Salvar o vídeo em um arquivo temporário
        video_dir = 'temp'
        os.makedirs(video_dir, exist_ok=True)
        video_path = os.path.join(video_dir, 'video_temp.mp4')

        with open(video_path, 'wb') as video_file:
            video_file.write(uploaded_file.read())

        # Inicializar a leitura do vídeo
        background_video = cv2.VideoCapture(video_path)

# Inicialização de variáveis
name_and_number = st.text_input("Nome e Número:")
##phone_input = st.text_input("Número de telefone:")
save_image = st.button("Salvar Foto")
##rotate_button = st.button("Girar no sentido horário")  # Botão de rotação
##rotation_angle = 0

# componente para escolher a webcam, no momento sem possibilidade de identificar nome
##webcams_disponiveis = __listar_webcams()
##webcam_selecionada = st.selectbox("Selecione a webcam:", webcams_disponiveis)

# Configurar a câmera (0 para câmera nativa, notebook)
cap = cv2.VideoCapture(1)

frameST = st.empty()

while True:
    ret, frame = cap.read()
    if not ret:
        st.warning("Câmera não iniciada")
        break

    # espelhamento correto da imagem
    # EM PÉ
    frame = cv2.flip(frame, 1)
    frame = cv2.rotate(frame, 2, frame)
    frame = cv2.flip(frame, 1)

    # DEITADO
    #frame = cv2.flipe(frame, 1)

    # Redimensionar o frame para uma resolução desejada
    
    frame = imutils.resize(frame, height=1080)
    frame = imutils.resize(frame, width=1080)

    # Aplicando rotação ao frame
    ##frame = imutils.rotate(frame, rotation_angle)

    if background_image is not None:
        frame = __remove_background(frame, background_image, lower_bound, upper_bound)

    if background_video is not None:
        frame = __remove_background_and_add_video(frame, background_video, lower_bound, upper_bound)

    frameST.image(frame, channels='BGR', use_column_width=True)

    if save_image:
        # Garantir que o diretório exista ou criá-lo
        save_dir = os.path.join(os.getcwd(), name_and_number)
        os.makedirs(save_dir, exist_ok=True)

        # Caminho completo para a imagem com o número do telefone
        image_path = os.path.join(save_dir, f'{name_and_number}.png')

        # Salvar a imagem como PNG
        cv2.imwrite(image_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        # Exibir mensagem na tela que a imagem foi salva
        st.write(f"Imagem salva como '{image_path}'")

        # Resetar o botão de salvar para evitar salvamentos repetidos
        save_image = False

        # Converter a imagem para PNG mantendo a qualidade
        img = Image.open(image_path)
        img.save(image_path, format='PNG', compress_level=0)

    # Condição da rotação ao apertar no botão
    ##if rotate_button:
        ##rotation_angle += 90
        ##rotation_angle %= 360  # Limitando a 360 graus

cap.release()  # Liberar a câmera
if background_video is not None:
    background_video.release()  # Liberar os recursos da câmera e do vídeo de fundo