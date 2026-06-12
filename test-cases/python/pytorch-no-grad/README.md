# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Wrap the inference loop in `torch.no_grad()` context manager to disable gradient computation tracking, which is unnecessary during inference and wastes memory and CPU cycles
- Expected energy saving when running this file 1.000 times
