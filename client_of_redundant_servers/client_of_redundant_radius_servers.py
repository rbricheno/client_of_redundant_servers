"""
Client of redundant RADIUS servers.
    :copyright: (c) 2018 by Robert Bricheno.
    :license: MIT, see LICENSE for more details.
"""
from pyrad.client import Client
from pyrad.dictionary import Dictionary
import pyrad.packet
from client_of_redundant_servers import ClientOfRedundantServers, CurrentServerFailed
import socket
import os
package_dir = os.path.dirname(os.path.abspath(__file__))
default_dictionary = os.path.join(package_dir,'dictionary.minimal')


class ClientOfRedundantRadiusServers(ClientOfRedundantServers):
    """Stores information about how to query RADIUS servers, and provides a simple interface for requests."""
    def __init__(self,
                 server_list: list,
                 nas_identifier: str,
                 schedule: str='round-robin',
                 dict_file=None,
                 server_timeout=3,
                 client_bind_ip=None):

        if dict_file is not None:
            # 'dict_file' is the path to your dictionary file
            self.dictionary = Dictionary(dict_file)
        else:
            self.dictionary = Dictionary(default_dictionary)

        # 'nas_identifier' contains a string corresponding to the NAS-Identifier RADIUS attribute identifying the NAS
        # originating the Access-Request. It's can be whatever you want, it's like a friendly name for your client.
        self.nas_identifier = nas_identifier

        # 'server_timeout' is an integer that should be set to the desired timeout for each individual RADIUS server,
        # in seconds. So if this is set to 3, and you have 4 radius servers in your server list, it may be 12 seconds
        # before the radius_auth method returns (if all servers time out).
        self.server_timeout = server_timeout

        # 'client_bind_ip' is used to specify the IP address on the client from which RADIUS requests should originate,
        # or just leave it as None if you don't care.
        self.client_bind_ip = client_bind_ip

        # 'server_list' must be a list of dictionaries, like this:
        #
        # [{'auth_port': 1812,
        #   'hostname': 'radius0.inst.example.com',
        #   'secret': b'xxxx'},
        #  {'auth_port': 1812,
        #   'hostname': 'radius1.inst.example.com',
        #   'secret': b'yyyy'}]
        #
        # 'auth_port' is the port of the RADIUS server running on 'hostname'. 'secret' is the secret that we share
        # with the RADIUS server running on 'hostname'.
        super().__init__(server_list, schedule)

    def _radius_auth_func(self, server, **kwargs):
        """More private method used to authenticate a user and password against the current RADIUS server. Returns
           False if the user is rejected, True if the user is accepted. Raises CurrentServerFailed if there was an
           error with the request (such as a timeout)."""
        try:
            srv = Client(server=server['hostname'], authport=server['auth_port'],
                         secret=server['secret'], dict=self.dictionary)
            srv.timeout = self.server_timeout
            if self.client_bind_ip is not None:
                # Binding to port 0 is the official way to bind to a OS-assigned random port.
                srv.bind((self.client_bind_ip, 0))
            req = srv.CreateAuthPacket(code=pyrad.packet.AccessRequest, User_Name=kwargs['user'],
                                       NAS_Identifier=self.nas_identifier)
            req["User-Password"] = req.PwCrypt(kwargs['password'])
            reply = srv.SendPacket(req)
            if reply.code == pyrad.packet.AccessAccept:
                return True
            else:
                return False
        except (pyrad.packet.PacketError, pyrad.client.Timeout, socket.error):
            raise CurrentServerFailed

    def radius_auth(self, user: str, password: str):
        """Public method used to authenticate a user and password against any available RADIUS server. Returns False
           if the user is rejected, True if the user is accepted. Raises AllAvailableServersFailed if no RADIUS
           server responded to a request in a useful way."""
        return self.request(self._radius_auth_func, user=user, password=password)
