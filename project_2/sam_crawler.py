from http_handler import HttpHandler
from html.parser import HTMLParser
import sys

class WebCrawler:

    def __init__(self, http, html):
        self.http = http
        self.html = html
        self.init = None
        self.visited = []
        self.visiting = None
        self.toVisit = []
        self.flags = []
    
    def connect(self):
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
        
        html.feed(main_menu)
        self.init = html.links

    def initialClean(self):
        # Removes everything in initial array that isn't leading to fakebook
        cleaned = []
        for index, link in enumerate(self.init):
            if self.init[index][0:9] == '/fakebook':
                cleaned.append(self.init[index])
        self.init = cleaned

    # Post initial setup methods
    def crawl(self, link):
        htmlToParse = HttpHandler.send_request(http, "GET", link)
        return htmlToParse

    def parse(self, rawHtml):
        parsed = html.feed(rawHtml)
        return parsed
    
    def clean(self, links):
        cleaned_links = []
        for index, link in enumerate(links):
            if links[index][0:9] == '/fakebook':
                cleaned_links.append(links[index])
        return cleaned_links

class HTMLHandler(HTMLParser):
    def __init__(self, links=[], flags=[]):
        HTMLParser.__init__(self)
        self.links = links
        self.flags = flags

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            link = dict(attrs).get('href')
            self.links.append(link)
    def handle_data(self, data):
        if data[0:5] == "FLAG:":
            flags.append(data)
            

if __name__ == "__main__":
    # Initial setup
    http = HttpHandler(False)
    html = HTMLHandler()
    crawler = WebCrawler(http, html)
    crawler.connect()
    crawler.initialClean()
    html.links = []

    # Prep for loop
    crawler.toVisit = crawler.init
    
    while len(crawler.flags) < 5:
        crawler.visiting = crawler.toVisit[-1]
        crawler.visited.append(crawler.visiting)
        del crawler.toVisit[-1]

        rawHtml = crawler.crawl(crawler.visiting)
        if rawHtml != None:
            html.feed(rawHtml)
        parsedHtml = html.links
        html.links = []
        cleanedHtml = crawler.clean(parsedHtml)
        flags = html.flags
        html.flags = []

        for index, flag in flags:
            crawler.flags.append(flags[index])

        for index, link in enumerate(cleanedHtml):
            if cleanedHtml[index] not in crawler.visited:
                if cleanedHtml[index] not in crawler.toVisit:
                    crawler.toVisit.append(cleanedHtml[index])    

        # Tester prints
        """ print('toVisit remaining:')
        print(len(crawler.toVisit))
        print('Visited links:')
        print(len(crawler.visited))
        print('Flags:')
        print(len(crawler.flags))
        print(crawler.flags) """
        
    print(crawler.flags)
