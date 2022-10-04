import pandas as pd
import os
import numpy as np
import cv2
import math
from statistics import mode, mean, stdev
from matplotlib import pyplot as plt
import paramiko
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

# Defining remote and local folder paths

folder_name = '' # name of experiment folder
remote_exp_folder = '' + folder_name + '/'  # folder where experiments are located (on remote server/cluster)
local_exp_folder = '' + folder_name + '\\'  # folder where you want to save all your experiments to on local computer
results_table_csv = '_' + folder_name # summary table name


# the files we are looking to copy from remote to local
log_file = 'train'  # log file we want to copy
# tensorboard_file = 'events'  # contains this at beginning of tensorboard file name
# conf_mat_file = 'conf_mat'
excel_log_file = 'csv' #'xlsx'

# Setting up remote connection requirements
port = 22
host = "" # remote host address
username = '' # username to login to remote host
password = '' # password to login to remote host
# username = input('Enter username for remote connection: ')
# password = input('Enter password for remote connection: ')  # password for remote connection
print()

# connecting to remote server (Turing)
transport = paramiko.Transport((host, port))
transport.connect(username=username, password=password)  # connect

sftp = paramiko.SFTPClient.from_transport(transport)

exp_folders_remote = sftp.listdir(remote_exp_folder)  # the experiment folders we want to search through for tensorboard and log files
# print(exp_folders_remote)

# loop through these experiment folders
local_folder_list = []
exp_folder_names_list = []
for exp_remote in exp_folders_remote:
    local_copy_folder = local_exp_folder + exp_remote + '/'  # create a local folder with the same name as the remote experiment folder
    if not os.path.isdir(local_copy_folder):  # create the local folder if doesnt already exist
        os.makedirs(local_copy_folder)
    exp_folder_names_list.append(exp_remote)
    local_folder_list.append(local_copy_folder)
    source_folder = remote_exp_folder + exp_remote + '/'  # remote experiment folder that contains tensorboard and log files
    inbound_files = sftp.listdir(source_folder)  # lists all files in the current experiment folder

    files_to_copy = []  # empty list to append files we want to copy to local (tensorboard and log file)
    # loop through all files in the experiment folder
    for file in inbound_files:
        # check if it is the log file we want to copy
        if file[0:5] == log_file:
            files_to_copy.append(file)
            # print(file)
        # check if it is the tensorboard file
        # elif file[0:6] == tensorboard_file:  # first 6 characters of tensorboard file is 'events'
        #     files_to_copy.append(file)
        #     # print(file)
        # elif file[0:8] == conf_mat_file:
        #     files_to_copy.append(file)
        elif file[-3:len(file)] == excel_log_file:
            files_to_copy.append(file)
        else:
            pass
    # copy files (Tensorboard and log file) from remote to local
    for f in files_to_copy:
        local_folder = local_copy_folder + f
        remote_folder = source_folder + f
        sftp.get(remote_folder, local_folder)

## Analyzing tensorboard folders like done in event_accu_tensorboard.py
i = 0
confirm_run_list = []
counter = 1 # variable that prints and updates to check how many experiments were found
for experiment in local_folder_list:
    file_list = os.listdir(experiment)
    csv_file = str(exp_folder_names_list[i]) + '.csv'
    i = i + 1
    for j in file_list:
        if j[-3:len(j)] == excel_log_file:
            excel_file_found = j
        else:
            pass

    excel_file = pd.read_csv(experiment + excel_file_found)

    train_loss = excel_file['Class Loss'].dropna().tolist()
    confirm_run = str(experiment[-6:-1]) + ": " + str(len(train_loss))
    confirm_run_list.append(confirm_run)
    # train_trans_loss = excel_file['Transfer Loss'].dropna().tolist()

    # for AFN specifically
    norm_loss = excel_file['Norm Loss'].dropna().tolist()
    src_feat_norm = excel_file['Source Feature Norm'].dropna().tolist()
    tgt_feat_norm = excel_file['Target Feature Norm'].dropna().tolist()
    train_tgt_acc = excel_file['Train Target Cls Acc'].dropna().tolist()

    train_src_acc = excel_file['Train Source Cls Acc'].dropna().tolist()
    # domain_acc = excel_file['Domain Acc'].dropna().tolist() ###### NOTE: train_tgt_acc is domain_acc for CDAN, copied from JAN analysis script ####
    val_loss = excel_file['Val Loss'].dropna().tolist()
    val_tgt_acc = excel_file['Val Target Acc'].dropna().tolist()
    test_loss = excel_file['Test Loss'].dropna().tolist()
    test_tgt_acc = excel_file['Test Target Acc'].dropna().tolist()

    log_train_loss = []
    for tl in train_loss:
        log_train_loss.append(math.log10(tl))

    log_norm_loss = []
    for ttl in norm_loss:
        log_norm_loss.append(math.log10(ttl))

    log_val_loss = []
    for vl in val_loss:
        log_val_loss.append(math.log10(vl))

    log_test_loss = []
    for testl in test_loss:
        log_test_loss.append(math.log10(testl))


    max_train_src_acc = max(train_src_acc)
    max_train_tgt_acc = max(train_tgt_acc)

    max_val_acc = max(val_tgt_acc)
    max_test_acc = max(test_tgt_acc)

    max_src_feat_norm = max(src_feat_norm)
    max_tgt_feat_norm = max(tgt_feat_norm)

    final_train_src_acc = train_src_acc[-1]
    final_train_tgt_acc = train_tgt_acc[-1]
    final_val_acc = val_tgt_acc[-1]
    final_test_acc = test_tgt_acc[-1]

    final_src_feat_norm = src_feat_norm[-1]
    final_tgt_feat_norm = tgt_feat_norm[-1]

    freq = 0
    ep_max_val_list = []
    ep = 1
    for vacc in val_tgt_acc:
        if vacc == max_val_acc:
            freq = freq + 1
            ep_max_val_list.append(ep)
        ep = ep + 1

    min_test_loss = min(test_loss)
    min_valid_loss = min(val_loss)
    min_train_loss = min(train_loss)
    min_norm_loss = min(norm_loss)

    mean_train_src_acc = mean(train_src_acc)
    mean_train_tgt_acc = mean(train_tgt_acc)
    mean_val_acc = mean(val_tgt_acc)
    mean_test_acc = mean(test_tgt_acc)
    mean_src_feat_norm = mean(src_feat_norm)
    mean_tgt_feat_norm = mean(tgt_feat_norm)

    # last_thresh_epochs_val_acc = val_acc_list[epoch_cutoff:]
    # thresh_mean_val_acc = mean(last_thresh_epochs_val_acc)
    # thresh_stdev_val_acc = stdev(last_thresh_epochs_val_acc)

    stdev_train_src_acc = stdev(train_src_acc)
    stdev_train_tgt_acc = stdev(train_tgt_acc)
    stdev_val_acc = stdev(val_tgt_acc)
    stdev_test_acc = stdev(test_tgt_acc)
    stdev_src_feat_norm = stdev(src_feat_norm)
    stdev_tgt_feat_norm = stdev(tgt_feat_norm)

    train_acc_src_list_ = [round(num, 2) for num in train_src_acc]  # rounded train src accuracies
    train_tgt_acc_list_ = [round(num, 2) for num in train_tgt_acc]  # rounded train tgt accuracies
    val_acc_list_ = [round(num, 2) for num in val_tgt_acc]  # rounded val accuracies
    test_acc_list_ = [round(num, 2) for num in test_tgt_acc]  # rounded val accuracies
    src_feat_norm_list_ = [round(num, 2) for num in src_feat_norm]
    tgt_feat_norm_list_ = [round(num, 2) for num in tgt_feat_norm]

    mode_train_src_acc = mode(train_acc_src_list_)
    mode_train_tgt_acc = mode(train_tgt_acc_list_)
    mode_val_acc = mode(val_acc_list_)
    mode_test_acc = mode(test_acc_list_)
    mode_src_feat_norm = mode(src_feat_norm_list_)
    mode_tgt_feat_norm = mode(tgt_feat_norm_list_)

    ################

    ###### WRITE ALL THESE METRICS TO CSV FILES, FOR EACH FOLD ######

    ################

    # avg_train_acc

    # get index of max val acc, find train acc at that index
    # new col: Train acc at max val accuracy epoch

    # print('Max TRAIN Accuracy: ', max_train_acc)
    # print('Max VALIDATION Accuracy: ', max_val_acc)
    #
    # print('Mode TRAIN Accuracy: ', mode_train_acc)
    # print('Mode VALIDATION Accuracy: ', mode_val_acc)

    df = pd.DataFrame()

    df['Train Source Accuracy'] = pd.Series(train_src_acc)
    df['Train Target Accuracy'] = pd.Series(train_tgt_acc)
    df['Validation Accuracy'] = pd.Series(val_tgt_acc)
    df['Test Accuracy'] = pd.Series(test_tgt_acc)

    df['Train Loss'] = pd.Series(train_loss)
    df['Norm Loss'] = pd.Series(norm_loss)
    df['Validation Loss'] = pd.Series(val_loss)
    df['Test Loss'] = pd.Series(test_loss)

    df['Source Feature Norm'] = pd.Series(src_feat_norm)
    df['Target Feature Norm'] = pd.Series(tgt_feat_norm)

    df['Train Log Loss'] = pd.Series(log_train_loss)
    df['Norm Log Loss'] = pd.Series(log_norm_loss)
    df['Validation Log Loss'] = pd.Series(log_val_loss)
    df['Test Log Loss'] = pd.Series(log_test_loss)

    df['Max TRAIN Source Accuracy'] = pd.Series(max_train_src_acc)
    df['Max TRAIN Target Accuracy'] = pd.Series(max_train_tgt_acc)
    df['Max VALIDATION Accuracy'] = pd.Series(max_val_acc)
    df['Max TEST Accuracy'] = pd.Series(max_test_acc)
    df['Max Source Feature Norm'] = pd.Series(max_src_feat_norm)
    df['Max Target Feature Norm'] = pd.Series(max_tgt_feat_norm)

    df['Mode TRAIN Source Accuracy'] = pd.Series(mode_train_src_acc)
    df['Mode TRAIN Target Accuracy'] = pd.Series(mode_train_tgt_acc)
    df['Mode VALIDATION Accuracy'] = pd.Series(mode_val_acc)
    df['Mode TEST Accuracy'] = pd.Series(mode_test_acc)
    df['Mode Source Feature Norm'] = pd.Series(mode_src_feat_norm)
    df['Mode Target Feature Norm'] = pd.Series(mode_tgt_feat_norm)

    df['Mean TRAIN Source Accuracy'] = pd.Series(mean_train_src_acc)
    df['Mean TRAIN Target Accuracy'] = pd.Series(mean_train_tgt_acc)
    df['Mean VALIDATION Accuracy'] = pd.Series(mean_val_acc)
    df['Mean TEST Accuracy'] = pd.Series(mean_test_acc)
    df['Mean Source Feature Norm'] = pd.Series(mean_src_feat_norm)
    df['Mean Target Feature Norm'] = pd.Series(mean_tgt_feat_norm)

    # df['Mean Thresh VALIDATION Accuracy'] = pd.Series(thresh_mean_val_acc)
    # df['STDEV Thresh VALIDATION Accuracy'] = pd.Series(thresh_stdev_val_acc)

    df['Min TRAIN Loss'] = pd.Series(min_train_loss)
    df['Min Norm Loss'] = pd.Series(min_norm_loss)
    df['Min VALIDATION Loss'] = pd.Series(min_valid_loss)
    df['Min Test Loss'] = pd.Series(min_test_loss)

    df['STDEV Train Source Accuracy'] = pd.Series(stdev_train_src_acc)
    df['STDEV Train Target Accuracy'] = pd.Series(stdev_train_tgt_acc)
    df['STDEV Valid Accuracy'] = pd.Series(stdev_val_acc)
    df['STDEV Test Accuracy'] = pd.Series(stdev_test_acc)
    df['STDEV Source Feature Norm'] = pd.Series(stdev_src_feat_norm)
    df['STDEV Target Feature Norm'] = pd.Series(stdev_tgt_feat_norm)

    df['Final TRAIN Source Accuracy'] = pd.Series(final_train_src_acc)
    df['Final TRAIN Target Accuracy'] = pd.Series(final_train_tgt_acc)
    df['Final Val Accuracy'] = pd.Series(final_val_acc)
    df['Final Test Accuracy'] = pd.Series(final_test_acc)
    df['Final Source Feature Norm'] = pd.Series(final_src_feat_norm)
    df['Final Target Feature Norm'] = pd.Series(final_tgt_feat_norm)

    # print for evaluating final val acc for tuning exps
    print("Final Val acc for tuning exps:")
    print(final_val_acc)

    df['Max Val Freq Count'] = pd.Series(freq)
    df['Max Val Epoch List'] = pd.Series(ep_max_val_list)

    df.to_csv(experiment + csv_file)

    # Plotting

    p1 = plt.figure()
    plt.plot(train_src_acc)
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Train Source Accuracy')
    plt.grid()
    plt.savefig(experiment + 'train_src_acc.jpg')

    p12 = plt.figure()
    plt.plot(train_tgt_acc)
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Train Target Accuracy')
    plt.grid()
    plt.savefig(experiment + 'train_tgt_acc.jpg')

    p2 = plt.figure()
    plt.plot(train_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Train Loss')
    plt.grid()
    plt.savefig(experiment + 'train_loss.jpg')

    p22 = plt.figure()
    plt.plot(norm_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Norm Loss')
    plt.grid()
    plt.savefig(experiment + 'norm_loss.jpg')

    p3 = plt.figure()
    plt.plot(val_tgt_acc)
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Validation Accuracy')
    plt.grid()
    plt.savefig(experiment + 'val_tgt_acc.jpg')

    p4 = plt.figure()
    plt.plot(val_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Validation Loss')
    plt.grid()
    plt.savefig(experiment + 'val_loss.jpg')

    p32 = plt.figure()
    plt.plot(test_tgt_acc)
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Test Accuracy')
    plt.grid()
    plt.savefig(experiment + 'test_tgt_acc.jpg')

    p42 = plt.figure()
    plt.plot(test_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Test Loss')
    plt.grid()
    plt.savefig(experiment + 'test_loss.jpg')

    p5 = plt.figure()
    plt.plot(log_val_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Log Loss')
    plt.title('Validation Log Loss')
    plt.grid()
    plt.savefig(experiment + 'val_log_loss.jpg')

    p52 = plt.figure()
    plt.plot(log_test_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Log Loss')
    plt.title('Test Log Loss')
    plt.grid()
    plt.savefig(experiment + 'test_log_loss.jpg')

    p6 = plt.figure()
    plt.plot(log_train_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Log Loss')
    plt.title('Train Log Loss')
    plt.grid()
    plt.savefig(experiment + 'train_log_loss.jpg')

    p62 = plt.figure()
    plt.plot(log_norm_loss)
    plt.xlabel('Epochs')
    plt.ylabel('Log Loss')
    plt.title('Norm Log Loss')
    plt.grid()
    plt.savefig(experiment + 'norm_log_loss.jpg')

    p7 = plt.figure() # colors: k, g, b, r
    plt.plot(train_src_acc, '-b', label='Train Source')
    plt.plot(train_tgt_acc, '-k', label='Train Target')
    plt.plot(val_tgt_acc, '-r', label='Valid')
    plt.plot(test_tgt_acc, '-g', label='Test')
    plt.legend(loc='lower right')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Train Valid Test Accuracy')
    plt.grid()
    plt.savefig(experiment + 'train_val_test_acc.jpg')

    p8 = plt.figure()
    plt.plot(train_loss, '-b', label='Train')
    plt.plot(norm_loss, '-k', label='Norm')
    plt.plot(val_loss, '-r', label='Valid')
    plt.plot(test_loss, '-g', label='Test')
    plt.legend(loc='upper right')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Train Valid Test Loss')
    plt.grid()
    plt.savefig(experiment + 'train_val_test_loss.jpg')

    p9 = plt.figure()
    plt.plot(log_train_loss, '-b', label='Train')
    plt.plot(log_norm_loss, '-k', label='Norm')
    plt.plot(log_val_loss, '-r', label='Valid')
    plt.plot(log_test_loss, '-g', label='Test')
    plt.legend(loc='upper right')
    plt.xlabel('Epochs')
    plt.ylabel('Log Loss')
    plt.title('Train Valid Test Log Loss')
    plt.grid()
    plt.savefig(experiment + 'train_val_test_log_loss.jpg')

    p10 = plt.figure()
    plt.plot(src_feat_norm, '-b', label='Source Feat Norm')
    plt.plot(tgt_feat_norm, '-k', label='Target Feat Norm')
    plt.legend(loc='lower right')
    plt.xlabel('Epochs')
    plt.ylabel('Feature Norm')
    plt.title('Source target Feature Norm')
    plt.grid()
    plt.savefig(experiment + 'src_tgt_feat_norm.jpg')

    print(counter)
    counter = counter + 1

####################################

# create table
df_metric_table = pd.DataFrame()
exp_combos = os.listdir(local_exp_folder)
# print(exp_combos)
# print("------------------------------")
for i in exp_combos:
    # print(i[-3:len(i)])
    if i[-3:len(i)] == 'txt' or i[-3:len(i)] == 'csv': # only look at experiment folders, ignore any text files or csv files in this local_exp_folder
        exp_combos.remove(i)
# print(exp_combos)

for folder in exp_combos:
    df_metric_table1 = pd.DataFrame()
    exp_files = os.listdir(local_exp_folder + folder)
    # print(exp_files)
    for exp_file in exp_files:
        if exp_file[0:4] == 'fold': #exp_file[-3:len(exp_file)] == 'csv':
            exp_csv = exp_file
            exp_name = exp_file #[0:-4]
# print(exp_name)
    # print(exp_csv)
    exp_df = pd.read_csv(local_exp_folder + folder + '/' + exp_csv)
    # print("LOOOOOOOOK", str(local_exp_folder + folder + '/' + exp_csv))
    max_train_src_acc = exp_df['Max TRAIN Source Accuracy'][0]
    max_train_tgt_acc = exp_df['Max TRAIN Target Accuracy'][0]
    max_valid_acc = exp_df['Max VALIDATION Accuracy'][0]
    max_test_acc = exp_df['Max TEST Accuracy'][0]
    max_src_feat_norm = exp_df['Max Source Feature Norm'][0]
    max_tgt_feat_norm = exp_df['Max Target Feature Norm'][0]

    mode_train_src_acc = exp_df['Mode TRAIN Source Accuracy'][0]
    mode_train_tgt_acc = exp_df['Mode TRAIN Target Accuracy'][0]
    mode_valid_acc = exp_df['Mode VALIDATION Accuracy'][0]
    mode_test_acc = exp_df['Mode TEST Accuracy'][0]
    mode_src_feat_norm = exp_df['Mode Source Feature Norm'][0]
    mode_tgt_feat_norm = exp_df['Mode Target Feature Norm'][0]

    mean_train_src_acc = exp_df['Mean TRAIN Source Accuracy'][0]
    mean_train_tgt_acc = exp_df['Mean TRAIN Target Accuracy'][0]
    mean_valid_acc = exp_df['Mean VALIDATION Accuracy'][0]
    mean_test_acc = exp_df['Mean TEST Accuracy'][0]
    mean_src_feat_norm = exp_df['Mean Source Feature Norm'][0]
    mean_tgt_feat_norm = exp_df['Mean Target Feature Norm'][0]

    # mean_thresh_valid_acc = exp_df['Mean Thresh VALIDATION Accuracy'][0]
    # stdev_thresh_valid_acc = exp_df['STDEV Thresh VALIDATION Accuracy'][0]

    stdev_train_src_acc = exp_df['STDEV Train Source Accuracy'][0]
    stdev_train_tgt_acc = exp_df['STDEV Train Target Accuracy'][0]
    stdev_val_acc = exp_df['STDEV Valid Accuracy'][0]
    stdev_test_acc = exp_df['STDEV Test Accuracy'][0]
    stdev_src_feat_norm = exp_df['STDEV Source Feature Norm'][0]
    stdev_tgt_feat_norm = exp_df['STDEV Target Feature Norm'][0]

    final_train_src_acc = exp_df['Final TRAIN Source Accuracy'][0]
    final_train_tgt_acc = exp_df['Final TRAIN Target Accuracy'][0]
    final_val_acc = exp_df['Final Val Accuracy'][0]
    final_test_acc = exp_df['Final Test Accuracy'][0]
    final_src_feat_norm = exp_df['Final Source Feature Norm'][0]
    final_tgt_feat_norm = exp_df['Final Target Feature Norm'][0]

    freq_max_val = exp_df['Max Val Freq Count'][0]
    epoch_list_max_val = exp_df['Max Val Epoch List'][0]

    # print(exp_df['Max VALIDATION Accuracy'][0])
    df_metric_table1['Experiment Name'] = pd.Series(exp_name)

    df_metric_table1['Max TRAIN Source Accuracy'] = pd.Series(max_train_src_acc)
    df_metric_table1['Max TRAIN Target Accuracy'] = pd.Series(max_train_tgt_acc)
    df_metric_table1['Max VALIDATION Accuracy'] = pd.Series(max_valid_acc)
    df_metric_table1['Max TEST Accuracy'] = pd.Series(max_test_acc)
    df_metric_table1['Max Source Feature Norm'] = pd.Series(max_src_feat_norm)
    df_metric_table1['Max Target Feature Norm'] = pd.Series(max_tgt_feat_norm)

    df_metric_table1['Mode TRAIN Source Accuracy'] = pd.Series(mode_train_src_acc)
    df_metric_table1['Mode TRAIN Target Accuracy'] = pd.Series(mode_train_tgt_acc)
    df_metric_table1['Mode VALIDATION Accuracy'] = pd.Series(mode_valid_acc)
    df_metric_table1['Mode TEST Accuracy'] = pd.Series(mode_test_acc)
    df_metric_table1['Mode Source Feature Norm'] = pd.Series(mode_src_feat_norm)
    df_metric_table1['Mode Target Feature Norm'] = pd.Series(mode_tgt_feat_norm)

    df_metric_table1['Mean TRAIN Source Accuracy'] = pd.Series(mean_train_src_acc)
    df_metric_table1['Mean TRAIN Target Accuracy'] = pd.Series(mean_train_tgt_acc)
    df_metric_table1['Mean VALIDATION Accuracy'] = pd.Series(mean_valid_acc)
    df_metric_table1['Mean TEST Accuracy'] = pd.Series(mean_test_acc)
    df_metric_table1['Mean Source Feature Norm'] = pd.Series(mean_src_feat_norm)
    df_metric_table1['Mean Target Feature Norm'] = pd.Series(mean_tgt_feat_norm)

    # df_metric_table1['Mean Thresh VALIDATION Accuracy'] = pd.Series(mean_thresh_valid_acc)
    # df_metric_table1['STDEV Thresh VALIDATION Accuracy'] = pd.Series(stdev_thresh_valid_acc)

    df_metric_table1['STDEV Train Source Accuracy'] = pd.Series(stdev_train_src_acc)
    df_metric_table1['STDEV Train Target Accuracy'] = pd.Series(stdev_train_tgt_acc)
    df_metric_table1['STDEV Valid Accuracy'] = pd.Series(stdev_val_acc)
    df_metric_table1['STDEV Test Accuracy'] = pd.Series(stdev_test_acc)
    df_metric_table1['STDEV Source Feature Norm'] = pd.Series(stdev_src_feat_norm)
    df_metric_table1['STDEV Target Feature Norm'] = pd.Series(stdev_tgt_feat_norm)

    df_metric_table1['Final TRAIN Source Accuracy'] = pd.Series(final_train_src_acc)
    df_metric_table1['Final TRAIN Target Accuracy'] = pd.Series(final_train_tgt_acc)
    df_metric_table1['Final Val Accuracy'] = pd.Series(final_val_acc)
    df_metric_table1['Final Test Accuracy'] = pd.Series(final_test_acc)
    df_metric_table1['Final Source Feature Norm'] = pd.Series(final_src_feat_norm)
    df_metric_table1['Final Target Feature Norm'] = pd.Series(final_tgt_feat_norm)

    df_metric_table1['Max Val Freq Count'] = pd.Series(freq_max_val)
    df_metric_table1['Max Val Epoch List'] = pd.Series(epoch_list_max_val)

    df_metric_table = pd.concat([df_metric_table1, df_metric_table], axis=0)

# df_metric_table.to_excel(local_exp_folder + results_table_csv + '_results_table.xlsx')
# print(df_metric_table)


max_train_src_accs = df_metric_table['Max TRAIN Source Accuracy'].tolist()
max_train_tgt_accs = df_metric_table['Max TRAIN Target Accuracy'].tolist()
max_val_accs = df_metric_table['Max VALIDATION Accuracy'].tolist()
max_test_accs = df_metric_table['Max TEST Accuracy'].tolist()
max_src_feat_norms = df_metric_table['Max Source Feature Norm'].tolist()
max_tgt_feat_norms = df_metric_table['Max Target Feature Norm'].tolist()

mode_train_src_accs = df_metric_table['Mode TRAIN Source Accuracy'].tolist()
mode_train_tgt_accs = df_metric_table['Mode TRAIN Target Accuracy'].tolist()
mode_val_accs = df_metric_table['Mode VALIDATION Accuracy'].tolist()
mode_test_accs = df_metric_table['Mode TEST Accuracy'].tolist()
mode_src_feat_norms = df_metric_table['Mode Source Feature Norm'].tolist()
mode_tgt_feat_norms = df_metric_table['Mode Target Feature Norm'].tolist()

mean_train_src_accs = df_metric_table['Mean TRAIN Source Accuracy'].tolist()
mean_train_tgt_accs = df_metric_table['Mean TRAIN Target Accuracy'].tolist()
mean_val_accs = df_metric_table['Mean VALIDATION Accuracy'].tolist()
mean_test_accs = df_metric_table['Mean TEST Accuracy'].tolist()
mean_src_feat_norms = df_metric_table['Mean Source Feature Norm'].tolist()
mean_tgt_feat_norms = df_metric_table['Mean Target Feature Norm'].tolist()

# mean_thresh_val_accs = df_metric_table['Mean Thresh VALIDATION Accuracy'].tolist()
# stdev_thresh_val_accs = df_metric_table['STDEV Thresh VALIDATION Accuracy'].tolist()

stdev_train_src_accs = df_metric_table['STDEV Train Source Accuracy'].tolist()
stdev_train_tgt_accs = df_metric_table['STDEV Train Target Accuracy'].tolist()
stdev_val_accs = df_metric_table['STDEV Valid Accuracy'].tolist()
stdev_test_accs = df_metric_table['STDEV Test Accuracy'].tolist()
stdev_src_feat_norms = df_metric_table['STDEV Source Feature Norm'].tolist()
stdev_tgt_feat_norms = df_metric_table['STDEV Target Feature Norm'].tolist()

final_train_src_accs = df_metric_table['Final TRAIN Source Accuracy'].tolist()
final_train_tgt_accs = df_metric_table['Final TRAIN Target Accuracy'].tolist()
final_val_accs = df_metric_table['Final Val Accuracy'].tolist()
final_test_accs = df_metric_table['Final Test Accuracy'].tolist()
final_src_feat_norms = df_metric_table['Final Source Feature Norm'].tolist()
final_tgt_feat_norms = df_metric_table['Final Target Feature Norm'].tolist()

# avgs
max_train_src_accs_avg = mean(max_train_src_accs)
max_train_tgt_accs_avg = mean(max_train_tgt_accs)
max_val_accs_avg = mean(max_val_accs)
max_test_accs_avg = mean(max_test_accs)
max_src_feat_norms_avg = mean(max_src_feat_norms)
max_tgt_feat_norms_avg = mean(max_tgt_feat_norms)

mode_train_src_accs_avg = mean(mode_train_src_accs)
mode_train_tgt_accs_avg = mean(mode_train_tgt_accs)
mode_val_accs_avg = mean(mode_val_accs)
mode_test_accs_avg = mean(mode_test_accs)
mode_src_feat_norms_avg = mean(mode_src_feat_norms)
mode_tgt_feat_norms_avg = mean(mode_tgt_feat_norms)

mean_train_src_accs_avg = mean(mean_train_src_accs)
mean_train_tgt_accs_avg = mean(mean_train_tgt_accs)
mean_val_accs_avg = mean(mean_val_accs)
mean_test_accs_avg = mean(mean_test_accs)
mean_src_feat_norms_avg = mean(mean_src_feat_norms)
mean_tgt_feat_norms_avg = mean(mean_tgt_feat_norms)

# mean_thresh_val_accs_avg = mean(mean_thresh_val_accs)
# stdev_thresh_val_accs_avg = mean(stdev_thresh_val_accs)

stdev_train_src_accs_avg = mean(stdev_train_src_accs)
stdev_train_tgt_accs_avg = mean(stdev_train_tgt_accs)
stdev_val_accs_avg = mean(stdev_val_accs)
stdev_test_accs_avg = mean(stdev_test_accs)
stdev_src_feat_norms_avg = mean(stdev_src_feat_norms)
stdev_tgt_feat_norms_avg = mean(stdev_tgt_feat_norms)

final_train_src_accs_avg = mean(final_train_src_accs)
final_train_tgt_accs_avg = mean(final_train_tgt_accs)
final_val_accs_avg = mean(final_val_accs)
final_test_accs_avg = mean(final_test_accs)
final_src_feat_norms_avg = mean(final_src_feat_norms)
final_tgt_feat_norms_avg = mean(final_tgt_feat_norms)


df_avgs = {'Experiment Name': 'AVERAGE',
           'Max TRAIN Source Accuracy': max_train_src_accs_avg,
           'Max TRAIN Target Accuracy': max_train_tgt_accs_avg,
           'Max VALIDATION Accuracy': max_val_accs_avg,
           'Max TEST Accuracy': max_test_accs_avg,
           'Max Source Feature Norm': max_src_feat_norms_avg,
           'Max Target Feature Norm': max_tgt_feat_norms_avg,

           'Mode TRAIN Source Accuracy': mode_train_src_accs_avg,
           'Mode TRAIN Target Accuracy': mode_train_tgt_accs_avg,
           'Mode VALIDATION Accuracy': mode_val_accs_avg,
           'Mode TEST Accuracy': mode_test_accs_avg,
           'Mode Source Feature Norm': mode_src_feat_norms_avg,
           'Mode Target Feature Norm': mode_tgt_feat_norms_avg,

           'Mean TRAIN Source Accuracy': mean_train_src_accs_avg,
           'Mean TRAIN Target Accuracy': mean_train_tgt_accs_avg,
           'Mean VALIDATION Accuracy': mean_val_accs_avg,
           'Mean TEST Accuracy': mean_test_accs_avg,
           'Mean Source Feature Norm': mean_src_feat_norms_avg,
           'Mean Target Feature Norm': mean_tgt_feat_norms_avg,

           # 'Mean Thresh VALIDATION Accuracy': mean_thresh_val_accs_avg,
           # 'STDEV Thresh VALIDATION Accuracy': stdev_thresh_val_accs_avg,

           'STDEV Train Source Accuracy': stdev_train_src_accs_avg,
           'STDEV Train Target Accuracy': stdev_train_tgt_accs_avg,
           'STDEV Valid Accuracy': stdev_val_accs_avg,
           'STDEV Test Accuracy': stdev_test_accs_avg,
           'STDEV Source Feature Norm': stdev_src_feat_norms_avg,
           'STDEV Target Feature Norm': stdev_tgt_feat_norms_avg,

           'Final TRAIN Source Accuracy': final_train_src_accs_avg,
           'Final TRAIN Target Accuracy': final_train_tgt_accs_avg,
           'Final Val Accuracy': final_val_accs_avg,
           'Final Test Accuracy': final_test_accs_avg,
           'Final Source Feature Norm': final_src_feat_norms_avg,
           'Final Target Feature Norm': final_tgt_feat_norms_avg
           }

df_metric_table = df_metric_table.append(df_avgs, ignore_index = True)

# stdevs
max_train_src_accs_stdev = stdev(max_train_src_accs)
max_train_tgt_accs_stdev = stdev(max_train_tgt_accs)
max_val_accs_stdev = stdev(max_val_accs)
max_test_accs_stdev = stdev(max_test_accs)
max_src_feat_norms_stdev = stdev(max_src_feat_norms)
max_tgt_feat_norms_stdev = stdev(max_tgt_feat_norms)

mode_train_src_accs_stdev = stdev(mode_train_src_accs)
mode_train_tgt_accs_stdev = stdev(mode_train_tgt_accs)
mode_val_accs_stdev = stdev(mode_val_accs)
mode_test_accs_stdev = stdev(mode_test_accs)
mode_src_feat_norms_stdev = stdev(mode_src_feat_norms)
mode_tgt_feat_norms_stdev = stdev(mode_tgt_feat_norms)

mean_train_src_accs_stdev = stdev(mean_train_src_accs)
mean_train_tgt_accs_stdev = stdev(mean_train_tgt_accs)
mean_val_accs_stdev = stdev(mean_val_accs)
mean_test_accs_stdev = stdev(mean_test_accs)
mean_src_feat_norms_stdev = stdev(mean_src_feat_norms)
mean_tgt_feat_norms_stdev = stdev(mean_tgt_feat_norms)

# mean_thresh_val_accs_stdev = stdev(mean_thresh_val_accs)
# stdev_thresh_val_accs_stdev = stdev(stdev_thresh_val_accs)

stdev_train_src_accs_stdev = stdev(stdev_train_src_accs)
stdev_train_tgt_accs_stdev = stdev(stdev_train_tgt_accs)
stdev_val_accs_stdev = stdev(stdev_val_accs)
stdev_test_accs_stdev = stdev(stdev_test_accs)
stdev_src_feat_norms_stdev = stdev(stdev_src_feat_norms)
stdev_tgt_feat_norms_stdev = stdev(stdev_tgt_feat_norms)

final_train_src_accs_stdev = stdev(final_train_src_accs)
final_train_tgt_accs_stdev = stdev(final_train_tgt_accs)
final_val_accs_stdev = stdev(final_val_accs)
final_test_accs_stdev = stdev(final_test_accs)
final_src_feat_norms_stdev = stdev(final_src_feat_norms)
final_tgt_feat_norms_stdev = stdev(final_tgt_feat_norms)


df_stdevs = {'Experiment Name': 'STDEV',
             'Max TRAIN Source Accuracy': max_train_src_accs_stdev,
             'Max TRAIN Target Accuracy': max_train_tgt_accs_stdev,
             'Max VALIDATION Accuracy': max_val_accs_stdev,
             'Max TEST Accuracy': max_test_accs_stdev,
             'Max Source Feature Norm': max_src_feat_norms_stdev,
             'Max Target Feature Norm': max_tgt_feat_norms_stdev,

             'Mode TRAIN Source Accuracy': mode_train_src_accs_stdev,
             'Mode TRAIN Target Accuracy': mode_train_tgt_accs_stdev,
             'Mode VALIDATION Accuracy': mode_val_accs_stdev,
             'Mode TEST Accuracy': mode_test_accs_stdev,
             'Mode Source Feature Norm': mode_src_feat_norms_stdev,
             'Mode Target Feature Norm': mode_tgt_feat_norms_stdev,

             'Mean TRAIN Source Accuracy': mean_train_src_accs_stdev,
             'Mean TRAIN Target Accuracy': mean_train_tgt_accs_stdev,
             'Mean VALIDATION Accuracy': mean_val_accs_stdev,
             'Mean TEST Accuracy': mean_test_accs_stdev,
             'Mean Source Feature Norm': mean_src_feat_norms_stdev,
             'Mean Target Feature Norm': mean_tgt_feat_norms_stdev,

             # 'Mean Thresh VALIDATION Accuracy': mean_thresh_val_accs_stdev,
             # 'STDEV Thresh VALIDATION Accuracy': stdev_thresh_val_accs_stdev,

             'STDEV Train Source Accuracy': stdev_train_src_accs_stdev,
             'STDEV Train Target Accuracy': stdev_train_tgt_accs_stdev,
             'STDEV Valid Accuracy': stdev_val_accs_stdev,
             'STDEV Test Accuracy': stdev_test_accs_stdev,
             'STDEV Source Feature Norm': stdev_src_feat_norms_stdev,
             'STDEV Target Feature Norm': stdev_tgt_feat_norms_stdev,

             'Final TRAIN Source Accuracy': final_train_src_accs_stdev,
             'Final TRAIN Target Accuracy': final_train_tgt_accs_stdev,
             'Final Val Accuracy': final_val_accs_stdev,
             'Final Test Accuracy': final_test_accs_stdev,
             'Final Source Feature Norm': final_src_feat_norms_stdev,
             'Final Target Feature Norm': final_tgt_feat_norms_stdev
             }

df_metric_table = df_metric_table.append(df_stdevs, ignore_index = True)

df_metric_table.to_excel(local_exp_folder + results_table_csv + '_results_table.xlsx')

print()
print("CONFIRM ALL EPOCHS RAN FOR ALL FOLDS:")
print(confirm_run_list)
print()

# print("Summary of Results to report for: " + str(results_table_csv))
# print("Final TRAIN Source Accuracy: " + str(round(final_train_src_accs_avg,2)) + " +/- " + str(round(final_train_src_accs_stdev,2)))
# print("Final Domain Accuracy: " + str(round(final_domain_accs_avg,2)) + " +/- " + str(round(final_domain_accs_stdev,2)))
# print("Final Val Accuracy: " + str(round(final_val_accs_avg,2)) + " +/- " + str(round(final_val_accs_stdev,2)))
# print("Final Test Accuracy: " + str(round(final_test_accs_avg,2)) + " +/- " + str(round(final_test_accs_stdev,2)))

print("Summary of Results to report for: " + str(results_table_csv))
print(str(round(final_train_src_accs_avg,2)) + " +/- " + str(round(final_train_src_accs_stdev,2)))
print(str(round(final_train_tgt_accs_avg,2)) + " +/- " + str(round(final_train_tgt_accs_stdev,2)))
print(str(round(final_val_accs_avg,2)) + " +/- " + str(round(final_val_accs_stdev,2)))
print(str(round(final_test_accs_avg,2)) + " +/- " + str(round(final_test_accs_stdev,2)))
# print(str(round(final_src_feat_norms_avg,2)) + " +/- " + str(round(final_src_feat_norms_stdev,2)))
# print(str(round(final_tgt_feat_norms_avg,2)) + " +/- " + str(round(final_tgt_feat_norms_stdev,2)))
