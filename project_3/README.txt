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

Backup_Crawler: A backup crawler was used acting as a backup should something happen to the main crawler. Backup_Crawler was written
before api_handler and thus uses the HTTP handler directly. Djikstra is correctly working in this crawler. This crawler
works by first parsing the beets of a user, then adding their friends to the graph, accounting for challenges that may
occur during those requests.

Difficulties:
HTTP Handler: The handler was able to adjust to the new changes without much hassle. Most of our issues came from upstream.

api_handler.py: The difficulties came from the way the data was structures and needing to extract various data points while
maintaining continuity.

backup_crawler: Most of backup crawler's issues came from assumptions about the responses from the Bitter API. Attempting
to access certain keys in either a null object or a JSON response that didn't have that key would result in a crash. THis
was alleviated by checking if the desired key existed in the response dict, and retrying the requests if it didn't.

Bittercrawler:

Testing:

HTTP Handler: Tests were created to make sure that the new function could send JSON, add headers, and send additional
requests after that.

api_handler.py: The simple test case in __main__ confirms all the functions work. Additional flags for debug responses and verbose debug
responses provided.

backup_crawler: Backup crawler was simply run until the desired keys were spit out, with bugs being fixed as they appeared.

Webcrawler:
