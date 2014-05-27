#!/usr/bin/python

import os
import sys
from model import ModelFitter

if len(sys.argv) != 3:
    print "Usage: python train_model.py dataset_dir_in_data_dir model_file"
    exit(1)

TRAINING_CSV_FILE = os.path.join("../../data/", sys.argv[1], "training.csv")
TESTING_CSV_FILE = os.path.join("../../data/", sys.argv[1], "testing.csv")
MODEL_FILE = os.path.join("../../data/", sys.argv[1], "output/", sys.argv[2])
CORES = 2

model = ModelFitter(TRAINING_CSV_FILE, cores=CORES)
model.test(TESTING_CSV_FILE, MODEL_FILE)