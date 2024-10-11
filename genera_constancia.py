import streamlit as st
import pandas as pd
from fpdf import FPDF
import zipfile
import os
import ast
from io import StringIO
from PIL import Image

# Función para generar el PDF con las dimensiones de la imagen de fondo
def generate_pdf(data, filename, background_image, font_settings, y_start, line_height_multiplier, additional_images):
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
            text_width = bg_width * 0.75
            pdf.set_xy((bg_width - text_width) / 2, y_start)
            
            lines = pdf.multi_cell(text_width, line_height, text, align='C', split_only=True)
            lines_count = len(lines)
            
            pdf.set_xy((bg_width - text_width) / 2, y_start)
            pdf.multi_cell(text_width, line_height, text, align='C')
            
            y_start += line_height * lines_count
    
    if additional_images:
        image_width = 130
        image_height = 130
        spacing = (bg_width - (image_width * len(additional_images))) / (len(additional_images) + 1)
        y_position = y_start + 20

        for i, image_path in enumerate(additional_images):
            if os.path.exists(image_path):
                try:
                    x_position = spacing + i * (image_width + spacing)
                    pdf.image(image_path, x=x_position, y=y_position, w=image_width, h=image_height)
                    
                    image_name = os.path.splitext(os.path.basename(image_path))[0]
                    pdf.set_font("Arial", size=30)
                    pdf.set_text_color(0, 0, 0)
                    text_width = pdf.get_string_width(image_name)
                    pdf.set_xy(x_position + (image_width - text_width) / 2, y_position + image_height + 20)
                    pdf.cell(text_width, 10, image_name, align='C')
                except RuntimeError as e:
                    st.error(f"No se pudo cargar la imagen {image_path}. Error: {e}")
            else:
                st.error(f"La imagen {image_path} no existe o no se pudo cargar.")

    pdf.output(filename)

# Configuración de Streamlit
st.title("Generador de constancias PUIC")

# Input para que el usuario introduzca el texto delimitado por "|"
st.markdown("### Introduce a los usuarios delimitado por '|', NO PUEDE HABER REGISTROS CON MISMO NOMBRE:")
input_text = st.text_area("", height=200, value="""
dirigido|nombre|por|actividad|eslogan|fecha
a|Eduardo Melo Gómez|Por haber asistido a la|Ponencia: "Infancias Derechos e Interculturalidad" que se llevó a cabo el 21 de junio de 2024 en el marco del Seminario Permanente de Diversidad Cultural e Interculturalidad.|"POR MI RAZA HABLARÁ EL ESPÍRITU"|Ciudad Universitaria, Cd. Mx., a 07 agosto 2024
a|José Eduardo Rendón Lezama|Por haber asistido a la|Ponencia: "Infancias Derechos e Interculturalidad" que se llevó a cabo el 21 de junio de 2024 en el marco del Seminario Permanente de Diversidad Cultural e Interculturalidad.|"POR MI RAZA HABLARÁ EL ESPÍRITU"|Ciudad Universitaria, Cd. Mx., a 07 agosto 2024
""")

# Convertir el texto en un DataFrame
if input_text:
    input_data = StringIO(input_text)
    df = pd.read_csv(input_data, sep="|", quotechar='~')
    st.write("Previsualización de la información:")
    st.dataframe(df)

    # Configuración dinámica de las fuentes basada en las columnas del DataFrame
    st.markdown("### Configuración de fuentes para cada columna")
    font_settings = {}
    for column in df.columns:
        st.subheader(f"Configuración de la columna: {column}")
        font_size = st.number_input(f"Tamaño de letra para '{column}':", min_value=1, value=35, step=1, key=f"size_{column}")
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
y_start_user = st.number_input("Altura en donde empezará el texto (pixeles):", min_value=0, value=460)

# Input para que el usuario defina el valor del interlineado
line_height_multiplier = st.number_input("Valor del interlineado:", min_value=0.5, value=1.3, step=0.1)

# Selectbox para que el usuario elija un valor entre 1, 2 o 3 para cargar imágenes adicionales
st.markdown("### Seleccione el número de firmantes:")
selected_value = st.selectbox("", options=[1, 2, 3])

# Cargar las imágenes adicionales según el valor seleccionado
uploaded_images = []
for i in range(selected_value):
    image = st.file_uploader(f"Cargar imagen adicional {i+1}", type=["png", "jpg", "jpeg"], key=f"additional_image_uploader_{i}")
    if image:
        image_path = image.name
        with open(image_path, "wb") as f:
            f.write(image.read())
        uploaded_images.append(image_path)

# Botón para generar PDFs
if input_text and font_settings:
    if st.button("Generar PDFs"):
        pdf_files = []
        for index, row in df.iterrows():
            data = row.to_dict()
            pdf_filename = f"{data['nombre']}.pdf"
            generate_pdf(data, pdf_filename, "imagenes/background.png", font_settings, y_start_user, line_height_multiplier, uploaded_images)
            pdf_files.append(pdf_filename)
        
        zip_filename = "pdf_files.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for pdf_file in pdf_files:
                zipf.write(pdf_file, os.path.basename(pdf_file))
        
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
