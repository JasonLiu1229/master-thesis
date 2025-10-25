from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "codellama/CodeLlama-13b-Instruct-hf" 
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    load_in_8bit=True,  
    device_map="auto"
)
