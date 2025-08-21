from peft import LoraConfig, get_peft_model
from transformers import TrainingArguments, Trainer

from model import model, tokenizer
from data_loader import create_dataset_from_jsonl
from data_preprocess import preprocess

# Load the dataset
train_dataset = create_dataset_from_jsonl("data/train")
eval_dataset = create_dataset_from_jsonl("data/eval")
test_dataset = create_dataset_from_jsonl("data/test")

# Preprocess the dataset
train_data = preprocess(train_dataset)
eval_data = preprocess(eval_dataset)
test_data = preprocess(test_dataset)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj","v_proj"],  # good default for LLaMA
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

training_args = TrainingArguments(
    output_dir="./code-llama-finetuned",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    logging_steps=10,
    num_train_epochs=3,
    save_strategy="epoch",
    fp16=True,
    evaluation_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=eval_data,
    tokenizer=tokenizer
)

def train():
    """Train the model using the Trainer API."""
    trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(training_args.output_dir)
    print("Training complete. Model and tokenizer saved.")
