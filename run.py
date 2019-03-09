#!/usr/bin/env python3

import sys
import pandas as pd
import ntpath
import torch
import argparse
import train
from torch.optim.lr_scheduler import StepLR

from model.SCUNet import Generator
from torch.optim.lr_scheduler import StepLR
from pickle import UnpicklingError
from exceptions import StopTrainingException
from preprocess import prepare_dataset

parser = argparse.ArgumentParser(description='U-Net model for music source separation')
subparsers = parser.add_subparsers(dest='mode')

train_p = subparsers.add_parser('train')
train_p.add_argument('-d', '--data_path', required=True,
                     help='path to your preprocessed CSV data file')
train_p.add_argument('-e', '--epochs', default='5', help='Number of epochs to train', type=int)
train_p.add_argument('--lr', default=None, help='Learning Rate', type=float)
train_p.add_argument('--batch_size', default=3, help='Batch Size', type=int)
train_p.add_argument('--model_weight_name', default='model_weights.pt', help='file name of Model Weights', type=str)
train_p.add_argument('--log_dir', default=None, help='Dir for logs', type=str)
train_p.add_argument('--log_name', default=None, help='Name for this experiment\'s log', type=str)
train_p.add_argument('--pretrained_model', default='', help='file name of PreTrained Weights to be loaded', type=str)
train_p.add_argument('--train_info_file', default=None, help='File to store training info', type=str)

gpu_group = train_p.add_mutually_exclusive_group()
gpu_group.add_argument('--cpu', action='store_true', help='train on CPU')
gpu_group.add_argument('--gpu', action='store_false', help='train on GPU')

preprocess_p = subparsers.add_parser('preprocess')
preprocess_p.add_argument('-d', '--data_path', required=True, help='path to your data directory')
preprocess_p.add_argument('-s', '--data_subset', required=True,
                          help='path to your CSV file linking paths of mixes and sources')
preprocess_p.add_argument('-o', '--out_dir', default='./numpy_data', help='Directory to save processed data')
preprocess_p.add_argument('-p', '--processed_csv_dir', default='./processed_dataset.csv',
                          help='Path to save processed CSV')

args = vars(parser.parse_args())

def main():
    args = vars(parser.parse_args())
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if args['mode'] == 'preprocess':
        # Read audio files once and store them with numpy extension for quicker processing during training
        # Make PREPARATION_NEEDED=True if dataset is new/changed, else set it False
        prepare_dataset(args['data_path'], args['data_subset'], args['out_dir'], args['processed_csv_dir'])
    elif args['mode'] == 'train':
        # Defining model
        model = Generator(1)

        # If pre-trained weights are specified, load them:
        if args['pretrained_model']:
            try:
                model.load_state_dict(torch.load(args['pretrained_model']))
            except (UnpicklingError, FileNotFoundError) as e:
                print(e)
                print('The pretrained model path is not correct!')
                return
        # Start training
        train.train(model,
                    args['data_path'],
                    scheduler=StepLR,
                    gpu=args['gpu'],
                    epochs=args['epochs'],
                    lr=args['lr'],
                    batch_size=args['batch_size'],
                    model_weight_name=args['model_weight_name'],
                    log_dir=args['log_dir'],
                    log_name=args['log_name'],
                    train_info_file=args['train_info_file'])

if __name__ == "__main__":
    try:
        main()
    except StopTrainingException as e:
        print (e)
