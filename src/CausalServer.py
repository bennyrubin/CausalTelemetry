import socket


class ReceiveEvent():
    def __init__(self, node_id, timestamp, send = None):
        self.node_id = node_id
        self.timestamp = timestamp
        self.send_event = send
    
    def set_send(self, send_ev):
        self.send_event = send_ev


class SendEvent():
    def __init__(self, node_id, timestamp, recv = None):
        self.node_id = node_id
        self.timestamp = timestamp
        self.recv_event = recv

    def set_recv(self, recv):
        self.recv_event = recv

class InternalEvent():
    def __init__(self, node_id, timestamp):
        self.node_id = node_id
        self.timestamp = timestamp 

class SpaceTime():
    def __init__(self):
        self.data = {}
    
    def insertEvent(self, event):
        id, timestamp = event

    def happened_before(ev1, ev2):
        pass

PORT = 55555

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 55555))


    while True:
        message, address = server_socket.recvfrom(1024)
        # message looks like
        # | receive send_eventID eventID message
        # note that the next_hop in the message should be switched with the nodeID
        print(f"message: {message} addr: {address}")

if __name__ == "__main__":
    main()

# TODO: Receive all the open hello messages from each router and put it into space time diagram
# TODO: Design space time diagram. I am thinking each router will have an ordered list of events and then there will be edges between send and receive events
#           maybe have a different class for each type. Internal no arrows, send have an out arrow and receive have an in arrow from a send event
# TODO: first query is happened_before(x) which gives list of all events that happened before it. happened_before(x,y) is true if x happened before y 
# TODO: Maybe talk to Nate/Rachit about data structure for space-time and how to best query it? 
# TODO: maybe a way to traverse the log to re-construct network state? 

# TODO: Overhead analyses both of latencies of running operations and on network bytes sent. Have to log how many bytes are received
# TODO: Can I reconstruct the state of each node? at different points in time, also know the state of other nodes using causality
# TODO: future work in handling failures. If a packet send doesn't have a corresponding receive