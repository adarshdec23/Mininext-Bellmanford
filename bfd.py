import config
import socket
import threading
import Queue
import json
import sys

class BF:

    # For communication between threads
    q = Queue.Queue()

    def __init__(self):
        self.dv = {}
        self.interfaces = {}
        self.connections = {}
        self.neighbour_ip = {}
        # Read the costs and id of the node
        self.read_config()
        # Listen, start the server to listen to incoming packets
        self.listen()
        # Set up connection with all neighbours
        self.connect()
        # Broadcast the initial costs to all neighbours
        self.send_all()
        # Main even loop
        self.run()

    # Method that is always listening to updates from other nodes.
    @staticmethod
    def thread_listener():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', config.port))
        # Okay, now that we have a socket let's start listening
        s.listen(config.max_listens)
        # Keep listening, don't ever stop.
        while True:
            # Blocking accept call
            connection, address = s.accept()
            # Read data till there's nothing left to read
            while True:
                try:
                    data = connection.recv(1024)
                    # Save the data onto the q
                    BF.q.put(data)
                    if not data:
                        break
                except socket.error:
                    # Don't do anything with an error. Life moves on with or without errors
                    pass

    def listen(self):
        # Spawn a thread that listens to incoming requests
        thread = threading.Thread(target=BF.thread_listener)
        thread.daemon = True
        thread.start()

    # Establish a connection with each neighbour
    def connect(self):
        for node, ip in self.neighbour_ip.items():
            port = config.port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            self.connections[node] = s

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


    def build_data_to_transmit(self):
        return json.dumps(self.dv)

    def send_all(self):
        data = self.build_data_to_transmit()
        for node in self.connections:
            try:
                self.connections[node].sendall(data)
            except:
                print ("Could not send data to:", node)

    def process_incoming(self, data):
        neighbour_dvs = json.loads(data)
        # Flag to check whether our dv has changed.
        change = False
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

    def run(self):
        # Run infinitely.
        print ("Routing table: ", self.dv)
        while True:
            change = False
            try:
                data = BF.q.get(timeout=config.frequency)
                change = self.process_incoming(data)
            except Queue.Empty:
                pass
            finally:
                # No change in dv, let's check the cost to check for changes
                change = change or self.check_costs()
                # If there is any change, then send to all nodes
                if change:
                    self.send_all()


if __name__ == '__main__':
    BF()