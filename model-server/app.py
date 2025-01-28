from flask import Flask, request, jsonify
from flask_cors import CORS  # Import Flask-CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
from vectorization.pdf_processing import pdf_to_text_chunks
from vectorization.indexing import PDFVectorStore
import torch

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the model and tokenizer
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    max_length = data.get("max_length", 50)

    # Tokenize input
    input_ids = tokenizer.encode(prompt, return_tensors="pt")

    # Generate response
    with torch.no_grad():
        output = model.generate(input_ids, max_length=max_length, do_sample=True, top_p=0.9, top_k=50)

    response_text = tokenizer.decode(output[0], skip_special_tokens=True)

    return jsonify({"response": response_text})


@app.route("/query", methods=["POST"])
def query():
    data = request.json
    prompt = data.get("prompt", "")
    max_length = data.get("max_length", 50)

    # Vectorize the file into memory
    # 1. Build or load your vector store
    vector_store = PDFVectorStore(embedding_model="all-MiniLM-L6-v2")

    # 2. Process and index PDF files
    pdf_files = ["/app/vectorization/1-G0.5ArchSpecs.pdf", "/app/vectorization/2-CaliberExhibits.pdf"]
    for pdf_file in pdf_files:
        chunks = pdf_to_text_chunks(pdf_file, chunk_size=5000, overlap=500)        
        vector_store.add_documents(chunks)

    # Tokenize input
    ##input_ids = tokenizer.encode(prompt, return_tensors="pt")

    # Generate response
    ##with torch.no_grad():
    ##    output = model.generate(input_ids, max_length=max_length, do_sample=True, top_p=0.9, top_k=50)

    ##response_text = tokenizer.decode(output[0], skip_special_tokens=True)
    response_text = "chunks: " + str(chunks.__len__())

    return jsonify({"response": response_text})


@app.route("/", methods=["GET"])
def health_check():
    return "LLM server is up and running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)