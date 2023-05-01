from __future__ import annotations
import socket
import bisect
import time
from datetime import datetime
import pickle

class ReceiveEvent():
    def __init__(self, node_id, timestamp, data, send:SendEvent = None):
        self.node_id = node_id
        self.timestamp = int(timestamp)
        self.send_event = send
        self.data = data
    
    #TODO: Implement equals function
    
    def __repr__(self):
        return f"id: {self.node_id}; timestamp: {self.timestamp}; data: {self.data}; send: ({self.send_event.node_id},{self.send_event.timestamp})"
    

class SendEvent():
    def __init__(self, node_id, timestamp, data, recv: ReceiveEvent = None):
        self.node_id = node_id
        self.timestamp = int(timestamp)
        self.recv_event = recv
        self.data = data

    def __repr__(self):
        return f"id: {self.node_id}; timestamp: {self.timestamp}; data: {self.data}; recv: ({self.recv_event.node_id},{self.recv_event.timestamp})"

class InternalEvent():
    def __init__(self, node_id, timestamp, data):
        self.node_id = node_id
        self.timestamp = int(timestamp)
        self.data = data
    def __repr__(self):
        return f"id: {self.node_id}; timestamp: {self.timestamp}; data: {self.data}"

class SpaceTime():
    def __init__(self):
        self.data = {}
    
    def insertEvent(self, event):
        events = self.data.get(event.node_id)
        if not events:
            self.data[event.node_id] = []
            events = self.data.get(event.node_id)
        bisect.insort(events, event, key=lambda x: x.timestamp)

    
    def happened_before(self, ev1, ev2):
        pass                

    def get(self, node_id, timestamp):
        events = self.data[node_id]
        timestamp = int(timestamp)
        return next(event for event in events if event.timestamp == timestamp)

PORT = 55555

def handle_log(diagram:SpaceTime, log):
    # TODO: need to find if associated send/receive in log and then pair them up. 
    # TODO: put enough info in ReceiveEvent so that I can add a send and associate it or add a receive and associate with a send
    # TODO: if there isn't anything to associate it with, then just input it
    # TODO: can probably assume if I get a receive event, its send event is already in. have a loud error otherwise
    
    data = log.split(" ")
    event_type = data[0]
    if event_type == "hello": # for intro/hello message
        pass
    elif event_type == "receive":
        send_node_id, send_timestamp = data[1].split(",")
        recv_node_id, recv_timestamp = data[2].split(",")
        message = " ".join(data[3:])
        print(f"Doing a receive for {recv_node_id} with send{send_node_id}")

        # assume send is already in it 
        send_event = diagram.get(send_node_id, send_timestamp)
        recv_event = ReceiveEvent(recv_node_id, recv_timestamp, message, send_event)
        send_event.recv_event = recv_event
        diagram.insertEvent(recv_event)
    elif event_type == "send":
        node_id, timestamp = data[1].split(",")
        message = " ".join(data[2:])
        send_event = SendEvent(node_id,timestamp,message)
        print(f"Doing a send for {node_id}")
        diagram.insertEvent(send_event)
    elif event_type == "internal":
        node_id, timestamp = data[1].split(",")
        print(f"timestamp: {timestamp}")
        message = " ".join(data[2:])
        print(f" message : {message}")
        diagram.insertEvent(InternalEvent(node_id, timestamp, message))


def write_log_pickle():
    pass

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 55555))

    diagram = SpaceTime()

    future = time.time() + 10
    done = False
    server_socket.settimeout(2)
    while True:
        try: 
            log, address = server_socket.recvfrom(1024)
        except TimeoutError as err:
            if time.time() > future and not done:
                done = True
                for key, value in diagram.data.items():
                    print(f"key: {key}, value: {value}")
                with open('diagram','wb+') as f:
                    pickle.dump(diagram, f)
            continue

        # message looks like
        # | receive send_eventID eventID message
        # note that the next_hop in the message should be switched with the nodeID
        print(f"log: {log.decode()}")
        log = log.decode()

        handle_log(diagram, log)




if __name__ == "__main__":
    main()

# TODO: Receive all the open hello messages from each router, including the ip address and put it into space time diagram. Also then replace all next_hop in messages with the ip of the node
# TODO: Design space time diagram. I am thinking each router will have an ordered list of events and then there will be edges between send and receive events
#           maybe have a different class for each type. Internal no arrows, send have an out arrow and receive have an in arrow from a send event
# TODO: first query is happened_before(x) which gives list of all events that happened before it. happened_before(x,y) is true if x happened before y 
# TODO: Maybe talk to Nate/Rachit about data structure for space-time and how to best query it? 
# TODO: maybe a way to traverse the log to re-construct network state? 

# TODO: Overhead analyses both of latencies of running operations and on network bytes sent. Have to log how many bytes are received
# TODO: Can I reconstruct the state of each node? at different points in time, also know the state of other nodes using causality
# TODO: future work in handling failures. If a packet send doesn't have a corresponding receive


# Internal events

# TODO: test send and receive 