from CausalServer import *
import networkx as nx
import matplotlib.pyplot as plt
import pickle

file = "data/diagram_2r"
file = "data/diagram_bug2"
file = "data/diagram_bug1"
file = "data/diagram_3r_2"



def convertToGraph():
    G = nx.DiGraph()
    with open(file,"rb") as f:
        diagram = pickle.load(f)
    for node in diagram.data.keys():
        events = diagram.data[node]
        for i,event in enumerate(events):
            id = int(event.node_id)
            timestamp = int(event.timestamp)
            if isinstance(event, SendEvent):
                color = 'red'
            elif isinstance(event, ReceiveEvent):
                color = 'green'
            else:
                color = 'blue'
            G.add_node((id,timestamp),pos=(id,timestamp),label=event.data, color = color)
            if i < len(events) - 1:
                next_event = events[i+1]
                G.add_edge((id, timestamp), (int(next_event.node_id),int(next_event.timestamp)))
        # if isinstance(event,ReceiveEvent):
        #     send = event.send_event
            if isinstance(event,SendEvent):
                recv = event.recv_event
                recv_node = (int(recv.node_id),int(recv.timestamp))
                G.add_edge((id,timestamp),recv_node)

    pos = nx.get_node_attributes(G,'pos')
    labels = nx.get_node_attributes(G,'label')
    color_map = []
    for node in G:
        color_map.append(G.nodes[node]['color'])
    flipped_pos = {node: (x,-y) for (node, (x,y)) in pos.items()}
    plt.figure(figsize=(18,18))
    nx.draw(G,flipped_pos,node_color = color_map,with_labels=False)
    nx.draw_networkx_labels(G,flipped_pos,labels)
    plt.savefig("graph_3r.png", dpi=1000, format="PNG")
    plt.show()
    


def onlyInternal():
    G = nx.DiGraph()
    with open(file,"rb") as f:
        diagram = pickle.load(f)
    for node in diagram.data.keys():
        events = diagram.data[node]
        y_coord = 0
        for i,event in enumerate(events):
            id = int(event.node_id)
            timestamp = int(event.timestamp)
            if isinstance(event, SendEvent):
                color = 'red'
                continue
            elif isinstance(event, ReceiveEvent):
                color = 'green'
                continue
            else:
                color = 'blue'
            y_coord = y_coord + 1
            G.add_node((id,timestamp),pos=(id,y_coord),label=event.data, color = color)
        # if isinstance(event,ReceiveEvent):
        #     send = event.send_event
            if isinstance(event,SendEvent):
                recv = event.recv_event
                recv_node = (int(recv.node_id),int(recv.timestamp))
                G.add_edge((id,timestamp),recv_node)

    pos = nx.get_node_attributes(G,'pos')
    labels = nx.get_node_attributes(G,'label')
    color_map = []
    for node in G:
        color_map.append(G.nodes[node]['color'])
    flipped_pos = {node: (x,-y) for (node, (x,y)) in pos.items()}
    nx.draw(G,flipped_pos,node_color = color_map,with_labels=False)
    nx.draw_networkx_labels(G,flipped_pos,labels)
    #plt.show()
    plt.savefig("graph.pdf")



def main():
    graph = {1: [1,2,3,4], 2: [5,6,7]}
    G = nx.DiGraph()
    for key in graph.keys():
        print(key)
        lst = graph[key]
        print(lst)
        for i,el in enumerate(lst):
            G.add_node((key,el), pos=(key, i))
    
    pos = nx.get_node_attributes(G,'pos')
    flipped_pos = {node: (x,-y) for (node, (x,y)) in pos.items()}
    print(G)
    nx.draw(G,flipped_pos,with_labels=True)
    plt.show()


if __name__ == "__main__":
    convertToGraph()
    #onlyInternal()