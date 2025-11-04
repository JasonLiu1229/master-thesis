from enum import Enum

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class ModelStyle(Enum):
    LlamaInstruct = (
        "inst"  # instruction-tuned LLaMA style models, makes use of [INST] tags
    )
    Plain = "plain"

_llm_model = None  # singleton

class LLM_Model:
    def __init__(self, device=None):
        self.model = None
        self.tokenizer = None
        self.model_id = None

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model_style: ModelStyle = None

    def generate(self, prompt, max_new_tokens=200, temperature=0.7, top_p=0.9):

        assert (
            self.model is not None
        ), "Model not loaded. Please load a model before generating text."
        assert (
            self.tokenizer is not None
        ), "Tokenizer not loaded. Please load a tokenizer before generating text."

        formatted_prompt = self._build_model_input(prompt)

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        response = self._postprocess(response, formatted_prompt)
        return response

    def get_model(self):
        return self.model
    
    def get_tokenizer(self):
        return self.tokenizer
    
    def get_device(self):
        return self.device

    def load_model(self, model_path):
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)i

        if self.tokenizer.pad_token_id is None:
            # fallback: use eos as pad
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.model.generation_config.pad_token_id = self.tokenizer.pad_token_id

        self.model_id = model_path
        self.model_style = self._infer_model_style(model_path)

    def set_model(self, model, model_name, tokenizer):
        """
        Set the model, model_name and tokenizer

        This is useful when loading a model from a local path or custom source.
        For example, after fine-tuning a model, you can set the model directly.

        Args:
            model: The model instance to set.
            model_name: The name or identifier of the model.
            tokenizer: The tokenizer instance to set.
        """
        self.model = model.to(self.device)
        self.tokenizer = tokenizer

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.model.generation_config.pad_token_id = self.tokenizer.pad_token_id

        self.model_id = model_name
        self.model_style = self._infer_model_style(model_name)

    def _infer_model_style(self, model_name: str):
        name = model_name.lower()

        if "codellama" in name and "instruct" in name:
            return ModelStyle.LlamaInstruct
        if "llama" in name and "instruct" in name:
            return ModelStyle.LlamaInstruct

        return ModelStyle.Plain

    def _build_model_input(self, user_prompt: str) -> str:
        if self.model_style == ModelStyle.LlamaInstruct:
            system_msg = (
                "You are a helpful, honest, coding-aware assistant. "
                "Answer as clearly as possible."
            )
            return f"[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n{user_prompt.strip()} [/INST]"

        return user_prompt.strip()

    def _postprocess(self, full_decoded_text: str, full_prompt: str) -> str:
        """
        Try to cut off the original prompt and any boilerplate so that
        we only keep the assistant's answer.
        Different models echo the full prompt before starting the answer.
        """

        text = full_decoded_text

        if text.startswith(full_prompt):
            text = text[len(full_prompt) :]

        text = text.lstrip()

        stop_markers = [
            "[INST]",
            "</s>",
        ]

        for marker in stop_markers:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx]

        return text

def get_model(model_id) -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        print("Loading LLM model into memory...")
        m = LLM_Model()
        m.load_model(model_id)
        _llm_model = m
    return _llm_model

if __name__ == "__main__":
    model_id = "codellama/CodeLlama-13b-hf"

    llm_model = get_model(model_id)

    prompt = (
        "Hello, this is a test prompt for the LLM model. Are you working correctly?"
    )
    
    response = llm_model.generate(prompt)
    print(response)
