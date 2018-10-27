import json
import socket


# HttpHandler used primarily to keep track of cookies
class HttpHandler:
    def __init__(self, debug=False):
        self.socket = None

        self.host = "odin.cs.uab.edu"
        self.port = 3001
        self.connected = False

        self.headers = dict()
        # User-Agent isn't needed, just for fun
        self.add_header("User-Agent",
                        "Mozilla/5.0 (compatible; HttpHandler/1.1; +http://group1.project3.cs334.cs.uab.edu)")
        self.add_header("Host", "odin.cs.uab.edu:3001")
        self.add_header("Connection", "keep-alive")
        self.add_header("Content-Type", "application/json")

        self.cookies = dict()

        self.debug = debug

    def add_header(self, key, value):
        self.headers[key] = value

    def set_debug(self, new_debug):
        self.debug = new_debug

    # Connects to Odin on port 3001
    # Returns true if successful, otherwise false
    # Needed just in case connection fails
    def connect(self):
        if self.connected:
            return False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10)

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
    def close(self):
        if not self.connected:
            return False

        ending_socket = self.socket
        self.socket = None
        self.connected = False

        try:
            ending_socket.close()
        except Exception as e:
            if self.debug:
                print("failed to close socket: " + str(e))
            return False

        return True

    # Sends a HTTP request over the connect
    # request_type = either "GET" or "POST"
    # url = portion of URL AFTER the domain
    #   i.e. http://odin.cs.uab.edu:3001/fakebook/ -> /fakebook/
    #   it is the job of the person using this function to remove the domain
    #   and make sure the path exists on http://odin.cs.uab.edu:3001
    # json_dict - a Python dict object
    # returns JSON response as a dict object
    # returns None if failed
    def send_request(self, request_type, url, json_dict):
        if not self.connected:
            if self.debug:
                print("Not connected. Make sure to use connect()")
            return None

        json_string = ""
        if json_dict is not None:
            try:
                json_string = json.dumps(json_dict)
            except Exception as e:
                if self.debug:
                    print("failed to parse dictionary: " + str(e))
                return None

        # Build the header
        request = request_type + " " + url + " HTTP/1.1\r\n"
        self.add_header("Content-Length", str(len(json_string)))
        for key, value in self.headers.items():
            request += key + ": " + value + "\r\n"

        # If there are saved cookies, add them to the request
        if len(self.cookies) != 0:
            request += "Cookie: "
            for key, val in self.cookies.items():
                request += key + '=' + val + "; "
            request = request[:-2] + "\r\n"

        # End the header and add the body
        request += "\r\n" + json_string

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
            while True:
                raw_response = raw_response.decode()
                response += raw_response

                if "0\r\n\r\n" in raw_response:
                    break

                raw_response = self.socket.recv(1024)

        except Exception as e:
            if self.debug:
                print("failed to read response from socket: " + str(e))
            return None

        response_lines = response.split("\r\n")

        # Handle HTTP Response Codes
        http_status = response_lines[0]
        if "HTTP" not in http_status:
            # We didn't get a HTTP response
            return None

        # Check for and store cookies
        for line in response_lines:
            if "Set-Cookie" in line:
                assignment_pos = line.find('=')
                cookie_name = line[line.find(':') + 2:assignment_pos]
                cookie_value = line[assignment_pos + 1:line.find(';')]
                self.cookies[cookie_name] = cookie_value

        if "301" in http_status or "302" in http_status:
            # Redirect
            if self.debug:
                print("encountered 301 Moved or 302 Found")
            for line in response_lines:
                if "Location" in line:
                    # Extract redirect url from Location header
                    redirect_url = line[line.find("://")+3:]
                    if "odin.cs.uab.edu" not in redirect_url:
                        # url redirects outside of Odin
                        if self.debug:
                            print("Tried to redirect outside of odin: " + redirect_url)
                        return None

                    new_request = redirect_url[redirect_url.find('/'):]
                    # Redirect is always GET
                    return self.send_request("GET", new_request, json_dict)

            # Didn't find a Location header
            return None

        if "401" in http_status or "403" in http_status or "404" in http_status:
            # Forbidden or Not Found - Stop looking
            if self.debug:
                print("encountered 401 Unauthorized, 403 Forbidden or 404 Not Found")
            return None

        if "500" in http_status:
            # Internal Server Error - Should retry
            if self.debug:
                print("encountered 500 Internal Server Error")
            return self.send_request(request_type, url, json_dict)

        # Strip HTTP header, 1.1 byte denotations
        response = response[response.find("\r\n\r\n")+4:response.rfind("0\r\n\r\n")]
        response = response[response.find('{'):response.rfind('}')+1]
        try:
            return json.loads(response)
        except Exception as e:
            if self.debug:
                print("Failed to parse JSON response: " + str(e))
            return None


if __name__ == "__main__":
    handler = HttpHandler(True)

    handler.connect()

    auth = {
        "email": "lazrak13@uab.edu",
        "password": "ecBA8sbo",
        "grant_type": "password"
    }
    auth_result = handler.send_request("POST", "/oauth/token", auth)
    handler.add_header("Authorization", auth_result["token_type"] + " " + auth_result["access_token"])
    bind_to_graph = handler.send_request("POST", "/api/v1/crawl_sessions/1", None)

    handler.close()
