import streamlit as st
import pandas as pd
from fpdf import FPDF
import zipfile
import os
import ast
from io import StringIO
from PIL import Image

# Función para generar el PDF con una imagen de fondo, texto parametrizado y añadir imágenes adicionales con nombres centrados
def generate_pdf(data, filename, background_image, font_settings, y_start, line_height_multiplier, additional_images):
    pdf = FPDF(unit='pt', format=[1650, 1275])
    pdf.add_page()
    pdf.image(background_image, x=0, y=0, w=1650, h=1275)
    
    for key, value in data.items():
        if key in font_settings:
            text = str(value)
            font_size = font_settings[key]['tamaño']
            font_type = font_settings[key]['tipo_letra']
            font_style = font_settings[key].get('estilo', '')  # Estilo normal por defecto
            font_color = font_settings[key].get('color', (0, 0, 0))  # Color negro por defecto
            
            pdf.set_font(font_type, font_style, size=font_size)
            pdf.set_text_color(*font_color)
            
            line_height = pdf.font_size * line_height_multiplier
            text_width = 1100  # Ancho fijo para el texto
            pdf.set_xy((1650 - text_width) / 2, y_start)
            
            # Contar el número de líneas que el texto ocupará
            lines = pdf.multi_cell(text_width, line_height, text, align='C', split_only=True)
            lines_count = len(lines)
            
            # Dibujar el texto con salto de línea automático
            pdf.set_xy((1650 - text_width) / 2, y_start)
            pdf.multi_cell(text_width, line_height, text, align='C')
            
            # Ajustar y_start dependiendo del número de líneas ocupadas
            y_start += line_height * lines_count
    
    # Distribuir las imágenes adicionales de manera uniforme y centrada con tamaño 130x130
    if additional_images:
        image_width = 130  # Ancho de cada imagen
        image_height = 130  # Alto de cada imagen
        spacing = (1650 - (image_width * len(additional_images))) / (len(additional_images) + 1)
        y_position = y_start + 20  # Posición vertical después del último texto

        for i, image_path in enumerate(additional_images):
            if os.path.exists(image_path):
                try:
                    x_position = spacing + i * (image_width + spacing)
                    pdf.image(image_path, x=x_position, y=y_position, w=image_width, h=image_height)
                    
                    # Añadir el nombre de la imagen debajo, centrado respecto a la imagen (sin extensión)
                    image_name = os.path.splitext(os.path.basename(image_path))[0]
                    pdf.set_font("Arial", size=30)
                    pdf.set_text_color(0, 0, 0)
                    text_width = pdf.get_string_width(image_name)
                    pdf.set_xy(x_position + (image_width - text_width) / 2, y_position + image_height + 20)  # 10 píxeles más abajo
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
    
    # Redimensionar la imagen al 60% de su tamaño original
    width, height = escudo_image.size
    new_size = (int(width * 0.9), int(height * 0.9))
    escudo_image_resized = escudo_image.resize(new_size)
    
    st.image(escudo_image_resized, use_column_width=False)
else:
    st.error(f"La imagen {escudo_image_path} no existe.")

# Cargar la imagen de fondo con valor predeterminado (después del título)
st.markdown("### Cargar imagen de fondo:")
background_image = st.file_uploader("", type=["png"], accept_multiple_files=False)
if background_image is None:
    background_image_path = "imagenes/background.png"
else:
    background_image_path = background_image.name
    with open(background_image_path, "wb") as f:
        f.write(background_image.read())

# Previsualizar la imagen de fondo cargada o predeterminada con tamaño 330x255
image = Image.open(background_image_path)
image = image.resize((330, 255))
st.image(image, caption="Previsualización de la imagen de fondo", use_column_width=False)

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
    df = pd.read_csv(input_data, sep="|", quotechar='~')  # Usar un caracter que no aparece en el texto
    st.write("Previsualización de la información:")
    st.dataframe(df)

# Input de texto para la configuración de las fuentes (después del DataFrame)
st.markdown("### Introduce la configuración de las fuentes (en formato de diccionario):")
font_settings_input = st.text_area("", height=300, value="""
{
    "dirigido": {"tamaño": 35, "tipo_letra": "Arial", "estilo": "", "color": (0, 0, 0)},
    "nombre": {"tamaño": 40, "tipo_letra": "Arial", "estilo": "B", "color": (0, 0, 0)},
    "por": {"tamaño": 35, "tipo_letra": "Arial", "estilo": "", "color": (0, 0, 0)},
    "actividad": {"tamaño": 40, "tipo_letra": "Arial", "estilo": "B", "color": (0, 0, 0)},
    "eslogan": {"tamaño": 35, "tipo_letra": "Arial", "estilo": "", "color": (0, 0, 0)},
    "fecha": {"tamaño": 35, "tipo_letra": "Arial", "estilo": "", "color": (0, 0, 0)}
}
""")

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

# Botón para generar PDFs (al final del proceso)
if input_text and font_settings_input:
    try:
        font_settings = ast.literal_eval(font_settings_input)
    except Exception as e:
        st.error(f"Error en la configuración de fuentes: {e}")
        font_settings = None
    
    if font_settings and st.button("Generar PDFs"):
        pdf_files = []
        for index, row in df.iterrows():
            data = row.to_dict()
            pdf_filename = f"{data['nombre']}.pdf"
            generate_pdf(data, pdf_filename, background_image_path, font_settings, y_start_user, line_height_multiplier, uploaded_images)
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
        
        # Limpiar archivos temporales
        for pdf_file in pdf_files:
            os.remove(pdf_file)
        os.remove(zip_filename)
        if background_image is not None:
            os.remove(background_image_path)
        for image_path in uploaded_images:
            os.remove(image_path)
