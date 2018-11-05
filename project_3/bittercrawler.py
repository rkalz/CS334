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
checked = []
unchecked = []
beets = []
flags = []

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

while(len(flags) < 5):
  handler.login(authorization)
  handler.crawl(sys.argv[3], handler.access_token)
  print(0)
  newPeople = handler.get_people(handler.crawl_session, [])
  while(newPeople):
    if(newPeople[0] not in checked) and (newPeople[0] not in unchecked):
      unchecked.append(newPeople[0])
      newPeople.remove(newPeople[0])
    else:
      newPeople.remove(newPeople[0])
  print(0.1)
  while(unchecked):
    users_friends = handler.get_friends(unchecked[0])
    beets = handler.get_beets(unchecked[0])
    while(beets):
      if beets[0]['text'][0:12] == "SECRET FLAG:":
                flags.append(beets[0]['text'])
                beets.remove(beets[0])
      else:
        beets.remove(beets[0])
    checked.append(unchecked[0])
    unchecked.remove(unchecked[0])
  print(0.2)

print(flags)