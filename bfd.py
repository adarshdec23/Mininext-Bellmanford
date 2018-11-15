import config
import socket
import threading
import Queue
import json
import sys
import time
from tabulate import tabulate


class BF:

    # For communication between threads
    q = Queue.Queue()

    def __init__(self):
        self.dv = {}
        self.interfaces = []
        self.neighbour_ip = {}
        # Read the costs and id of the node
        self.read_config()
        # Listen, start the server to listen to incoming packets
        self.listen()
        # Wait for a while for the thread to go up
        time.sleep(0.5)
        # Broadcast the initial costs to all neighbours
        self.send_all()
        # Main even loop
        self.run()

    # Method that is always listening for updates from other nodes.
    @staticmethod
    def thread_listener():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', config.port))
        # Okay, now that we have a socket let's start listening
        s.listen(config.max_listens)
        with open(config.raw_log_file, 'w+', buffering=0) as flog:
            # Keep listening, don't ever stop.
            while True:
                # Blocking accept call
                flog.write("Waiting for a message\n")
                connection, address = s.accept()
                flog.write("Got a message yay!\n")
                # Read data till there's nothing left to read
                while True:
                    try:
                        data = connection.recv(1024)
                        if not data:
                            flog.write("Nothing more to get, breaking\n")
                            break
                        # Save the data onto the q
                        flog.write(data)
                        BF.q.put(data)
                    except socket.error:
                        # Don't do anything with an error. Life moves on with or without errors
                        flog.write("Socket error while trying to listen")

    def listen(self):
        # Spawn a thread that listens to incoming requests
        print ("Spawning a thread")
        thread = threading.Thread(target=BF.thread_listener)
        thread.daemon = True
        thread.start()

    # Establish a connection with each neighbour
    def connect(self, ip):
        port = config.port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False
        while not connected:
            try:
                s.connect((ip, port))
                connected = True
            except:
                print ("Failed to connect to: ", ip)
                print ("Backing off for two seconds before next re-try")
                time.sleep(2)
        return s

    def read_config(self):
        # Read my name and interfaces
        with open(config.config_file) as f:
            j = json.load(f)
            self.dv['id'] = j['id']
            for item in j["neighbours"]:
                neighbour, ip, cost = item["node"], item["ip"], item["cost"]
                self.dv[ip] = (neighbour, cost)
                self.neighbour_ip[neighbour] = ip
            for item in j["interfaces"]:
                self.dv[item] = (self.dv['id'], 0)  # Zero cost to our own interfaces
                self.interfaces.append(item)
        print ("Configuration read")

    def build_data_to_transmit(self):
        return json.dumps(self.dv)+config.DELIM

    def send_all(self):
        data = self.build_data_to_transmit()
        for node in self.neighbour_ip:
            try:
                print ("Sending data to: ", node, data)
                s = self.connect(self.neighbour_ip[node])
                s.sendall(data)
            except:
                print ("Could not send data to:", node)
            s.close()

    def process_incoming(self, data):
        print("Received: ", data)
        if not data:
            return False
        neighbour_dvs = json.loads(data)
        # Flag to check whether our dv has changed.
        change = False
        print (self.neighbour_ip)
        if neighbour_dvs['id'] == self.dv['id']:
            return False
        neighbour_ip = self.neighbour_ip[neighbour_dvs['id']]
        for ip in neighbour_dvs:
            if ip == 'id':
                continue
            possible_cost = int(neighbour_dvs[ip][config.COST]) + int(self.dv[neighbour_ip][config.COST])
            if self.dv.get(ip, (" ", sys.maxint))[config.COST] > possible_cost:
                self.dv[ip] = (neighbour_dvs['id'], possible_cost)
                change = True
        return change

    def check_costs(self):
        """
        Read the costs file to check whether there is any change
        :return: True if there's a change, False otherwise
        """
        return False
        change = False
        with open(config.config_file, 'r') as f:
            j = json.load(f)
            for item in j["neighbours"]:
                ip, cost = item["ip"], item["cost"]
                if cost != self.dv[ip][config.COST]:
                    change = True
                    self.dv[ip] = (ip, cost)
        return change


    def print_routing_table(self):
        """
        Dynamically build a routing table. This is not ideal, but it's comparatively simple to
        rebuild the table every time the method is called
        :return: None
        """
        table = []
        header = ["Destination Network", "Next Hop", "Cost"]
        # Add immediate neighbours to the routing table
        for node, ip in self.neighbour_ip.items():
            # [IP, NextHOP, COST]
            table.append([ip, "Direct", self.dv[ip][config.COST]])
        neighbour_ip = self.neighbour_ip.keys()
        for dest in self.dv:
            next_hop, cost = self.dv[dest]
            if dest in neighbour_ip or dest in self.interfaces:
                # Already considered in the previous loop, so ignore
                # Or it's me, so ignore
                continue
            table.append([dest, next_hop, cost])
        print(tabulate(table, headers=header))

    def run(self):
        # Run infinitely.
        print ("Routing table: ", self.dv)
        while True:
            change = False
            try:
                data = BF.q.get(timeout=config.frequency)
                messages = data.split(config.DELIM)
                for message in messages:
                    if not message:
                        continue
                    change = change or self.process_incoming(message)
            except Queue.Empty:
                pass
            finally:
                # No change in dv, let's check the cost file for changes
                change = change or self.check_costs()
                # If there is any change, then send to all nodes
                if change:
                    print ("The DV was changed. So we send the updated costs to everyone")
                    self.print_routing_table()
                    self.send_all()
                else:
                    print("No change in the distance vector. Cost not updated, current state is:")
                    self.print_routing_table()


if __name__ == '__main__':
    try:
        BF()
    except KeyboardInterrupt:
        print("Bbye. Hope this kills my child")
