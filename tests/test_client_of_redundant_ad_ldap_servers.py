import mock
import unittest
import logging
from client_of_redundant_servers.client_of_redundant_ad_ldap_servers import ClientOfRedundantAdLdapServers
from client_of_redundant_servers.client_of_redundant_servers import AllAvailableServersFailed
import ldap3.core.exceptions

logging.disable(logging.CRITICAL)


class TestClientOfRedundantAdLdapServers(unittest.TestCase):
    """Tests for `client_of_redundant_ad_ldap_servers.py`."""

    def setUp(self):
        self.fake_server_dict = {'srvr-dc1.myad.private.example.com': {'port': 636,
                                                                       'ssl': True,
                                                                       'validate': True},
                                 'srvr-dc2.myad.private.example.com': {'port': 636,
                                                                       'ssl': True,
                                                                       'validate': True}}

        self.no_validate_dict = {'srvr-dc1.myad.private.example.com': {'port': 636,
                                                                       'ssl': True,
                                                                       'validate': False},
                                 'srvr-dc2.myad.private.example.com': {'port': 636,
                                                                       'ssl': True,
                                                                       'validate': False}}

        self.no_ssl_dict = {'srvr-dc1.myad.private.example.com': {'port': 636,
                                                                  'ssl': False,
                                                                  'validate': False},
                            'srvr-dc2.myad.private.example.com': {'port': 636,
                                                                  'ssl': False,
                                                                  'validate': False}}

    def test_new_client_has_variables(self):
        fake_server_dict = {}
        a_client = ClientOfRedundantAdLdapServers(fake_server_dict, "test")
        self.assertEqual("test", a_client.ldap_search_base)
        self.assertEqual(None, a_client.ad_domain)

    def test_new_client_with_ad_domain_has_variables(self):
        fake_server_dict = {}
        a_client = ClientOfRedundantAdLdapServers(fake_server_dict, "test", ad_domain="corncrake")
        self.assertEqual("test", a_client.ldap_search_base)
        self.assertEqual("corncrake", a_client.ad_domain)

    def test_client_ldap_auth_no_servers(self):
        fake_server_dict = {}
        a_client = ClientOfRedundantAdLdapServers(fake_server_dict, "test")
        self.assertRaises(AllAvailableServersFailed, a_client.ldap_auth, ldap_uid="test", ldap_pass="1234")

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.Tls')
    def test_client_ldap_auth_some_servers(self, mock_tls, mock_ldap3):
        a_client = ClientOfRedundantAdLdapServers(self.fake_server_dict, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        mocked_tls = mock_tls.return_value
        hostname = list(self.fake_server_dict.keys())[0]
        mock_ldap3.Server.assert_called_with(hostname,
                                             port=self.fake_server_dict[hostname]['port'],
                                             use_ssl=self.fake_server_dict[hostname]['ssl'],
                                             tls=mocked_tls)
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_unvalidated_servers(self, mock_ldap3):
        a_client = ClientOfRedundantAdLdapServers(self.no_validate_dict, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        hostname = list(self.no_validate_dict.keys())[0]
        mock_ldap3.Server.assert_called_with(hostname,
                                             port=self.no_validate_dict[hostname]['port'],
                                             use_ssl=self.no_validate_dict[hostname]['ssl'])
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_servers_without_ssl(self, mock_ldap3):
        a_client = ClientOfRedundantAdLdapServers(self.no_ssl_dict, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        hostname = list(self.no_ssl_dict.keys())[0]
        mock_ldap3.Server.assert_called_with(hostname,
                                             port=self.no_ssl_dict[hostname]['port'])
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_some_servers_with_ad_domain(self, mock_ldap3):
        a_client = ClientOfRedundantAdLdapServers(self.fake_server_dict, "test", ad_domain="testdomain")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        mocked_server = mock_ldap3.Server.return_value
        mock_ldap3.Connection.assert_called_with(mocked_server, 'test@testdomain', '1234', auto_bind=True)
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_failing_servers(self, mock_ldap3):
        a_client = ClientOfRedundantAdLdapServers(self.fake_server_dict, "test")
        # This '__enter__' is how we mock the 'with ldap3.Connection...' context manager
        mock_ldap3.Connection.return_value.__enter__.return_value.entries = []
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        self.assertEqual(False, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_bind_error(self, mock_ldap3):
        # Explicitly un-mock the exception we are testing
        mock_ldap3.Connection.side_effect = ldap3.core.exceptions.LDAPBindError()
        mock_ldap3.core.exceptions.LDAPBindError = ldap3.core.exceptions.LDAPBindError
        a_client = ClientOfRedundantAdLdapServers(self.no_ssl_dict, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        self.assertEqual(False, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_ldap_exception(self, mock_ldap3):
        # Explicitly un-mock the exception we are testing
        mock_ldap3.Connection.side_effect = ldap3.core.exceptions.LDAPException()
        mock_ldap3.core.exceptions.LDAPException = ldap3.core.exceptions.LDAPException
        # Also un-mock the previous exception, as we check for it when handling LDAPException
        mock_ldap3.core.exceptions.LDAPBindError = ldap3.core.exceptions.LDAPBindError

        a_client = ClientOfRedundantAdLdapServers(self.no_ssl_dict, "test")
        self.assertRaises(AllAvailableServersFailed, a_client.ldap_auth, ldap_uid="test", ldap_pass="1234")


if __name__ == '__main__':
    unittest.main()
