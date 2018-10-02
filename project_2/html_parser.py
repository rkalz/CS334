from http_handler import HttpHandler


class HtmlHandler:
    def __init__(self):
        self.login_page = None
        self.main_menu = None
        self.user_menu = None

    def getHtml(self):
        handler = HttpHandler(True)

        handler.connect()

        # Test a get
        login_page = handler.send_request("GET", "/accounts/login")
        if login_page is not None:
            self.login_page = login_page
            print(self.login_page)

        # Get authenticity token from login page
        token_identifier = "name=\"authenticity_token\" value=\""
        token_start = login_page.find(token_identifier)
        token = ""
        if token_start != -1:
            auth_token = login_page[token_start + len(token_identifier):]
            auth_token = auth_token[:auth_token.find("\"")]
            token += "&authenticity_token=" + auth_token

        # Test POST and params
        main_menu = None
        if token != "":
            main_menu = handler.send_request("POST",
                                             "/accounts/login/?login[password]=5HRYDLKA&login[email]=lazrak13" + token)
        if main_menu is not None:
            self.main_menu = main_menu
            print(self.main_menu)

        # Test GET with cookies
        if main_menu is not None:
            user_menu = handler.send_request("GET", "/fakebook/156714994/")
            if user_menu is not None:
                self.user_menu = user_menu
                print(self.user_menu)

        handler.close()


if __name__ == "__main__":
    handler = HtmlHandler()
    handler.getHtml()
