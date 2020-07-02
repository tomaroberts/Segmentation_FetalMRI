#
# Dataloaders
#
# Author: Irina Grigorescu
# Date:      28-05-2020
#
# File with Data loaders for training/testing
#

from __future__ import print_function, division
import os
import torch
import torchio
from torchvision.transforms import Compose
import numpy as np
import pandas as pd
import nibabel as nib
from torch.utils.data import Dataset


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class LocalisationDataLoader(Dataset):
    """
    Localisation dataset for semantic segmentation
    """

    def __init__(self, csv_file, root_dir, is_augment=False, shuffle=True, transform=None):
        """
        Constructor
        :param csv_file: Path to the csv file with file locations and file names
        :param root_dir: Path to data
        :param shuffle: if True reshuffles indices for every get item
        :param transform: optional transform to be applied
        """
        self.data_file = pd.read_csv(csv_file)
        self.input_folder = root_dir
        self.shuffle = shuffle
        self.indices = np.arange(len(self.data_file))  # indices of the data [0 ... N-1]
        self.transform = transform
        self.is_augment = is_augment

        # Normalisation
        # -- Z-Normalisation
        to_znorm = torchio.transforms.ZNormalization()
        # -- Rescaling between 0 and 1
        to_rescl = torchio.transforms.RescaleIntensity(out_min_max=(0.0, 1.0))
        # Put them all together
        self.preprocessing = Compose([to_znorm, to_rescl])

        # Augmentation
        self.to_motion = torchio.transforms.RandomMotion(degrees=2.0,
                                                         translation=2.0,  # 3.0
                                                         num_transforms=1,
                                                         p=0.25,
                                                         seed=None)
        self.to_spike = torchio.transforms.RandomSpike(num_spikes=1,
                                                       intensity=0.2,
                                                       p=0.2,
                                                       seed=None)
        self.to_affine = torchio.transforms.RandomAffine(scales=(0.5, 1.5),
                                                         degrees=(180),
                                                         isotropic=True,
                                                         default_pad_value='minimum')

        self.shuffle_indices()

    def __len__(self):
        """
        Number of elements per epoch
        :return:
        """
        return len(self.data_file)

    def __getitem__(self, item):
        if torch.is_tensor(item):
            item = item.tolist()

        self.shuffle_indices()
        item = self.indices[item]

        # Get image and lab names:
        img_name = os.path.join(self.input_folder,
                                self.data_file.iloc[item, 0])
        lab_name = os.path.join(self.input_folder,
                                self.data_file.iloc[item, 1])

        # Read data:
        subject = torchio.Subject(
            t2w=torchio.Image(img_name, torchio.INTENSITY),
            label=torchio.Image(lab_name, torchio.LABEL),
        )
        dataset = torchio.ImagesDataset([subject])

        # Pre process subject
        transformed_subj = self.preprocessing(dataset[0])

        # Augment subject
        transformed_subj = self.augment_data(transformed_subj)

        # Create sample
        img_ = transformed_subj['t2w']['data'][0, :, :, :].numpy().astype(np.float32)
        lab_ = transformed_subj['label']['data'][0, :, :, :].numpy().astype(np.float32)
        lab_ = np.abs((lab_ - np.min(lab_)) / (np.max(lab_) - np.min(lab_) + 1e-6))
        lab_[lab_ >= 0.5] = 1.0
        lab_[lab_ < 0.5] = 0.0
        img_aff = transformed_subj['t2w']['affine']
        lab_aff = transformed_subj['label']['affine']
        subj_name = self.data_file.iloc[item, 0].split('.nii')[0]

        # Create sample_img:
        sample = {'image': img_,
                  'lab': lab_,
                  'name': subj_name,
                  'img_aff': img_aff,
                  'seg_aff': lab_aff}

        # Transform
        if self.transform:
            sample = self.transform(sample)

        return sample

    def augment_data(self, subject):
        """
        Augmentation
        """
        if self.is_augment:
            # Choose to do motion, spike or both
            augmentation_choice = np.random.choice([0, 1, 2, 3])
            if augmentation_choice == 0:
                aug_img = Compose([self.to_affine])(subject)
            elif augmentation_choice == 1:
                aug_img = Compose([self.to_motion])(subject)
            elif augmentation_choice == 2:
                aug_img = Compose([self.to_spike])(subject)
            else:
                aug_img = Compose([self.to_affine, self.to_motion])(subject)

            return aug_img
        else:
            return subject

    def shuffle_indices(self):
        """
        Shuffle indices in case self.shuffle is True
        :return: nada de nada
        """
        if self.shuffle:
            np.random.shuffle(self.indices)
        else:
            self.indices = np.arange(len(self.data_file))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class RandomCrop2D(object):
    """
    Randomly crop the image and label in a sample_img
    """

    def __init__(self, output_size, is_random=True):
        self.is_random = is_random

        # Check it's instance of a tuple or int
        assert isinstance(output_size, (int, tuple))

        # If int make into a tuple
        if isinstance(output_size, int):
            self.output_size = (output_size, output_size, output_size)
        # Else check it has 3 sizes
        else:
            assert len(output_size) == 3
            self.output_size = output_size

    def __call__(self, sample):
        image, lab = sample['image'], sample['lab']

        # Get image size
        h, w, d = image.shape[:3]

        # New sizes for the image
        new_h, new_w, new_d = self.output_size

        # Pad image in case new_i > i
        pad_value = np.min(image)
        if new_h >= h:
            pad_ = (new_h - h) // 2 + 1
            image = np.pad(image, ((pad_, pad_), (0, 0), (0, 0)), 'constant', constant_values=pad_value)
            lab = np.pad(lab, ((pad_, pad_), (0, 0), (0, 0)), 'constant', constant_values=pad_value)

        if new_w >= w:
            pad_ = (new_w - w) // 2 + 1
            image = np.pad(image, ((0, 0), (pad_, pad_), (0, 0)), 'constant', constant_values=pad_value)
            lab = np.pad(lab, ((0, 0), (pad_, pad_), (0, 0)), 'constant', constant_values=pad_value)

        h, w, d = image.shape[:3]

        if self.is_random:
            # Get patch starting point
            patch_x = np.random.randint(0, h - new_h)
            patch_y = np.random.randint(0, w - new_w)

        else:
            # Calculate centre of mass
            coords_x, coords_y, coords_z = np.meshgrid(np.arange(0, w) - (w - 1) / 2,
                                                       np.arange(0, h) - (h - 1) / 2,
                                                       np.arange(0, d) - (d - 1) / 2)
            coords_x = np.round(np.mean(coords_x * np.sum(lab, axis=0)) + (h - 1) / 2)
            coords_y = np.round(np.mean(coords_y * np.sum(lab, axis=0)) + (w - 1) / 2)

            print(coords_x, coords_y)

            # Calculate start point of patch
            patch_y = 0 if (int(coords_x - new_h // 2) < 0 or int(coords_x + new_h // 2) >= h) \
                else int(coords_x - new_h // 2)
            patch_x = 0 if (int(coords_y - new_w // 2) < 0 or int(coords_y + new_w // 2) >= w) \
                else int(coords_y - new_w // 2)

        # Create new image
        image = image[patch_x: patch_x + new_h,
                      patch_y: patch_y + new_w,
                      :]
        # Create new lab
        lab = lab[patch_x: patch_x + new_h,
                  patch_y: patch_y + new_w,
                  :]

        return {'image': image,
                'lab': lab,
                'name': sample['name'],
                'img_aff': sample['img_aff'],
                'seg_aff': sample['seg_aff']}


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class ToTensor(object):
    """Convert ndarrays in sample_img to Tensors."""

    def __call__(self, sample):

        # Expanding for batch size
        image_ = np.expand_dims(sample['image'], 0).astype(dtype=np.float32)
        lab_ = np.expand_dims(sample['lab'], 0).astype(dtype=np.float32)

        # Transform to Pytorch tensor
        sample = {'image': (torch.from_numpy(image_)).float(),
                  'lab': (torch.from_numpy(lab_)).float(),
                  'name': sample['name'],
                  'img_aff': sample['img_aff'],
                  'seg_aff': sample['seg_aff']}

        return sample
