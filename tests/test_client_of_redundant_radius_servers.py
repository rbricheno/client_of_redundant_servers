import mock
import unittest
import logging
from client_of_redundant_servers.client_of_redundant_radius_servers import ClientOfRedundantRadiusServers
from client_of_redundant_servers.client_of_redundant_servers import AllAvailableServersFailed
from collections import OrderedDict
import os
import pyrad.packet
import socket

logging.disable(logging.CRITICAL)


class TestClientOfRedundantAdLdapServers(unittest.TestCase):
    """Tests for `client_of_redundant_radius_servers.py`."""

    def setUp(self):
        self.fake_server_dict = OrderedDict()
        self.fake_server_dict['radius0.inst.example.com'] = {'auth_port': 1812,
                                                             'secret': b'xxxx'}
        self.fake_server_dict['radius1.inst.example.com'] = {'auth_port': 1812,
                                                             'secret': b'yyyy'}

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Dictionary')
    def test_new_client_has_variables(self, mock_dictionary):
        fake_server_dict = OrderedDict()
        package_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_dictionary = os.path.join(package_parent_dir, 'client_of_redundant_servers', 'dictionary.minimal')
        a_client = ClientOfRedundantRadiusServers(fake_server_dict, "test")
        mock_dictionary.assert_called_with(default_dictionary)
        self.assertEqual("test", a_client.nas_identifier)
        self.assertEqual(3, a_client.server_timeout)
        self.assertEqual(None, a_client.client_bind_ip)
        self.assertEqual(fake_server_dict, a_client.server_dict)

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Dictionary')
    def test_new_client_has_manual_dictionary(self, mock_dictionary):
        fake_server_dict = OrderedDict()
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_dictionary = os.path.join(test_dir, 'dictionary.fictional')
        _ = ClientOfRedundantRadiusServers(fake_server_dict, "test", dict_file=test_dictionary)
        mock_dictionary.assert_called_with(test_dictionary)

    def test_client_radius_auth_no_servers(self):
        fake_server_dict = OrderedDict()
        a_client = ClientOfRedundantRadiusServers(fake_server_dict, "test")
        self.assertRaises(AllAvailableServersFailed, a_client.radius_auth, user="test", password="1234")

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Client')
    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Dictionary')
    def test_client_radius_auth_fails(self, mock_dictionary, mock_pyrad_client):
        a_client = ClientOfRedundantRadiusServers(self.fake_server_dict, "test")
        result = a_client.radius_auth(user="test", password="1234")
        hostname = list(self.fake_server_dict.keys())[0]
        mock_pyrad_client.assert_called_with(server=hostname,
                                             authport=self.fake_server_dict[hostname]['auth_port'],
                                             secret=self.fake_server_dict[hostname]['secret'],
                                             dict=mock_dictionary.return_value)
        self.assertEqual(False, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Client')
    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Dictionary')
    def test_client_radius_auth_succeeds(self, mock_dictionary, mock_pyrad_client):
        mock_pyrad_client.return_value.SendPacket.return_value.code = pyrad.packet.AccessAccept
        a_client = ClientOfRedundantRadiusServers(self.fake_server_dict, "test")
        result = a_client.radius_auth(user="test", password="1234")
        # We don't bind to a specific IP
        assert not mock_pyrad_client.return_value.bind.called
        hostname = list(self.fake_server_dict.keys())[0]
        mock_pyrad_client.assert_called_with(server=hostname,
                                             authport=self.fake_server_dict[hostname]['auth_port'],
                                             secret=self.fake_server_dict[hostname]['secret'],
                                             dict=mock_dictionary.return_value)
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Client')
    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Dictionary')
    def test_client_radius_auth_with_client_ip_succeeds(self, mock_dictionary, mock_pyrad_client):
        mock_pyrad_client.return_value.SendPacket.return_value.code = pyrad.packet.AccessAccept
        a_client = ClientOfRedundantRadiusServers(self.fake_server_dict, "test", client_bind_ip='192.168.0.1')
        result = a_client.radius_auth(user="test", password="1234")
        # We must bind to the given IP
        mock_pyrad_client.return_value.bind.assert_called_with(('192.168.0.1', 0))
        hostname = list(self.fake_server_dict.keys())[0]
        mock_pyrad_client.assert_called_with(server=hostname,
                                             authport=self.fake_server_dict[hostname]['auth_port'],
                                             secret=self.fake_server_dict[hostname]['secret'],
                                             dict=mock_dictionary.return_value)
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Client')
    def test_client_radius_auth_packet_error_exception(self, mock_pyrad_client):
        a_client = ClientOfRedundantRadiusServers(self.fake_server_dict, "test")
        mock_pyrad_client.side_effect = pyrad.packet.PacketError
        self.assertRaises(AllAvailableServersFailed, a_client.radius_auth, user="test", password="1234")

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Client')
    def test_client_radius_auth_timeout_exception(self, mock_pyrad_client):
        a_client = ClientOfRedundantRadiusServers(self.fake_server_dict, "test")
        mock_pyrad_client.side_effect = pyrad.client.Timeout
        self.assertRaises(AllAvailableServersFailed, a_client.radius_auth, user="test", password="1234")

    @mock.patch('client_of_redundant_servers.client_of_redundant_radius_servers.Client')
    def test_client_radius_auth_socket_error_exception(self, mock_pyrad_client):
        a_client = ClientOfRedundantRadiusServers(self.fake_server_dict, "test")
        mock_pyrad_client.side_effect = socket.error
        self.assertRaises(AllAvailableServersFailed, a_client.radius_auth, user="test", password="1234")
