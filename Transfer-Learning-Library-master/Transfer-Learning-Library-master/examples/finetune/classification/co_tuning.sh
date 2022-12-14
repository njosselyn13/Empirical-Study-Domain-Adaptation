#!/usr/bin/env bash
# Supervised Pretraining
# CUB-200-2011
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 100 --seed 0 --log logs/co_tuning/cub200_100
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 50 --seed 0 --log logs/co_tuning/cub200_50
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 30 --seed 0 --log logs/co_tuning/cub200_30
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 15 --seed 0 --log logs/co_tuning/cub200_15

# Standford Cars
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 100 --seed 0 --log logs/co_tuning/car_100
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 50 --seed 0 --log logs/co_tuning/car_50
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 30 --seed 0 --log logs/co_tuning/car_30
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 15 --seed 0 --log logs/co_tuning/car_15

# Aircrafts
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 100 --seed 0 --log logs/co_tuning/aircraft_100
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 50 --seed 0 --log logs/co_tuning/aircraft_50
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 30 --seed 0 --log logs/co_tuning/aircraft_30
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 15 --seed 0 --log logs/co_tuning/aircraft_15

# MoCo (Unsupervised Pretraining)
#CUB-200-2011
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 100 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cub200_100 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 50 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cub200_50 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 30 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cub200_30 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/cub200 -d CUB200 -sr 15 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cub200_15 --pretrained checkpoints/moco_v1_200ep_backbone.pth

# Standford Cars
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 100 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cars_100 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 50 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cars_50 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 30 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cars_30 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/stanford_cars -d StanfordCars -sr 15 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/cars_15 --pretrained checkpoints/moco_v1_200ep_backbone.pth

# Aircrafts
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 100 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/aircraft_100 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 50 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/aircraft_50 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 30 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/aircraft_30 --pretrained checkpoints/moco_v1_200ep_backbone.pth
CUDA_VISIBLE_DEVICES=0 python co_tuning.py data/aircraft -d Aircraft -sr 15 --seed 0 --lr 0.1 -i 2000 --lr-decay-epochs 3 6 9 --epochs 12 \
  --log logs/moco_pretrain_co_tuning/aircraft_15 --pretrained checkpoints/moco_v1_200ep_backbone.pth
