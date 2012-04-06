#!/usr/bin/env python
# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012
#
# Deliberately written to compile in IronPython and PyPy

import sys, unittest
if sys.path[0]!='.': sys.path.insert(0, '.')
from LibTest import *

class TestParseBEXMLWithLib(TestParseWithLib, unittest.TestCase):

    @property
    def repoURI(self):
        return "file://tests/bugs.bugseverywhere.org.xml"

    @property
    def profile(self):
        return False

if __name__=="__main__":
    unittest.main()
        