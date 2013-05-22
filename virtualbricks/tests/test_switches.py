from virtualbricks import switches
from virtualbricks.tests import unittest, stubs


def patch_brick(brick, output, input):
    brick.send = output.append
    brick.recv = input.pop


class TestSwitch(unittest.TestCase):

    def test_base(self):
        sw = switches.Switch(stubs.FactoryStub(), "test_switch")
        self.assertEqual(len(sw.socks), 1)
        self.assertEqual(sw.socks[0].path, sw.path())
        self.assertIs(sw.proc, None)

    def test_live_management_callbacks(self):
        sw = switches.Switch(stubs.FactoryStub(), "test_switch")
        output, input = [], []
        patch_brick(sw, output, input)
        input.append("ok")
        sw.cfg.numports = "33"
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], "port/setnumports 33")
        sw.cfg["numports"] = 33
        self.assertEqual(len(output), 1)