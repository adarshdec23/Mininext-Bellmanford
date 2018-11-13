class BF:
    def __init__(self):
        self.dv = {}
        self.neighbours = []
        self.id = None
        # Read the costs and id of the node
        self.read_config()
        # Set up connection with all neighbours
        self.connect()
        self.senf_update()
        self.run()


    def run(self):
        pass



class Packet:

    pass


if __name__ == '__main__':
    BF()