#!/usr/bin/python

import sys
import os
from data import CSVDataProcessor

if len(sys.argv) != 2:
    print "usage: python process_data.py path_to_csv"
    exit(1)

csv_files = []
for filename in os.listdir(sys.argv[1]):
    print os.path.splitext(filename)[1]
    if os.path.splitext(filename)[1] == ".csv":
        csv_files.append(filename)

print "found %d csv files" % len(csv_files)
for csv_file in csv_files:
    print "processing %s..." % csv_file
    csv_processor = CSVDataProcessor(os.path.join(sys.argv[1], csv_file))
    csv_processor.read(threshold=50, rand_sampling=True)
    csv_processor.read(threshold=50, rand_sampling=False)

print "done!"