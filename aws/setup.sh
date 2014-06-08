#!/bin/bash

# setup numpy and scipy
sudo apt-get install python-pip python-dev build-essential
sudo pip install numpy
sudo apt-get install libatlas-base-dev gfortran
sudo pip install scipy

# setup s3cmd
sudo apt-get install s3cmd
echo "ACCESS KEY: AKIAIGQCJ2QMLH6GQJGQ"
echo "SECRET KEY: 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"
s3cmd --configure

# setup git repo
sudo apt-get install git-core
git clone https://github.com/Hongxia/cs341.git

# pull data
mkdir /home/ubuntu/cs341/data
cd /home/ubuntu/cs341/data 
s3cmd get -r s3://cs341-amazon/hive-input/Arts_rand
s3cmd get -r s3://cs341-amazon/hive-input/Arts_temp
s3cmd get -r s3://cs341-amazon/hive-input/Books_rand
s3cmd get -r s3://cs341-amazon/hive-input/Books_temp
s3cmd get -r s3://cs341-amazon/hive-input/Gourmet_Foods_rand
s3cmd get -r s3://cs341-amazon/hive-input/Gourmet_Foods_temp
s3cmd get -r s3://cs341-amazon/hive-input/Movies_rand
s3cmd get -r s3://cs341-amazon/hive-input/Movies_temp
s3cmd get -r s3://cs341-amazon/hive-input/Music_rand
s3cmd get -r s3://cs341-amazon/hive-input/Music_temp
s3cmd get -r s3://cs341-amazon/hive-input/Video_Games_rand
s3cmd get -r s3://cs341-amazon/hive-input/Video_Games_temp