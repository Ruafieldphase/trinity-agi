
import torch
import json
import os
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig, 
    Trainer, 
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. CONSTANTS
MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"
DATA_PATH = "C:/workspace/agi/outputs/sovereign_training_seed.json"
OUTPUT_DIR = "C:/workspace/agi/models/shion_v1_lora"

# 2. SEED PREPARATION
def prepare_resonance_dataset(path, tokenizer):
    with open(path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    def tokenize_function(example):
        text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}{tokenizer.eos_token}"
        return tokenizer(text, truncation=True, max_length=1024, padding="max_length")

    dataset = Dataset.from_list(raw_data)
    tokenized_dataset = dataset.map(tokenize_function, remove_columns=dataset.column_names)
    return tokenized_dataset

# 3. ENGINE INITIALIZATION
print(f"📡 [RESONANCE] Initializing 2070 Super Engine...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16, # RTX 2070 Optimized
    bnb_4bit_use_double_quant=True
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16 # Hard-force FP16
)

model = prepare_model_for_kbit_training(model)

# 4. LORA BOUNDARY CONFIG
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# 5. TRAINING ARGUMENTS (Stable Version)
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    max_steps=300, # Focused short burst for efficiency
    logging_steps=10,
    save_steps=100,
    fp16=True, # Strictly use FP16
    bf16=False, # RTX 2070 Safety
    optim="adamw_torch",
    remove_unused_columns=False,
    report_to="none"
)

# 6. EXECUTE RESONANCE
dataset = prepare_resonance_dataset(DATA_PATH, tokenizer)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)

print("🚀 [RESONANCE] Starting Sovereign Training...")
trainer.train()

# 7. SAVE MANIFESTATION
model.save_pretrained(OUTPUT_DIR)
print(f"✅ [SUCCESS] Sovereign Weights evolved at {OUTPUT_DIR}")
