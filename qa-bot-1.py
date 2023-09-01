from flask import Flask, render_template, request
import fitz  # PyMuPDF use pip install PyMupdf
import docx
import pandas as pd
from transformers import pipeline

app = Flask(__name__)

qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

knowledge_base = ""

def extract_text_from_pdf(pdf_data):
    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
    extracted_text = ""

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        page_text = page.get_text("text")
        extracted_text += page_text

    return extracted_text

@app.route("/", methods=["GET", "POST"])
def index():
    global knowledge_base

    ans = ""
    document_content = ""

    if request.method == "POST":
        if "document_upload" in request.files:
            uploaded_file = request.files["document_upload"]
            if uploaded_file.filename != "":
                file_extension = uploaded_file.filename.split(".")[-1].lower()
                file_data = uploaded_file.read()

                if file_extension == "pdf":
                    document_content = extract_text_from_pdf(file_data)
                elif file_extension == "docx":
                    doc = docx.Document(file_data)
                    document_content = "\n".join([p.text for p in doc.paragraphs])
                elif file_extension in ["csv", "xlsx"]:
                    df = pd.read_csv(file_data) if file_extension == "csv" else pd.read_excel(file_data)
                    document_content = df.to_string(index=False)  # Display DataFrame as text
                else:
                    document_content = file_data.decode("utf-8", errors="ignore")

                knowledge_base += document_content
                print(f"knowledge_base = {knowledge_base}")

        user_question = request.form.get("user_question")
        if user_question:
            answer = qa_pipeline(question=user_question, context=knowledge_base)
            ans = answer["answer"]
            return {"answer": ans}

    return render_template("csv-bot.html", answer=ans)

if __name__ == "__main__":
    app.run(debug=True, port=5010)
