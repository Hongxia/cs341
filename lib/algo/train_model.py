#!/usr/bin/python

import os
import sys
from model import ModelFitter

if len(sys.argv) != 2:
    print "Usage: python train_model.py csv_file_name_in_data_dir"
    exit(1)

CSV_FILE = os.path.join("../../data/", sys.argv[1])
DEBUG = True
CORES = 2
EM_ITERS = 40
LBFGS_ITERS = 10

LAMBDA = 1

model = ModelFitter(LAMBDA, CSV_FILE, cores=CORES)

for i in range(EM_ITERS):
    print "EM_ITERATION_# %d" % (i+1)
    model.update_params(max_iter=LBFGS_ITERS, DEBUG=DEBUG)
    model.update_exps(DEBUG=DEBUG)
