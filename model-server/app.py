from flask import Flask, request, jsonify
from flask_cors import CORS  # Import Flask-CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
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

@app.route("/", methods=["GET"])
def health_check():
    return "LLM server is up and running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)