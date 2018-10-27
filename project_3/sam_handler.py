# Yeah I'll rename it later

import json
from http_handler import HttpHandler

### DeBUGGING COMMENTS###

# Init
http = HttpHandler(False)
authorization = {
  "email": "lazrak13@uab.edu",
  "password": "ecBA8sbo",
  "grant_type": "password"
}

# Test connection
http.connect()

print("----")
print("Status of connection:")
print(http.connected)

# Test Authorization
oauth_response = http.send_request("POST", "/oauth/token", authorization)
access_token = oauth_response['access_token']
http.add_header("Authorization", oauth_response["token_type"] + " " + access_token)

print("----")
print("access_token: ")
print(access_token)
print("----")
print("http headers: ")
print(http.headers)
print("----")
print("http cookies: ")
print(http.cookies)

print("----")
print("Authorization finished")


bind_to_graph = http.send_request("POST", "/api/v1/crawl_sessions/1", None)

print("----")
print("bind_to_graph: ")
print(bind_to_graph)
