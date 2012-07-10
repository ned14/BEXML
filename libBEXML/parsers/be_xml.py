# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

from ..xmlparserbase import XMLComment, XMLIssue, XMLParser

import os, logging
from copy import copy, deepcopy

log=logging.getLogger(__name__)


class BEXMLComment(XMLComment):
    """A comment loaded from an XML based BE repo"""

    def __init__(self, parentIssue, commentelem):
        XMLComment.__init__(self, parentIssue, commentelem)


class BEXMLIssue(XMLIssue):
    """An issue loaded from an XML based BE repo"""

    def __init__(self, parser, bugelem):
        XMLIssue.__init__(self, parser, bugelem, mapToBE={'created':('time', lambda xmlelem:xmlelem.text), 'extra-string':('extra-strings', lambda xmlelem:xmlelem.text)}, dontprocess=set(['comment']))

    @XMLIssue.element.setter
    def element(self, value):
        XMLIssue.element.fset(self, value)
        for valueelem in self.element.findall("comment"):
            if valueelem.tag=="comment":
                self.addComment(BEXMLComment(self, valueelem))


class BEXMLParser(XMLParser):
    """Parses an XML based BE repo"""

    @classmethod
    def _schemapath(cls):
        return os.path.join(os.path.dirname(__file__), "bexml.xsd")

    @classmethod
    def _sourceopen(cls, uri):
        return open(uri.pathname, 'r') if uri.scheme=="file" else urllib2.urlopen(str(self.uri))

    def _XMLIssue(self, bugelem, **pars):
        ret=copy(self.BEXMLIssue)
        ret.element=bugelem
        return ret

    def __init__(self, uri, encoding="utf-8"):
        XMLParser.__init__(self, uri, encoding)
        self.BEXMLIssue=BEXMLIssue(self, None)

    def try_location(self, mimetype=None, first256bytes=None):
        score, errmsg=XMLParser.try_location(self, mimetype, first256bytes)
        if score>=0 and first256bytes is not None and '<be-xml>' in first256bytes: score+=100
        return (score, errmsg)

def instantiate(uri, **args):
    return BEXMLParser(uri, **args)
