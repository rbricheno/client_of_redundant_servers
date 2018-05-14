from client_of_redundant_servers.client_of_redundant_radius_servers import ClientOfRedundantRadiusServers
from client_of_redundant_servers.client_of_redundant_servers import AllAvailableServersFailed
from collections import OrderedDict

CLIENT_BIND_IP = "10.0.0.2"
NAS_IDENTIFIER = "CoolRADIUSClient"
SERVER_TIMEOUT = 3
RADIUS_SERVERS = OrderedDict()
RADIUS_SERVERS['radius0.inst.example.com'] = {'auth_port': 1812,
                                              'secret': b'xxxx'}
RADIUS_SERVERS['radius1.inst.example.com'] = {'auth_port': 1812,
                                              'secret': b'yyyy'}

servers = ClientOfRedundantRadiusServers(server_dict=RADIUS_SERVERS,
                                         nas_identifier=NAS_IDENTIFIER,
                                         server_timeout=SERVER_TIMEOUT,
                                         client_bind_ip=CLIENT_BIND_IP)

user = 'test'
password = '1234'

try:
    auth_user = servers.radius_auth(user, password)
    if auth_user:
        print("Accepted")
    else:
        print("Rejected")
except AllAvailableServersFailed:
    print("Error: no servers available")
