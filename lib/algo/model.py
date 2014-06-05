import time
import csv
import json
import scipy
import os
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
    
    def __init__(self, training_csv_file, cores, chunksize):
        self.cores = cores
        self.chunksize = chunksize
        self.training_csv_file = training_csv_file
        self._read_training_data()

    '''
    Public Interface
    '''           
    def update_params(self, reg_param, max_iter=-1):
        pre_ts = time.time()
        if max_iter > 0:
            p, f, d = scipy.optimize.fmin_l_bfgs_b(ModelFitter.objective, x0=self.params, \
                                                args=(self.user_ratings, self.num_users, self.num_products, self.num_reviews, \
                                                      reg_param, self.cores, self.chunksize, True), \
                                                approx_grad=False, maxiter=max_iter, disp=0)
        else:
            p, f, d = scipy.optimize.fmin_l_bfgs_b(ModelFitter.objective, x0=self.params, \
                                                args=(self.user_ratings, self.num_users, self.num_products, self.num_reviews, \
                                                      reg_param, self.cores, self.chunksize, True), \
                                                approx_grad=False, disp=0)
        self.params = array(p)
        post_ts = time.time()

        return f, post_ts - pre_ts

    def update_exps(self, reg_param):
        pre_ts = time.time()
        for user_id in self.user_ratings:
            acc_cost_table = self._build_acc_cost_table(user_id)
            self._update_exp(user_id, acc_cost_table)
        obj = ModelFitter.objective(self.params, self.user_ratings, self.num_users, self.num_products, self.num_reviews, reg_param, self.cores, self.chunksize, False)
        post_ts = time.time()
        return obj, post_ts - pre_ts

    def validate_model(self):
        pre_ts = time.time()
        val_error = float32(0)
        pp = ParamParser(self.num_users, self.num_products, self.params)
        user_exp_levels = ModelFitter.summarize_user_exp_levels(self.user_ratings)
        for user_id in self.val_user_ratings:
            for rating in self.val_user_ratings[user_id]:
                timestamp = rating[3]
                rating[4] = ModelFitter.get_exp_level(user_id, timestamp, user_exp_levels)
        
        val_user_ratings_array = concatenate([rating for user, rating in self.val_user_ratings.items()])
        pool = Pool(self.cores)
        for result in pool.imap_unordered(calculate_error, \
                                   [(pp, user_rating) for user_rating in val_user_ratings_array], \
                                   chunksize=self.chunksize):
            error, e, u, p = result
            val_error += error ** 2
        pool.close()
        pool.join()
        val_error /= self.val_num_reviews
        post_ts = time.time()
        return val_error, post_ts - pre_ts

    def test_model(self, params, user_exp_levels):
        pre_ts = time.time()
        test_error = float32(0)
        pp = ParamParser(self.num_users, self.num_products, params)
        for user_id in self.test_user_ratings:
            for rating in self.test_user_ratings[user_id]:
                timestamp = rating[3]
                rating[4] = ModelFitter.get_exp_level(user_id, timestamp, user_exp_levels)

        test_user_ratings_array = concatenate([rating for user, rating in self.test_user_ratings.items()])
        pool = Pool(self.cores)
        for result in pool.imap_unordered(calculate_error, \
                                   [(pp, user_rating) for user_rating in test_user_ratings_array], \
                                   chunksize=self.chunksize):
            error, e, u, p = result
            test_error += error ** 2
        pool.close()
        pool.join()
        test_error /= self.test_num_reviews
        post_ts = time.time()
        return test_error, post_ts - pre_ts

    def train(self, validation_file, output_file, reg_param, min_em_iters, lbfgs_iters, description=""):
        self._read_validation_data(validation_file)

        print "TRAINING MODEL (running at least %d EM iterations, each consists of %d LBFGS iterations) ..." % (min_em_iters, lbfgs_iters)
        validation_errors = []
        iter_count = 0
        while True:
            iter_count += 1
            print "[%d]: " % iter_count,
            pf, ptime = self.update_params(reg_param, max_iter=lbfgs_iters)
            print "update theta, %f (%d)" % (pf, ptime),
            print " | ",
            ef, etime = self.update_exps(reg_param)
            print "update E, %f (%d)" % (ef, etime),
            print " | ",
            vf, vtime = self.validate_model()
            print "validate, %f (%d)" % (vf, vtime)
            
            validation_errors.append(vf)
            if len(validation_errors) == 1 or vf < min_vf:
                min_vf = vf
                min_params = copy(self.params)
                min_user_ratings = copy(self.user_ratings)
            if iter_count > min_em_iters and validation_errors[-1] >= validation_errors[-2]:
               break

        print "TRAINING COMPLETED in %d iterations... validation errors: %s" % (iter_count, str(validation_errors))

        print "WRITING PARAMS AND EXP_LEVELS (validation error = %f) TO %s..." % (min_vf, os.path.basename(output_file))
        output_json = {}
        output_json["description"] = description
        output_json["params"] = min_params.tolist()
        user_exp_levels = ModelFitter.summarize_user_exp_levels(min_user_ratings.tolist())
        json_user_exp_levels = {}
        for user_id in user_exp_levels:
            json_user_exp_levels[str(user_id)] = user_exp_levels[user_id].tolist()

        output_json["user_exp_levels"] = json_user_exp_levels
        output_json["user_mapping"] = self.user_mapping
        output_json["product_mapping"] = self.product_mapping
        with open(output_file, "wb") as output:
            json.dump(output_json, output, sort_keys=True, indent=4)

    def test(self, testing_file, model_file):
        self._read_testing_data(testing_file)
        print "PARSING PARAMS AND USER EXPERIENCE LEVELS..."
        params, user_exp_levels = self._read_model_file(model_file)
        print "TESTING MODEL... ",
        tf, ttime = self.test_model(params, user_exp_levels)
        print "%f (%d)" % (tf, ttime)

    '''
    Private Helpers
    '''

    # parsing helpers
    def _read_training_data(self):
        print "Reading training data...",
        self.user_ratings = {}
        self.user_mapping = {}
        self.product_mapping = {}

        self.num_users = 0
        self.num_products = 0
        self.num_reviews = 0

        with open(self.training_csv_file, "rb") as training_csv_file:
            csv_reader = csv.reader(training_csv_file, delimiter=",")
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
                self.user_ratings[user_id][i][4] = exp_level - 1
                alphas[exp_level - 1] += self.user_ratings[user_id][i][2]
                alpha_counts[exp_level - 1] += 1

        # init params
        self.params = append(alphas/alpha_counts, random.rand(sum(ParamParser.params_dimensions(self.num_users, self.num_products)) - exp_level))
        print "%d reviews from %d users on %d products" % (self.num_reviews, self.num_users, self.num_products)

    def _read_validation_data(self, validation_file):
        print "Reading validation data...",
        self.val_user_ratings = {}
        self.val_num_reviews = int32(0)
        val_num_del_reviews = int32(0)

        with open(validation_file, "rb") as validation_csv_file:
            csv_reader = csv.reader(validation_csv_file, delimiter=",")
            for row in csv_reader:
                product_id_str = row[0]
                user_id_str = row[1]
                rating = float32(row[2])
                timestamp = int32(row[3])

                user_id = self.user_mapping[user_id_str]
                if product_id_str in self.product_mapping:
                    self.val_num_reviews += 1
                    product_id = self.product_mapping[product_id_str]
                    if user_id not in self.val_user_ratings:
                        self.val_user_ratings[user_id] = empty((0, 5))
                    self.val_user_ratings[user_id] = append(self.val_user_ratings[user_id], [[product_id, user_id, rating, timestamp, -1]], axis=0)
                else:
                    val_num_del_reviews += 1

        print "processed %d reviews (ignored %d reviews)" % (self.val_num_reviews, val_num_del_reviews)

    def _read_testing_data(self, testing_file):
        print "Reading testing data...",
        self.test_user_ratings = {}
        self.test_num_reviews = int32(0)
        test_num_del_reviews = int32(0)

        with open(testing_file, "rb") as testing_csv_file:
            csv_reader = csv.reader(testing_csv_file, delimiter=",")
            for row in csv_reader:
                product_id_str = row[0]
                user_id_str = row[1]
                rating = float32(row[2])
                timestamp = int32(row[3])

                user_id = self.user_mapping[user_id_str]
                if product_id_str in self.product_mapping:
                    self.test_num_reviews += 1
                    product_id = self.product_mapping[product_id_str]
                    if user_id not in self.test_user_ratings:
                        self.test_user_ratings[user_id] = empty((0, 5))
                    self.test_user_ratings[user_id] = append(self.test_user_ratings[user_id], [[product_id, user_id, rating, timestamp, -1]], axis=0)
                else:
                    test_num_del_reviews += 1

        print "processed %d reviews (ignored %d reviews)" % (self.test_num_reviews, test_num_del_reviews)

    def _read_model_file(self, model_file):
        with open(model_file, "rb") as model_f:
            model_json = json.load(model_f)
        
        params = array(model_json["params"])
        user_exp_levels = {}
        json_user_exp_levels = model_json["user_exp_levels"]
        for user_id_str in json_user_exp_levels:
            user_exp_levels[int(user_id_str)] = array(json_user_exp_levels[user_id_str])
        
        return params, user_exp_levels

    # training helpers
    def _build_acc_cost_table(self, user_id):
        ratings = self.user_ratings[user_id]
        pp = ParamParser(self.num_users, self.num_products, self.params)
        cost_table = zeros((exp_level, len(ratings)))
        for i, rating in enumerate(ratings):
            for e in range(exp_level):
                dup_rating = copy(rating)
                dup_rating[4] = e
                error, e, u, p = calculate_error((pp, dup_rating))
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
        
        for rating_index in range(len(ratings)-2, -1, -1):
            next_exp = min_path[rating_index+1]
            if next_exp == 0:
                min_path[rating_index] = next_exp
            else:
                min_cost, min_exp = min((cost, exp) for (exp, cost) in enumerate(acc_cost_table[next_exp-1:next_exp+1, rating_index]))
                min_path[rating_index] = next_exp - 1 + min_exp

        for i, exp in enumerate(min_path):
            ratings[i][4] = exp

    @staticmethod
    def objective(params, *args):
        user_ratings, num_users, num_products, num_reviews, reg_param, cores, chunksize, calculate_gradient = args
        user_ratings_array = concatenate([rating for user, rating in user_ratings.items()])
        pp = ParamParser(num_users, num_products, params)

        # objective
        obj = float32(0)
        reg = float32(0)
        # gradient
        if calculate_gradient:
            gradients = zeros(sum(ParamParser.params_dimensions(num_users, num_products)))
            gp = ParamParser(num_users, num_products, gradients)

        pool = Pool(cores)
        for result in pool.imap_unordered(calculate_error, \
                                   [(pp, user_rating) for user_rating in user_ratings_array], \
                                   chunksize=chunksize):
            error, e, u, p = result
            if calculate_gradient:
                gp.incr_alpha(e, 2 * error)
                gp.incr_betau(e, u, 2 * error)
                gp.incr_betai(e, p, 2 * error)
                for k in range(k_level):
                    gp.incr_gammau(e, u, k, 2 * error * pp.gammaik(e, p, k))
                    gp.incr_gammai(e, p, k, 2 * error * pp.gammauk(e, u, k))
            obj += error ** 2
        pool.close()
        pool.join()
 
        obj /= num_reviews
        num_alpha_betas = pp.num_alpha + pp.num_betai + pp.num_betau
        for e in range(exp_level-1):
            reg += linalg.norm(params[e:num_alpha_betas:exp_level] - params[e+1:num_alpha_betas:exp_level], ord=None)**2
            for k in range(k_level):
              reg += linalg.norm(params[num_alpha_betas+e*k_level+k::exp_level*k_level] - params[num_alpha_betas+(e+1)*k_level+k::exp_level*k_level])**2 
        obj += (reg_param * reg)

        if calculate_gradient:
            gradients /= num_reviews
            # e = 0
            gradients[0:num_alpha_betas:exp_level] += \
              (2*params[0:num_alpha_betas:exp_level] - \
               2*params[1:num_alpha_betas:exp_level]) * reg_param
            for k in range(k_level):
                gradients[num_alpha_betas+k::exp_level*k_level] += \
                  (2*params[num_alpha_betas+k::exp_level*k_level] - \
                   2*params[num_alpha_betas+k_level+k::exp_level*k_level]) * reg_param
            # e = 1,2,3
            for e in range(1, exp_level-1):
                gradients[e:num_alpha_betas:exp_level] += \
                  (4*params[e:num_alpha_betas:exp_level] - \
                   2*params[e-1:num_alpha_betas:exp_level] - \
                   2*params[e+1:num_alpha_betas:exp_level]) * reg_param
                for k in range(k_level):
                    gradients[num_alpha_betas+e*k_level+k::exp_level*k_level] += \
                      (4*params[num_alpha_betas+e*k_level+k::exp_level*k_level] - \
                       2*params[num_alpha_betas+(e-1)*k_level+k::exp_level*k_level] - \
                       2*params[num_alpha_betas+(e+1)*k_level+k::exp_level*k_level]) * reg_param
            # e = 4
            gradients[4:num_alpha_betas:exp_level] += \
              (2*params[4:num_alpha_betas:exp_level] - \
               2*params[3:num_alpha_betas:exp_level]) * reg_param
            for k in range(k_level):
                gradients[num_alpha_betas+4*k_level+k::exp_level*k_level] += \
                  (2*params[num_alpha_betas+4*k_level+k::exp_level*k_level] - \
                   2*params[num_alpha_betas+3*k_level+k::exp_level*k_level]) * reg_param
 
        if calculate_gradient:
            return obj, gradients
        else:
            return obj

    # validation helpers
    @staticmethod
    def get_exp_level(user_id, timestamp, user_exp_levels):
        prev_exp = user_exp_levels[user_id][0][2]
        for review in user_exp_levels[user_id]:
            start_timestamp = review[0]
            end_timestamp = review[1]
            curr_exp = review[2]
            if start_timestamp > timestamp:
                return prev_exp
            elif end_timestamp >= timestamp:
                return curr_exp
            else:
                prev_exp = curr_exp
        return curr_exp

    @staticmethod
    def summarize_user_exp_levels(user_ratings):
        user_exp_levels = {}
        for user_id in user_ratings:
            if user_id not in user_exp_levels:
                first_exp = user_ratings[user_id][0][4]
                first_timestamp = user_ratings[user_id][0][3]
                user_exp_levels[user_id] = array([[first_timestamp, 0, first_exp, 0]])

            prev_exp = first_exp
            for review in user_ratings[user_id]:
                curr_exp = review[4]
                curr_timestamp = review[3]
                if curr_exp == prev_exp:
                    user_exp_levels[user_id][-1][1] = curr_timestamp
                    user_exp_levels[user_id][-1][3] += 1
                if curr_exp > prev_exp:
                    user_exp_levels[user_id] = append(user_exp_levels[user_id], [[curr_timestamp, curr_timestamp, curr_exp, 1]], axis=0)
                prev_exp = curr_exp

        return user_exp_levels