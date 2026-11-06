# Deep Learning from Scratch in 1400 Lines (ResNet-18 Experiment)

## Requirements

- Cuda 12.3 compatible GPU
- Docker

Tested inside Linux, you may adapt pre-docker steps

---
## Install Steps

Run a Docker to guarantee the GPU lib compatibility. Create a local folder first as the experiment volume path.

```
cd ~/
git clone https://github.com/NoSavedDATA/Neve_benchmarks.git
cd Neve_benchmarks/resnet_cifar
docker build -t neve-frost .
docker run --gpus all -v ~/Neve_benchmarks:/frost_exp/Neve_benchmarks -it neve-frost bash
```


Install the Frost package using Neve packet manager
```
nsm i NoSavedDATA/frost
```

Download Cifar-10 and remove frost function prototypes to avoid conflicts
```
chmod +x setup.sh
./setup.sh
```

Run experiment
```
time neve neve_samples/all_in_one.nv
```

- It took around 10 minutes to run 20k steps with a RTX 4090.
- Feel free to change the hyperparammeters in neve_samples/all_in_one.nv

---
## Results

3 seeds in a RTX 4090.

| Language | Acc | Time | Backend |
| :--- | :--- | :--- | :--- |
| **Neve** | 75.4%+-0.70 | 359+-2s | Naive Kernel |
| **Neve** | 74.39%+-1.35 | 47+-1s | Partial cuDNN |
| **PyTorch** | 74.82%+-1.27 | 64s+-6s | cuDNN |

I got similar results in the [old NSK paper](https://arxiv.org/pdf/2409.11600). That early Neve version had most of the Deep Learning framework implemented in C++ and CUDA throught interop. Now almost everything is implemented in high-level Neve.

Naive GPU kernels must be substituted by kernels with Matrix Multiplications in order to better match cuDNN behaviour.

---

## Second Benchmark (Frost & Networks Libs)

Reinstall the frost library (setup.sh erases the include.nv content). Also, install the networks lib.

```
nsm r frost
nsm i NoSavedDATA/frost NoSavedDATA/networks
```

Now run the ResNet with cuDNN implementation.

```
time neve neve_samples/resnet_frost.nv
```


---
## Third Benchmark (PyTorch)

```
pip install -r requirements.txt
```

```
time python3 pytorch_samples/resnet_cifar10.py 
```

---
## Limitations
- Neve binary currently only works in Linux;
- Ultra-rare GC crashes.

---
## Future work
- Improve tensor abstractions;
- Asses GANs, audio networks and LLMs;
- Neve flash-attention.

