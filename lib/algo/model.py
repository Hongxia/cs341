import csv
import scipy
import numpy
import operator
from scipy import optimize

exp_level = 5
k_level = 5

class Params:
    
    def __init__(self, num_users, num_products, init_alphas=[0]*exp_level, params_array=None):
        self.num_users = num_users
        self.num_products = num_products

        self.num_alpha = exp_level
        self.num_betau = exp_level * num_users
        self.num_betai = exp_level * num_products
        self.num_gammau = exp_level * num_users * k_level
        self.num_gammai = exp_level * num_products * k_level

        if params_array is None:
            self.params_array = [float(0)] * (self.num_alpha + \
                self.num_betai + self.num_betau + \
                self.num_gammai + self.num_gammau)

            # init alphas
            for e in range(0, exp_level):
                self.set_alpha(e, init_alphas[e])

        else:
            self.params_array = params_array

    # getters
    def alpha(self, e):
        return self.params_array[e]

    def betau(self, e, u):
        index = exp_level * u + e
        return self.params_array[self.num_alpha + self.num_betai + index]
      
    def betai(self, e, i):
        index = exp_level * i + e
        return self.params_array[self.num_alpha + index]

    def gammau(self, e, u, k):
        index = (k_level + exp_level) * u + k_level * e + k
        return self.params_array[self.num_alpha + self.num_betai + self.num_betau + self.num_gammai + index]

    def gammai(self, e, i, k):
        index = (k_level + exp_level) * i + k_level * e + k
        return self.params_array[self.num_alpha + self.num_betai + self.num_betau + index]

    # setters
    def set_alpha(self, e, value):
        self.params_array[e] = value

    def set_betau(self, e, u, value):
        index = exp_level * u + e
        self.params_array[self.num_alpha + self.num_betai + index] = value

    def set_betai(self, e, i, value):
        index = exp_level * i + e
        self.params_array[self.num_alpha + index] = value

    def set_gammau(self, e, u, k, value):
        index = (k_level + exp_level) * u + k_level * e + k
        self.params_array[self.num_alpha + self.num_betai + self.num_betau + self.num_gammai + index] = value

    def set_gammai(self, e, i, k, value):
        index = (k_level + exp_level) * i + k_level * e + k
        self.params_array[self.num_alpha + self.num_betai + self.num_betau + index] = value

class Review:
    
    # e = 0 ... exp_leve - 1
    def __init__(self, user_id, product_id, rating, timestamp):
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.timestamp = timestamp
        self.exp = -1

class ModelFitter:
    
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self._read()

    def _read(self):
        self.user_ratings_map = {}
        self.user_mapping = {}
        self.product_mapping = {}
        self.num_users = 0
        self.num_products = 0
        with open(self.csv_file, "rb") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                product_id = row[0]
                user_id = row[1]
                rating = float(row[2])
                timestamp = int(row[3])

                # normalized user id
                if user_id not in self.user_mapping:
                    self.user_mapping[user_id] = self.num_users
                    self.num_users += 1
                n_user_id = self.user_mapping[user_id]

                if product_id not in self.product_mapping:
                    self.product_mapping[product_id] = self.num_products
                    self.num_products += 1
                n_product_id = self.product_mapping[product_id]

                if n_user_id not in self.user_ratings_map:
                    self.user_ratings_map[n_user_id] = []
                self.user_ratings_map[n_user_id].append(Review(user_id, product_id, rating, timestamp))

        alphas = [0] * exp_level
        alpha_counts = [0] * exp_level
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

        # init_alphas
        self.init_alphas = [float(alpha/(count+1)) for alpha, count in zip(alphas, alpha_counts)]
        self.params = Params(self.num_users, self.num_products, self.init_alphas)

        print "num_user %d" % self.num_users
        print "num_prod %d" % self.num_products

    @staticmethod
    def calculate_error(params, model, review):
        e = review.exp
        u = model.user_mapping[review.user_id]
        p = model.product_mapping[review.product_id]

        rec = params.alpha(e)
        rec += params.betau(e, u) + params.betai(e, p)
        for k in range(0, k_level):
            rec += params.gammau(e, u, k) * params.gammai(e, p, k)
        return abs(rec - review.rating)

    @staticmethod
    def objective(params_array, *args):
        model = args[0]
        params = Params(model.num_users, model.num_products, params_array=params_array)
        obj = float(0)
        for n_user_id in model.user_ratings_map:
            for review in model.user_ratings_map[n_user_id]:
                obj += ModelFitter.calculate_error(params, model, review)**2
        return obj

    @staticmethod
    def convergence(xk):
        print "1"

    def fit_params(self):
        p, f, d = scipy.optimize.fmin_l_bfgs_b(ModelFitter.objective, \
                                                x0=numpy.array(self.params.params_array), \
                                                args=(self,), approx_grad=True, \
                                                maxiter=2, iprint=1, callback=ModelFitter.convergence)
        #p, f, d = scipy.optimize.fmin_l_bfgs_b(objective1, x0=numpy.array(init_params), \
        #    args=(0,0), approx_grad=True, maxiter=2, iprint=1, callback=ModelFitter.convergence)
        return (p, f, d)


#init_params=[0]*200000
#def objective1(params, *args):
#    return float(0)