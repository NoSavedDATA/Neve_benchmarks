```bash
cd ~/
git clone https://github.com/NoSavedDATA/Neve_benchmarks
cd Neve_benchmarks/net
docker build -t neve_sockets .
docker run --name neve --gpus all --network host -v ~/Neve_benchmarks:/frost_exp/Neve_benchmarks -it neve_sockets bash
```

Run Neve server

```bash
neve server.nv
```

Open another terminal without the docker instance and run wrk.

To install wrk
```bash
# arch install
sudo pacman -S wrk
# ubuntu install
apt update && apt install wrk
```
Then run
```bash
# two threads, each with two connections
wrk -t2 -c2 -d30s -s boxplot.lua http://127.0.0.1:8080/
# 12 threads with 1000 connections
wrk -t12 -c1000 -d30s -s boxplot.lua http://127.0.0.1:8080/
```


Evaluate Go
```bash
go build -o server net_bench.go
./server
```
Then run one of the wrk commands
