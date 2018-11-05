How to run:
./bittercrawler.py [server] [port] [username] [password] [graph id]

Approach:
HTTP Handler:

api_handler.py: Abstracts the api for use by the bittercrawler, the appraoch was that it would simply the work of programming the
bittercrawler by simplifying interactions with the api. The api_handler sits on top of the http_handler and allows it to make all the
neccesary requests. 

Bittercrawler:

Difficulties:
HTTP Handler: 

api_handler.py: The difficulties came from the way the data was structures and needing to extract various data points while
maintaining continuity. 

Bittercrawler:

Testing:

api_handler.py: The simple test case in __main__ confirms all the functions work. Additional flags for debug responses and verbose debug
responses provided.

Webcrawler: 
