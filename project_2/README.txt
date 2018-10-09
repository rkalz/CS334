NEEDS UPDATING!

How to run:
python3 webcrawler.py <username> <password>
./webcrawler.py <username> <password>

Approach:
HTTP Handler: The high level implementation of the HTTP handler was straightforward: Open a socket, send the request,
receive the response, handle it based on what was received, handle exceptions, and close the socket when done. My code
would either return the HTML response, or None if something happened (exceptions, 4XX error code). The header had some
properties hard coded (User-Agent, Host, Connection), and other values set based on whether there was a body (Content-
Length, Content-Type) or the state of the handler object (Cookies). Responses were read in until the HTTP/1.1
termination string ("0\r\n\r\n") was read. Response handling was determined based on if the first line started with
"HTTP 1.1" and then the response code was extracted and used to handle the response (4XX errors, redirects, OK).
Cookies would then be updated, and the appropriate action would be made based on the response (retry redirect,
return None, return the HTML response)

HTML Handler: HTML Handler recieved any HTML given to it's parsing functions and sorted through it to extract all the links and the flags. It then returned an array of each which allowed the program to function.

Difficulties:
HTTP Handler: There were several difficulties involved with writing the HTTP handler. With the original Flask(?) server,
without headers, the request would be sent in chunks, meaning the first chunk would arrive without the authenticity
token and return an error. This was resolved by specifying Content-Length. Another issue I ran into was that the socket
closed after each request. Since the requests were HTTP/1.0, this was expected behavior, and the code was changed to
create a new socket for each request.
When the backend was changed to Rails, it was decided to adapt the code to HTTP/1.1. Host and Connection headers were
added to meet HTTP/1.1 standards and to allow working with a single socket without opening and closing it, respectively.
The new code also had to account for how HTTP/1.1 handles chunked body responses (the body starts with the number of
bytes to be sent, and ends with 0\r\n\r\n).
By far the biggest nuisance when working on this project was sending the authenticity token. The token used characters
usually reserved by HTTP. To address this, characters generally have URL encoding complements as to tell HTTP not to
treat this as a special character, but as a character literal. The only character that needed to be replaced was "+"
with "%2B", which fixed that issue.

HTML Handler: At first I used the python html.parser library but it proved to be inadequate for finding flags or links. The way it functioned was not ideal for a use case where it would be given large amounts of HTML and need to return very specific data. BeautifulSoup solved this issue by providing easier to use functions that could sift through the large amount of data in a better way. I also had to account for None returned from the HTTP Handler which caused the program to crash at first.

Testing:
HTTP Handler: Three test cases were devised to ensure that the HTTP handler was working. The first was a simple GET
request, to ensure that the socket was correctly sending requests, reading responses, and properly
formatting HTML output. The second was sending a POST with URL parameters, testing POST, storing cookies, properly
formatting the body, and handling redirects. The final was sending a GET after authentication, made to test
usage of cookies to handle authentication. All test cases combined would test keeping the socket alive. Wireshark
was used to monitor any network activity that might not be evident in the response handling code by filtering packets
"tcp.port == 3001 and http".

HTML Handler: The simple test case in __main__ confirms that it will return data from the appropriate tags.

