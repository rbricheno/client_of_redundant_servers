from client_of_redundant_servers.client_of_redundant_ad_ldap_servers import ClientOfRedundantAdLdapServers
from client_of_redundant_servers.client_of_redundant_servers import AllAvailableServersFailed
from collections import OrderedDict

LDAP_SERVERS = OrderedDict()
LDAP_SERVERS['srvr-dc1.myad.private.example.com'] = {'port': 636,
                                                     'ssl': True,
                                                     'validate': True}
LDAP_SERVERS['srvr-dc2.myad.private.example.com'] = {'port': 636,
                                                     'ssl': True,
                                                     'validate': True}

LDAP_AD_DOMAIN = 'myad'
LDAP_SEARCH_BASE = 'ou=Users,ou=MyOrg,dc=myad,dc=private,dc=example,dc=com'

servers = ClientOfRedundantAdLdapServers(server_dict=LDAP_SERVERS,
                                         ad_domain=LDAP_AD_DOMAIN,
                                         ldap_search_base=LDAP_SEARCH_BASE)

ldap_uid = 'test'
ldap_pass = '1234'

try:
    auth_user = servers.ldap_auth(ldap_uid, ldap_pass)
    if auth_user:
        print("Accepted")
    else:
        print("Rejected")
except AllAvailableServersFailed:
    print("Error: no servers available")
