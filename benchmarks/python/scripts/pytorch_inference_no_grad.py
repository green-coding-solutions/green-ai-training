import time
import torch
import torch.nn as nn

class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 10),
        )

    def forward(self, x):
        return self.layers(x)

N = 10_000
model = MLP()
model.eval()
inputs = torch.randn(1, 512)

with torch.no_grad():
    for _ in range(N):
        output = model(inputs)

print(f"{time.time_ns()} inferences={N}")
