import copy
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum

import torch
from peft import PeftModel
from prompts import SYSTEM_INSTRUCTION
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig,
)


class ModelStyle(Enum):
    LlamaInstruct = "inst"
    Plain = "plain"


@dataclass
class LocalUsage:
    """Token counts + latency for a local model generation call."""

    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


_llm_model = None  # singleton
_model_lock = threading.Lock()


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
        self._gen_config = None

    @torch.inference_mode()
    def generate(
        self,
        prompt,
        max_new_tokens=256,
        temperature=0.25,
        top_p=0.85,
        top_k=5,
        do_sample=False,
        sys_instruction: str = SYSTEM_INSTRUCTION,
    ) -> str:
        """Generate text. Returns only the response string (backwards compatible)."""
        text, _ = self.generate_with_usage(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=do_sample,
            sys_instruction=sys_instruction,
        )
        return text

    @torch.inference_mode()
    def generate_with_usage(
        self,
        prompt,
        max_new_tokens=256,
        temperature=0.25,
        top_p=0.85,
        top_k=5,
        do_sample=False,
        sys_instruction: str = SYSTEM_INSTRUCTION,
    ) -> tuple[str, LocalUsage]:
        """
        Generate text and return (response_text, LocalUsage).

        Token counts come from the tokenizer directly so they are exact,
        not estimated, important for comparing local vs. API model costs
        in the thesis.
        """
        with _model_lock:
            assert self.model is not None, "Model not loaded."
            assert self.tokenizer is not None, "Tokenizer not loaded."

            formatted_prompt = self._build_model_input(
                prompt, sys_instruction=sys_instruction
            )
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            prompt_tokens: int = inputs["input_ids"].shape[1]

            if not self._gen_config:
                self._gen_config = GenerationConfig(
                    do_sample=do_sample,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                )

            t0 = time.perf_counter()
            outputs = self.model.generate(
                **inputs.to(self.model.device),
                max_new_tokens=max_new_tokens,
                generation_config=copy.deepcopy(self._gen_config),
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            latency_ms = (time.perf_counter() - t0) * 1000

            generated_ids = outputs[0][inputs["input_ids"].shape[1] :]
            completion_tokens: int = generated_ids.shape[0]

            text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            usage = LocalUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=round(latency_ms, 1),
            )

            return text.strip(), usage

    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer

    def get_device(self):
        return self.device

    def _tokenize_prompt(self, user_prompt: str, sys_instruction: str):
        # Qwen chat template path: tokenize directly
        if "qwen" in self.model_id.lower() and getattr(
            self.tokenizer, "chat_template", None
        ):
            messages = [
                {"role": "system", "content": sys_instruction},
                {"role": "user", "content": user_prompt.strip()},
            ]
            try:
                return self.tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    tokenize=True,
                    return_tensors="pt",
                )
            except TypeError:
                text = self.tokenizer.apply_chat_template(
                    messages, add_generation_prompt=True, tokenize=False
                )
                return self.tokenizer(text, return_tensors="pt")

        formatted = self._build_model_input(
            user_prompt, sys_instruction=sys_instruction
        )
        return self.tokenizer(formatted, return_tensors="pt")

    def load_model(self, model_path, quantize: str = "int4"):
        _enable_speed_flags()

        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        quantization_config = None
        if torch.cuda.is_available() and quantize == "int4":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
        elif torch.cuda.is_available() and quantize == "int8":
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)

        load_kwargs = dict(
            device_map="auto",
            low_cpu_mem_usage=True,
        )

        if quantization_config is None:
            load_kwargs["torch_dtype"] = torch_dtype
        else:
            load_kwargs["quantization_config"] = quantization_config

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, **load_kwargs
        ).eval()

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

    def load_local_model(self, local_model_path):
        assert os.path.exists(
            local_model_path
        ), f"Model path does not exists: {local_model_path}"

        self.tokenizer = AutoTokenizer.from_pretrained(local_model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            local_model_path, torch_dtype="auto", device_map="auto"
        ).eval()

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

    def _build_model_input(
        self,
        user_prompt: str,
        sys_instruction: str = "You are a helpful coding assistant.",
    ) -> str:
        if "qwen" in self.model_id.lower() and getattr(
            self.tokenizer, "chat_template", None
        ):
            messages = [
                {"role": "system", "content": sys_instruction},
                {"role": "user", "content": user_prompt.strip()},
            ]
            return self.tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=False
            )
        if self.model_style == ModelStyle.LlamaInstruct:
            return f"[INST] <<SYS>>\n{sys_instruction}\n<</SYS>>\n\n{user_prompt.strip()} [/INST]"
        return user_prompt.strip()

    def _postprocess(self, full_decoded_text: str, full_prompt: str) -> str:
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


def get_local_model(local_model_path, adapter=None) -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        print("Loading local LLM model into memory...")
        m = LLM_Model()
        try:
            m.load_model(local_model_path)
            if adapter:
                m.model = PeftModel.from_pretrained(m.model, adapter).eval()
            m.set_model(m.model, local_model_path, m.tokenizer)
        except Exception as e:
            print(f"Error loading local model {local_model_path}: {e}")
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

    response, usage = llm_model.generate_with_usage(prompt)
    print(response)
    print(f"Prompt tokens:     {usage.prompt_tokens}")
    print(f"Completion tokens: {usage.completion_tokens}")
    print(f"Latency:           {usage.latency_ms} ms")
    print(
        f"Tokens/sec:        {usage.completion_tokens / (usage.latency_ms / 1000):.1f}"
    )
