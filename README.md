# Client of redundant servers

[![Build Status](https://travis-ci.org/rbricheno/client_of_redundant_servers.svg?branch=master)](https://travis-ci.org/rbricheno/client_of_redundant_servers)
[![codecov](https://codecov.io/gh/rbricheno/client_of_redundant_servers/branch/master/graph/badge.svg)](https://codecov.io/gh/rbricheno/client_of_redundant_servers)
[![PyPI version](https://badge.fury.io/py/client-of-redundant-servers.svg)](https://badge.fury.io/py/client-of-redundant-servers)

Generic client of redundant servers. A simple framework to make requests of unreliable servers.
Throws an exception if no servers are available, otherwise returns a result from the first server that doesn't fail.
Supports round-robin, fixed, and random orders of servers.

The intention is that you can use this to glue together things that are otherwise slightly tedious, 
using your own client classes which inherit from ClientOfRedundantServers.


## Installation
```
pip install client-of-redundant-servers
```


## Usage

Say you have some web servers, all serving the same content, and you want to get a file from any one.
You don't care which server responds, but you don't want to have to manually look for failures and try again.

`client_of_redundant_servers` lets you write things like this:

```python
import requests
import client_of_redundant_servers as cors


class ClientOfRedundantWebServers(cors.ClientOfRedundantServers):
    def __init__(self, url_list: list):
        # Super().__init__ wants a dict, but this example is so simple that
        # a list can be used to create a dict of None.
        url_dict = dict((value, None) for value in url_list)
        super().__init__(url_dict)

    def _get_file_func(self, url):
        try:
            r =  requests.get(url)
            # Check for errors that didn't raise a requests.exception
            if not r.ok:
                raise cors.CurrentServerFailed
            return r
        except requests.exceptions.RequestException:
            raise cors.CurrentServerFailed

    def get_file(self):
        return self.request(self._get_file_func)


# Only picking on Ubuntu because it is widely mirrored.
urls = ["http://badserver.example.com/badfile",
        "http://www.mirrorservice.org/sites/cdimage.ubuntu.com/cdimage/releases/16.04/release/SHA256SUMS",
        "http://nl.archive.ubuntu.com/ubuntu-cdimages/16.04/release/SHA256SUMS"]

client = ClientOfRedundantWebServers(urls)
try:
    r = client.get_file()
    print(r.text)
    print("*****")
    print("Retrieved from : " + r.url)
except cors.AllAvailableServersFailed:
    print("Error! No servers were available to service the request.")
```

If you run that, you'll see that the client tries to retrieve the file from `badserver`,
which fails, so it continues to try the next available server.

See the "examples" directory for some examples that might be useful.
Currently there's a RADIUS client using [pyrad](https://github.com/wichert/pyrad)
and an Active Directory LDAP client using [ldap3](https://github.com/cannatag/ldap3).
