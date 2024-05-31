from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from io import BytesIO
import os
import img2pdf
from pypdf import PdfReader, PdfWriter, Transformation
import tempfile
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
            if PdfReader(BytesIO(file_bytes)).is_encrypted:
                raise ValueError("Please Decrypt The Following PDF File Before Merging: " + file_name + file_extension)
            file_pdf_bytesio = resize_pdf(BytesIO(file_bytes))
            merged_pdf.append(file_pdf_bytesio)
        elif file_extension == "":
            raise ValueError("No uploaded files found.")
        else:
            raise ValueError("Unsupported file type for the following file: " + file_extension)

    merged_pdf_bytesio = BytesIO()
    merged_pdf.write(merged_pdf_bytesio)
    merged_pdf.close()
    merged_pdf_bytesio.seek(0)
    return merged_pdf_bytesio

def convert_img_to_pdf(img_bytes):
    img_pdf_bytesio = BytesIO(img2pdf.convert(img_bytes))
    img_pdf_bytesio.seek(0)
    resized_pdf_bytesio = resize_pdf(img_pdf_bytesio)
    resized_pdf_bytesio.seek(0)
    return resized_pdf_bytesio

def convert_docx_to_pdf(docx_bytes):
    # Create a temporary file in memory
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
        temp_docx.write(docx_bytes)
        temp_docx_path = temp_docx.name
    # Create temporary file for output PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output_file:
        temp_output_file_path = temp_output_file.name

    # Command to convert DOCX to PDF using LibreOffice
    command = [
        'C:\\Program Files\\LibreOffice\\program\\soffice.exe',
        '--headless',  # Run in headless mode (no GUI)
        '--convert-to', 'pdf',  # Convert to PDF format
        '--outdir', os.path.dirname(temp_output_file_path),  # Output directory for converted file
        temp_docx_path  # Input DOCX file
    ]    
    
    subprocess.run(command)

    # Read the content of the output PDF file
    with open(temp_docx_path.replace('.docx', '.pdf'), 'rb') as temp_output_file:
        output_bytesio = BytesIO(temp_output_file.read())

    output_bytesio.seek(0)
    resized_pdf_bytesio = resize_pdf(output_bytesio)
    resized_pdf_bytesio.seek(0)
    # Delete temporary files
    os.unlink(temp_docx_path)
    os.unlink(temp_docx_path.replace('.docx', '.pdf'))
    os.unlink(temp_output_file_path)
    return resized_pdf_bytesio

def resize_pdf(pdf_bytesio):
    resized_pdf_bytesio = BytesIO()
    pdf_reader = PdfReader(pdf_bytesio)
    resized_writer = PdfWriter()

    for page_number in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_number]
        og_width = page.mediabox.width
        og_height = page.mediabox.height
        a4_width = 595
        a4_height = 842

        scale_x = a4_width / og_width
        scale_y = a4_height / og_height
        scaling_param = min(scale_x, scale_y)

        y_offset = (a4_height - og_height * scaling_param) / 2

        op = Transformation().scale(sx=(scaling_param), sy=(scaling_param)).translate(ty=y_offset)
        page.add_transformation(op)
        page.mediabox.lower_left = (0,0)
        page.mediabox.upper_right = (a4_width, a4_height)

        resized_writer.add_page(page)

    resized_writer.write(resized_pdf_bytesio)
    resized_pdf_bytesio.seek(0)
    return resized_pdf_bytesio

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        applicant_name = request.form.get('applicant_name')
        uploaded_files = request.files.getlist('uploaded_files')

        files_dict = {uploaded_file.filename: uploaded_file for uploaded_file in uploaded_files}
        ordered_file_names = request.form.get('ordered_files').split('|||')

        ordered_files = [files_dict[name] for name in ordered_file_names]

        try:
            merged_pdf_bytesio = process_files(ordered_files)
            return send_file(merged_pdf_bytesio, as_attachment=True, download_name=f'{applicant_name}.pdf')
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
