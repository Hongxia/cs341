from parser import ParamParser
from numpy import *
import time
import multiprocessing
from multiprocessing import Process, Queue

exp_level = 5
k_level = 5

def worker_calculate_error(queue, params, user_ratings, num_users, num_products, calculate_gradient, shared_gradients):
    pp = ParamParser(num_users, num_products, params)
    if calculate_gradient:
        gradients = zeros(sum(ParamParser.params_dimensions(num_users, num_products)))
        gp = ParamParser(num_users, num_products, gradients)
    obj = 0
    for user_rating in user_ratings:
        e = user_rating[4]
        u = user_rating[1]
        p = user_rating[0]
        rating = user_rating[2]
        rec = pp.alpha(e) + pp.betau(e, u) + pp.betai(e, p) + dot(pp.gammau(e, u), pp.gammai(e, p))
        error = (rec - rating)
        obj += error ** 2
        if calculate_gradient:
            gp.incr_alpha(e, 2 * error)
            gp.incr_betau(e, u, 2 * error)
            gp.incr_betai(e, p, 2 * error)
            for k in range(k_level):
                gp.incr_gammau(e, u, k, 2 * error * pp.gammaik(e, p, k))
                gp.incr_gammai(e, p, k, 2 * error * pp.gammauk(e, u, k))
    
    queue.put(obj)
    if calculate_gradient:
        shared_gradients += gp.params