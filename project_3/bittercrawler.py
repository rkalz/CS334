from api_handler import ApiHandler
import sys
import math

"""Creates the ApiHndler"""
authorization = {
  "email": sys.argv[1],
  "password": sys.argv[2],
  "grant_type": "password"
}

handler = ApiHandler(authorization, True)
users_friends = []
vertices = []

def verticeMaker(people_friends):
  while(people_friends):
    if(people_friends[0][1]['friends']):
      if((people_friends[0][0], people_friends[0][0][1]['friends'][0]['uid'], people_friends[0][0][1]['friends'][0]['length']) not in vertices):
        vertices.append(people_friends[0][0], people_friends[0][0][1]['friends'][0]['uid'], people_friends[0][0][1]['friends'][0]['length'])
        people_friends.remove(people_friends[0][0][1]['friends'][0])
    else:
      people_friends.remove(people_friends[0])

def dijkstra(start, end, people_friends):
  print(1)
  nextVert = None
  currentVert = start
  totalDis = 0
  verticeMaker(people_friends)
  currentSet = vertices

  while(currentVert != end):
    if(currentVert == currentSet[0][1]):
      nextDis = math.inf
      currentDis = currentSet[0][2] + totalDis
      if(currentDis < nextDis):
        nextDis = currentDis
        nextVert = currentSet[0][0]
        currentSet.remove(currentSet[0])
      else:
        totalDis = nextDis + totalDis
        currentVert = nextVert
    else:
      currentSet.remove(currentSet[0])
  return totalDis

while(len(handler.secret_flags) < 5):
  handler.login(authorization)
  handler.crawl(sys.argv[3], handler.access_token)
  print(handler.secret_flags)
  handler.get_flags([])
  print(0)
  handler.get_people(handler.crawl_session, [])
  print(0.1)
  users_friends = handler.get_friends([])
  print(0.2)
  if(handler.get_people(sys.argv[3], handler.access_token) == False):
    print(0.3)
    print(handler.crawled_people)
    print(users_friends)
    challenge = handler.get_challenge()
    if(challenge != False):
      solution = dijkstra(challenge[0], challenge[1], users_friends)
      print(handler.post_challenge(solution))

print(handler.secret_flags)