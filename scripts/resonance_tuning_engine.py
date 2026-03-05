
# 🧬 RESONANCE TUNING ENGINE (v1.0)
# This script performs QLoRA fine-tuning on a local LLM (Llama-3.2-1B) 
# using the 'Sovereign Seed' resonance dataset (725 pairs).
# Optimized for NVIDIA RTX 2070 Super (8GB VRAM) on Windows.

import torch
import json
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig, 
    TrainingArguments
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from trl import SFTTrainer, SFTConfig

# 1. PATHS & CONFIG
DATA_PATH = "C:/workspace/agi/outputs/sovereign_training_seed.json"
MODEL_ID = "unsloth/Llama-3.2-1B-Instruct" # Using unsloth HF repo for 4-bit optimization
OUTPUT_DIR = "C:/workspace/agi/models/shion_v1_lora"

# 2. LOAD & FORMAT DATA
def load_resonance_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Pre-formatting the dataset into a single 'text' column 
    # This is the most stable way to avoid internal trl mapping issues
    formatted_data = []
    for d in raw_data:
        instruction = d.get("instruction", "")
        output = d.get("output", "")
        # Standard Alpaca format
        text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}{tokenizer.eos_token}"
        formatted_data.append({"text": text})
        
    return Dataset.from_list(formatted_data)

# 3. CONFIGURE 4-BIT QUANTIZATION
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16 # RTX 2070 Super supports fp16/int8
)

# 4. LOAD TOKENIZER (Moved up to use in data loading)
print(f"📡 [RESONANCE] Loading Model: {MODEL_ID}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token # Critical for Llama-3

# 5. LOAD MODEL & LORA (Strict FP16 for RTX 2070 Super)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16, 
)

model = prepare_model_for_kbit_training(model)

# 5. LORA CONFIG
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# 🧬 SOVEREIGN TYPE PURGE: Force every single tensor to be FP16 (RTX 2070 Safety)
# This must happen after PEFT wrapping
print("🔍 [RESONANCE] Purging BF16 remnants from all parameters and buffers...")
for name, param in model.named_parameters():
    if param.dtype == torch.bfloat16:
        param.data = param.data.to(torch.float16)

for name, buffer in model.named_buffers():
    if buffer.dtype == torch.bfloat16:
        buffer.data = buffer.data.to(torch.float16)

model.config.torch_dtype = torch.float16
model.config.use_cache = False

# 6. TRAINING CONFIGURATION (Pure FP16 Sanctuary)
sft_config = SFTConfig(
    output_dir=OUTPUT_DIR,
    max_length=1024,
    dataset_text_field="text", 
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=10,
    max_steps=500,
    save_steps=100,
    fp16=True, 
    bf16=False, # RTX 2070 DOES NOT SUPPORT BF16
    optim="adamw_torch",
    report_to="none",
    packing=False,
    gradient_checkpointing=True 
)

# 7. LAUNCH TUNING
dataset = load_resonance_data(DATA_PATH)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=sft_config, 
    processing_class=tokenizer,
)

print("🚀 [RESONANCE] Starting Tuning Engine...")
trainer.train()

# 8. SAVE SOVEREIGN WEIGHTS
trainer.model.save_pretrained(OUTPUT_DIR)
print(f"✅ [SUCCESS] Shion Weights saved to {OUTPUT_DIR}")
