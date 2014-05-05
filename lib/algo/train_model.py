#!/usr/bin/python

import sys
from model import ModelFitter

if len(sys.argv) == 2:
    CSV_FILE = sys.argv[1]
else:
    CSV_FILE = "../../data/toy1.csv"

DEBUG = True
CORES = 2
EM_ITERS = 10
LBFGS_ITERS = 10

model = ModelFitter(CSV_FILE, cores=CORES)

for i in range(EM_ITERS):
    model.update_params(max_iter=LBFGS_ITERS, DEBUG=DEBUG)
    model.update_exps(DEBUG=DEBUG)