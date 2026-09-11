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
cd Neve_benchmarks
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
Second Benchmark (Frost & Networks Libs)

Reinstall the frost library (setup.sh erases the include.nv content). Also, install the networks lib.

```
nsm r NoSavedDATA/frost
nsm i NoSavedDATA/frost
nsm i NoSavedDATA/networks
```

Now run the ResNet with cuDNN implementation.

```
time neve neve_samples/resnet_frost.nv
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
