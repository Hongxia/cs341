#!/usr/bin/python

if len(sys.argv) != 3:
    print "Usage: python find_common_users.py file_1 file_2"
    exit(1)
file_1 = sys.argv[1]
file_2 = sys.argv[2]

def parse_json_output(file):
    with open(file, "rb") as json_output:
        model = json.load(json_output)
        return model["user_mapping"]

user_mapping_1 = parse_json_output(file_1)
user_mapping_2 = parse_json_output(file_2)

common_users = set(user_mapping_1.keys()) & set(user_mapping_2.keys())
print json.dumps(list(common_users), sort_keys=True, indent=4)
