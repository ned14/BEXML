#!/usr/bin/env python
# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012
#
# Deliberately written to compile in IronPython and PyPy

import sys, unittest
if sys.path[0]!='.': sys.path.insert(0, '.')
from LibTest import *

class TestParseBErepoWithLib(TestParseWithLib, unittest.TestCase):

    @property
    def repoURI(self):
        return "file://tests/bugs.bugseverywhere.org"

    @property
    def filter(self):
        return "Trevor"

if __name__=="__main__":
    unittest.main()
            