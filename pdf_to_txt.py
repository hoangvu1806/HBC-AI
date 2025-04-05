import os
import fitz
from pdf2image import convert_from_path
import pytesseract
import time
from pathlib import Path
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.models.ocr_mac_model import OcrMacOptions
from docling.models.tesseract_ocr_cli_model import TesseractCliOcrOptions
from docling.models.tesseract_ocr_model import TesseractOcrOptions

# Đường dẫn đến Tesseract và Poppler (cần cài đặt trước)
pytesseract.pytesseract.tesseract_cmd = r"D:\ITApp\Tesseract-OCR\tesseract.exe"
poppler_path = r"D:\ITApp\poppler-24.08.0\Library\bin"

# Đường dẫn đến thư mục gốc và thư mục đích
root_dir = r"E:\HBC\DATA_NHANSU\THONG BAO MOI"  # Thư mục gốc chứa các tệp PDF
output_dir = r"E:\HBC\DATA_NHANSU\THONG BAO MOI_TEXT"  # Thư mục mới để lưu các tệp TXT
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True
pipeline_options.ocr_options.use_gpu = True
pipeline_options.table_structure_options.do_cell_matching = True
pipeline_options.ocr_options.lang = ["vi"]
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=32, device=AcceleratorDevice.AUTO
)

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Hàm trích xuất văn bản từ PDF chứa văn bản trực tiếp
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        # Mở tệp PDF bằng fitz
        doc = fitz.open(pdf_path)
        # Duyệt qua từng trang trong PDF
        for page in doc:
            # Trích xuất văn bản từ trang
            extracted = page.get_text().encode('utf-8').decode('utf-8')
            if extracted:
                text += extracted + "\n"  # Thêm dòng mới sau mỗi trang
        # Đóng tệp PDF sau khi xử lý
        doc.close()
        # conv_result = doc_converter.convert(pdf_path)
        # text = conv_result.document.export_to_markdown()
        # Trả về văn bản nếu trích xuất thành công
        if text.strip():
            print(f"{pdf_path}: Trích xuất văn bản thành công.")
            return text
        else:
            print(f"{pdf_path}: Không có văn bản trực tiếp, chuyển sang OCR.")
            return extract_text_with_ocr(pdf_path)
        
    except Exception as e:
        print(f"Lỗi khi trích xuất văn bản từ {pdf_path}: {e}")
        return extract_text_with_ocr(pdf_path)

# Hàm trích xuất văn bản từ PDF quét bằng OCR
def extract_text_with_ocr(pdf_path):
    text = ""
    try:
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        for i, img in enumerate(images):
            extracted_text = pytesseract.image_to_string(img, lang="vie")  # Ngôn ngữ tiếng Việt
            text += f"\n--- Trang {i+1} ---\n{extracted_text}\n"
        print(f"{pdf_path}: OCR hoàn tất.")
        return text
    except Exception as e:
        print(f"Lỗi khi trích xuất OCR từ {pdf_path}: {e}")
        return ""

# Hàm tạo thư mục nếu chưa tồn tại
def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Tạo thư mục: {directory}")

# Hàm duyệt cây thư mục và xử lý tệp PDF
def process_directory(root_dir, output_dir):
    for root, dirs, files in os.walk(root_dir):
        # Tính đường dẫn tương đối từ thư mục gốc
        relative_path = os.path.relpath(root, root_dir)
        # Tạo đường dẫn tương ứng trong thư mục đích
        target_dir = os.path.join(output_dir, relative_path)
        create_dir_if_not_exists(target_dir)
        
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                print(f"Đang xử lý: {pdf_path}")
                
                # Trích xuất văn bản
                text = extract_text_from_pdf(pdf_path)
                
                # Tạo đường dẫn tệp TXT trong thư mục đích
                txt_filename = os.path.splitext(file)[0] + '.txt'
                txt_path = os.path.join(target_dir, txt_filename)
                
                # Lưu văn bản vào tệp TXT
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Đã lưu vào: {txt_path}\n")

# Chạy chương trình
if __name__ == "__main__":
    print("Bắt đầu xử lý cây thư mục...\n")
    create_dir_if_not_exists(output_dir)
    process_directory(root_dir, output_dir)
    print("Hoàn tất! Kiểm tra các tệp TXT trong thư mục đích.")