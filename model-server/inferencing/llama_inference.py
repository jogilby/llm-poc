# llama_inference.py
import torch
from transformers import LlamaForCausalLM, LlamaTokenizer, GenerationConfig, pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

class LlamaQA:
    def __init__(self, model_path="meta-llama/Llama-2-7b-hf", low_precision=False):
        """
        model_path: local path or huggingface repo for LLaMA weights
        low_precision: if True, use 4-bit quantization (bitsandbytes)
        """
        print("path=", model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        if low_precision:
            # 4-bit quantization
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                load_in_4bit=True,
                device_map="auto",
                torch_dtype=torch.float16
            )
        else:
            # FP16
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                torch_dtype=torch.float16
            )

        self.model.eval()
        # Create a text-generation pipeline
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device_map="auto"
        )

    def answer_question(self, question, context_chunks, max_tokens=256):
        """
        Construct a prompt using the retrieved context and question,
        then run inference to generate an answer.
        """
        context_text = "\n".join(context_chunks)
        prompt = f"""You are a helpful assistant. Use the following context to answer the question.
Context:
{context_text}

Question: {question}
Answer:
"""

        generation_config = GenerationConfig(
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            top_k=50,
        )

        outputs = self.generator(
            prompt,
            max_new_tokens=max_tokens,
            generation_config=generation_config
        )
        # The pipeline returns a list of dicts with 'generated_text'
        answer = outputs[0]["generated_text"]
        # Extract just the portion after "Answer:"
        answer_split = answer.split("Answer:")
        if len(answer_split) > 1:
            return answer_split[-1].strip()
        return answer