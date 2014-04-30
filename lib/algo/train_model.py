#!/usr/bin/python

import sys
import time
from model import ModelFitter

if len(sys.argv) < 2:
    print "usage: python train_model train.csv"
    exit(1)

csv_file = sys.argv[1]
model = ModelFitter(csv_file)
pre_ts = time.time()
p, f, d = model.fit_params()
post_ts = time.time()
print "L_BFGS_B Run-time: %f seconds" % (post_ts - pre_ts)
