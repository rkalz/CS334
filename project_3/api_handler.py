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
        # Resource tracking
        self.available_graphs = []
        self.crawled_people = []
        self.secret_flags = []
        self.challenges = []
        self.friend_network = []

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

    """ Gets all available graphs, we do 2, 3, and 4. """

    def get_graphs(self):
        try:
            graph_dict = self.http.send_request("GET", "/api/v1/graphs", None)
            for item in graph_dict['graphs']:
                self.available_graphs.append(item['graph_id'])
            return self.available_graphs
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get or set graphs.")
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

    """ Extracts individual uid's. Pass a people_list - it can be empty: get_people(crawl_session, people_list=[]) """

    def get_people(self, crawl_session, people_list):
        try:
            self.sort_people(people_list)
            for item in crawl_session['data']['people']:
                if item['uid'] not in self.crawled_people:
                    self.crawled_people.append(item['uid'])
                people_list.append(item['uid'])
            return people_list
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get people - check crawl_session and ensure you are passing at least an empty empty along with the crawl_session.")
            return False

    """ Gets random people from the current crawl, the server knows which crawl you are on automatically. I added tracking above to help out. Only returns the list you pass to it, however it does add any new people to the global list. """

    def get_random_people(self, people_list):
        try:
            self.sort_people(people_list)
            random_selection = self.http.send_request(
                "GET", "/api/v1/graphs/random_people", None)
            for item in random_selection['people']:
                if item['uid'] not in self.crawled_people:
                    self.crawled_people.append(item['uid'])
                    people_list.append(item['uid'])
            return people_list
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get random people - Check that you've initated a crawl as that's a prerequisite ")
            return False

    """ Will get all of the friends of either a list of people you pass it or the globaly collected friend network in the handler. Passing an empty array for people_list
  will return the global network list. """

    def get_friends(self, people_list):
        try:
            local_friend_network = []
            if people_list == []:
                for i in range(len(self.crawled_people)):
                    current_user = self.crawled_people[i]
                    friend_list = self.http.send_request(
                        "GET", "/api/v1/friends/"+str(self.crawled_people[i]), None)
                    user_and_friends = (current_user, friend_list)
                    local_friend_network.append(user_and_friends)
                    self.friend_network.append(friend_list)
                return local_friend_network
            elif people_list != []:
                self.sort_people(people_list)
                for i in range(len(people_list)):
                    current_user = self.crawled_people[i]
                    friend_list = self.http.send_request(
                        "GET", "/api/v1/friends/"+str(people_list[i]), None)
                    user_and_friends = (current_user, friend_list)
                    local_friend_network.append(user_and_friends)
                    self.friend_network.append(friend_list)
                return local_friend_network
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get list of friends - ensure you are passing at least an empty array..")
            return False

    """ 
  Keeps track of all the people by adding them to the global list if they aren't already on it. 
  """

    def sort_people(self, people_list):
        try:
            if people_list == []:
                return False
            elif people_list != []:
                for i in range(len(people_list)):
                    if people_list[i] not in self.crawled_people:
                        self.crawled_people.append(people_list[i])
                return True
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to sort people correctly.")
            return False

    """ Gets a challenge if you have one. If none will return False. """

    def get_challenge(self):
        try:
            challenge = self.http.send_request(
                "GET", "/api/v1/challenges/", None)
            if challenge['challenge'] != None:
                self.challenges.append(challenge)
                return challenge
            else:
                return False
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get challegne - make sure you have one!")
            return False

    """ Function to post solution to a challenge - if you have one. {'error': "You don't have a challenge ready!"}
  If you fail server will return {'failure': 'You did not get the right answer. Better luck next time!'} """

    def post_challenge(self, solution):
        try:
            response = self.http.send_request(
                "POST", "/api/v1/challenges/", solution)
            return response
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to post challenge.")
            return False

    """ Function to go through list of people's beets and extract flags. Flags are tracked globally on handler. 
  If you don't pass a list it will use the global list.  """

    def get_flags(self, people_list):
        try:
            if people_list == []:
                # Iterates through people array
                for i in range(len(self.crawled_people)):
                    # Makes GET request for the beet of that person
                    beet = self.http.send_request(
                        "GET", "/api/v1/beets/"+str(self.crawled_people[i]), None)
                    # Iterates through the beets of that person, checking each for the first 12 characters that match "SECRET FLAG:"
                    for item in beet['beets']:
                        # If it matches append it to secret_flags array
                        if item['text'][0:12] == "SECRET FLAG:":
                            self.secret_flags.append(item['text'])
            elif people_list != []:
                self.sort_people(people_list)
                for i in range(len(self.crawled_people)):
                    beet = self.http.send_request(
                        "GET", "/api/v1/beets/"+str(self.crawled_people[i]), None)
                    for item in beet['beets']:
                        if item['text'][0:12] == "SECRET FLAG:":
                            self.secret_flags.append(item['text'])
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to get flags - ensure you're passing at least an empty list.")
            return False

    """ API is JSON based -
  
  * Every function that makes an http request returns a Python Dictionary. The server returns json but http_handler serializes it. 
  
  * If you want json data use jsonify() or json.dumps() below.

  * When manipulating the data in program make sure it is type dict and not type string (json)
    i.e.
      dict = json.loads(json) or use dictify() below

  * Recieving data as Python Dict - in memory object vs JSON - string representation of an object

  Example accessing a single point of data in an array of Python Dicts: print(dict[0]['key'][0]) 
  """

    def jsonify(self, dict_data):
        try:
            json_data = self.json.dumps(dict_data)
            return json_data
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to jsonify - check you've imported everything correctly.")
            return False

    def dictify(self, json_data):
        try:
            dict_data = json.loads(json_data)
            return dict_data
        except Exception as e:
            if self.debug:
                print("ApiHandler: Error: "+str(e) +
                      " Failed to dictify - check you've imported everything correctly.")
            return False


""" Main testing function - plenty of examples here. """
if __name__ == "__main__":

    # Unimplemented - likely to go in logic class.
    # print("./api_handler odin.cs.uab.edu 3001 Lazrak13 ecBA8sbo 1")

    """ Initalization of ApiHandler - Debug set to true ( also sets it to true for HttpHandler )

    Second parameter is for verboseDebug output for the tests: """

    handler = ApiHandler(True, True)

    # Auth dict
    authorization = {
        "email": "lazrak13@uab.edu",
        "password": "ecBA8sbo",
        "grant_type": "password"
    }
    # Testing type
    if handler.verboseDebug:
        print("ApiHandler: ")
        print("---------------------------")
        print("Checking type: "+str(type(authorization)))
        print("---------------------------")

    # Tests connection and logs in - stores token.
    if handler.verboseDebug:
        print("ApiHandler: ")
        print("---------------------------")
        print("Attempting connection and login: " +
              str(handler.login(authorization)))
        print("---------------------------")
    else:
        handler.login(authorization)

    # Use to get list of graphs
    if handler.verboseDebug:
        graphs = handler.get_graphs()
        print("ApiHandler: ")
        print("---------------------------")
        print("Attempting to get available graphs: "+str(graphs))
        print("---------------------------")
    else:
        graphs = handler.get_graphs()

    # Keeping track of current instances of each as a backup
    if handler.verboseDebug:
        current_token = handler.access_token
        print("ApiHandler: ")
        print("---------------------------")
        print("Keeping track of local and global tokens seperatly: ")
        print("Global token: "+str(handler.access_token) +
              " Local token: "+str(current_token))
        print("---------------------------")
    else:
        current_token = handler.access_token

    # Using test graph for initial crawl - returns crawl_session dict
    if handler.verboseDebug:
        current_crawl = handler.crawl(graphs[0], current_token)
        print("ApiHandler: ")
        print("---------------------------")
        print("Using test graph - should return crawl_session dict: ")
        print("Current crawl_session: "+str(current_crawl))
        print("---------------------------")
    else:
        current_crawl = handler.crawl(graphs[0], current_token)

    # Extracts uids into array
    if handler.verboseDebug:
        current_people = handler.get_people(current_crawl, people_list=[])
        print("ApiHandler: ")
        print("---------------------------")
        print("Testing local people list: "+str(current_people))
        print("---------------------------")
    else:
        current_people = handler.get_people(current_crawl, people_list=[])

    # Uses uids to get flags out of user beets
    if handler.verboseDebug:
        handler.get_flags(current_people)
        print("ApiHandler: ")
        print("---------------------------")
        print("Getting flags from people's beets in the passed list: " +
              str(handler.secret_flags))
        print("---------------------------")
    else:
        handler.get_flags(current_people)

    # Use this to get more people from current crawl without recrawling
    if handler.verboseDebug:
        randomly_selected_people = handler.get_random_people(people_list=[])
        print("ApiHandler: ")
        print("---------------------------")
        print("Testing randomly selected people from graph currently being crawled: ")
        print("Graph: "+str(handler.crawl_session['graph_id']))
        print("Random selections: "+str(randomly_selected_people))
        print("---------------------------")
    else:
        randomly_selected_people = handler.get_random_people(people_list=[])

    # Examples on how to get the local or global list of friends:
    if handler.verboseDebug:
        local_list = handler.get_friends(current_people)
        global_list = handler.get_friends(people_list=[])
        print("ApiHandler: ")
        print("---------------------------")
        print("Local list: "+str(local_list))
        print("global list: "+str(global_list))
        print("---------------------------")
    else:
        local_list = handler.get_friends(current_people)
        global_list = handler.get_friends(people_list=[])

    # Examples of json de/serialization:
    if handler.verboseDebug:
        json_data = handler.jsonify(global_list[0])
        dict_data = handler.dictify(json_data)
        print("ApiHandler: ")
        print("---------------------------")
        print("JSON Data: "+str(json_data))
        print("JSON Type: "+str(type(json_data)))
        print("---------------------------")
        print("Dictionary Data: "+str(dict_data))
        print("Dictionary Type: "+str(type(dict_data)))
        print("---------------------------")
    else:
        json_data = handler.jsonify(global_list[0])
        dict_data = handler.dictify(json_data)

    # Use to get challenge again if you lost it, can also check handler.challenges array
    if handler.verboseDebug:
        print("ApiHandler: ")
        print("---------------------------")
        print("Getting challenge: "+str(handler.get_challenge()))
        print("---------------------------")
    else:
        challenge = handler.get_challenge()
    # Solution example from api.docs:
    # Type dict - POST function in http_handler does conversions to json
    solution = {
        "distance": 0
    }
    # Testing type:
    if handler.verboseDebug:
        print("ApiHandler: ")
        print("---------------------------")
        print("Testing type: "+str(type(solution)))
        print("---------------------------")
    # POST challenge solution
    if handler.verboseDebug:
        print("ApiHandler: ")
        print("---------------------------")
        print("Posting challenge: "+str(handler.post_challenge(solution)))
        print("---------------------------")
    else:
        handler.post_challenge(solution)

    # Closing connection and ending test
    if handler.verboseDebug:
        print("ApiHandler: ")
        print("---------------------------")
        print("Closing connection and sockets - Errors: "+str(handler.close()))
        print("---------------------------")
    else:
        handler.close()
