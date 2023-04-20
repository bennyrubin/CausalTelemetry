import sys 
import argparse
import time
import socket
import select
import subprocess


class RIBEntry():
    def __init__(self, prefix, next_hop, as_path, local_pref, selected):
        self.prefix = prefix
        self.next_hop = next_hop 
        self.as_path = as_path 
        self.local_pref = local_pref 
        self.selected = selected
    def prefix(self): return self.prefix
    def next_hop(self): return self.next_hop
    def prefix(self): return self.prefix
    def as_path(self): return self.as_path
    def local_pref(self): return self.local_pref
    def selected(self): return self.selected

class TableKey:
    def __init__(self, prefix, next_hop):    # ipaddrn and netmaskn as 32-bit integers
        self.prefix  = prefix
        self.next_hop = next_hop
    def ipaddr(self): return self.prefix.split("/")[0]
    def prefix(self): return self.prefix
    def next_hop(self): return self.next_hop
    def __hash__(self):
        return hash(self.prefix) ^ hash(self.next_hop)
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.prefix == other.prefix and self.next_hop == other.next_hop
        else:
            return False 
    def __str__(self):
        return f"{self.prefix} + {self.next_hop}"
    def __repr__(self):
        return f"{self.prefix} + {self.next_hop}"


# arguments are ip address for subnet (announcements), neighbor IP addresses, and AS number. 
# can probably actually derive AS number from ip address
# Opening hello message will also share AS number info 

BGP_PORT = 1179
ASN = 0
SOURCE = ""
SERVER_IP = "192.168.0.100"


# have a table that has the key as the tablekey and the value as a RIBEntry.
RIBTable = {}
local_prefs = {}
logical_clock = 0


def initiate_connections(neighbors):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', BGP_PORT))
    server_socket.listen()
    read_list = [server_socket]
    print(f"ASN {ASN} created server Socket")
    time.sleep(.2)
    client_sockets = []
    
    for (ip, server, local_pref) in neighbors:
        server = "true" in server
        print(f"ASN {ASN} ip: {ip} server: {server}")
        if not server:
            print(f"ASN {ASN} about to connect to {ip}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, BGP_PORT))
            client_sockets.append(client_socket)

    while True:
        readable, writable, errored = select.select(read_list, [], [], 1)
        if len(readable) == 0:
            break
        for s in readable:
            print(f"ASN {ASN} about to accept")
            client_socket, address = s.accept()
            client_sockets.append(client_socket)
            print(f"ASN {ASN} was connected to")
    
    print(f"ASN {ASN} has {len(client_sockets)} sockets")
    return client_sockets

def send_server(message):
    causal_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (SERVER_IP, 55555)
    causal_socket.sendto(message, addr)
    
def send_and_log():
    # every send message should embed the event ID, semi-colon seperated
    # eventID;message --> node_id,timestamp;message
    pass

def recv_and_log(updates):
    global logical_clock
    # eventID;message --> node_id,timestamp;message
    stripped_updates = []
    for update in updates:
        send_eventID, stripped_update = update.split(";")
        stripped_updates.append(stripped_update)
        message = f"receive {send_eventID} {ASN},{logical_clock}"
        logical_clock += 1
    # every receive should parse the embed event ID 
    # TODO: grab the info I need and then strip it before returning it
    return stripped_updates

def log_internal():
    pass

def read_updates(sock):
    # read until I end with a newline. Could have multiple requests
    while True:
        buffer = ''
        data = sock.recv(1024)
        if not data:
            pass
            #print("Disconnected") #will this happen if link down? probably not. 
        buffer += data.decode()
        if buffer.endswith("\n"):
            updates = buffer.split("\n")[:-1]
            return updates
        
def select_route(sockets, prefix, neighbor_from):
    global RIBTable

    if ASN == "1":
        print(f"{ASN} selecting route from {RIBTable}")

    keys = list(RIBTable.keys())
    keys = [key for key in keys if key.prefix == prefix]

    if not keys: #no routes
        # send withdrawal to neighbors
        for sock in sockets:
            if sock.getpeername()[0] != neighbor_from:
                message = f"withdraw {prefix} {sock.getsockname()[0]} empty\n"
                sock.sendall(message.encode())
        return

    selected_route = [key for key in keys if RIBTable[key].selected] # invariant that at most one is selected at any time
    selected_route = selected_route[0] if selected_route else None

    best_key = keys[0]
    if ASN == "3":
        print(keys)
    for key in keys:
        route = RIBTable[key]
        best_route = RIBTable[best_key]

        if ASN == "3":
            print(f"key: {key} local pref {route.local_pref} as_path: {route.as_path}")
        # first check local_pref
        if route.local_pref != best_route.local_pref:
            if route.local_pref > best_route.local_pref:
                best_key = key
        elif len(route.as_path) < len(best_route.as_path): # then check as_path length
            best_key = key

    if ASN == "3":
        print(f"best route: {best_key}")

    command = f"ip route del {best_key.prefix}"
    subprocess.run(command, shell=True)
    if selected_route:
        RIBTable[selected_route].selected = False
    RIBTable[best_key].selected = True
    print(f"ASN {ASN} add route to {best_key.prefix} via {best_key.next_hop}\n")
    command = f"ip route add {best_key.prefix} via {best_key.next_hop} src {SOURCE}"
    subprocess.run(command, shell=True)

    # send announcements for neighbors. 
    for sock in sockets:
        if sock.getpeername()[0] != neighbor_from:
            as_path = ",".join(RIBTable[best_key].as_path) + f",{ASN}"
            message = f"update {prefix} {sock.getsockname()[0]} {as_path}\n"
            sock.sendall(message.encode())
    # TODO: remove current route to IP address in linux routing table (might have to do this before I over-write the route)
    # if selected_route exists then set selected to 0 
    # set best_key selected to 1
    # add best_key route to linux routing table
    # advertise best_key route to all neighbors, except for neighbor_from. Make sure to set neighbor correctly to be my own IP address, and add ASN to as_path




    # get all of the keys for that prefix
    
    # get the current selected route

    # calculate the best route. If it is not the current route (which if it's none will always be the case) then remove current route from linux routing table (assuming it's not none) and add new one
    # then advertise the new route to neighbors. 
    # set old best route selected to 0 and new best route selected to 1. 


    # if best route is empty (meaning no routes) then advertise withdrawal to neighbor sockets, except for neighbor_from. 

    # in the case of update or withdraw it's possible one is already selected, so make sure to set that to 0 after selecting the right one
    # in the case of withdraw it's possible there are no longer any routes, in which case it should return -1 (returns 0 if successful)
    # in that case of no route, send a withdraw to all neighbors that are not the one that sent it originally (withdrawNeighbor)
    # if a route is updated, then send an update to everyone except for neighbor

    # after selecting route, if I have to make selected 0 for an entry, then remove it from linux routing
    # if I make select 1 for an entry, add it to linux routing

    


def route_filter(update): 

    #localprefs

    # should probably make this a JSON input at some point
    vals = update.split(" ")
    action = vals[0] #either update or withdraw
    prefix = vals[1]
    neighbor = vals[2]
    local_pref = local_prefs[neighbor]
    as_path = vals[3].split(",")
    if ASN in as_path:
        return None, None
    entry = RIBEntry(prefix, neighbor, as_path, local_pref, False)
    return entry, action

def process_updates(sockets, updates):
    global RIBTable
    # update looks like:
    # <update/withdraw> prefix neighbor as1,as2,as3 
    for update in updates:
        rib_entry, action = route_filter(update)
        if not rib_entry: # ASN was in the asn_path
            continue

        #prefix and next hop should be unique, so only one entry per those for withdraw and update should make sure to update THAT entry and not add a new one

        # I can just plug it into the table and set selected to 0. select_route will decide if it needs to send an update/withdraw and select the correct route. 
        if action == "update":
            key = TableKey(rib_entry.prefix, rib_entry.next_hop)
            RIBTable[key] = rib_entry
        elif action == "withdraw":
            command = f"ip route del {rib_entry.prefix}"
            subprocess.run(command, shell=True)
            key = TableKey(rib_entry.prefix, rib_entry.next_hop)
            print(f"asn {ASN} withdraw route key: {key}")
            if key in RIBTable:
                del RIBTable[key]
            else:
                print(f"{ASN} tried to withdraw {key}, but not in table")

            # TODO: take it out of the RIBtable and linux routing table

        select_route(sockets, rib_entry.prefix, rib_entry.next_hop)

        # for sending update can use socket.getsockname()

        # pass each update message through the filter to get local_pref
        # turn it into RIB entry data structure
        # if the prefix is new just add it to the RIB and linux routing table
        # if it's already in there, compare it to current selected and if it's better than replace it as selected and in linux routing table 
        # if it's a withdraw, then remove the route and select a new one. 
        # any time a new selected route is chosen, I should send an update message to neighbors, unless next_hop is that neighbor 

        # need a way to test if the connection link went down, then should send a withdraw message to all neighbors (except for the down link one)


        # if a router changes its route it's just an update message. This has to clear the old entry (from the same AS), because it cant have two different paths to the same prefix from the same AS. 
        # if a route goes down and there's no alternative, then it sends a withdrawal, until an AS has an alternative and it is propogated. 
   

def main():
    # TODO: local pref has to be passed in as an argument
    global ASN
    global local_prefs
    global SOURCE

    parser = argparse.ArgumentParser()

    parser.add_argument('--ip', type=str, required=True)
    parser.add_argument('--neighbor', nargs=3, action='append', type=str, required=True)


    args = parser.parse_args()

    ip = args.ip
    neighbors = args.neighbor
    print(f"ip: {args.ip} \nneighbors: {args.neighbor}")


    for (ip_, server, local_pref) in neighbors: # set local_prefs
        local_prefs[ip_] = int(local_pref)


    ASN = ip.split(".")[2]
    SOURCE = ip[:-4] + "1"
    sockets = initiate_connections(neighbors)

    # <update/withdraw> prefix neighbor as1,as2,as3 

    # send announcements for neighbors. 
    for sock in sockets:
        print(f"socket name: {sock.getsockname()}")
        addr = sock.getsockname()[0]
        message = f"update {ip} {addr} {ASN}\n"
        sock.sendall(message.encode())

    future = time.time() + 3
    sent = False
    message = b'test'
    # main loop for running BGP
    while True:
        read_sockets, write_sockets, error_sockets = select.select(sockets, [], [], .5)

        for sock in read_sockets:
            updates = read_updates(sock)
            process_updates(sockets, updates)
        

        

        # if ASN == "3" and time.time() > future and not sent:
        #     print(f"len sockets: {len(sockets)}")
        #     sock = sockets[1]
        #     print("withdrawing route")
        #     sent = True
        #     print(f"{ASN} sending withdraw to {sock.getpeername()[0]} from {sock.getsockname()[0]} ")
        #     message = f"withdraw 10.0.2.0/24 {sock.getsockname()[0]} {ASN}\n"
        #     sock.sendall(message.encode())

    #TODO: Send packets to central server for send, recieve, and internal events. Page 3 of causal telemetry paper
    #           need to keep track of logical time-stamp ID and node ID (ASN). Re-read causal telemetry EuroP4 paper
    # TODO: Add to setup a hello message where the server can get the ASN and IP (10.x.x.x) of each router and put it into the space-time data structure
    # TODO: Change all sending to include the event ID (ASN and logical_clock). And also increase the logical_clock after each one, and also send it to the log (maybe have a log function)
    # TODO: Change all receive to parse the eventID and then add to the log. and increment logical clock
    # TODO: decide which internal events I want to log and make sure to increment logical clock

    # use select framework to read all the data. Use data format with \n for messages to make parsing easy 


# once I get sockets, use select and polling framework. 


# handle the select polling of the socket connections 
    # need to figure out what it looks like when a link goes down from socket POV
        # I think it's using the timeout
    # do I need MRAI timer? 
# upon update message receive need to change the RIB table and update kernel routing tables
# then send out new update messages 

# FIB table:
# IP announced, next hop, AS path, local pref, selected (bool)

# MRAI timer:
# dictionary with entry for each ip address prefix (make sure to remove when withdraw)
# if I send an update, withdraw then don't update again until it's been 30 seconds. might need some fancy. or just a queue of waiting messages to send. 

if __name__ == "__main__":
    main()