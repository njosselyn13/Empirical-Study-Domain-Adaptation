import random
import time
import warnings
import sys
import argparse
import shutil
import os
import csv
import pandas as pd
import os.path as osp

start_time = time.time()

import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.optim import SGD
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader
import torchvision.transforms as T
import torch.nn.functional as F

sys.path.append('../../..')
from dalib.modules.domain_discriminator import DomainDiscriminator
from dalib.adaptation.dann import DomainAdversarialLoss, ImageClassifier

# import common.vision.datasets as datasets
from torchvision import datasets

import common.vision.models as models
from common.vision.transforms import ResizeImage
from common.utils.data import ForeverDataIterator
from common.utils.metric import accuracy, ConfusionMatrix
from common.utils.meter import AverageMeter, ProgressMeter
from common.utils.logger import CompleteLogger
from common.utils.analysis import collect_feature, tsne, a_distance

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("DEVICE:")
print(device)
print()

def main(args: argparse.Namespace):
    logger = CompleteLogger(args.log, args.phase)
    print(args)

    progressFilePath = args.log + "/" + "log_file_" + str(args.log[-1]) + ".csv"

    if not os.path.isfile(progressFilePath):
        with open(progressFilePath, "w") as outputfile:
            writer = csv.DictWriter(outputfile, lineterminator='\n',
                                    fieldnames=["Epoch", "Train Loss", "Train Transfer Loss", "Train Cls Loss", "Train Source Cls Acc",
                                                "Domain Acc", "Val Loss", "Val Target Acc", "Test Loss", "Test Target Acc"])
            writer.writeheader()

    if args.seed is not None:
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        cudnn.deterministic = True
        warnings.warn('You have chosen to seed training. '
                      'This will turn on the CUDNN deterministic setting, '
                      'which can slow down your training considerably! '
                      'You may see unexpected behavior when restarting '
                      'from checkpoints.')

    cudnn.benchmark = True

    # Data loading code
    normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    if args.center_crop:
        train_transform = T.Compose([
            ResizeImage(256),
            T.CenterCrop(224),
            T.RandomHorizontalFlip(),
            T.ToTensor(),
            normalize
        ])
    else:
        train_transform = T.Compose([
            ResizeImage(256),
            T.RandomResizedCrop(224),
            T.RandomHorizontalFlip(),
            T.ToTensor(),
            normalize
        ])
    val_transform = T.Compose([
        ResizeImage(256),
        T.CenterCrop(224),
        T.ToTensor(),
        normalize
    ])

    # dataset = datasets.__dict__[args.data]
    # train_source_dataset = dataset(root=args.root, task=args.source, download=True, transform=train_transform)
    # train_source_loader = DataLoader(train_source_dataset, batch_size=args.batch_size,
    #                                  shuffle=True, num_workers=args.workers, drop_last=True)
    # train_target_dataset = dataset(root=args.root, task=args.target, download=True, transform=train_transform)
    # train_target_loader = DataLoader(train_target_dataset, batch_size=args.batch_size,
    #                                  shuffle=True, num_workers=args.workers, drop_last=True)
    #
    # val_dataset = dataset(root=args.root, task=args.target, download=True, transform=val_transform)
    # val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    #
    # if args.data == 'DomainNet':
    #     test_dataset = dataset(root=args.root, task=args.target, split='test', download=True, transform=val_transform)
    #     test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    # else:
    #     test_loader = val_loader

    ###########
    ###########
    # Copied code for data loading from updated CDAN


    # dataset = datasets.__dict__[args.data]
    # train_source_dataset = dataset(root=args.root, task=args.source, download=True, transform=train_transform)
    root_dir = args.root
    task_source = args.source
    if task_source == "amazon" or task_source == "dslr" or task_source == "webcam":
        path_source = root_dir + "train/" + task_source + "/images"
        print("Source Path: ", path_source)
        num_class = len(os.listdir(root_dir + "train/" + task_source + "/images/"))
    elif task_source == "indoor" or task_source == "outdoor":
        path_source = root_dir + "train/" + task_source
        print("Source Path: ", path_source)
        num_class = len(os.listdir(root_dir + "train/" + task_source + "/"))
    else:
        path_source = root_dir + "train/" + task_source
        print("Source Path: ", path_source)
        num_class = len(os.listdir(root_dir + "train/" + task_source + "/"))
    train_source_dataset = datasets.ImageFolder(path_source, transform=train_transform)
    train_source_loader = DataLoader(train_source_dataset, batch_size=args.batch_size,
                                     shuffle=True, num_workers=args.workers, drop_last=True)

    # train_target_dataset = dataset(root=args.root, task=args.target, download=True, transform=train_transform)
    task_target = args.target
    if task_target == "amazon" or task_target == "dslr" or task_target == "webcam":
        path_target = root_dir + "train/" + task_target + "/images"
        print("Target Path: ", path_target)
    elif task_target == "outdoor" or task_target == "indoor":
        path_target = root_dir + "train/" + task_target
        print("Target Path: ", path_target)
    else:
        path_target = root_dir + "train/" + task_target
        print("Target Path: ", path_target)
    train_target_dataset = datasets.ImageFolder(path_target, transform=train_transform)
    train_target_loader = DataLoader(train_target_dataset, batch_size=args.batch_size,
                                     shuffle=True, num_workers=args.workers, drop_last=True)

    # val_dataset = dataset(root=args.root, task=args.target, download=True, transform=val_transform)
    task_target_val = args.target
    if task_target_val == "amazon" or task_target_val == "dslr" or task_target_val == "webcam":
        path_target_val = root_dir + "val/" + task_target_val + "/images"
    elif task_target_val == "indoor" or task_target_val == "outdoor":
        path_target_val = root_dir + "val/" + task_target_val
    else:
        path_target_val = root_dir + "val/" + task_target_val
    val_dataset = datasets.ImageFolder(path_target_val, transform=val_transform)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)

    if args.data == 'DomainNet':
        # test_dataset = dataset(root=args.root, task=args.target, split='test', download=True, transform=val_transform)
        task_target_test = args.target

        # path_test = root_dir + "test/" + task_target_test
        path_test = '../../../../../../copy_DomainNet_all_correct/DomainNet/cross_val_folds/' + "test/" + task_target_test

        print("Path Test: ", path_test)
        test_dataset = datasets.ImageFolder(path_test, transform=val_transform)
        test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    elif args.data == 'ARL':
        print("ARL")
        task_target_test = args.target
        path_test = '../../../../../../ARL_data/cross_val_folds/' + "test/" + task_target_test
        test_dataset = datasets.ImageFolder(path_test, transform=val_transform)
        test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    else:
        print('OFFICE31')
        task_target_test = args.target
        path_test = '../../../../../../Office31/Original_images/cross_val_folds/'+ "test/" + task_target_test + "/images"
        # if task_target_test == "amazon" or task_target_test == "dslr" or task_target_test == "webcam":
        #     path_test = root_dir + "test/" + task_target_test + "/images"
        # else:
        #     path_test = root_dir + "test/" + task_target_test
        test_dataset = datasets.ImageFolder(path_test, transform=val_transform)
        test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
        # test_loader = val_loader


    train_source_iter = ForeverDataIterator(train_source_loader)
    train_target_iter = ForeverDataIterator(train_target_loader)

    # create model
    print("=> using pre-trained model '{}'".format(args.arch))
    backbone = models.__dict__[args.arch](pretrained=True)

    # num_classes = train_source_dataset.num_classes
    num_classes = num_class
    print()
    print("NUM CLASSES:")
    print(num_classes)
    print()

    # DELETE THIS -- for TSNE ANALYSIS ONLY
    # num_classes=345

    classifier = ImageClassifier(backbone, num_classes, bottleneck_dim=args.bottleneck_dim).to(device)
    domain_discri = DomainDiscriminator(in_feature=classifier.features_dim, hidden_size=1024).to(device)

    # define optimizer and lr scheduler
    optimizer = SGD(classifier.get_parameters() + domain_discri.get_parameters(),
                    args.lr, momentum=args.momentum, weight_decay=args.weight_decay, nesterov=True)
    lr_scheduler = LambdaLR(optimizer, lambda x:  args.lr * (1. + args.lr_gamma * float(x)) ** (-args.lr_decay))

    # define loss function
    domain_adv = DomainAdversarialLoss(domain_discri).to(device)

    # resume from the best checkpoint
    if args.phase != 'train':
        checkpoint = torch.load(logger.get_checkpoint_path('best'), map_location='cpu')
        classifier.load_state_dict(checkpoint)

    # analysis the model
    if args.phase == 'analysis':
        # extract features from both domains
        feature_extractor = nn.Sequential(classifier.backbone, classifier.bottleneck).to(device)
        source_feature = collect_feature(train_source_loader, feature_extractor, device)
        target_feature = collect_feature(train_target_loader, feature_extractor, device)
        # plot t-SNE
        tSNE_filename = osp.join(logger.visualize_directory, 'TSNE.png')
        tsne.visualize(source_feature, target_feature, tSNE_filename)
        print("Saving t-SNE to", tSNE_filename)
        # calculate A-distance, which is a measure for distribution discrepancy
        A_distance = a_distance.calculate(source_feature, target_feature, device)
        print("A-distance =", A_distance)
        return

    if args.phase == 'test':
        acc1, loss_val = validate(test_loader, classifier, args)
        print(acc1)
        return

    # start training
    best_acc1 = 0.
    for epoch in range(args.epochs):

        # train for one epoch
        loss_record, trans_loss_record, cls_loss_record, cls_acc_record, domain_acc_record = train(train_source_iter, train_target_iter, classifier, domain_adv, optimizer,
              lr_scheduler, epoch, args)

        # evaluate on validation set
        acc1, loss_val = validate(val_loader, classifier, args)

        testacc1, test_loss_val = validate(test_loader, classifier, args)

        # remember best acc@1 and save checkpoint
        torch.save(classifier.state_dict(), logger.get_checkpoint_path('latest'))
        if acc1 > best_acc1:
            shutil.copy(logger.get_checkpoint_path('latest'), logger.get_checkpoint_path('best'))
        best_acc1 = max(acc1, best_acc1)

        with open(progressFilePath, "a") as outputfile:  # create csv if not already made
            writer = csv.DictWriter(outputfile, lineterminator='\n',
                                    fieldnames=["Epoch", "Train Loss", "Train Transfer Loss", "Train Cls Loss", "Train Source Cls Acc",
                                                "Domain Acc", "Val Loss", "Val Target Acc", "Test Loss", "Test Target Acc"])  # define headers
            writer.writerow(
                {"Epoch": epoch, "Train Loss": loss_record, "Train Transfer Loss": trans_loss_record, "Train Cls Loss": cls_loss_record, "Train Source Cls Acc": cls_acc_record, "Domain Acc": domain_acc_record,
                 "Val Loss": loss_val, "Val Target Acc": acc1, "Test Loss": test_loss_val, "Test Target Acc": testacc1})


    print("best_acc1 = {:3.1f}".format(best_acc1))

    # evaluate on test set
    classifier.load_state_dict(torch.load(logger.get_checkpoint_path('best')))
    acc1, loss_val = validate(test_loader, classifier, args)
    print("test_acc1 = {:3.1f}".format(acc1))

    print("Experiment Total Time: ")
    print("--- %s seconds ---" % (time.time() - start_time))
    print()
    print("-----------------------")
    print()

    logger.close()


def train(train_source_iter: ForeverDataIterator, train_target_iter: ForeverDataIterator,
          model: ImageClassifier, domain_adv: DomainAdversarialLoss, optimizer: SGD,
          lr_scheduler: LambdaLR, epoch: int, args: argparse.Namespace):
    batch_time = AverageMeter('Time', ':5.2f')
    data_time = AverageMeter('Data', ':5.2f')
    losses = AverageMeter('Loss', ':6.2f')
    cls_accs = AverageMeter('Cls Acc', ':3.1f')
    domain_accs = AverageMeter('Domain Acc', ':3.1f')
    trans_losses = AverageMeter('Trans Loss', ':5.4f')
    cls_losses = AverageMeter('Cls Loss', ':5.4f')

    progress = ProgressMeter(
        args.iters_per_epoch,
        [batch_time, data_time, losses, trans_losses, cls_losses, cls_accs, domain_accs],
        prefix="Epoch: [{}]".format(epoch))

    # switch to train mode
    model.train()
    domain_adv.train()

    end = time.time()

    for i in range(args.iters_per_epoch):
        x_s, labels_s = next(train_source_iter)
        x_t, _ = next(train_target_iter)

        x_s = x_s.to(device)
        x_t = x_t.to(device)
        labels_s = labels_s.to(device)

        # measure data loading time
        data_time.update(time.time() - end)

        # compute output
        x = torch.cat((x_s, x_t), dim=0)
        y, f = model(x)
        y_s, y_t = y.chunk(2, dim=0)
        f_s, f_t = f.chunk(2, dim=0)

        cls_loss = F.cross_entropy(y_s, labels_s)
        transfer_loss = domain_adv(f_s, f_t)
        domain_acc = domain_adv.domain_discriminator_accuracy
        loss = cls_loss + transfer_loss * args.trade_off

        cls_acc = accuracy(y_s, labels_s)[0]

        losses.update(loss.item(), x_s.size(0))
        cls_accs.update(cls_acc.item(), x_s.size(0))
        domain_accs.update(domain_acc.item(), x_s.size(0))
        trans_losses.update(transfer_loss.item(), x_s.size(0)) # not included in original code, copied from cdan in case i need??????
        cls_losses.update(cls_loss.item(), x_s.size(0))


        # compute gradient and do SGD step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        lr_scheduler.step()

        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()

        if i % args.print_freq == 0:
            progress.display(i)

    return losses.avg, trans_losses.avg, cls_losses.avg, cls_accs.avg, domain_accs.avg


def validate(val_loader: DataLoader, model: ImageClassifier, args: argparse.Namespace) -> float:
    batch_time = AverageMeter('Time', ':6.3f')
    losses = AverageMeter('Loss', ':.4e')
    top1 = AverageMeter('Acc@1', ':6.2f')
    top5 = AverageMeter('Acc@5', ':6.2f')
    progress = ProgressMeter(
        len(val_loader),
        [batch_time, losses, top1, top5],
        prefix='Test: ')

    # switch to evaluate mode
    model.eval()
    if args.per_class_eval:
        classes = val_loader.dataset.classes
        confmat = ConfusionMatrix(len(classes))
    else:
        confmat = None

    with torch.no_grad():
        end = time.time()
        for i, (images, target) in enumerate(val_loader):
            images = images.to(device)
            target = target.to(device)

            # compute output
            output, _ = model(images)
            loss = F.cross_entropy(output, target)

            # measure accuracy and record loss
            acc1, acc5 = accuracy(output, target, topk=(1, 5))
            if confmat:
                confmat.update(target, output.argmax(1))
            losses.update(loss.item(), images.size(0))
            top1.update(acc1.item(), images.size(0))
            top5.update(acc5.item(), images.size(0))

            # measure elapsed time
            batch_time.update(time.time() - end)
            end = time.time()

            if i % args.print_freq == 0:
                progress.display(i)

        print(' * Acc@1 {top1.avg:.3f} Acc@5 {top5.avg:.3f}'
              .format(top1=top1, top5=top5))
        if confmat:
            print(confmat.format(classes))

    return top1.avg, losses.avg


if __name__ == '__main__':
    architecture_names = sorted(
        name for name in models.__dict__
        if name.islower() and not name.startswith("__")
        and callable(models.__dict__[name])
    )

    # dataset_names = sorted(
    #     name for name in datasets.__dict__
    #     if not name.startswith("__") and callable(datasets.__dict__[name])
    # )

    parser = argparse.ArgumentParser(description='DANN for Unsupervised Domain Adaptation')
    # dataset parameters
    parser.add_argument('root', metavar='DIR',
                        help='root path of dataset')
    parser.add_argument('-d', '--data', metavar='DATA', default='Office31',
                        help='dataset: ') # + ' | '.join(dataset_names) +
                             # ' (default: Office31)')
    parser.add_argument('-s', '--source', help='source domain(s)')
    parser.add_argument('-t', '--target', help='target domain(s)')
    parser.add_argument('--center-crop', default=False, action='store_true',
                        help='whether use center crop during training')
    # model parameters
    parser.add_argument('-a', '--arch', metavar='ARCH', default='resnet18',
                        choices=architecture_names,
                        help='backbone architecture: ' +
                             ' | '.join(architecture_names) +
                             ' (default: resnet18)')
    parser.add_argument('--bottleneck-dim', default=256, type=int,
                        help='Dimension of bottleneck')
    parser.add_argument('--trade-off', default=1., type=float,
                        help='the trade-off hyper-parameter for transfer loss')
    # training parameters
    parser.add_argument('-b', '--batch-size', default=32, type=int,
                        metavar='N',
                        help='mini-batch size (default: 32)')
    parser.add_argument('--lr', '--learning-rate', default=0.01, type=float,
                        metavar='LR', help='initial learning rate', dest='lr')
    parser.add_argument('--lr-gamma', default=0.001, type=float, help='parameter for lr scheduler')
    parser.add_argument('--lr-decay', default=0.75, type=float, help='parameter for lr scheduler')
    parser.add_argument('--momentum', default=0.9, type=float, metavar='M',
                        help='momentum')
    parser.add_argument('--wd', '--weight-decay',default=1e-3, type=float,
                        metavar='W', help='weight decay (default: 1e-3)',
                        dest='weight_decay')
    parser.add_argument('-j', '--workers', default=2, type=int, metavar='N',
                        help='number of data loading workers (default: 4)')
    parser.add_argument('--epochs', default=20, type=int, metavar='N',
                        help='number of total epochs to run')
    parser.add_argument('-i', '--iters-per-epoch', default=1000, type=int,
                        help='Number of iterations per epoch')
    parser.add_argument('-p', '--print-freq', default=100, type=int,
                        metavar='N', help='print frequency (default: 100)')
    parser.add_argument('--seed', default=None, type=int,
                        help='seed for initializing training. ')
    parser.add_argument('--per-class-eval', action='store_true',
                        help='whether output per-class accuracy during evaluation')
    parser.add_argument("--log", type=str, default='dann',
                        help="Where to save logs, checkpoints and debugging images.")
    parser.add_argument("--phase", type=str, default='train', choices=['train', 'test', 'analysis'],
                        help="When phase is 'test', only test the model."
                             "When phase is 'analysis', only analysis the model.")
    args = parser.parse_args()
    main(args)

