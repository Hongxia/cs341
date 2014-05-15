from numpy import *

# Method 1: file dump experience level of each user (for each product) to file in formatted way, and able to read this.

# Method 2: file dump list of all params, and able to read all params

def dump_exp_level(user_reviews, output):
	print "Dumping experience levels"
	print user_reviews
	# output.write("user_reviews\n")
	for user_id in user_reviews:
		reviews = user_reviews[user_id]		
		output.write(str(user_id) + "\n")
		old_exp_level = -1
		for review in reviews:
			if review[4] != old_exp_level or old_exp_level == -1:
				output.write(str(review[3]) + ",") # timestamp
				output.write(str(review[4]) + "\n") # exp level
				old_exp_level = review[4]

def dump_params(params, output):
	print "Dumping model params"
	print params
	# output.write("params\n")
	for p in params:
		output.write(str(p) + "\n")

def read_output(output):
	user_exp_level = {}
	params = array([])
	reading_params = False
	with open('output.out', 'rb') as output:
		for line in output:
			if line == "\n":
				reading_params = True
				continue
			if reading_params:
				num = int32(line.strip())
				params = append(params, [num], axis=0)
			else:
				if "," in line:
					timestamp, exp_level = line.split(",")
					timestamp = int32(timestamp.strip())
					exp_level = int32(exp_level.strip())
					user_exp_level[user_id] = append(user_exp_level[user_id], [[timestamp, exp_level]], axis=0)
				else:
					user_id = int32(line.strip())
					user_exp_level[user_id] = empty((0, 2))
	return user_exp_level, params

if __name__ == "__main__":
	# numpy 2d array
  user_reviews = {4: array([[1, 2, 3, 5234234, 3], [5, 6, 7, 234234432, 1], [10, 20, 30, 4023232, 5]]), 
		9: array([[11, 21, 31, 512342, 4], [5, 6, 7, 912343214, 2], [19, 21, 21, 23234232, 4]])}
	# print user_reviews
  params = array([4, 5, 9])
	# print params
  with open('output.out', "wb") as output:
  	dump_exp_level(user_reviews, output)	
  	# New line indicates separation
  	output.write("\n")
  	dump_params(params, output)
  print 
  print "Reading the output file"
  user_exp_level, param = read_output(output)
  print user_exp_level
  print param

