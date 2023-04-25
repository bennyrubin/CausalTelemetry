from mininet.net import Mininet
from mininet.node import Node
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel, info
import sys

class LinuxRouter( Node ):	# from the Mininet library
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        info ('enabling forwarding on ', self)
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

class BGPTopo(Topo):

    router_count = 0

    def add_subnet(self, router):
        self.router_count += 1
        switch = self.addSwitch(f's{self.router_count}')
        IP = self.nodeInfo(router)['ip'][:-3]
        self.addLink(switch,
                     router,
                     intfName2=f'r{self.router_count}-s{self.router_count}',
                     params2={'ip': f'{IP}/24'})
        
        host = self.addHost(name=f'd{self.router_count}',
                          ip=IP + "0/24",
                          defaultRoute= f"via {IP}")
        self.addLink(host, switch)


    # later refactor this to use a JSON file 
    def build(self, **_opts):

        # Add 2 routers in two different subnets
        r1 = self.addHost('r1', cls=LinuxRouter, ip='10.0.0.1/24')
        r2 = self.addHost('r2', cls=LinuxRouter, ip='10.0.1.1/24')
        r3 = self.addHost('r3', cls=LinuxRouter, ip='10.0.2.1/24')

        routers = [r1,r2,r3]

        for r in routers:
            self.add_subnet(r)

        # Add router-router link in a new subnet for the router-router connection
        self.addLink(r1,
                     r2,
                     intfName1='r1-r2',
                     intfName2='r2-r1',
                     params1={'ip': '1.1.2.1/24'},
                     params2={'ip': '1.1.2.2/24'})
        
        self.addLink(r2,
                     r3,
                     intfName1='r2-r3',
                     intfName2='r3-r2',
                     params1={'ip': '1.2.3.1/24'},
                     params2={'ip': '1.2.3.2/24'})
        
        # can make all the routers connect to a switch in the same subnet
        # ex: 192.168.0.0 <-- causal_tel server
        # 192.168.0.1 ... 192.168.0.n
        server = self.addHost('server', ip='192.168.0.100/24')
        server_switch = self.addSwitch("s100")
        self.addLink(server, server_switch)
        for router in routers:
            id = self.nodeInfo(router)['ip'][:-3].split(".")[2]
            info(f"IP: {id}")
            self.addLink(router, server_switch, intfName1=f"{router}-server", 
                         params1={'ip':f'192.168.0.{id}/24'})

        

def main():
    bgp_topo = BGPTopo()
    net = Mininet(topo = bgp_topo, autoSetMacs = True)

    # Add routing for reaching networks that aren't directly connected
    # command to add connectivity between r1 subnet and r2 subnet
    # info(net['r1'].cmd("ip route add 10.0.1.0/24 via 1.1.2.2"))
    # info(net['r2'].cmd("ip route add 10.0.0.0/24 via 1.1.2.1"))
    print("NET LINKS")
    print(bgp_topo.links())

    net.start()

    net[ 'r1' ].popen('python3 -u simpleBGP.py --ip 10.0.0.0/24 --neighbor 1.1.2.2 true 100', stdout=sys.stdout, stderr=sys.stdout)
    net[ 'r2' ].popen('python3 -u simpleBGP.py --ip 10.0.1.0/24 --neighbor 1.1.2.1 false 100', stdout=sys.stdout, stderr=sys.stdout)
    net[ 'server' ].popen('python3 -u CausalServer.py',stdout=sys.stdout, stderr=sys.stdout)


    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    main()