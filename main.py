import argparse
import torch
import torch.optim as optim
import torch.nn as nn
from model.model import Encoder, Decoder, BaselineModel
# from model.metric import my_metric, my_metric2
from datasets import Vocabulary
import datasets.dataloader as dataloader
from trainer import Trainer
from logger.logger import Logger
import pickle
from torchvision import transforms
from utils import *


parser = argparse.ArgumentParser(description='Show and Tell')
parser.add_argument('-lr', '--learning_rate', default=0.001, type=float,
                    help='learning rate for the model')
parser.add_argument('-b', '--batch-size', default=4, type=int,
                    help='mini-batch size (default: 4)')
parser.add_argument('-e', '--epochs', default=32, type=int,
                    help='number of total epochs (default: 32)')
parser.add_argument('--resume', default='', type=str,
                    help='path to latest checkpoint (default: none)')
parser.add_argument('--verbosity', default=2, type=int,
                    help='verbosity, 0: quiet, 1: per epoch, 2: complete (default: 2)')
parser.add_argument('--save-dir', default='model/saved', type=str,
                    help='directory of saved model (default: model/saved)')
parser.add_argument('--save-freq', default=1, type=int,
                    help='training checkpoint frequency (default: 1)')
parser.add_argument('--dataset', default="mscoco", type=str,
                    help='dataset used [mscoco | flickr8k | flickr30k | sbu | pascal]')

parser.add_argument('--embed_size', default=256, type=int,
                    help='dimension for word embedding vector')
parser.add_argument('--hidden_size', default=512, type=int,
                    help='dimension for lstm hidden layer')
parser.add_argument('--cnn_model', default="resnet18", type=str,
                    help='pretrained cnn model used')


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def main(args):

    # transform
    train_transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    #transforms.RandomCrop(224),
                    transforms.RandomHorizontalFlip(),
                    transforms.ToTensor(), 
                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    val_transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(), 
                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    vocab = dataloader.get_vocab(dataset=args.dataset)()
    # Data loader and validation split
    data_loader = dataloader.get_data_loader(dataset=args.dataset)(mode="train",
                                                                   transform=train_transform,
                                                                   vocab=vocab,
                                                                   batch_size=args.batch_size,
                                                                   shuffle=True,
                                                                   num_workers=0)
    valid_data_loader = dataloader.get_data_loader(dataset=args.dataset)(mode="val",
                                                                         transform=val_transform,
                                                                         vocab=vocab,
                                                                         batch_size=args.batch_size,
                                                                         shuffle=False,
                                                                         num_workers=0)

    # Model
    model = BaselineModel(args.embed_size, args.hidden_size, len(vocab), num_layers=1, cnn_model=args.cnn_model).to(device)
    
    model.summary()
    # A logger to store training process information
    logger = Logger()

    # Specifying loss function, metric(s), and optimizer
    loss = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)

    
    # An identifier (prefix) for saved model
    identifier = type(model).__name__ + '_'

    # Trainer instance
    trainer = Trainer(model, loss, metrics=None,
                      data_loader=data_loader,
                      valid_data_loader=valid_data_loader,
                      optimizer=optimizer,
                      epochs=args.epochs,
                      logger=logger,
                      save_dir=args.save_dir,
                      save_freq=args.save_freq,
                      resume=args.resume,
                      verbosity=args.verbosity,
                      identifier=identifier,
                      )

    # # Start training!
    trainer.train()

    # # See training history
    # print(logger)


if __name__ == '__main__':
    main(parser.parse_args())
