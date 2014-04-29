import sys
import csv
from data import CSVDataProcessor

# Evaluate recommender system according to Mean Squared Error (MSE)
# Equation 6 from Julian's paper. 
# csv file format: product_id, user_id, rating, timestamp

# Returns a map from (user_id, product_id) to rating
def read_file(filename):
	ratings_map = {}
	with open(filename, "rb") as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=",")
		for row in csv_reader:
			product_id = row[0]
			user_id = row[1]
			rating = float(row[2])
			timestamp = int(row[3])

			if user_id != "unknown":
				ratings_map[(user_id, product_id)] = rating
	return ratings_map

def find_MSE(our_rating_file, true_rating_file):
	our_rating_map = read_file(our_rating_file)
	true_rating_map = read_file(true_rating_file)
	error = 0
	count = 0
	unaccounted = 0
	for (user_id, product_id) in our_rating_map:
		our_rating = our_rating_map[(user_id, product_id)]
		if (user_id, product_id) in true_rating_map:
			true_rating = true_rating_map[(user_id, product_id)]
			error += (true_rating - our_rating)**2
			count += 1
		else:
			unaccounted += 1
	total = unaccounted + count
	percentUnaccounted = float(unaccounted) / total
	return (float(error) / count, percentUnaccounted, total)

def main():
	if len(sys.argv) != 3:
		print "Usage: python", sys.argv[0], "your_file ground_truth_file"
		exit(-1)
	res = find_MSE(sys.argv[1], sys.argv[2])
	print "Results over", res[2], "cases" 
	print "\tMean Squared Error:", res[0]
	print "\t% unaccounted", res[1]


# Given timestamp, return exp level of user
def find_exp_level(timestamp, user_id):
	user_reviews = [] # should get list of user Review objects, sorted by time
	exp_level = 0
	for rev in user_reviews:
		exp_level = rev.exp_level
		if rev.timestamp > timestamp: return exp_level
	return exp_level
	
if __name__ == "__main__":
  main()