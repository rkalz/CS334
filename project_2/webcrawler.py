from http_handler import HttpHandler
from html_parser import HtmlHandler
import sys

# Arrays for flags, visited and unvisited pages
flags = []
metropolis = []
frontier = []

# Username and password from commandline
user = sys.argv[1]
password = sys.argv[2]

http = HttpHandler(False)
html = HtmlHandler()

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

web_page = html.parseHtml(main_menu)

while(len(flags) < 5):
    if (not web_page[0]) and (not web_page[1]):
        print('the web page')
        print(web_page)
        print(1)
        if "/fakebook" in frontier[0]:
            print('the frontier')
            print(frontier)
            print(2)
            html_page = http.send_request("GET", frontier[0])
            web_page = html.parseHtml(html_page)
            metropolis.append(frontier[0])
            frontier.remove(frontier[0])
            continue
        else:
            print(2)
            metropolis.append(frontier[0])
            frontier.remove(frontier[0])
            continue
    if (web_page[0]) or (web_page[1]):
        print(3)
        print(web_page)
        if (web_page[0][0] not in frontier) and (web_page[0][0] not in metropolis):
            print(4)
            print("4", web_page)
            frontier.append(web_page[0][0])
            web_page[0].remove(web_page[0][0])
            print("4.5", web_page)
        else:
            web_page[0].remove(web_page[0][0])
        if web_page[1]:
            print(5)
            flags.append(web_page[1][0])
            web_page[1].remove(web_page[1][0])
        

print(frontier)
print(web_page[0])
print(metropolis)
print(flags)