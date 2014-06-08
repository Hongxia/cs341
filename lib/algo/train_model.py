#!/usr/bin/python

import os
import sys
import time
from model import ModelFitter

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print "Usage: python train_model.py dataset_dir_in_data_dir [description]"
    exit(1)

DESCRIPTION = ""
if len(sys.argv) == 3:
    DESCRIPTION = sys.argv[2]

TRAINING_CSV_FILE = os.path.join("../../data/", sys.argv[1], "training.csv")
VALIDATION_CSV_FILE = os.path.join("../../data/", sys.argv[1], "validation.csv")
OUTPUT_DIR = os.path.join("../../data/", sys.argv[1], "output/")
os.system("mkdir -p " + OUTPUT_DIR)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, str(int(time.time())))
LAMBDA = 1
LBFGS_ITERS = 10
MIN_EM_ITERS = 10

CORES = 2
model = ModelFitter(TRAINING_CSV_FILE, CORES)
model.train(VALIDATION_CSV_FILE, OUTPUT_FILE, LAMBDA, MIN_EM_ITERS, LBFGS_ITERS, DESCRIPTION)
