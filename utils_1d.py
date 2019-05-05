# basic library imports
import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy import random
from tqdm import tqdm

# pandas setting 
pd.set_option('display.max_columns', None)  
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', -1)
pd.options.display.max_rows = 5000

# encoding the classes
from sklearn.preprocessing import LabelEncoder

# librosa for audion feature extraction
import librosa
import gc
import pickle
import random
from multiprocessing import Pool
from PIL import Image
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split

# plotly libraries
import plotly.graph_objs as go
from plotly import tools
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
init_notebook_mode(connected=True)
import plotly_express as px


# keras components for constructing the model
import tensorflow as tf
from tensorflow.keras import optimizers, losses, activations, models
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, LearningRateScheduler
from tensorflow.keras.layers import (Dense, Input, Dropout, Convolution1D, 
MaxPool2D, GlobalMaxPool1D, GlobalAveragePooling1D, concatenate)
from tensorflow.keras.applications.xception import Xception



def input_to_target(base_data_path = 'data/'):

    # audio files and their corresponding labels
    train_path = base_data_path + "train/Train/*.wav"
    train_label_path = base_data_path +  "train.csv"
    test_path =  base_data_path + "test/Test/*.wav"

    # input
    train_files = glob.glob(train_path)
    train_files = pd.DataFrame({'train_file_paths': train_files})
    train_files['ID'] = train_files['train_file_paths'].apply(lambda x:x.split('/')[-1].split('.')[0])
    train_files['ID'] = train_files['ID'].astype(int)
    train_files = train_files.sort_values(by='ID')
    test_files = glob.glob(test_path)

    # target
    train_labels = pd.read_csv(train_label_path)
    train_file_to_label = train_files.merge(train_labels, on= "ID", how='inner')

    # encoding the classes
    int_encode = LabelEncoder()
    train_file_to_label['class_int_encode'] = int_encode.fit_transform(train_file_to_label['Class'])
    
    
    return train_file_to_label


def audio_normalization(data):
    
    max_data = np.max(data)
    min_data = np.min(data)
    data = (data-min_data)/(max_data-min_data+0.0001)
    return data-0.5

def load_audio_file(file_path, input_length=64000):
    
    data, sr = librosa.core.load(file_path, sr=16000) 
    if len(data)>input_length:
        
        max_offset = len(data)-input_length
        offset = np.random.randint(max_offset)
        data = data[offset:(input_length+offset)]
              
    else:
        
        if input_length > len(data):
            max_offset = input_length - len(data)
            offset = np.random.randint(max_offset)
            
        else:
            offset = 0
        
        data = np.pad(data, (offset, input_length - len(data) - offset), "constant")
        data = audio_normalization(data)
        
    return data


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def generator(file_paths, target_labels, batch_size=32):
    while True:
        file_paths, target_labels = shuffle(file_paths, target_labels)
        
        for batch_files, batch_labels in zip(chunker(file_paths, size=batch_size),
                                             chunker(target_labels, size= batch_size)):

            batch_data = [load_audio_file(fpath) for fpath in batch_files]
            batch_data = np.array(batch_data)[:,:,np.newaxis]
            
            
            yield batch_data, batch_labels