#!/usr/bin/env python3

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
#Goes to new web pages to find new links and flags
    if (not web_page[0]) and (not web_page[1]):
        if "/fakebook" in frontier[0]:
            html_page = http.send_request("GET", frontier[0])
            if html_page != None:
                web_page = html.parseHtml(html_page)
                metropolis.append(frontier[0])
                frontier.remove(frontier[0])
                continue
        else:
            metropolis.append(frontier[0])
            frontier.remove(frontier[0])
            continue
#Adds web pages into frontier and checks for flags
    if (web_page[0]) or (web_page[1]):
        if (web_page[0][0] not in frontier) and (web_page[0][0] not in metropolis):
            frontier.append(web_page[0][0])
            web_page[0].remove(web_page[0][0])
        else:
            web_page[0].remove(web_page[0][0])
        if web_page[1]:
            flags.append(web_page[1][0])
            web_page[1].remove(web_page[1][0])

#Prints flags
for flag in flags:
    print(flag)