"""
Example topology of Quagga routers
"""

import inspect
import os
from mininext.topo import Topo
from mininext.services.quagga import QuaggaService

from collections import namedtuple

QuaggaHost = namedtuple("QuaggaHost", "name ip loIP")
net = None


class QuaggaTopo(Topo):

    "Creates a topology of Quagga routers"

    def __init__(self):
        """Initialize a Quagga topology with 5 routers, configure their IP
           addresses, loop back interfaces, and paths to their private
           configuration directories."""
        Topo.__init__(self)

        # Directory where this file / script is located"
        selfPath = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))  # script directory

        # Initialize a service helper for Quagga with default options
        quaggaSvc = QuaggaService(autoStop=False)

        # Path configurations for mounts
        quaggaBaseConfigPath = selfPath + '/configs/'

	# Save order of node numeber/order to node name
	h1 = 0
	r1 = 1
	r2 = 2
	r3 = 3
	r4 = 4
	h2 = 5


        # List of Quagga host configs
        quaggaHosts = []
        quaggaHosts.append(QuaggaHost(name='h1', ip='10.10.11.1/24',
                                      loIP=None))
	quaggaHosts.append(QuaggaHost(name='r1', ip='10.10.11.2/24',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='r2', ip='10.10.12.2/24',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='r3', ip='10.10.13.2/24',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='r4', ip='10.10.14.2/24',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='h2', ip='10.10.16.2/24',
                                      loIP=None))



	quaggaContainers =[]
        # Setup each Quagga router, add a link between it and the IXP fabric
        for host in quaggaHosts:

            # Create an instance of a host, called a quaggaContainer
            quaggaContainers.append(self.addHost(name=host.name,
                                           ip=host.ip,
                                           hostname=host.name,
                                           privateLogDir=True,
                                           privateRunDir=True,
                                           inMountNamespace=True,
                                           inPIDNamespace=True,
                                           inUTSNamespace=True))


            # Configure and setup the Quagga service for this node
            quaggaSvcConfig = \
                {'quaggaConfigPath': quaggaBaseConfigPath + host.name}
            self.addNodeService(node=host.name, service=quaggaSvc,
                                nodeConfig=quaggaSvcConfig)

	# Link between h1 r1
        self.addLink(quaggaContainers[h1],quaggaContainers[r1], params1={'ip':'10.10.11.1/24'}, params2={'ip':'10.10.11.2/24'})
        self.addLink(quaggaContainers[r1],quaggaContainers[r2], params1={'ip':'10.10.12.1/24'}, params2={'ip':'10.10.12.2/24'})
        self.addLink(quaggaContainers[r1],quaggaContainers[r3], params1={'ip':'10.10.13.1/24'}, params2={'ip':'10.10.13.2/24'})
        self.addLink(quaggaContainers[r2],quaggaContainers[r4], params1={'ip':'10.10.14.1/24'}, params2={'ip':'10.10.14.2/24'})
        self.addLink(quaggaContainers[h2],quaggaContainers[r4], params1={'ip':'10.10.16.2/24'}, params2={'ip':'10.10.16.1/24'})
        self.addLink(quaggaContainers[r3],quaggaContainers[r4], params1={'ip':'10.10.15.1/24'}, params2={'ip':'10.10.15.2/24'})
