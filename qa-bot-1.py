from flask import Flask, render_template, request, redirect, url_for
import fitz  # PyMuPDF
import docx
import pandas as pd
# from transformers import pipeline

import json
import requests

app = Flask(__name__)

# qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

filename_content = []
knowledge_base = ""
uploaded_documents = []  # List to store uploaded document names
chat_history = []
chat_dict = {}

def extract_text_from_pdf(pdf_data):
    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
    extracted_text = ""

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        page_text = page.get_text("text")
        extracted_text += page_text

    return extracted_text

@app.route("/")
def index():
    return redirect(url_for("document_upload"))

@app.route("/upload", methods=["GET", "POST"])
def document_upload():
    global knowledge_base  # Access the knowledge_base variable

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
                    document_content = df.to_string(index=False)
                else:
                    document_content = file_data.decode("utf-8", errors="ignore")

                filename_content_dict = {uploaded_file.filename : document_content}
                filename_content.append(filename_content_dict)
                print(f"filename_content === {filename_content}")

                uploaded_documents.append(uploaded_file.filename)

    print(f"uploaded_documents = {uploaded_documents}")
    return render_template("upload.html", uploaded_documents=uploaded_documents)

@app.route("/remove-document", methods=["POST"])
def remove_document():
    filename = request.form.get("filename")
    print(f"filename = {filename}")

    if filename in uploaded_documents:
        uploaded_documents.remove(filename)
    
    for content in filename_content:
        if filename in content.keys():
            content.pop(filename)
    print(f"filename_content = {filename_content}")
    return redirect(url_for("document_upload"))


# @app.route("/green_grey")
# def green_grey():
#     return render_template("green_grey_1.html")

@app.route("/qa", methods=["GET", "POST"])
def qa():
    global knowledge_base
    global chat_history
    global chat_dict
    knowledge_base = ""

    print(f"filename_content = {filename_content}")
    print(f"knowledge_base knowledge_base = {knowledge_base}")
    ans = ""
    if request.method == "POST":
        data = request.get_json()
        print(f"data = {data}")
        user_question = data.get("user_question")
        print(f"user_question = {user_question}")

        if user_question:
            for content in filename_content:
                knowledge_base+=str(content.values()) + " "
        
                knowledge_base = knowledge_base.replace("dict_values([\'","").replace("\'])","").replace("\\r","").replace("\\n","").replace('dict_values([])',"").replace("dict_values([","").replace("])","")

            print(f"knowledge_base user_question = {knowledge_base}")
            # answer = qa_pipeline(question=user_question, context=knowledge_base)
            # ans = answer["answer"]

            prompt = f"""<s>[INST] <<SYS>>\n\n<</SYS>>\n\ncontent = {knowledge_base}\n
            based on the provided content answer the following question \n
            question = {user_question} [/INST]
            """

            print(f"prompt = {prompt}")

            url = 'http://107.223.129.74:5000/api/v1/chat'
            

            payload = json.dumps({
                'user_input': prompt,
        'max_new_tokens': 200,
        'auto_max_new_tokens': False,
        'max_tokens_second': 0,
        'encoder_repetition_penalty': 1,
        'history': { 'internal': [], 'visible': [] },
        'mode': 'instruct',
        'your_name': 'You',
        'regenerate': False,
        '_continue': False,
        'chat_instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',
        'preset': 'None',
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.9,
        'typical_p': 1,
        'epsilon_cutoff': 0,
        'eta_cutoff': 0,
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.15,
        'repetition_penalty_range': 0,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'num_return_sequences': 1,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'grammar_string': '',
        'guidance_scale': 1,
        'negative_prompt': '',
        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': True,
        'custom_token_bans': '',
        'skip_special_tokens': True,
        'use_cache': True,
        'stopping_strings': []
            })
            # print('Printing payload', payload)
            headers = {
            'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            print(f"response = {response}")

            print(f"res === {response.text}")

            d = response.text

            response_dict = response.json()
            print(f"response_dict === {response_dict}")

            ans = response_dict['results'][0]['history']['visible'][0][1]

            print(f"answer === {ans}")
            chat_dict["user_question"] = user_question
            chat_dict["answer"] = ans
            chat_history.append(chat_dict)
            print(f"chat_history = {chat_history}")
            return {"answer": ans}

    return render_template("green_grey_1.html", answer=ans)

if __name__ == "__main__":
    app.run(debug=True, port=5010)
