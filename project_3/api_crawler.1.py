# NEEDS CHANGING TO CLASS FORMAT

import json
from http_handler import HttpHandler

# Init
http = HttpHandler(False)
authorization = {
  "email": "lazrak13@uab.edu",
  "password": "ecBA8sbo",
  "grant_type": "password"
}
people = []
secret_flags = []
friend_network_dict = []
friend_network_json = []
challenges = []

""" import json
 
json_data = '{"name": "Brian", "city": "Seattle"}'
python_obj = json.loads(json_data)
print json.dumps(python_obj, sort_keys=True, indent=4) """

# Connecting
http.connect()
# Authorization - Getting json response
oauth_response = http.send_request("POST", "/oauth/token", authorization)
# Extracting access token
access_token = oauth_response['access_token']
# Adding proper header to http object
http.add_header("Authorization", oauth_response["token_type"] + " " + access_token)

# GET info about available graphs
available_graphs = http.send_request("GET", "/api/v1/graphs", None)

# Making POST request for initial crawl, this binds to the auth key!
crawl_session = http.send_request("POST", "/api/v1/crawl_sessions/2", None)

# GET random selection people from crawl, need to have initated a crawl to use this.
random_selection = http.send_request("GET", "/api/v1/graphs/random_people", None)

# Iterating through initial graph to take out uids
for item in crawl_session['people']:
  people.append(item['uid'])

# Iterates through people array
for i in range(len(people)):
  # Makes GET request for the beet of that person
  beet = http.send_request("GET", "/api/v1/beets/"+str(people[i]), None)
  # Iterates through the beets of that person, checking each for the first 12 characters that match "SECRET FLAG:"
  for item in beet['beets']:
    # If it matches append it to secret_flags array
    if item['text'][0:12] == "SECRET FLAG:":
      secret_flags.append(item['text'])

# GET challenge
challenge = http.send_request("GET", "/api/v1/challenges/", None)
challenges.append(challenge)

# POST challenge

# GET friends:

""" Using Json and Python dicts:
When manipulating the data in program make sure it is a dict and not a string (json)
i.e.
  dict = json.loads(json)
When sending data back over the network in POST requests serialize the dict into json data format
i.e.
  json = json.dumps(dict)
Recieving data as Python Dict - in memory object vs json - string representation
Example accessing a single point of data in an array of python dicts: 
print(friend_network_dict[0]['friends'][0]) - friend_network_dict[0th array][key value of dict][0th element from that key value]"""

# DICT
for i in range(len(people)):

  friend_list = http.send_request("GET", "/api/v1/friends/"+str(people[i]), None)
  friend_network_dict.append(friend_list)

# JSON:
for i in range(len(people)):
  # Recieves as Python Dict
  friend_list = http.send_request("GET", "/api/v1/friends/"+str(people[i]), None)
  # Uses Python json library to serialize the dict into json data format to send over HTTP
  friend_network_json.append(json.dumps(friend_list))

""" Dict/Json data is stored in arrays - make sure to properly extract the json from the array before attempting to serialize/send. ( Shown above )

print("DICT: "+str(friend_network_dict))
print("JSON: "+str(friend_network_json)) """