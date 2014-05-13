import time
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

    rec = pp.alpha(e) + pp.betau(e, u) + pp.betai(e, p) + dot(pp.gammau(e, u), pp.gammai(e, p))
    return rec - rating, e, u, p

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
    
    def __init__(self, csv_file, cores=1):
        self.csv_file = csv_file
        self.cores = cores
        self._read()

    def _read(self):
        #self.user_ratings_map = {}
        self.user_ratings = {}
        self.user_mapping = {}
        self.product_mapping = {}

        self.num_users = int32(0)
        self.num_products = int32(0)
        self.num_reviews = int32(0)

        with open(self.csv_file, "rb") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                product_id_str = row[0]
                user_id_str = row[1]
                rating = float32(row[2])
                timestamp = int32(row[3])

                self.num_reviews += 1
                # normalized user id
                if user_id_str not in self.user_mapping:
                    self.user_mapping[user_id_str] = self.num_users
                    self.num_users += 1
                user_id = self.user_mapping[user_id_str]
                # normalized product id
                if product_id_str not in self.product_mapping:
                    self.product_mapping[product_id_str] = self.num_products
                    self.num_products += 1
                product_id = self.product_mapping[product_id_str]

                if user_id not in self.user_ratings:
                    self.user_ratings[user_id] = empty((0, 5))
                self.user_ratings[user_id] = append(self.user_ratings[user_id], [[product_id, user_id, rating, timestamp, -1]], axis=0)
        
        alphas = zeros(exp_level, dtype=float32)
        alpha_counts = zeros(exp_level, dtype=float32)
        for user_id in self.user_ratings:
            # assign exp level at uniform distribution, round down except for the last level
            num_user_ratings = len(self.user_ratings[user_id])
            count = 0
            for e in range(0, exp_level):
                for i in range(0, num_user_ratings/exp_level):
                    self.user_ratings[user_id][count][4] = e
                    alphas[e] += self.user_ratings[user_id][count][2]
                    alpha_counts[e] += 1
                    count += 1

            # set remaining to max experience level
            for i in range(count, num_user_ratings):
                self.user_ratings[user_id][count][4] = exp_level - 1
                alphas[exp_level - 1] += self.user_ratings[user_id][count][2]
                alpha_counts[exp_level - 1] += 1

        # init params
        self.params = append(alphas/alpha_counts, zeros(sum(ParamParser.params_dimensions(self.num_users, self.num_products)) - exp_level, dtype=float32))
        
        print "num_user %d" % self.num_users
        print "num_prod %d" % self.num_products
        print "num_reviews %d" % self.num_reviews

    @staticmethod
    def objective(params, *args):
        user_ratings, num_users, num_products, cores, calculate_gradient = args
        user_ratings_array = concatenate([rating for user, rating in user_ratings.items()])
        pp = ParamParser(num_users, num_products, params)

        # objective
        obj = float32(0)
        # gradient
        if calculate_gradient:
            gradients = zeros(sum(ParamParser.params_dimensions(num_users, num_products)))
            gp = ParamParser(num_users, num_products, gradients)

        pool = Pool(cores)
        for result in pool.imap_unordered(calculate_error, \
                                   [(pp, user_rating) for user_rating in user_ratings_array], \
                                   chunksize=8192):
            error, e, u, p = result
            if calculate_gradient:
                gp.incr_betau(e, u, 2 * error)
                gp.incr_betai(e, p, 2 * error)
                for k in range(k_level):
                    gp.incr_gammau(e, u, k, 2 * error * pp.gammaik(e, p, k))
                    gp.incr_gammai(e, p, k, 2 * error * pp.gammauk(e, u, k))
            obj += error ** 2
        pool.close()
        pool.join()

        if calculate_gradient:
            return obj, gradients
        else:
            return obj
            
    def update_params(self, max_iter=-1, DEBUG=False):
        if DEBUG:
            print "Updating Params (max_iter=%d) ..." % max_iter
            pre_ts = time.time()
        if max_iter > 0:
            p, f, d = scipy.optimize.fmin_l_bfgs_b(ModelFitter.objective, x0=self.params, \
                                                args=(self.user_ratings, self.num_users, self.num_products, self.cores, True), \
                                                approx_grad=False, maxiter=max_iter, disp=0) # TODO: change 0 to DEBUG
        else:
            p, f, d = scipy.optimize.fmin_l_bfgs_b(ModelFitter.objective, x0=self.params, \
                                                args=(self.user_ratings, self.num_users, self.num_products, self.cores, True), \
                                                approx_grad=False, disp=0) # TODO: change 0 to debug
        self.params = array(p)
        if DEBUG:
            post_ts = time.time()
            print "Params Updated (%d seconds). Func = %f" % (post_ts - pre_ts, f)

    def update_exps(self, DEBUG=False):
        if DEBUG:
            print "Updating Experience Levels...",
            pre_ts = time.time()
        for user_id in self.user_ratings:
            acc_cost_table = self._build_acc_cost_table(user_id)
            self._update_exp(user_id, acc_cost_table)
        if DEBUG:
            post_ts = time.time()
            obj = ModelFitter.objective(self.params, self.user_ratings, self.num_users, self.num_products, self.cores, False)
            print "Experience Levels Updated (%d seconds). Func = %f" % (post_ts - pre_ts, obj)

    def _build_acc_cost_table(self, user_id):
        ratings = self.user_ratings[user_id]
        pp = ParamParser(self.num_users, self.num_products, self.params)
        cost_table = zeros((exp_level, len(ratings)))
        for i, rating in enumerate(ratings):
            for e in range(exp_level):
                error, e, u, p = calculate_error((pp, rating))
                cost_table[e][i] = abs(error)
        
        acc_cost_table = copy(cost_table)
        for i in range(exp_level):
            for j in range(1, len(ratings)):
                if i == 0:
                    acc_cost_table[i][j] = acc_cost_table[i][j-1] + cost_table[i][j]
                else:
                    acc_cost_table[i][j] = min(acc_cost_table[i][j-1], acc_cost_table[i-1][j-1]) + cost_table[i][j]
        return acc_cost_table

    def _update_exp(self, user_id, acc_cost_table):
        ratings = self.user_ratings[user_id]
        min_path = zeros(len(ratings))
        min_cost, min_exp = min((cost, exp) for (exp, cost) in enumerate(acc_cost_table[:, len(ratings)-1]))
        min_path[len(ratings)-1] = min_exp
        
        for rating_index in range(len(ratings)-2, 0, -1):
            next_exp = min_path[rating_index+1]
            if next_exp == 0:
                min_path[rating_index] = next_exp
            else:
                min_cost, min_exp = min((cost, exp) for (exp, cost) in enumerate(acc_cost_table[next_exp-1:next_exp+1, rating_index]))
                min_path[rating_index] = min_exp

        for i, exp in enumerate(min_path):
            ratings[i][4] = exp
