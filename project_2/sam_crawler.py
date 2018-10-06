from http_handler import HttpHandler
from html_parser import HtmlHandler
import sys

class WebCrawler:

    def __init__(self):
        self.flags = []
        self.visited = []
        self.unvisited = []
    
    def connect(self, http, html):
        # Username and password from commandline
        user = sys.argv[1]
        password = sys.argv[2]

        #Logs into fakebook
        HttpHandler.connect(http)
        login_page = HttpHandler.send_request(http, "GET", "/accounts/login")
        token_identifier = "name=\"authenticity_token\" value=\""
        token_start = login_page.find(token_identifier)
        token = ""
        if token_start != -1:
            auth_token = login_page[token_start + len(token_identifier):]
            auth_token = auth_token[:auth_token.find("\"")]
            token += "&authenticity_token=" + auth_token

        if token != "":
            main_menu = http.send_request("POST", "/accounts/login/?login[password]=" + password + "&login[email]=" + user + token)
        else:
            print("You need to login!")

        return html.parseHtml(main_menu)
    
    def clean(self, list):
        cleaned = []
        for index, link in enumerate(list[0]):
            if list[0][index][0:9] == '/fakebook':
                cleaned.append(list[0][index])
        return cleaned

    def crawl(self, list, http, html):
        visited = []
        for index, link in enumerate(list):
            page = HttpHandler.send_request(http, "GET", list[index])
            visited.append(list[index])
            page_parsed = html.parseHtml(page)
            if len(page_parsed[1]) != 0:
                for index, flag in enumerate(page_parsed[1]):
                    self.flags.append(page_parsed[1][index])
            return self.clean(page_parsed), visited

if __name__ == "__main__":
    http = HttpHandler(False)
    html = HtmlHandler()

    crawler = WebCrawler()
    main_menu = crawler.connect(http, html)
    initial = crawler.clean(main_menu)

    collected = crawler.crawl(initial, http, html)
