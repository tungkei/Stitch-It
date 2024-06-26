from flask import Flask, request, render_template, send_file, jsonify
from io import BytesIO
import os
import img2pdf
from pypdf import PdfReader, PdfWriter, Transformation, PaperSize
import tempfile
import pythoncom
from docx2pdf import convert
from waitress import serve
import webbrowser
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'

logging.getLogger("img2pdf").setLevel(logging.ERROR)

a4_width, a4_height = (PaperSize.A4.width, PaperSize.A4.height)
a4_aspect_ratio = a4_width / a4_height

def process_files(uploaded_files):
    merged_pdf = PdfWriter()

    for uploaded_file in uploaded_files:
        file_name, file_extension = os.path.splitext(uploaded_file.filename)
        file_bytes = uploaded_file.read()
        if file_extension in [".jpg", ".jpeg", ".png"]:
            file_pdf_bytesio = convert_img_to_pdf(file_bytes)
            merged_pdf.append(file_pdf_bytesio)
        elif file_extension == ".docx":
            file_pdf_bytesio = convert_docx_to_pdf(file_bytes)
            merged_pdf.append(file_pdf_bytesio)
        elif file_extension == ".pdf":
            try:
                file_bytesio = BytesIO(file_bytes)
                PdfReader(file_bytesio)
                merged_pdf.append(file_bytesio)
            except Exception as e:
                if ("File has not been decrypted" in str(e)):
                    raise ValueError("Please decrypt the following PDF file before merging:\n" + file_name + file_extension)
                else:
                    raise e

    merged_pdf_bytesio = BytesIO()
    merged_pdf.write(merged_pdf_bytesio)
    merged_pdf.close()
    merged_pdf_bytesio.seek(0)

    # Resize to uniformed PDF size
    resized_bytesio = resize_pdf(merged_pdf_bytesio)
    return resized_bytesio

def convert_img_to_pdf(img_bytes):
    img_pdf_bytesio = BytesIO(img2pdf.convert(img_bytes))
    img_pdf_bytesio.seek(0)
    return img_pdf_bytesio

def convert_docx_to_pdf(docx_bytes):
    pythoncom.CoInitialize()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
        temp_docx.write(docx_bytes)
        temp_docx_path = temp_docx.name
    temp_pdf_path = temp_docx_path.replace('.docx', '.pdf')
    convert(temp_docx_path, temp_pdf_path)
    with open(temp_pdf_path, 'rb') as temp_pdf:
        docx_pdf_bytesio = BytesIO(temp_pdf.read())
    os.unlink(temp_docx_path)
    os.unlink(temp_pdf_path)
    docx_pdf_bytesio.seek(0)  
    return docx_pdf_bytesio
 
def resize_pdf(pdf_bytesio):
    new_dimensions = get_new_page_dimensions(pdf_bytesio)
    resized_pdf_bytesio = BytesIO()
    pdf_reader = PdfReader(pdf_bytesio)
    resized_writer = PdfWriter()

    new_width = new_dimensions["width"]
    new_height = new_dimensions["height"]

    for page_number in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_number]
        og_width = page.mediabox.width
        og_height = page.mediabox.height

        # Only scale if new dimensions are different from original dimensions
        if not (og_width == new_width and og_height == new_height):
            scale_x = new_width / og_width
            scale_y = new_height / og_height
            scaling_param = min(scale_x, scale_y)

            transformed_width = og_width * scaling_param
            transformed_height = og_height * scaling_param
            
            if scale_x < scale_y: # Centre vertically
                y_offset = (new_height - transformed_height) / 2
                op = Transformation().scale(sx=(scaling_param), sy=(scaling_param)).translate(ty=y_offset)
            else: # Centre horizontally
                x_offset = (new_width - transformed_width) / 2
                op = Transformation().scale(sx=(scaling_param), sy=(scaling_param)).translate(tx=x_offset)

            page.mediabox.lower_left = (0,0)
            page.mediabox.upper_right = (new_width, new_height)
            page.add_transformation(op)

        resized_writer.add_page(page)

    resized_writer.write(resized_pdf_bytesio)
    resized_writer.close()
    resized_pdf_bytesio.seek(0)
    return resized_pdf_bytesio
    
def get_smallest_page(pdf_bytesio):
    smallest_page = None
    pdf_reader = PdfReader(pdf_bytesio)
        
    for page_number in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_number]
        page_width = page.mediabox.width
        page_height = page.mediabox.height

        if page_width < a4_width or page_height < a4_height:
        # Update smallest_page if it's the first smaller page or has smaller dimensions
            if smallest_page is None or (page_width < smallest_page["width"] or page_height < smallest_page["height"]):
                smallest_page = {"width": page_width, "height": page_height}
    return smallest_page

def get_new_page_dimensions(pdf_bytesio):
    smallest_page_dims = get_smallest_page(pdf_bytesio)
    new_dimensions = None
    if smallest_page_dims:
        new_width = min(smallest_page_dims["width"], smallest_page_dims["height"] * a4_aspect_ratio)
        new_height = min(smallest_page_dims["height"], smallest_page_dims["width"] / a4_aspect_ratio)
        new_dimensions = {"width": new_width, "height": new_height}
    else:
        new_dimensions = {"width": a4_width, "height": a4_height}
    return new_dimensions

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        applicant_name = request.form.get('applicant-name')
        uploaded_files = request.files.getlist('uploaded-files')

        files_dict = {uploaded_file.filename: uploaded_file for uploaded_file in uploaded_files}
        ordered_file_names = request.form.get('ordered-files').split('|||')

        ordered_files = [files_dict[name] for name in ordered_file_names]

        try:
            merged_pdf_bytesio = process_files(ordered_files)
            return send_file(merged_pdf_bytesio, as_attachment=True, download_name=f'{applicant_name}.pdf')
        except ValueError as e:
            error_message = str(e)
            return jsonify({'error': error_message}), 400
        except Exception as e:
            error_message = str(e)
            return jsonify({'error': 'Internal server error:\n' + error_message}), 500

    return render_template('index.html')

if __name__ == '__main__':
    print("Server is running on http://127.0.0.1:5000\n")
    print("Press Ctrl + C to stop the server after you have finished using the Stitch It app.\n")
    print("This console will be closed automatically once the server is stopped.\n")
    webbrowser.open('http://127.0.0.1:5000')
    serve(app, host='0.0.0.0', port=5000)
