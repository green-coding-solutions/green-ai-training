import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

p = argparse.ArgumentParser()
p.add_argument("--base_model", required=True)
p.add_argument("--lora", required=True)
p.add_argument("--output", required=True)
a = p.parse_args()

base = AutoModelForCausalLM.from_pretrained(
    a.base_model,
    torch_dtype=torch.float16,
    device_map="auto",
    local_files_only=True,
)

model = PeftModel.from_pretrained(
    base, a.lora, local_files_only=True
)
model = model.merge_and_unload(safe_merge=True)
model.save_pretrained(a.output, safe_serialization=True)

tokenizer = AutoTokenizer.from_pretrained(
    a.base_model, local_files_only=True
)
tokenizer.save_pretrained(a.output)
