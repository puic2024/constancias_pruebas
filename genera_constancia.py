import streamlit as st
import pandas as pd
from fpdf import FPDF
import zipfile
import os
from io import StringIO
from PIL import Image

# Función para generar el PDF con una imagen de fondo, texto parametrizado y añadir imágenes adicionales con nombres centrados
def generate_pdf(data, filename, background_image, font_settings, y_start, line_height_multiplier, additional_images, image_scale, text_size):
    # Obtener las dimensiones de la imagen de fondo
    bg_image = Image.open(background_image)
    bg_width, bg_height = bg_image.size
    
    pdf = FPDF(unit='pt', format=[bg_width, bg_height])
    pdf.add_page()
    pdf.image(background_image, x=0, y=0, w=bg_width, h=bg_height)
    
    for key, value in data.items():
        if key in font_settings:
            text = str(value)
            font_size = font_settings[key]['tamaño']
            font_type = font_settings[key]['tipo_letra']
            font_style = font_settings[key].get('estilo', '')
            font_color = font_settings[key].get('color', (0, 0, 0))
            
            pdf.set_font(font_type, font_style, size=font_size)
            pdf.set_text_color(*font_color)
            
            line_height = pdf.font_size * line_height_multiplier
            text_width = bg_width * 0.75  # Ancho relativo para el texto (75% del ancho de la imagen)
            pdf.set_xy((bg_width - text_width) / 2, y_start)
            
            # Contar el número de líneas que el texto ocupará
            lines = pdf.multi_cell(text_width, line_height, text, align='C', split_only=True)
            lines_count = len(lines)
            
            # Dibujar el texto con salto de línea automático
            pdf.set_xy((bg_width - text_width) / 2, y_start)
            pdf.multi_cell(text_width, line_height, text, align='C')
            
            y_start += line_height * lines_count
    
    # Distribuir las imágenes adicionales de manera uniforme y centrada
    if additional_images:
        image_width = 130 * (image_scale / 100)
        image_height = 130 * (image_scale / 100)
        spacing = (bg_width - (image_width * len(additional_images))) / (len(additional_images) + 1)
        y_position = y_start + 20

        for i, image_path in enumerate(additional_images):
            if os.path.exists(image_path):
                try:
                    x_position = spacing + i * (image_width + spacing)
                    pdf.image(image_path, x=x_position, y=y_position, w=image_width, h=image_height)
                    
                    image_name = os.path.splitext(os.path.basename(image_path))[0]
                    pdf.set_font("Arial", size=text_size)
                    pdf.set_text_color(0, 0, 0)
                    text_width = pdf.get_string_width(image_name)
                    pdf.set_xy(x_position + (image_width - text_width) / 2, y_position + image_height + 20)
                    pdf.cell(text_width, 10, image_name, align='C')
                except RuntimeError as e:
                    st.error(f"No se pudo cargar la imagen {image_path}. Error: {e}")
            else:
                st.error(f"La imagen {image_path} no existe o no se pudo cargar.")

    pdf.output(filename)

# Función para crear archivos ZIP
def create_zip(pdf_files, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for pdf_file in pdf_files:
            zipf.write(pdf_file, os.path.basename(pdf_file))

# Configuración de Streamlit
st.title("Generador de constancias PUIC")

# Mostrar la imagen "escudo.jpg" justo después del título con una reducción al 60% de su tamaño original
escudo_image_path = "imagenes/escudo.jpg"
if os.path.exists(escudo_image_path):
    escudo_image = Image.open(escudo_image_path)
    width, height = escudo_image.size
    new_size = (int(width * 0.9), int(height * 0.9))
    escudo_image_resized = escudo_image.resize(new_size)
    st.image(escudo_image_resized, use_column_width=False)
else:
    st.error(f"La imagen {escudo_image_path} no existe.")

# Cargar la imagen de fondo con valor predeterminado (después del título)
st.markdown("# 1. Cargar imagen de fondo:")
background_image = st.file_uploader("", type=["png"], accept_multiple_files=False)
if background_image is None:
    background_image_path = "imagenes/background.png"
else:
    background_image_path = background_image.name
    with open(background_image_path, "wb") as f:
        f.write(background_image.read())

# Previsualizar la imagen de fondo cargada o predeterminada
image = Image.open(background_image_path)
image = image.resize((330, 255))
st.image(image, caption="Previsualización de la imagen de fondo", use_column_width=False)

# Cargar un archivo CSV
st.markdown("# 2. Cargar archivo CSV con datos:")
uploaded_file = st.file_uploader("Elige un archivo CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Previsualización de la información:")
    st.dataframe(df)

    # Configuración dinámica de las fuentes basada en las columnas del DataFrame
    st.markdown("# 3. Configuración de fuentes para cada columna")
    font_settings = {}
    for column in df.columns:
        st.subheader(f"- Configuración de la columna: {column}")
        font_size = st.number_input(f"Tamaño de letra para '{column}':", min_value=1, value=28, step=1, key=f"size_{column}")
        font_type = st.selectbox(f"Tipo de letra para '{column}':", options=["Arial", "Courier", "Helvetica"], key=f"font_{column}")
        font_style = st.selectbox(f"Estilo de letra para '{column}':", options=["", "B", "I", "BI"], key=f"style_{column}")
        font_color = st.color_picker(f"Color de letra para '{column}':", value='#000000', key=f"color_{column}")

        # Convertir el color de hexadecimal a RGB
        font_color_rgb = tuple(int(font_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Guardar configuración en el diccionario
        font_settings[column] = {
            "tamaño": font_size,
            "tipo_letra": font_type,
            "estilo": font_style,
            "color": font_color_rgb
        }

# Input para que el usuario defina la altura inicial del texto
st.markdown("# 4. Altura e interlineado del texto")
y_start_user = st.number_input("Altura en donde empezará el texto (pixeles):", min_value=0, value=260)

# Input para que el usuario defina el valor del interlineado
line_height_multiplier = st.number_input("Valor del interlineado:", min_value=0.5, value=1.3, step=0.1)

# Selectbox para que el usuario elija un valor entre 1, 2 o 3 para cargar imágenes adicionales
st.markdown("# 5. Seleccione el número de firmantes:")
selected_value = st.selectbox("Número de firmantes:", options=[1, 2, 3])

# Cargar las imágenes adicionales según el valor seleccionado
uploaded_images = []
for i in range(selected_value):
    image = st.file_uploader(f"Cargar firma {i+1} (sin acentos)", type=["png", "jpg", "jpeg"], key=f"additional_image_uploader_{i}")
    if image:
        image_path = image.name
        with open(image_path, "wb") as f:
            f.write(image.read())
        uploaded_images.append(image_path)

# Slider para definir el porcentaje de tamaño de las imágenes adicionales
st.markdown("### Porcentaje de tamaño de las firmas (QR):")
image_scale = st.slider("Ajusta el porcentaje de las dimensiones de las imágenes adicionales:", min_value=1, max_value=100, value=100)

# Input para definir el tamaño del texto de las imágenes adicionales
st.markdown("### Tamaño del texto de las firmas:")
text_size = st.number_input("Tamaño del texto para las imágenes adicionales:", min_value=1, value=20, step=1)

# Botón para generar PDFs
if uploaded_file and font_settings and uploaded_images:
    if st.button("Generar PDFs"):
        pdf_files = []
        for index, row in df.iterrows():
            data = row.to_dict()
            pdf_filename = f"{data['nombre']}.pdf"
            generate_pdf(data, pdf_filename, background_image_path, font_settings, y_start_user, line_height_multiplier, uploaded_images, image_scale, text_size)
            pdf_files.append(pdf_filename)
        
        zip_filename = "pdf_files.zip"
        create_zip(pdf_files, zip_filename)
        
        with open(zip_filename, "rb") as f:
            bytes_data = f.read()
            st.download_button(
                label="Descargar ZIP",
                data=bytes_data,
                file_name=zip_filename,
                mime="application/zip"
            )
        
        for pdf_file in pdf_files:
            os.remove(pdf_file)
        os.remove(zip_filename)
        if background_image is not None:
            os.remove(background_image_path)
