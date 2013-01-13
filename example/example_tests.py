import time
import unittest


class TestSubClass(unittest.TestCase):
    def test_something_in_first_subclass(self):
        pass

    
class TestSubSubClass(TestSubClass):
    def setUp(self):
        pass
        
    def test_a_thing(self):
        time.sleep(0.001)

    def test_something_else(self):
        time.sleep(0.2)

    def test_yet_again(self):
        time.sleep(0.4)


def test_1():
    time.sleep(0.0001)


def test_2():
    time.sleep(0.001)


def test_3():
    time.sleep(0.01)


def test_4():
    time.sleep(0.3)


def test_5():
    time.sleep(1) 


def test_6():
    time.sleep(0.6)


def test_7():
    time.sleep(0.8)

    
def test_8():
    time.sleep(0.9)
