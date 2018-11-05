How to run:
./bittercrawler.py [server] [port] [username] [password] [graph id]

Approach:
HTTP Handler: The HTTP handler was mostly unchanged from Project 2. The only major differences being that the handler
sends all data as application/json, and has an extra input for a body. Also, an extra function was added to allow changing
the request headers based on a response (in this case, the auth token)

api_handler.py: Abstracts the api for use by the bittercrawler, the appraoch was that it would simply the work of programming the
bittercrawler by simplifying interactions with the api. The api_handler sits on top of the http_handler and allows it to make all the
neccesary requests. 

Bittercrawler:

Difficulties:
HTTP Handler: The handler was able to adjust to the new changes without much hassle. Most of our issues came from upstream.

api_handler.py: The difficulties came from the way the data was structures and needing to extract various data points while
maintaining continuity. 

Bittercrawler:

Testing:

HTTP Handler: Tests were created to make sure that the new function could send JSON, add headers, and send additional
requests after that.

api_handler.py: The simple test case in __main__ confirms all the functions work. Additional flags for debug responses and verbose debug
responses provided.

Webcrawler: 
