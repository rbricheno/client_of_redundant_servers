import unittest
import types
import logging

from client_of_redundant_servers.client_of_redundant_servers import ClientOfRedundantServers,\
                                                                    CurrentServerFailed,\
                                                                    AllAvailableServersFailed
from collections import OrderedDict


logging.disable(logging.CRITICAL)


class FakeException(Exception):
    pass


class FakeServer(object):
    def __init__(self, bad):
        self.used = False
        self.bad = bad

    def do_server_task(self):
        self.used = True
        if self.bad:
            raise FakeException
        else:
            return True


class ClientOfRedundantFakeServers(ClientOfRedundantServers):
    def __init__(self, server_dict: OrderedDict, schedule='round-robin'):
        super().__init__(server_dict, schedule)

    def _fake_server_func(self, server):
        try:
            return server.do_server_task()
        except FakeException:
            raise CurrentServerFailed

    def fake_func(self):
        return self.request(self._fake_server_func)


class TestClientOfRedundantServers(unittest.TestCase):
    """Tests for `client_of_redundant_servers.py`."""

    def test_new_client_has_variables(self):
        fake_server_dict = OrderedDict()
        a_client = ClientOfRedundantServers(fake_server_dict)
        self.assertEqual(0, a_client._server_list_len)
        self.assertEqual(0, a_client._rr_position)
        self.assertEqual('round-robin', a_client._schedule)

    def test_cannot_use_fictional_schedule(self):
        fake_server_dict = {}
        self.assertRaises(NotImplementedError, ClientOfRedundantServers, fake_server_dict, "bananas")

    def test_rr_pos_advances(self):
        fake_server_dict = OrderedDict()
        fake_server_dict[FakeServer(False)] = None
        fake_server_dict[FakeServer(False)] = None
        fake_server_dict[FakeServer(False)] = None
        a_client = ClientOfRedundantFakeServers(fake_server_dict)
        self.assertEqual(0, a_client._rr_position)
        self.assertEqual(3, a_client._server_list_len)
        result = a_client.fake_func()
        self.assertEqual(True, result)
        self.assertEqual(1, a_client._rr_position)
        result2 = a_client.fake_func()
        self.assertEqual(True, result2)
        self.assertEqual(2, a_client._rr_position)
        result3 = a_client.fake_func()
        self.assertEqual(True, result3)
        self.assertEqual(0, a_client._rr_position)

    def test_bad_server_list(self):
        fake_server_dict = OrderedDict()
        fake_server_dict[FakeServer(True)] = None
        fake_server_dict[FakeServer(True)] = None
        a_client = ClientOfRedundantServers(fake_server_dict)

        def just_raise(self):
            raise CurrentServerFailed

        a_client.just_raise = types.MethodType(just_raise, a_client)
        self.assertRaises(AllAvailableServersFailed, a_client.request, just_raise)

    def test_servers_used_rr(self):
        fake_server_1 = FakeServer(False)
        fake_server_2 = FakeServer(False)
        fake_server_3 = FakeServer(False)
        fake_server_dict = OrderedDict()
        fake_server_dict[fake_server_1] = None
        fake_server_dict[fake_server_2] = None
        fake_server_dict[fake_server_3] = None
        a_client = ClientOfRedundantFakeServers(fake_server_dict)
        self.assertEqual(False, fake_server_1.used)
        self.assertEqual(False, fake_server_2.used)
        self.assertEqual(False, fake_server_3.used)
        _ = a_client.fake_func()
        self.assertEqual(True, fake_server_1.used)
        self.assertEqual(False, fake_server_2.used)
        self.assertEqual(False, fake_server_3.used)
        _ = a_client.fake_func()
        self.assertEqual(True, fake_server_1.used)
        self.assertEqual(True, fake_server_2.used)
        self.assertEqual(False, fake_server_3.used)
        _ = a_client.fake_func()
        self.assertEqual(True, fake_server_1.used)
        self.assertEqual(True, fake_server_2.used)
        self.assertEqual(True, fake_server_3.used)

    def test_servers_used_fixed(self):
        fake_server_1 = FakeServer(False)
        fake_server_2 = FakeServer(False)
        fake_server_3 = FakeServer(False)
        fake_server_dict = OrderedDict()
        fake_server_dict[fake_server_1] = None
        fake_server_dict[fake_server_2] = None
        fake_server_dict[fake_server_3] = None
        a_client = ClientOfRedundantFakeServers(fake_server_dict, schedule='fixed')
        self.assertEqual(False, fake_server_1.used)
        self.assertEqual(False, fake_server_2.used)
        self.assertEqual(False, fake_server_3.used)
        _ = a_client.fake_func()
        self.assertEqual(True, fake_server_1.used)
        self.assertEqual(False, fake_server_2.used)
        self.assertEqual(False, fake_server_3.used)
        _ = a_client.fake_func()
        self.assertEqual(True, fake_server_1.used)
        self.assertEqual(False, fake_server_2.used)
        self.assertEqual(False, fake_server_3.used)

    def test_servers_used_random(self):
        fake_server_1 = FakeServer(False)
        fake_server_2 = FakeServer(False)
        fake_server_dict = OrderedDict()
        fake_server_dict[fake_server_1] = None
        fake_server_dict[fake_server_2] = None
        a_client = ClientOfRedundantFakeServers(fake_server_dict, schedule='random')
        self.assertEqual(False, fake_server_1.used)
        self.assertEqual(False, fake_server_2.used)
        _ = a_client.fake_func()
        any_one_server_used = (fake_server_1.used or fake_server_2.used) \
            and not (fake_server_1.used and fake_server_2.used)
        self.assertEqual(True, any_one_server_used)


if __name__ == '__main__':
    unittest.main()
