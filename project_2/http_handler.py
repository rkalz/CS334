import socket

# HttpHandler used primarily to keep track of cookies
class HttpHandler:
    def __init__(self, debug):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(30)

        self.host = "odin.cs.uab.edu"
        self.port = 3001
        self.cookies = dict()

        self.debug = debug


    # Connects to Odin on port 3001
    # Returns true if successful, otherwise false
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
        except Exception as e:
            if self.debug:
                print("failed to connect to socket: " + str(e))
            return False

        return True

    # Sends a HTTP request over the connect
    # type = either "GET" or "POST"
    # url = portion of URL AFTER the domain
    #   i.e. http://odin.cs.uab.edu:3001/fakebook -> /fakebook
    #   it is the job of the person using this function to remove the domain
    #   and make sure the path exists on http://odin.cs.uab.edu:3001
    #   URL parameters should be passed (/fakebook/?user=hello&pass=there)
    # returns (True, raw HTML response) if successful
    # returns (False, None) if failed
    def send_request(self, type, url):
        body = None
        if url.find("?") != -1:
            # Remove url paramaters and place them in body
            url = url[:url.find("?")]
            body = url[url.find("?"):]

        request = type + " " + url + " HTTP/1.0\r\n"
        request += "User-Agent: CS 334 Project 2 Group 1\r\n" # This is just for fun
        # If there are saved cookies, add them to the request
        if len(self.cookies) != 0:
            request += "Cookie: "
            for key, val in self.cookies.items():
                request += key
                request += "="
                request += "; "
            request += "\r\n"
        request += "\r\n"
        if body is not None:
            request += body + "\r\n"
            request += "\r\n"

        # Encode and send request, return False if socket fails
        request = request.encode()
        try:
            self.socket.sendall(request)
        except Exception as e:
            if self.debug:
                print("failed to send to socket: " + str(e))
            return False, _

        # Read entire response, return if socket fails
        try:
            response = ""
            raw_response = self.socket.recv(4096)
            while len(raw_response) > 0:
                raw_response = raw_response.decode()
                response += raw_response
                raw_response = self.socket.recv(4096)
        except Exception as e:
            if self.debug:
                print("failed to read response from socket: " + str(e))
            return False, _

        response_lines = response.split("\r\n")

        # Handle HTTP Response Codes
        http_status = response_lines[0]
        if http_status.find("HTTP") == -1:
            # We didn't get a HTTP response
            return False, None

        if http_status.find("301") != -1 or http_status.find("302") != -1:
            # Redirect by finding location header
            if self.debug:
                print("encountered 301 Moved or 302 Found")
            for line in response_lines:
                if line.find("Location") != -1:
                    # Extract redirect url from Location header
                    redirect_url = line[line.find(":") + 2]
                    if redirect_url.find("odin.cs.uab.edu") == -1:
                        # url redirects outside of Odin
                        return False, None

                    # Strip domain/port from request (five characters after the colon from the port number
                    redirect_url = redirect_url[redirect_url.rfind(":") + 5:]
                    return self.send_request(request, redirect_url)

            # Didn't find a Location header
            return False, None

        if http_status.find("403") != -1 or http_status.find("404") != -1:
            # Forbidden or Not Found - Stop looking
            if self.debug:
                print("encountered 403 Forbidden or 404 Not Found")
            return False, None

        if http_status.find("500") != -1:
            # Internal Server Error - Should retry
            if self.debug:
                print("encountered 500 Internal Server Error")
            return self.send_request(request, url)

        # Check for and store cookies
        for line in response_lines:
            if line.find("Set-Cookie") != 0:
                cookie_name = line[line.find(":") + 2:line.find("=")]
                cookie_value = line[line.find("=") + 1:line.find(";")]
                self.cookies[cookie_name] = cookie_value

        return True, response


if __name__ == "__main__":
    debug = True
    handler = HttpHandler(debug=True)
    socket_status = handler.connect() # Implemented in case socket connect fails on first try
    if not socket_status:
        print("Failed to connect")
    else:
        print(handler.send_request("GET", "/fakebook/")[1])