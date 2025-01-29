from flask import Flask, request, jsonify
import logging
from flask_cors import CORS  # Import Flask-CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
from vectorization.pdf_processing import pdf_to_text_chunks
from vectorization.indexing import PDFVectorStore
from inferencing.huggingface_qa_inference import ExtractiveQAPipeline
from inferencing.llama_inference import LlamaQA
import torch

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# Configure Flask's logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
app.logger.setLevel(logging.INFO)


# Load the model and tokenizer
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

@app.route("/generate", methods=["POST"])
def generate():
    app.logger.info("generate called")
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


    # (Alternatively, for a smaller QA model)
    qa_model = ExtractiveQAPipeline(model_name="deepset/roberta-base-squad2")

    # 5. Retrieve top chunks from the vector store
    top_chunks = vector_store.search(prompt, top_k=6)
    #print("found chunks\n", top_chunks)
    # 6. Generate an answer using LLaMA (or the smaller QA model)
    ##answer = llama_qa.answer_question(user_question, top_chunks)
    response_text = qa_model.answer_question(prompt, top_chunks)  # if using extractive QA

    # Tokenize input
    ##input_ids = tokenizer.encode(prompt, return_tensors="pt")

    # Generate response
    ##with torch.no_grad():
    ##    output = model.generate(input_ids, max_length=max_length, do_sample=True, top_p=0.9, top_k=50)

    ##response_text = tokenizer.decode(output[0], skip_special_tokens=True)    

    return jsonify({"response": response_text})


@app.route("/queryllm", methods=["POST"])
def queryllm():
    app.logger.info("queryllm called")
    data = request.json
    prompt = data.get("prompt", "")
    max_length = data.get("max_length", 50)

    # Vectorize the file into memory
    # 1. Build or load your vector store
    vector_store = PDFVectorStore(embedding_model="all-MiniLM-L6-v2")

    # 2. Process and index PDF files
    pdf_files = ["/app/vectorization/1-G0.5ArchSpecs.pdf"]#, "/app/vectorization/2-CaliberExhibits.pdf"]
    for pdf_file in pdf_files:
        chunks = pdf_to_text_chunks(pdf_file, chunk_size=5000, overlap=500)        
        vector_store.add_documents(chunks)


    # (Alternatively, for a smaller QA model)
    large_model = LlamaQA()

    # 5. Retrieve top chunks from the vector store
    top_chunks = vector_store.search(prompt, top_k=6)
    
    # 6. Generate an answer using LLaMA (or the smaller QA model)
    ##answer = llama_qa.answer_question(user_question, top_chunks)
    response_text = large_model.answer_question(prompt, top_chunks)  # if using extractive QA

    # Tokenize input
    ##input_ids = tokenizer.encode(prompt, return_tensors="pt")

    # Generate response
    ##with torch.no_grad():
    ##    output = model.generate(input_ids, max_length=max_length, do_sample=True, top_p=0.9, top_k=50)

    ##response_text = tokenizer.decode(output[0], skip_special_tokens=True)    

    return jsonify({"response": response_text})


@app.route("/checkup", methods=["GET"])
def hardware_check():
    result = " isavailable=" + str(torch.cuda.is_available())  # Should return True
    result += " device_count=" + str(torch.cuda.device_count())  # Should return the number of GPUs
    result += " get_device_name=" + str(torch.cuda.get_device_name(0))  # Should print the GPU model
    return result

@app.route("/", methods=["GET"])
def health_check():
    return "LLM server is up and running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)