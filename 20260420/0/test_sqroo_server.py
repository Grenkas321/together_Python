import multiprocessing
import socket
import time
import unittest

import sqroo


class TestSqrootsServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = multiprocessing.Process(target=sqroo.srv)
        cls.proc.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.join()

    def setUp(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("127.0.0.1", 1337))

    def tearDown(self):
        self.s.close()

    def test_no_roots(self):
        self.assertEqual(sqroo.sqrootnet("1 0 1", self.s), "")

    def test_one_root(self):
        self.assertEqual(sqroo.sqrootnet("1 2 1", self.s), "-1.0")

    def test_two_roots(self):
        self.assertEqual(sqroo.sqrootnet("1 0 -1", self.s), "-1.0 1.0")

    def test_exception(self):
        self.assertEqual(sqroo.sqrootnet("0 1 2", self.s), "")


if __name__ == "__main__":
    unittest.main()