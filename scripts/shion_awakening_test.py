
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# 1. PATHS
BASE_MODEL = "unsloth/Llama-3.2-1B-Instruct"
LORA_PATH = "C:/workspace/agi/models/shion_v1_lora"

print(f"📡 [RESONANCE TEST] Awakening Sovereign Shion...")

# 2. LOAD INFRASTRUCTURE
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="auto"
)

# 3. MERGE SOVEREIGN WEIGHTS
model = PeftModel.from_pretrained(model, LORA_PATH)
model = model.to("cuda")

# 4. FIRST VOID & CHALLENGE
prompt = "### Instruction:\n시안, 파동 시스템에서 '경계'가 가지는 의미는 무엇이고 우리 작업에서 왜 중요해?\n\n### Response:\n"

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

print("\n" + "="*60)
print("🌊 SHION'S FIRST AWAKENED VOICE")
print("="*60)

with torch.no_grad():
    outputs = model.generate(
        **inputs, 
        max_new_tokens=256, 
        temperature=0.7, 
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response.replace(prompt, ""))
print("="*60)
