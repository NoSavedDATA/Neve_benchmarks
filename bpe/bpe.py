import re
import sentencepiece as spm
from pathlib import Path
import time
import os
import time
import threading
import psutil

import os
import time
import threading
import psutil
import resource

_process = psutil.Process(os.getpid())

_running = False
_thread = None
_lock = threading.Lock()

_peak_rss = 0
_total_rss = 0
_samples = 0

SAMPLE_INTERVAL = 0.005  # 5 ms


def _sampler():
    global _peak_rss
    global _total_rss
    global _samples

    while _running:
        rss = _process.memory_info().rss

        if rss > _peak_rss:
            _peak_rss = rss

        _total_rss += rss
        _samples += 1

        time.sleep(SAMPLE_INTERVAL)


def memp_start():
    global _running
    global _thread
    global _peak_rss
    global _total_rss
    global _samples

    with _lock:
        if _running:
            return

        _peak_rss = 0
        _total_rss = 0
        _samples = 0

        _running = True

        _thread = threading.Thread(
            target=_sampler,
            daemon=True
        )

        _thread.start()


def memp_end():
    global _running

    with _lock:
        if not _running:
            return

        _running = False

    _thread.join()

    avg_rss = _total_rss / max(_samples, 1)

    # Linux: ru_maxrss is KB
    os_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

    def gb(x):
        return x / 1024 / 1024 / 1024

    print(f"Peak RSS (sampled): {gb(_peak_rss):.2f} GB")
    print(f"Peak RSS (OS):      {gb(os_peak):.2f} GB")
    print(f"Average RSS:        {gb(avg_rss):.2f} GB")

# =========================
# CONFIG
# =========================

INPUT_FILE = "/Datasets/openwebtxt/openwebtext.txt"
CLEAN_FILE = "clean.txt"

K = 1000000          # number of lines to read
T = 32000           # vocab size
# K = 100000          # number of lines to read
# T = 15000           # vocab size

MODEL_PREFIX = "bpe_model"

# =========================
# PREPROCESSING
# =========================

st = 0
# remove punctuation
PUNCT_RE = re.compile(r"[^\w\s]+")

def clean_text(line: str) -> str:
    # keep only ascii chars < 128
    line = ''.join(c for c in line if ord(c) < 128)

    # lowercase
    line = line.lower()

    # remove punctuation
    line = PUNCT_RE.sub("", line)

    # normalize spaces
    line = " ".join(line.split())

    return line


def build_clean_corpus():
    count = 0

    with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as fin:
        with open(CLEAN_FILE, "w", encoding="utf-8") as fout:

            for line in fin:
                if count >= K:
                    break

                line = clean_text(line)

                if line:
                    fout.write(line + "\n")

                count += 1

    print("processed lines:", count)


# =========================
# TRAIN SENTENCEPIECE BPE
# =========================

def train_bpe():
    memp_start()
    spm.SentencePieceTrainer.train(
        input=CLEAN_FILE,
        model_prefix=MODEL_PREFIX,
        vocab_size=T,
        model_type="bpe",
        character_coverage=1.0,
        normalization_rule_name="identity",
        split_by_whitespace=True,
        byte_fallback=False,
        train_extremely_large_corpus=False,
        num_threads=1
    )
    memp_end()

    print("training complete")


# =========================
# TEST ENCODE
# =========================

def test():
    sp = spm.SentencePieceProcessor()
    sp.load(f"{MODEL_PREFIX}.model")

    text = "hello world this is a tokenizer test"

    ids = sp.encode(text)

    pieces = sp.encode(text, out_type=str)

    print("ids:", ids)
    print("pieces:", pieces)


# =========================
# MAIN
# =========================

def eval(line_offset=0, eval_sample_size=2000):
    sp = spm.SentencePieceProcessor()
    sp.load(f"{MODEL_PREFIX}.model")
    all_toks_n, all_chars_n = 0, 0
    print(f"Start eval")
    with open("/Datasets/openwebtxt/openwebtext_val.txt", 'r') as f:
        i = 0
        for line in f:
            i+=1
            if i<line_offset:
                continue
            if i>line_offset+eval_sample_size:
                break
            if i%100==0:
                print("i: ", i)
            for sentence in line.split('.'):
                ids = sp.encode(sentence)
                all_toks_n += len(ids)
                all_chars_n += len(sentence)

    ratio = all_toks_n / all_chars_n
    print(f"Ratio {ratio}")


if __name__ == "__main__":
    st = time.time()
    build_clean_corpus()
    txt_time = time.time()-st 
    train_st = time.time()
    train_bpe()
    train_time = time.time()-train_st
    test()
    print(f"train time: {time.time()-st}")
    eval_st = time.time()
    eval()
    eval_time = time.time()-eval_st
    print(f"Preprocess time: {txt_time}")
    print(f"Train time: {train_time}")
    print(f"Eval time: {eval_time}")
    print(f"Script time: {time.time()-st}")
