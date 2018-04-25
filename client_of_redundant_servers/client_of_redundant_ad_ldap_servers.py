"""
Client of redundant Active Directory LDAP servers.
    :copyright: (c) 2018 by Robert Bricheno.
    :license: MIT, see LICENSE for more details.
"""
import ldap3
import ldap3.core.exceptions
from ldap3.core.tls import Tls, ssl
from client_of_redundant_servers import ClientOfRedundantServers, CurrentServerFailed


class ClientOfRedundantAdLdapServers(ClientOfRedundantServers):
    """Stores information about how to query (Active Directory) LDAP servers, and provides a simple interface for
       requests."""
    def __init__(self,
                 server_list: list,
                 ldap_search_base: str,
                 schedule='round-robin',
                 ad_domain=None):

        # LDAP Search Base String. Also known as the Base DN (Distinguished Name). Probably something like:
        # 'ou=Users,ou=MyOrg,dc=myad,dc=private,dc=example,dc=com'
        self.ldap_search_base = ldap_search_base

        # You may be required to append an AD domain to an LDAP uid in order to establish an LDAP connection as that
        # user. Any 'ad_domain' set here is appended to the uid to create the username.
        self.ad_domain = ad_domain

        # 'server_list' must be a list of dictionaries, like this:
        #
        # [{'hostname': 'srvr-dc1.myad.private.example.com',
        #   'port': 636,
        #   'ssl': True,
        #   'validate': True},
        #  {'hostname': 'srvr-dc2.myad.private.example.com',
        #   'port': 636,
        #   'ssl': True,
        #   'validate': True}]
        #
        # 'port' is the port of the LDAP server running on 'hostname'. 'ssl' indicates whether we should attempt to use
        # SSL when communicating with this LDAP server. 'validate' means that we not only require SSL, but that we also
        # require the LDAP server to use a valid SSL certificate.
        super().__init__(server_list, schedule)

    def _ldap_auth_func(self, server, **kwargs):
        """More private method used to authenticate a user and password against the current LDAP server. Returns
           False if the user is rejected, True if the user is accepted. Raises CurrentServerFailed if there was an
           error with the request (such as a timeout). Basically, if you can bind as a user, then the user is valid."""
        try:
            ldap_username = kwargs['ldap_uid']
            if self.ad_domain is not None:
                ldap_username = kwargs['ldap_uid'] + '@' + self.ad_domain

            search_filter = "(&(objectClass=user)(cn=" + kwargs['ldap_uid'] + "))"
            attrs = ['*']

            if server['ssl']:
                if server['validate']:
                    tls = Tls(validate=ssl.CERT_REQUIRED)
                    ldap_server = ldap3.Server(server['hostname'], port=server['port'], use_ssl=True, tls=tls)
                else:
                    ldap_server = ldap3.Server(server['hostname'], port=server['port'], use_ssl=True)
            else:
                ldap_server = ldap3.Server(server['hostname'], port=server['port'])

            with ldap3.Connection(ldap_server, ldap_username, kwargs['ldap_pass'], auto_bind=True) as conn:
                conn.search(self.ldap_search_base, search_filter, attributes=attrs)
                if conn.entries:
                    return True
                else:
                    return False
        except ldap3.core.exceptions.LDAPBindError:
            # Invalid credentials
            return False
        except ldap3.core.exceptions.LDAPException:
            # Some other error
            raise CurrentServerFailed

    def ldap_auth(self, ldap_uid: str, ldap_pass: str):
        """Public method used to authenticate a user and password against any available LDAP server. Returns False
           if the user is rejected, True if the user is accepted. Raises AllAvailableServersFailed if no LDAP
           server responded to a request in a useful way."""
        return self.request(self._ldap_auth_func, ldap_uid=ldap_uid, ldap_pass=ldap_pass)
