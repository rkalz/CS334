import json
import sys

from http_handler import HttpHandler

""" 
Quick use: 

authorization = {
  "email": "Email@uab.edu",
  "password": "Password",
  "grant_type": "password"
}

handler = ApiHandler(authorization)

More examples below in __main__
"""


class ApiHandler:
    def __init__(self, debug=False, verboseDebug=False):
        # Libraries - Pass True if you get issues, change back before turning in. )
        self.http = HttpHandler(debug)
        self.json = json
        self.sys = sys
        # Debug
        self.debug = debug
        self.verboseDebug = verboseDebug
        # Auth tracking
        self.authorization = None
        self.access_token = None
        self.used_tokens = []
        self.crawl_session = None

    """ Checks for connection and logs in, keeping track of access_token due to crawl's limitations.
  When you switch graphs or if your token expires you will need to call this again.

  ### Unimplemented ###
  ./api_handler [server] [port] [username] [password] [graph id] 
  ./api_handler odin.cs.uab.edu 3001 Lazrak13 ecBA8sbo 1

  - Not sure this will actually go here, might need to move it to the logic class and pass the arguments again.
  """

    def login(self, authorization):
        try:
            self.authorization = authorization
            self.http.connect()
            # Authorization - Getting json response
            oauth_response = self.http.send_request(
                "POST", "/oauth/token", authorization)
            # Extracting access token
            self.access_token = oauth_response['access_token']
            self.used_tokens.append(self.access_token)
            # Adding proper header to http object
            self.http.add_header(
                "Authorization", oauth_response["token_type"] + " " + self.access_token)
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to connect or login - check http_handler")
            return False

    """ End connection to server and kills sockets """

    def close(self):
        try:
            self.http.close()
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to close connection or kill sockets - check http_handler")
            return False

    """ Crawls the api for the initial graph. You will need to call this multiple times for each graph - 
  Creates a new Crawl Session that is immutably bound to the current authorization token 
  
  Pass desired graph and an access_token that hasn't already been used for a different graph. 
  
  Returns crawl_session dict in case you need to keep track. Data is accessed: crawl_session['key'] - for data: crawl_session['data']['people'][Array position]['uid']
  
  get_people() does the above.
  """

    def crawl(self, graph_id, access_token):
        try:
            data = self.http.send_request(
                "POST", "/api/v1/crawl_sessions/"+str(graph_id), None)
            crawl_session = {
                'data': data,
                'graph_id': graph_id,
                'access_token': access_token
            }
            self.crawl_session = crawl_session
            self.access_token = access_token
            return crawl_session
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to crawl - Check that access token hasn't already been used on another graph.")
            return False

    def get_people(self, crawl_session, newPeople):
        try:
            for item in crawl_session['data']['people']:
                if item['uid']:
                    newPeople.append(item['uid'])
            return newPeople
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get people - check crawl_session and ensure you are passing at least an empty empty along with the crawl_session.")
            return False
    
    def get_friends(self, person):
        friend_list = self.http.send_request(
            "GET", "/api/v1/friends/"+str(person), None)
        return person, friend_list

    def get_beets(self, person):
        beets = []
        beet = self.http.send_request(
        "GET", "/api/v1/beets/"+str(person), None)
        print(beet)
        if(beet is not None):
            if(beet.keys() == 'beets'):
                for i in range(len(beet['beets'])):
                    beets.append(beet['beets'][i])
            return beets

    def get_challenge(self):
        challenge = self.http.send_request(
                "GET", "/api/v1/challenges/", None)
        return challenge