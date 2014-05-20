from numpy import *

# Method 1: file dump experience level of each user (for each product) to file in formatted way, and able to read this.

# Method 2: file dump list of all params, and able to read all params

def dump_exp_level(user_reviews, output):
	# print "Dumping experience levels"
	# print user_reviews
	# output.write("user_reviews\n")
	for user_id in user_reviews:
		reviews = user_reviews[user_id]		
		output.write(str(user_id) + "\n")
		old_exp_level = -1
		count = 0
		prev_review = None
		for review in reviews:
			if old_exp_level == -1: 
				start_time = review[3]
				old_exp_level = review[4]
			
			if review[4] != old_exp_level:
				output.write(str(start_time) + ",") # start_time
				output.write(str(prev_review[3]) + ",") # end_time
				output.write(str(old_exp_level) + ",") # exp level
				output.write(str(count) + "\n") # num_reivews
				count = 0
				old_exp_level = review[4]
				start_time = review[3]
			count += 1
			prev_review = review
		output.write(str(start_time) + ",") # start_time
		output.write(str(review[3]) + ",") # end_time
		output.write(str(review[4]) + ",") # exp level
		output.write(str(count) + "\n") # num_reivews

def dump_params(params, output):
	print "Dumping model params"
	print params
	# output.write("params\n")
	for p in params:
		output.write(str(p) + "\n")

# map user_id to list of lists
# each list has (start_time, end_time, exp, num_reviews)
def read_output(filename):
	user_exp_level = {}
	params = array([])
	reading_params = False
	with open(filename, 'rb') as output:
		for line in output:
			if line == "\n":
				reading_params = True
				continue
			if reading_params:
				num = int32(line.strip())
				params = append(params, [num], axis=0)
			else:
				if "," in line:
					start_time, end_time, exp_level, num_reviews = line.split(",")
					start_time = int32(start_time.strip())
					end_time = int32(end_time.strip())
					exp_level = int32(exp_level.strip())
					num_reviews = int32(num_reviews.strip())
					user_exp_level[user_id] = append(user_exp_level[user_id], [[start_time, end_time, exp_level,  num_reviews]], axis=0)
				else:
					user_id = int32(line.strip())
					user_exp_level[user_id] = empty((0, 4))
	return user_exp_level, params

# Assume reviews are ordered by time in user_exp_level
def get_exp_level(user_id, timestamp, user_exp_level):
	reviews = user_exp_level[user_id]
	old_exp_level = reviews[0][2]
	for review in reviews:
		if review[1] > timestamp: return old_exp_level
		old_exp_level = review[2]
	return reviews[len(reviews) - 1][2]

def create_exp_mem(user_reviews):
	# print "hell"
	user_exp_level = {}
	for user_id in user_reviews:
		if user_id not in user_exp_level: user_exp_level[user_id] = empty((0, 4))
		reviews = user_reviews[user_id]
		old_exp_level = -1
		count = 0
		prev_review = None
		for review in reviews:
			if old_exp_level == -1: 
				start_time = review[3]
				old_exp_level = review[4]
			
			if review[4] != old_exp_level:
				user_exp_level[user_id] = append(user_exp_level[user_id], [[start_time, prev_review[3], old_exp_level,  count]], axis=0)
				count = 0
				old_exp_level = review[4]
				start_time = review[3]
			count += 1
			prev_review = review
		user_exp_level[user_id] = append(user_exp_level[user_id], [[start_time, prev_review[3], review[4],  count]], axis=0)
	return user_exp_level

if __name__ == "__main__":
	# numpy 2d array
  user_reviews = {4: array([[1, 2, 3, 100, 3], [1, 2, 3, 102, 3], [1, 2, 3, 109, 3], [1, 2, 3, 120, 3],[5, 6, 7, 150, 4], [10, 20, 30, 300, 5], [10, 20, 30, 304, 5], [10, 20, 30, 309, 5]]), 
		9: array([[11, 21, 31, 100, 1], [5, 6, 7, 150, 1], [19, 21, 21, 300, 1]])}
  params = array([4, 5, 9])

  user_exp_level_mem = create_exp_mem(user_reviews)
  print user_exp_level_mem
  # with open('output.out', "wb") as output:
  # 	dump_exp_level(user_reviews, output)
  # 	output.write("\n") # New line indicates separation
  # 	dump_params(params, output)
  # print
  # print "Reading the output file"
  # user_exp_level, param = read_output('output.out')
  # # print user_exp_level
  # # print param
  # print get_exp_level(4, 50, user_exp_level)
  # print get_exp_level(4, 148, user_exp_level)
  # print get_exp_level(4, 200, user_exp_level)
  # print get_exp_level(4, 250, user_exp_level)
  # print get_exp_level(4, 350, user_exp_level)
  # print
  # print get_exp_level(9, 80, user_exp_level)
  # print get_exp_level(9, 100, user_exp_level)


