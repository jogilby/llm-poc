# huggingface_qa_inference.py
from transformers import pipeline

class ExtractiveQAPipeline:
    def __init__(self, model_name="deepset/roberta-base-squad2"):
        self.qa_pipeline = pipeline("question-answering", model=model_name, tokenizer=model_name)

    def answer_question(self, question, context_chunks):
        """
        For extractive QA, we can just pick the best chunk, or search across them.
        We'll do a simple approach: pick the chunk with the highest score.
        """
        best_answer = None
        best_score = float("-inf")

        for chunk in context_chunks:
            result = self.qa_pipeline(question=question, context=chunk)
            if result["score"] > best_score:
                best_score = result["score"]
                best_answer = result["answer"]

        return best_answer