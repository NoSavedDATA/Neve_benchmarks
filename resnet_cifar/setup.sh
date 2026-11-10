#!/bin/bash
set -e

echo "Downloading CIFAR-10 dataset..."
wget -q --show-progress https://data.pjreddie.com/files/cifar.tgz
tar -xzf cifar.tgz
rm cifar.tgz

echo "Applying Frost include.nv workaround..."
rm ~/.local/neve/lib/frost/include.nv
touch ~/.local/neve/lib/frost/include.nv

echo "----------------------------------------"
echo "Setup complete! You can now run the benchmark:"
echo "time neve neve_samples/all_in_one.nv"
