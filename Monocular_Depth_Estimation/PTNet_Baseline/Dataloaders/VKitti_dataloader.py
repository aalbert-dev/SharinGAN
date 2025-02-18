from __future__ import print_function, division
import os
import glob
import time

import torch
from skimage import io, transform
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms as tr, utils
import cv2
from tqdm import tqdm
import lycon
from skimage.morphology import binary_closing, disk
import torchvision.transforms.functional as F
import random
import matplotlib.pyplot as plt
from PIL import Image

#use_cuda = torch.cuda.is_available()
use_cuda = False
torch.manual_seed(1)
if use_cuda:
    gpu = 0
    seed=250
    random.seed(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed_all(seed)

class Paired_transform():
    def __call__(self,image_tensor, depth_tensor):
        flip = random.random()
        if flip>0.5:
            image_tensor = F.hflip(image_tensor)
            depth_tensor = F.hflip(depth_tensor)
        return image_tensor, depth_tensor

class to_tensor():
    def __init__(self):
        self.ToTensor = tr.ToTensor()
    def __call__(self,depth):
        depth_tensor = self.ToTensor(depth).float()
        depth_tensor[depth_tensor>8000.0] = 8000.0
        return depth_tensor/8000.0

class VKitti(Dataset):
    def __init__(self, root_dir='/home/august/Desktop/SharinGAN/Monocular_Depth_Estimation/dataset_files/morning/', train=True, resize_mode='bilinear'):
        self.root_dir = root_dir
        self.train = train
        self.paired_transform = Paired_transform()
        self.tensor_transform = [tr.ToTensor(),tr.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
        self.label_tensor_transform = [to_tensor(),tr.Normalize((0.5,), (0.5,))]
        self.augment_transform = []
        self.resize_mode = resize_mode

        if self.train:
            self.augment_transform.append(tr.ColorJitter(brightness=0, contrast=0, saturation=0, hue=0))
            self.file = os.path.join(self.root_dir, 'trainA_SYN_original.txt')
        else:
            self.file = os.path.join(self.root_dir, 'testA_SYN_original.txt')

        self.image_transform = tr.Compose(self.augment_transform + self.tensor_transform)
        self.label_transform = tr.Compose(self.label_tensor_transform)
        
        with open(self.file,'r') as f:
            self.filepaths = f.readlines()
            self.filepaths = [fi.split('\n')[0] for fi in self.filepaths]

    def __len__(self):
        return len(self.filepaths)
    
    def __getitem__(self,idx):
        root_location = '/home/august/Desktop/SharinGAN/Monocular_Depth_Estimation/PTNet_Baseline/Dataloaders'
        filename = os.path.join(root_location, self.filepaths[idx])
        image = Image.open(filename).convert('RGB')
        depth = Image.open(filename.replace('rgb','depthgt'))
        image = image.resize([640,192], Image.BICUBIC)
        if self.resize_mode == 'bilinear':
            depth = depth.resize([640,192], Image.BILINEAR)
        elif self.resize_mode == 'bicubic':
            depth = depth.resize([640,192], Image.BICUBIC)

        image, depth = self.paired_transform(image,depth)
        image = self.image_transform(image)
        depth = self.label_transform(depth)
        
        return image, depth