#!/usr/bin/python

import os
import sys
from model import ModelFitter

if len(sys.argv) != 2:
    print "Usage: python train_model.py dataset_dir_in_data_dir"
    exit(1)

TRAINING_CSV_FILE = os.path.join("../../data/", sys.argv[1], "training.csv")
VALIDATION_CSV_FILE = os.path.join("../../data/", sys.argv[1], "validation.csv")
CORES = 2
LAMBDA = 1
LBFGS_ITERS = 5
MIN_EM_ITERS = 5

model = ModelFitter(LAMBDA, TRAINING_CSV_FILE, VALIDATION_CSV_FILE, cores=CORES)
model.train(MIN_EM_ITERS, LBFGS_ITERS)
