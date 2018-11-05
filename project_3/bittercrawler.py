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
  print(0)
  handler.login(authorization)
  handler.crawl(sys.argv[3], handler.access_token)
  newPeople = handler.get_people(handler.crawl_session, [])
  while(newPeople):
    print(1)
    if(newPeople[0] not in checked) and (newPeople[0] not in unchecked):
      print(2)
      unchecked.append(newPeople[0])
      newPeople.remove(newPeople[0])
    else:
      print(3)
      newPeople.remove(newPeople[0])
  while(unchecked):
    print(4)
    users_friends = handler.get_friends(unchecked[0])
    beets = handler.get_beets(unchecked[0])
    print(beets)
    while(beets):
      print(5)
      if(beets['beets'][0]['text'][0:12] == "SECRET FLAG:"):
        print(6)
        flags.append(beets['beets'][0]['text'])
        beets.remove(beets['beets'][0])
      else:
        print(7)
        beets.remove(beets['beets'][0])
    checked.append(unchecked[0])
    unchecked.remove(unchecked[0])
  print(flags)

print(flags)