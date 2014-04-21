import csv
import operator
import random

class Review:

    def __init__(self, user_id, product_id, rating, timestamp):
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.timestamp = timestamp

class DataProcessor:

    def __init__(self, csv_file):
        self.csv_file = csv_file

    def _process(self, threshold=0, collapse=False):
        user_reviews = {}
        with open(self.csv_file, "rb") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                product_id = row[0]
                user_id = row[1]
                rating = float(row[2])
                timestamp = int(row[3])
                
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

    def process(self, rand_sampling=True, threshold=0, collapse=False, rates=[0.8, 0.1, 0.1]):
        # training, validation, testing data in percentages
        assert sum(rates) <= 1

        training_reviews = {}
        validation_reviews = {}
        testing_reviews = {}

        user_reviews = self._process(threshold, collapse)
        if rand_sampling:
            for user_id in user_reviews:
                random.shuffle(user_reviews[user_id])

        for user_id in user_reviews:
            len_reviews = len(user_reviews[user_id])
            training_reviews[user_id] = user_reviews[user_id][:int(len_reviews*rates[0])]
            validation_reviews[user_id] = user_reviews[user_id][int(len_reviews*rates[0]):int(len_reviews*(rates[0]+rates[1]))]
            testing_reviews[user_id] = user_reviews[user_id][int(len_reviews*(rates[0]+rates[1])):int(len_reviews*(rates[0]+rates[1]+rates[2]))]

            if rand_sampling:
                training_reviews[user_id].sort(key=operator.attrgetter("timestamp"))
                validation_reviews[user_id].sort(key=operator.attrgetter("timestamp"))
                testing_reviews[user_id].sort(key=operator.attrgetter("timestamp"))

        return training_reviews, validation_reviews, testing_reviews