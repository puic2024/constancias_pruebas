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
            text_width = bg_width * 0.75  # Ancho relativo para el texto (75% del ancho de la imagen)
            pdf.set_xy((bg_width - text_width) / 2, y_start)
            
            # Contar el número de líneas que el texto ocupará
            lines = pdf.multi_cell(text_width, line_height, text, align='C', split_only=True)
            lines_count = len(lines)
            
            # Dibujar el texto con salto de línea automático
            pdf.set_xy((bg_width - text_width) / 2, y_start)
            pdf.multi_cell(text_width, line_height, text, align='C')
            
            # Ajustar y_start dependiendo del número de líneas ocupadas
            y_start += line_height * lines_count
    
    # Distribuir las imágenes adicionales de manera uniforme y centrada
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

# El resto de la configuración de Streamlit sigue igual
