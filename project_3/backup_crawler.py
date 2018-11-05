from project_3.http_handler import HttpHandler
import heapq
import sys


class Node:
    def __init__(self, id):
        self.id = id
        self.cost = sys.maxsize
        self.parent = None
        self.children = set()

    def __repr__(self):
        return str(self.id)

    def __lt__(self, other):
        return self.cost < other.cost

    def __eq__(self, other):
        return self.cost == other.cost


def djikstra(start, end, nodes):
    if start not in nodes or end not in nodes:
        return -1

    queue = []
    nodes[start].cost = 0

    for _, node in nodes.items():
        if node.id != start:
            node.cost = sys.maxsize
        node.parent = None
        heapq.heappush(queue, node)

    while len(queue) != 0:
        parent = heapq.heappop(queue)
        for child in parent.children:
            if child in nodes:
                child_node = nodes[child]
                new_cost = parent.cost + 1
                if new_cost < child_node.cost:
                    child_node.cost = new_cost
                    child_node.parent = parent.id
                    heapq.heapify(queue)

    path = []
    node_id = end
    if nodes[end].parent is None:
        return -1

    while node_id is not None:
        path.append(nodes[node_id].id)
        node_id = nodes[node_id].parent

    return len(path)-1


if __name__ == "__main__":
    handler = HttpHandler()
    handler.connect()

    auth = {
        "email": "rofael@uab.edu",
        "password": "24QM6tTz",
        "grant_type": "password"
    }

    users_to_process = []
    flags = []
    visited_nodes = dict()

    auth_result = handler.send_request("POST", "/oauth/token", auth)
    handler.add_header("Authorization", auth_result["token_type"] + " " + auth_result["access_token"])
    starting_nodes = handler.send_request("POST", "/api/v1/crawl_sessions/2", None)
    for user in starting_nodes["people"]:
        users_to_process.append(Node(user['uid']))

    while len(users_to_process) != 0 and len(flags) != 5:
        user = users_to_process.pop(0)
        beets_response = handler.send_request("GET", "/api/v1/beets/"+str(user.id), None)
        if beets_response is None:
            users_to_process.append(user)
            continue

        if "challenge" in beets_response:
            users_to_process.append(user)
            if "from" in beets_response["challenge"] and "to" in beets_response["challenge"]:
                shortest_path = djikstra(beets_response["challenge"]["from"], beets_response["challenge"]["to"],
                                         visited_nodes)
                challenge_response = handler.send_request("POST", "/api/v1/challenges", {"distance": shortest_path})
            continue
        else:
            if "beets" in beets_response:
                for beet in beets_response["beets"]:
                    if "text" in beet:
                        text = beet["text"]
                        if "SECRET FLAG" in text:
                            print(text)
                            flags.append(text)
            else:
                users_to_process.append(user)
                continue

        friends_response = handler.send_request("GET", "/api/v1/friends/"+str(user.id), None)
        if friends_response is None:
            users_to_process.append(user)
            continue

        if "challenge" in friends_response:
            users_to_process.append(user)
            shortest_path = djikstra(friends_response["challenge"]["from"], friends_response["challenge"]["to"],
                                     visited_nodes)
            challenge_response = handler.send_request("POST", "/api/v1/challenges", {"distance": shortest_path})
            continue
        else:
            if "friends" in friends_response:
                for friend in friends_response["friends"]:
                    user.children.add(friend['uid'])
                    if friend['uid'] not in visited_nodes:
                        users_to_process.append(Node(friend['uid']))
            else:
                users_to_process.append(user)
                continue

        visited_nodes[user.id] = user

    print(flags)

    handler.close()


