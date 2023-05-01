import os

try:
    os.mkdir('train_data/')
    os.mkdir('val_data/')
    os.mkdir('train_data/pic')
    os.mkdir('val_data/pic')
except:
    pass