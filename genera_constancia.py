import streamlit as st
import pandas as pd
from fpdf import FPDF
import zipfile
import os
import ast
from io import StringIO
from PIL import Image
from pdf2image import convert_from_path

# Función para generar el PDF temporal
def generate_temp_pdf(data, filename, background_image, font_settings, y_start, line_height_multiplier, additional_images):
    pdf = FPDF(unit='pt', format=[1650, 1275])
    pdf.add_page()
    pdf.image(background_image, x=0, y=0, w=1650, h=1275)
    
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
            text_width = 1100
            pdf.set_xy((1650 - text_width) / 2, y_start)
            
            lines = pdf.multi_cell(text_width, line_height, text, align='C', split_only=True)
            lines_count = len(lines)
            
            pdf.set_xy((1650 - text_width) / 2, y_start)
            pdf.multi_cell(text_width, line_height, text, align='C')
            
            y_start += line_height * lines_count
    
    if additional_images:
        image_width = 130
        image_height = 130
        spacing = (1650 - (image_width * len(additional_images))) / (len(additional_images) + 1)
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

# Resto de la configuración de Streamlit (igual que antes)

# Botón para previsualizar el primer PDF
if input_text and font_settings_input:
    try:
        font_settings = ast.literal_eval(font_settings_input)
    except Exception as e:
        st.error(f"Error en la configuración de fuentes: {e}")
        font_settings = None
    
    if font_settings and st.button("Previsualizar PDF"):
        try:
            first_row = df.iloc[0].to_dict()  # Obtener la primera fila del DataFrame
            temp_pdf_filename = "temp_preview.pdf"
            generate_temp_pdf(first_row, temp_pdf_filename, background_image_path, font_settings, y_start_user, line_height_multiplier, uploaded_images)
            
            # Convertir el PDF a imagen para mostrar en Streamlit
            images = convert_from_path(temp_pdf_filename, dpi=200)
            if images:
                st.image(images[0], caption="Vista previa del PDF", use_column_width=True)
            os.remove(temp_pdf_filename)  # Limpiar el archivo temporal después de la vista previa
        except Exception as e:
            st.error(f"Error al generar la vista previa: {e}")

# Botón para generar PDFs (igual que antes, solo que se presenta después de la vista previa)
if input_text and font_settings_input and st.button("Generar PDFs"):
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
    
    for pdf_file in pdf_files:
        os.remove(pdf_file)
    os.remove(zip_filename)
    if background_image is not None:
        os.remove(background_image_path)
    for image_path in uploaded_images:
        os.remove(image_path)
