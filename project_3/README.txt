How to run:
./bittercrawler.py [server] [port] [username] [password] [graph id]

Approach:
HTTP Handler: The HTTP handler was mostly unchanged from Project 2. The only major differences being that the handler
sends all data as application/json, and has an extra input for a body. Also, an extra function was added to allow changing
the request headers based on a response (in this case, the auth token)

api_handler.py: Abstracts the api for use by the bittercrawler, the appraoch was that it would simply the work of programming the
bittercrawler by simplifying interactions with the api. The api_handler sits on top of the http_handler and allows it to make all the
neccesary requests. 

Bittercrawler: The crawler was not much different than assignment 2. The main differences was having to figure out how to account for the 
challenges. The crwaler tracks who's beets have and have not been checked for flags. Once the crawler ran into a challenge, it would then solve
the challenge by using dijkstra's. 

Difficulties:
HTTP Handler: The handler was able to adjust to the new changes without much hassle. Most of our issues came from upstream.

api_handler.py: The difficulties came from the way the data was structures and needing to extract various data points while
maintaining continuity. 

Bittercrawler:The hardest part of designing the crawler, was figuring out how to manipulate the data in a way it could be tracked.

Testing:

HTTP Handler: Tests were created to make sure that the new function could send JSON, add headers, and send additional
requests after that.

api_handler.py: The simple test case in __main__ confirms all the functions work. Additional flags for debug responses and verbose debug
responses provided.

Bittercrawler: Testing was pretty straight forward. Throughout development, each piece of logic was tested by adding print statements to see if
specific list were being manipulated properly. After that, the only testing was in finding the flags.
