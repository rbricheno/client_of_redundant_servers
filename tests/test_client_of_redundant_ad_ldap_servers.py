import mock
import unittest
import logging
from client_of_redundant_servers.client_of_redundant_ad_ldap_servers import ClientOfRedundantAdLdapServers
from client_of_redundant_servers.client_of_redundant_servers import AllAvailableServersFailed
import ldap3.core.exceptions

logging.disable(logging.CRITICAL)


class TestClientOfRedundantAdLdapServers(unittest.TestCase):
    """Tests for `client_of_redundant_servers.py`."""

    def test_new_client_has_variables(self):
        fake_server_list = []
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        self.assertEqual("test", a_client.ldap_search_base)
        self.assertEqual(None, a_client.ad_domain)

    def test_new_client__with_ad_domain_has_variables(self):
        fake_server_list = []
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test", ad_domain="corncrake")
        self.assertEqual("test", a_client.ldap_search_base)
        self.assertEqual("corncrake", a_client.ad_domain)

    def test_client_ldap_auth_no_servers(self):
        fake_server_list = []
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        self.assertRaises(AllAvailableServersFailed, a_client.ldap_auth, "test_user", "1234")

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.Tls')
    def test_client_ldap_auth_some_servers(self, mock_tls, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': True},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': True}]
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")

        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        mocked_tls = mock_tls.return_value
        mock_ldap3.Server.assert_called_with(fake_server_list[0]['hostname'],
                                             port=fake_server_list[0]['port'],
                                             use_ssl=fake_server_list[0]['ssl'],
                                             tls=mocked_tls)
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_unvalidated_servers(self, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': False},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': False}]
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        mock_ldap3.Server.assert_called_with(fake_server_list[0]['hostname'],
                                             port=fake_server_list[0]['port'],
                                             use_ssl=fake_server_list[0]['ssl'])
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_nossl_servers(self, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': False,
                             'validate': False},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': False,
                             'validate': False}]
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        mock_ldap3.Server.assert_called_with(fake_server_list[0]['hostname'],
                                             port=fake_server_list[0]['port'])
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_some_servers_with_ad_domain(self, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': True},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': True}]
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test", ad_domain="testdomain")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        mocked_server = mock_ldap3.Server.return_value
        mock_ldap3.Connection.assert_called_with(mocked_server, 'test@testdomain', '1234', auto_bind=True)
        self.assertEqual(True, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_failing_servers(self, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': True},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': True,
                             'validate': True}]
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        mock_ldap3.Connection.return_value.__enter__.return_value.entries = []
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        self.assertEqual(False, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_binderror(self, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': False,
                             'validate': False},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': False,
                             'validate': False}]
        # Explicitly un-mock the exception we are testing
        mock_ldap3.Connection.side_effect = ldap3.core.exceptions.LDAPBindError()
        mock_ldap3.core.exceptions.LDAPBindError = ldap3.core.exceptions.LDAPBindError
        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        result = a_client.ldap_auth(ldap_uid="test", ldap_pass="1234")
        self.assertEqual(False, result)

    @mock.patch('client_of_redundant_servers.client_of_redundant_ad_ldap_servers.ldap3')
    def test_client_ldap_auth_ldap_exception(self, mock_ldap3):
        fake_server_list = [{'hostname': 'srvr-dc1.myad.private.example.com',
                             'port': 636,
                             'ssl': False,
                             'validate': False},
                            {'hostname': 'srvr-dc2.myad.private.example.com',
                             'port': 636,
                             'ssl': False,
                             'validate': False}]
        # Explicitly un-mock the exception we are testing
        mock_ldap3.Connection.side_effect = ldap3.core.exceptions.LDAPException()
        mock_ldap3.core.exceptions.LDAPException = ldap3.core.exceptions.LDAPException
        # Also un-mock the previous exception, as we check for it when handling LDAPException
        mock_ldap3.core.exceptions.LDAPBindError = ldap3.core.exceptions.LDAPBindError

        a_client = ClientOfRedundantAdLdapServers(fake_server_list, "test")
        self.assertRaises(AllAvailableServersFailed, a_client.ldap_auth, ldap_uid="test", ldap_pass="1234")


if __name__ == '__main__':
    unittest.main()
