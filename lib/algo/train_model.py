#!/usr/bin/python

import sys
from model import ModelFitter

if len(sys.argv) == 4:
    CSV_FILE = sys.argv[1]
else:
    CSV_FILE = "../../data/Movies_training.csv"

DEBUG = True
CORES = 2
EM_ITERS = 40
LBFGS_ITERS = 10

model = ModelFitter(CSV_FILE, cores=CORES)

for i in range(EM_ITERS):
    print "EM_ITERATION_# %d" % (i+1)
    model.update_params(max_iter=LBFGS_ITERS, DEBUG=DEBUG)
    model.update_exps(DEBUG=DEBUG)
