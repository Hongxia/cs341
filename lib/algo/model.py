import csv
import scipy
from numpy import *
import operator
from scipy import optimize
from multiprocessing import Pool

exp_level = 5
k_level = 5

def calculate_error(args):
    pp, user_rating = args
    e = user_rating[4]
    u = user_rating[1]
    p = user_rating[0]
    rating = user_rating[2]

    rec = pp.alpha(e)
    rec += pp.betau(e, u) + pp.betai(e, p)
    rec += dot(pp.gammau(e, u), pp.gammai(e, p))
    return rec - rating, e, u, p

class Review:
    
    # e = 0 ... exp_leve - 1
    def __init__(self, user_id, product_id, rating, timestamp):
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.timestamp = timestamp
        self.exp = -1

class ParamParser:

    @staticmethod
    def params_dimensions(num_users, num_products):
        num_alpha = exp_level
        num_betau = exp_level * num_users
        num_betai = exp_level * num_products
        num_gammau = exp_level * num_users * k_level
        num_gammai = exp_level * num_products * k_level
        return num_alpha, num_betau, num_betai, num_gammau, num_gammai
    
    def __init__(self, num_users, num_products, params):
        self.params = params
        self.num_users = num_users
        self.num_products = num_products

        self.num_alpha, self.num_betau, \
        self.num_betai, self.num_gammau, \
        self.num_gammai = ParamParser.params_dimensions(num_users, num_products)

    # getters
    def alpha(self, e):
        return self.params[e]

    def betau(self, e, u):
        index = exp_level * u + e
        return self.params[self.num_alpha + self.num_betai + index]

    def betai(self, e, i):
        index = exp_level * i + e
        return self.params[self.num_alpha + index]

    def gammau(self, e, u):
        index = (k_level + exp_level) * u + k_level * e
        index += self.num_alpha + self.num_betai + self.num_betau + self.num_gammai
        return self.params[index:index+k_level]

    def gammai(self, e, i):
        index = (k_level + exp_level) * i + k_level * e
        index += self.num_alpha + self.num_betai + self.num_betau
        return self.params[index:index+k_level]

    def gammauk(self, e, u, k):
        index = (k_level + exp_level) * u + k_level * e + k
        return self.params[self.num_alpha + self.num_betai + self.num_betau + self.num_gammai + index]

    def gammaik(self, e, i, k):
        index = (k_level + exp_level) * i + k_level * e + k
        return self.params[self.num_alpha + self.num_betai + self.num_betau + index]

    # incrementors
    def incr_alpha(self, e, value):
        self.params[e] += value

    def incr_betau(self, e, u, value):
        index = exp_level * u + e
        self.params[self.num_alpha + self.num_betai + index] += value

    def incr_betai(self, e, i, value):
        index = exp_level * i + e
        self.params[self.num_alpha + index] += value

    def incr_gammau(self, e, u, k, value):
        index = (k_level + exp_level) * u + k_level * e + k
        self.params[self.num_alpha + self.num_betai + self.num_betau + self.num_gammai + index] += value

    def incr_gammai(self, e, i, k, value):
        index = (k_level + exp_level) * i + k_level * e + k
        self.params[self.num_alpha + self.num_betai + self.num_betau + index] += value

class ModelFitter:
    
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self._read()

    def _read(self):
        self.user_ratings_map = {}
        self.user_mapping = {}
        self.product_mapping = {}

        self.num_users = int32(0)
        self.num_products = int32(0)
        self.num_reviews = int32(0)

        with open(self.csv_file, "rb") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                product_id = row[0]
                user_id = row[1]
                rating = float32(row[2])
                timestamp = int32(row[3])

                self.num_reviews += 1
                # normalized user id
                if user_id not in self.user_mapping:
                    self.user_mapping[user_id] = self.num_users
                    self.num_users += 1
                n_user_id = self.user_mapping[user_id]
                # normalized product id
                if product_id not in self.product_mapping:
                    self.product_mapping[product_id] = self.num_products
                    self.num_products += 1
                n_product_id = self.product_mapping[product_id]

                if n_user_id not in self.user_ratings_map:
                    self.user_ratings_map[n_user_id] = []
                self.user_ratings_map[n_user_id].append(Review(n_user_id, n_product_id, rating, timestamp))
          
        alphas = zeros(exp_level, dtype=float32)
        alpha_counts = zeros(exp_level, dtype=float32)
        for n_user_id in self.user_ratings_map:
            # sort in time
            self.user_ratings_map[n_user_id].sort(key=operator.attrgetter("timestamp"))
            # assign exp level at uniform distribution, round down except for the last level
            num_user_ratings = len(self.user_ratings_map[n_user_id])
            count = 0
            for e in range(0, exp_level):
                for i in range(0, num_user_ratings/exp_level):
                    self.user_ratings_map[n_user_id][count].exp = e
                    alphas[e] += self.user_ratings_map[n_user_id][count].rating
                    alpha_counts[e] += 1
                    count += 1

            # set remaining to max experience level
            for i in range(count, num_user_ratings):
                self.user_ratings_map[n_user_id][count].exp = exp_level - 1
                alphas[exp_level - 1] += self.user_ratings_map[n_user_id][count].rating
                alpha_counts[exp_level - 1] += 1

        self.params = append(alphas/alpha_counts, \
                zeros(sum(ParamParser.params_dimensions(self.num_users, self.num_products)) \
                        - exp_level, dtype=float32))
        
        # init vec
        count = 0
        self.user_ratings = empty([self.num_reviews, 5])
        for n_user_id in self.user_ratings_map:
            for review in self.user_ratings_map[n_user_id]:
                self.user_ratings[count,:] = [review.product_id, review.user_id, review.rating, review.timestamp, review.exp]
                count += 1

        print "num_user %d" % self.num_users
        print "num_prod %d" % self.num_products
        print "num_reviews %d" % self.num_reviews

    @staticmethod
    def objective(params, *args):
        user_ratings, num_users, num_products = args
        pp = ParamParser(num_users, num_products, params)

        # objective
        obj = float32(0)
        # gradient
        gradients = zeros(sum(ParamParser.params_dimensions(num_users, num_products)))
        gp = ParamParser(num_users, num_products, gradients)

        pool = Pool(2)
        for result in pool.imap_unordered(calculate_error, \
                                   [(pp, user_rating) for user_rating in user_ratings], \
                                   chunksize=8192):
            error, e, u, p = result
            gp.incr_betau(e, u, 2 * error)
            gp.incr_betai(e, p, 2 * error)
            for k in range(k_level):
                gp.incr_gammau(e, u, k, 2 * error * pp.gammaik(e, p, k))
                gp.incr_gammai(e, p, k, 2 * error * pp.gammauk(e, u, k))
            obj += error ** 2
        pool.close

        return obj, gradients

        # user_ratings_map, num_users, num_products = args
        # pp = ParamParser(num_users, num_products, params)
        # obj = 0
        # for n_user_id in user_ratings_map:
        #     for review in user_ratings_map[n_user_id]:
        #         obj += ModelFitter.calculate_error(pp, review)**2
        # return obj

    @staticmethod
    def fprime(params, *args):
        return zeros(len(params))

    def fit_params(self):
        p, f, d = scipy.optimize.fmin_l_bfgs_b(ModelFitter.objective, x0=self.params, \
                                                args=(self.user_ratings, self.num_users, self.num_products), \
                                                approx_grad=False, iprint=1)
        return (p, f, d)