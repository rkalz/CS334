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

# Connecting
http.connect()
# Authorization - Getting json response
oauth_response = http.send_request("POST", "/oauth/token", authorization)
# Extracting access token
access_token = oauth_response['access_token']
# Adding proper header to http object
http.add_header("Authorization", oauth_response["token_type"] + " " + access_token)

# Making POST request for initial graph
bind_to_graph = http.send_request("POST", "/api/v1/crawl_sessions/1", None)

# Iterating through initial graph to take out uids
for item in bind_to_graph['people']:
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

print(secret_flags)