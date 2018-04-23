"""
Generic client of redundant servers.
    :copyright: (c) 2018 by Robert Bricheno.
    :license: MIT, see LICENSE for more details.
"""
from random import shuffle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CurrentServerFailed(Exception):
    pass


class AllAvailableServersFailed(Exception):
    pass


class ClientOfRedundantServers(object):
    """Stores information about how to query servers, and provides a simple interface for requests."""
    def __init__(self, server_list: list, schedule: str='round-robin', **kwargs):
        self.server_list = server_list

        # '_rr_position' and '_server_list_len' are used internally to keep track of which server should be used as
        # the first in the server list when using round-robin scheduling.
        self._server_list_len = len(self.server_list)
        self._rr_position = 0

        # 'schedule' is a string used to set the desired scheduling strategy. It must be 'round-robin' to use the
        # round-robin strategy, 'random' to use the random strategy, or 'fixed' to use the deterministic strategy
        # which uses the servers in the order listed every time.
        if schedule not in ['round-robin', 'random', 'fixed']:
            raise NotImplementedError("Schedule type " + schedule + " not implemented")
        self._schedule = schedule

    def request(self, func_to_call, **kwargs):
        """Public method used to make a request of any available server. Returns a useful result if the request
           succeeds. Raises AllAvailableServersFailed if no server responded to a request in a useful way. The
           argument func_to_call is a function that will be run against each server in turn."""
        if self._schedule == 'round-robin':
            # Round-robin server order, servers are tried starting from the next server in the list each time.
            # The starting position in the new list moves forward each time the method is called with this schedule.
            new_list = self.server_list[self._rr_position:self._server_list_len]\
                       + self.server_list[0:self._rr_position]
            self._rr_position += 1
            if self._rr_position >= self._server_list_len:
                self._rr_position = 0
            return self._request_recursive(func_to_call, new_list, **kwargs)

        if self._schedule == 'random':
            # Pseudo-random server order, servers are tried in a random order each time.
            new_list = list(self.server_list)
            shuffle(new_list)
            return self._request_recursive(func_to_call, new_list, **kwargs)

        # Fixed schedule, servers are tried in the order in which they are defined.
        if self._schedule == 'fixed':
            return self._request_recursive(func_to_call, self.server_list, **kwargs)

        raise NotImplementedError("Schedule type " + self._schedule + " not implemented")

    def _request_recursive(self, func_to_call, server_list: list, **kwargs):
        """More private method used to recursively check each server until one doesn't fail."""
        if not server_list:
            # Default case, raise an exception if there are no servers to check.
            logger.error("All available servers failed.")
            raise AllAvailableServersFailed()

        current_server = server_list[0]

        try:
            # Do something with current server
            return func_to_call(current_server, **kwargs)
        except CurrentServerFailed:
            # Use the original list, minus the server we already tried.
            logger.warning("Server " + str(current_server) + " failed.")
            return self._request_recursive(func_to_call, server_list[1:], **kwargs)
