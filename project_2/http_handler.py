import socket


# HttpHandler used primarily to keep track of cookies
class HttpHandler:
    def __init__(self, debug=False):
        self.socket = None

        self.host = "odin.cs.uab.edu"
        self.port = 3001
        self.cookies = dict()
        self.connected = False

        self.debug = debug

    def set_debug(self, new_debug):
        self.debug = new_debug

    # Connects to Odin on port 3001
    # Returns true if successful, otherwise false
    # Needed just in case connection fails
    def _connect(self):
        if self.connected:
            return False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(30)

        try:
            self.socket.connect((self.host, self.port))
        except Exception as e:
            if self.debug:
                print("failed to connect to socket: " + str(e))
            return False

        self.connected = True
        return True

    # Close the socket when done
    # Returns true if successful, otherwise false
    def _close(self):
        if not self.connected:
            return False

        try:
            self.socket.close()
        except Exception as e:
            if self.debug:
                print("failed to close socket: " + str(e))
            return False

        self.socket = None
        self.connected = False
        return True

    # Sends a HTTP request over the connect
    # request_type = either "GET" or "POST"
    # url = portion of URL AFTER the domain
    #   i.e. http://odin.cs.uab.edu:3001/fakebook/ -> /fakebook/
    #   it is the job of the person using this function to remove the domain
    #   and make sure the path exists on http://odin.cs.uab.edu:3001
    #   URL parameters should be passed like "/fakebook/?username=hello&password=there"
    # returns raw HTML response if successful
    # returns None if failed
    def send_request(self, request_type, url):
        self._connect()

        body = None
        if url.find("?") != -1:
            # Remove url paramaters and place them in body
            body = url[url.find("?")+1:]
            url = url[:url.find("?")]

        # Build the header
        request = request_type + " " + url + " HTTP/1.0\r\n"
        # User-Agent isn't needed, just for fun
        request += \
            "User-Agent: Mozilla/5.0 (compatible; HttpHandler/1.0; +http://group1.project2.cs334.cs.uab.edu)\r\n"
        # If there are saved cookies, add them to the request
        if len(self.cookies) != 0:
            request += "Cookie: "
            for key, val in self.cookies.items():
                request += key
                request += "="
                request += val
                request += "; "
            request = request[:len(request)-2]
            request += "\r\n"
        if body is not None:
            if self.debug:
                request += "Content-Type: application/x-www-form-urlencoded\r\n"  # Makes body look pretty in Wireshark
            request += "Content-Length: " + str(len(body)) + "\r\n"  # Will otherwise send in chunks
        request += "\r\n"                                            # (HTTP/1.0 doesn't support chunks)

        # Add body to request if present
        if body is not None:
            request += body

        # Encode and send request, return False if socket fails
        request = request.encode()
        try:
            self.socket.sendall(request)
        except Exception as e:
            if self.debug:
                print("failed to send to socket: " + str(e))
            return None

        # Read entire response, return if socket fails
        try:
            response = ""
            raw_response = self.socket.recv(1024)
            while len(raw_response) > 0:
                raw_response = raw_response.decode()
                response += raw_response
                raw_response = self.socket.recv(1024)
        except Exception as e:
            if self.debug:
                print("failed to read response from socket: " + str(e))
            return None

        self._close()
        response_lines = response.split("\r\n")

        # Handle HTTP Response Codes
        http_status = response_lines[0]
        if http_status.find("HTTP") == -1:
            # We didn't get a HTTP response
            return None

        # Check for and store cookies
        for line in response_lines:
            if line.find("Set-Cookie") != -1:
                cookie_name = line[line.find(":") + 3:line.find("=")]
                cookie_value = line[line.find("=") + 1:line.find(";")]
                self.cookies[cookie_name] = cookie_value

        if http_status.find("301") != -1 or http_status.find("302") != -1:
            # Redirect
            if self.debug:
                print("encountered 301 Moved or 302 Found")
            for line in response_lines:
                if line.find("Location") != -1:
                    # Extract redirect url from Location header
                    redirect_url = line[line.find("://")+3:]
                    if redirect_url.find("odin.cs.uab.edu") == -1:
                        # url redirects outside of Odin
                        return None

                    new_request = redirect_url[redirect_url.find("/"):]
                    # Redirect is always GET
                    return self.send_request("GET", new_request)

            # Didn't find a Location header
            return None

        if http_status.find("403") != -1 or http_status.find("404") != -1:
            # Forbidden or Not Found - Stop looking
            if self.debug:
                print("encountered 403 Forbidden or 404 Not Found")
            return None

        if http_status.find("500") != -1:
            # Internal Server Error - Should retry
            if self.debug:
                print("encountered 500 Internal Server Error")
            return self.send_request(request_type, url)

        # Remove HTTP stuff from response for HTML parser
        response = response[response.find("<"):]

        return response


if __name__ == "__main__":
    handler = HttpHandler()

    # Test simple get
    home_page = handler.send_request("GET", "/")
    if home_page is not None:
        print(home_page)

    # Test a redirecting page
    login_page = handler.send_request("GET", "/fakebook/")
    if login_page is not None:
        print(login_page)

    # Get CSRF middleware token from login page
    token_identifier = "name='csrfmiddlewaretoken' value='"
    token_start = login_page.find(token_identifier)
    token = ""
    if token_start != -1:
        token = login_page[token_start + len(token_identifier):]
        token = token[:token.find('\'')]
        token = "&csrfmiddlewaretoken=" + token

    # Test POST and params
    main_menu = handler.send_request("POST",
                                     "/accounts/login/?password=BMWTGME7&username=rofael&next=/fakebook/" + token)
    if main_menu is not None:
        print(main_menu)

    # Test GET with cookies
    user_menu = handler.send_request("GET", "/fakebook/156714994/")
    if user_menu is not None:
        print(user_menu)
