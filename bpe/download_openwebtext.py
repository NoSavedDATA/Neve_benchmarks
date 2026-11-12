import os
from datasets import load_dataset

print("Loading stream...")
dataset = iter(load_dataset("Skylion007/openwebtext", split="train", streaming=True))

print("Writing train split (1M rows)...")
with open("/Datasets/openwebtxt/openwebtext.txt", "w", encoding="utf-8") as f:
    for _ in range(1000002):
        f.write(next(dataset)["text"].replace("\n", " ") + "\n")

print("Writing val split (15k rows)...")
with open("/Datasets/openwebtxt/openwebtext_val.txt", "w", encoding="utf-8") as f:
    for _ in range(15002):
        f.write(next(dataset)["text"].replace("\n", " ") + "\n")

print("Done!")

os._exit(0)
