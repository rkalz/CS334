from api_handler import ApiHandler
import sys

"""Creates the ApiHndler"""
authorization = {
  "email": sys.argv[1],
  "password": sys.argv[2],
  "grant_type": "password"
}

handler = ApiHandler(authorization, True)
users_friends = []
vertices = []

"""Logs into Bitter and starts crawl session"""
handler.login(authorization)
handler.crawl(2, handler.access_token)

def verticeMaker(people_friends):
  while(people_friends):
    if(people_friends[0][1]['friends']):
      if((people_friends[0][0], people_friends[0][0][1]['friends'][0]['uid'], people_friends[0][0][1]['friends'][0]['length']) not in vertices):
        vertices.append(people_friends[0][0], people_friends[0][0][1]['friends'][0]['uid'], people_friends[0][0][1]['friends'][0]['length'])
        people_friends.remove(people_friends[0][0][1]['friends'][0])
    else:
      people_friends.remove(people_friends[0])

def dijkstra(start, end, people_friends):
  print()

handler.get_people(handler.crawl_session, [])
users_friends = (handler.get_friends([]))
users_friends[0][0][1]['friends'][0]['length']