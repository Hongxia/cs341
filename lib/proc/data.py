import csv
import operator
import random
import os

##
# Notes: csv file format: product_id, user_id, rating, timestamp
##

class Review:

    def __init__(self, user_id, product_id, rating, timestamp):
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.timestamp = timestamp

class CSVDataProcessor:

    def __init__(self, csv_file):
        self.csv_file = csv_file

    def _read(self, threshold=0, collapse=False):
        user_reviews = {}
        with open(self.csv_file, "rb") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                product_id = row[0]
                user_id = row[1]
                rating = float(row[2])
                timestamp = int(row[3])
                
                if user_id != "unknown":
                    if user_id not in user_reviews:
                        user_reviews[user_id] = []
                    user_reviews[user_id].append(Review(user_id, product_id, rating, timestamp))

        if threshold > 1:
            collapsed_reviews = []
            for user_id, reviews in user_reviews.items():
                if len(reviews) < threshold:
                    collapsed_reviews += reviews
                    del user_reviews[user_id]

            if collapse:
                user_reviews["collapsed_reviews"] = collapsed_reviews

        for user_id in user_reviews:
            user_reviews[user_id].sort(key=operator.attrgetter("timestamp"))

        return user_reviews

    def _write(self, user_reviews, name):
        # overwrites file if it already exists
        with open(name, "wb") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",")
            for user_id in user_reviews:
                for review in user_reviews[user_id]:
                    csv_writer.writerow([review.product_id, review.user_id, review.rating, review.timestamp])

    def read(self, threshold=0, collapse=False, rand_sampling=True, sampling_rates=[0.8, 0.1, 0.1], write_to_file=True):
        # training, validation, testing data in percentages
        assert sum(sampling_rates) <= 1

        training_reviews = {}
        validation_reviews = {}
        testing_reviews = {}

        user_reviews = self._read(threshold, collapse)
        if rand_sampling:
            for user_id in user_reviews:
                random.shuffle(user_reviews[user_id])

        for user_id in user_reviews:
            len_reviews = len(user_reviews[user_id])
            training_reviews[user_id] = user_reviews[user_id][:int(len_reviews*sampling_rates[0])]
            validation_reviews[user_id] = user_reviews[user_id][int(len_reviews*sampling_rates[0]):int(len_reviews*(sampling_rates[0]+sampling_rates[1]))]
            testing_reviews[user_id] = user_reviews[user_id][int(len_reviews*(sampling_rates[0]+sampling_rates[1])):int(len_reviews*(sampling_rates[0]+sampling_rates[1]+sampling_rates[2]))]

            if rand_sampling:
                training_reviews[user_id].sort(key=operator.attrgetter("timestamp"))
                validation_reviews[user_id].sort(key=operator.attrgetter("timestamp"))
                testing_reviews[user_id].sort(key=operator.attrgetter("timestamp"))

        if write_to_file:
            path, filename = os.path.split(self.csv_file)
            if rand_sampling:
                dump_path = os.path.join(path, os.path.splitext(filename)[0] + "_rand")
            else:
                dump_path = os.path.join(path, os.path.splitext(filename)[0] + "_temp")
            # make directory of the name of the csv file
            if not os.path.exists(dump_path):
                os.mkdir(dump_path)
            self._write(training_reviews, os.path.join(dump_path, "training.csv"))
            self._write(validation_reviews, os.path.join(dump_path, "validation.csv"))
            self._write(testing_reviews, os.path.join(dump_path, "testing.csv"))

        return training_reviews, validation_reviews, testing_reviews


