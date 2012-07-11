#!/usr/bin/env python
# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: July 2012
#
# Does about ? issues/sec

try:
    from nedproductionsRedmineAPIKey import nedproductionsRedmineAPIKey
except:
    nedproductionsRedmineAPIKey=None

import sys, unittest
if sys.path[0]!='tests': sys.path.insert(0, 'tests')
if sys.path[0]!='.': sys.path.insert(0, '.')
from LibTest import *

class TestParseRedmineWithLib(TestParseWithLib, unittest.TestCase):

    @property
    def repoURI(self):
        return "http://www.nedproductions.biz/redmine?project_id=bexml-test-project&limit=1"+("&key="+nedproductionsRedmineAPIKey if nedproductionsRedmineAPIKey is not None else "")

    @property
    def filter(self):
        return "Niall"

if __name__=="__main__":
    unittest.main()
    