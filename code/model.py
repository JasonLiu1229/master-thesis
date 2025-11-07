from enum import Enum

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class ModelStyle(Enum):
    LlamaInstruct = "inst"
    Plain = "plain"


_llm_model = None  # singleton


def _enable_speed_flags():
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True


# GPT helped with optimizing loading and inference settings
class LLM_Model:
    def __init__(self, device=None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model = None
        self.tokenizer = None
        self.model_id = None
        self.model_style: ModelStyle = None

    @torch.inference_mode()
    def generate(
        self, prompt, max_new_tokens=256, temperature=0.2, top_p=0.9, do_sample=False, sys_role: str = "You are a helpful coding assistant."
    ):
        assert self.model is not None, "Model not loaded."
        assert self.tokenizer is not None, "Tokenizer not loaded."

        formatted_prompt = self._build_model_input(prompt, sys_role=sys_role)
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt")

        outputs = self.model.generate(
            **inputs.to(self.model.device),
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature,
            top_p=top_p,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        return text.strip()
    
    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer

    def get_device(self):
        return self.device

    def load_model(self, model_path):
        _enable_speed_flags()

        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        load_kwargs = dict(
            torch_dtype=torch_dtype, device_map="auto", low_cpu_mem_usage=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)
        self.model.eval()

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)

        if "qwen" in model_path.lower():
            if self.tokenizer.eos_token is None:
                self.tokenizer.eos_token = "<|im_end|>"
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = getattr(
                    self.tokenizer, "unk_token", "<|extra_0|>"
                )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.model.generation_config.pad_token_id = self.tokenizer.pad_token_id

        self.model_id = model_path
        self.model_style = self._infer_model_style(model_path)

        self._warmup()

    @torch.inference_mode()
    def _warmup(self):
        try:
            prompt = "Hello"
            formatted = self._build_model_input(prompt)
            inputs = self.tokenizer(formatted, return_tensors="pt").to(
                self.model.device
            )
            _ = self.model.generate(
                **inputs, max_new_tokens=4, do_sample=False, use_cache=True
            )
        except Exception:
            pass

    def set_model(self, model, model_name, tokenizer):
        self.model = model
        self.model.eval()
        self.tokenizer = tokenizer
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.model.generation_config.pad_token_id = self.tokenizer.pad_token_id
        self.model_id = model_name
        self.model_style = self._infer_model_style(model_name)
        self._warmup()

    def _infer_model_style(self, model_name: str):
        name = model_name.lower()
        if "qwen" in name:
            return ModelStyle.Plain
        if "codellama" in name and "instruct" in name:
            return ModelStyle.LlamaInstruct
        if "llama" in name and "instruct" in name:
            return ModelStyle.LlamaInstruct
        return ModelStyle.Plain

    def _build_model_input(self, user_prompt: str, sys_role:str = "You are a helpful coding assistant.") -> str:
        if "qwen" in self.model_id.lower() and getattr(self.tokenizer, "chat_template", None):
            messages = [
                {"role": "system", "content": sys_role},
                {"role": "user", "content": user_prompt.strip()},
            ]

            return self.tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=False
            )
        if self.model_style == ModelStyle.LlamaInstruct:
            system_msg = "You are a helpful, honest, coding-aware assistant. Answer as clearly as possible."
            return f"[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n{user_prompt.strip()} [/INST]"
        return user_prompt.strip()

    def _postprocess(self, full_decoded_text: str, full_prompt: str) -> str:
        # No-op
        return full_decoded_text

def get_model(model_id) -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        print("Loading LLM model into memory...")
        m = LLM_Model()
        try:
            m.load_model(model_id)
        except Exception as e:
            print(f"Error loading model {model_id}: {e}")
            raise
        _llm_model = m
    return _llm_model


def update_model(model: LLM_Model):
    global _llm_model
    _llm_model = model


if __name__ == "__main__":
    model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"

    llm_model = get_model(model_id)

    prompt = (
        "Hello, this is a test prompt for the LLM model. Are you working correctly?"
    )

    response = llm_model.generate(prompt)
    print(response)
