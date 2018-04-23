# client_of_redundant_servers

[![Build Status](https://travis-ci.org/rbricheno/client_of_redundant_servers.svg?branch=master)](https://travis-ci.org/rbricheno/client_of_redundant_servers)
[![codecov](https://codecov.io/gh/rbricheno/client_of_redundant_servers/branch/master/graph/badge.svg)](https://codecov.io/gh/rbricheno/client_of_redundant_servers)

Generic client of redundant servers. A simple framework to make requests of unreliable servers. Throws an exception if no servers are available, otherwise returns a result from the first server that doesn't fail. Supports round-robin, fixed, and random orders of servers.
