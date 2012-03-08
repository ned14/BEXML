# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

from ..parserbase import ParserBase
from ..issue import Issue as IssueBase
from ..comment import Comment as CommentBase

import os, logging, urlparse, urllib2
from lxml import etree
from encodings import utf_8 as ironpython_utf8_override
from collections import namedtuple
from uuid import UUID

log=logging.getLogger(__name__)


class BEXMLComment(CommentBase):
    """A comment loaded from an XML based BE repo"""

    def __init__(self, parentIssue, commentelem):
        CommentBase.__init__(self, parentIssue)
        self.element=commentelem

    @property
    def isStale(self):
        """True if the XML backing for this comment is newer than us"""
        if not self.isLoaded or not self.tracksStaleness:
            return None
        return True

    def load(self, reload=False):
        """Loads in the comment from XML"""
        if not reload and self.isLoaded:
            return
        values={}
        for valueelem in self.element:
            values[valueelem.tag]=valueelem.text
        notloaded=self._load_mostly(values)
        self.isLoaded=True
        if len(notloaded)>0:
            log.warn("The following values from comment "+str(self.uuid)+" were not recognised: "+repr(notloaded))
        self.isDirty=False


class BEXMLIssue(IssueBase):
    """An issue loaded from an XML based BE repo"""

    def __init__(self, bugelem):
        IssueBase.__init__(self)
        self.element=bugelem
        for valueelem in self.element.findall("comment"):
            if valueelem.tag=="comment":
                self.addComment(BEXMLComment(self, valueelem))

    @property
    def isStale(self):
        """True if the XML backing for this issue is newer than us"""
        if not self.isLoaded or not self.tracksStaleness:
            return None
        return True

    def load(self, reload=False):
        """Loads in the issue from XML"""
        if not reload and self.isLoaded:
            return
        values={}
        for valueelem in self.element:
            if valueelem.tag!="comment":
                tag=valueelem.tag
                if tag=="created": tag="time"
                elif tag=="extra-string": tag="extra-strings"
                values[tag]=valueelem.text
        notloaded=self._load_mostly(values)
        self.isLoaded=True
        if len(notloaded)>0:
            log.warn("The following values from issue "+str(self.uuid)+" were not recognised: "+repr(notloaded))
        self.isDirty=False


class BEXMLParser(ParserBase):
    """Parses an XML based BE repo"""
    bexml_schema=etree.XMLSchema(file=os.path.join(os.path.dirname(__file__), "bexml.xsd"))

    def __init__(self, uri, encoding="utf-8"):
        ParserBase.__init__(self, uri)
        self.source=None
        self.__bugs={}

    def try_location(self, mimetype=None, first256bytes=None):
        up=urlparse.urlparse(self.uri)
        data=None
        if up.scheme=="file":
            path=self._pathFromURI()
            if path[-4:]!='.xml':
                return (-999, "'"+path+"' is not an XML file")
            if not os.path.isfile(path):
                return (-998, "'"+path+"' is not a file")

        # Is this a mimetype I can live with?
        score=1
        if mimetype=="text/xml" or mimetype=="application/xml": score+=5
        if first256bytes is not None and '<be-xml>' in first256bytes: score+=100
        return (score, None)

    def reload(self):
        """Start parsing a BE XML file"""
        if self.source is None:
            assert self.try_location()[0]>0
        if self.source is not None:
            self.source.close()
            self.source=None
        self.__bugs={}
        if self.uri[:4]=="file":
            self.source=open(self._pathFromURI(), 'r')
        else:
            self.source=urllib2.urlopen(self.uri)

    def parseIssues(self, issuefilter=None):
        if self.source is None:
            self.reload()
        if len(self.__bugs)==0:
            for _, bugelem in etree.iterparse(self.source, tag='bug', schema=self.bexml_schema):
                issue=BEXMLIssue(bugelem)
                self.__bugs[issue.uuid]=issue
                if issuefilter is None or issue._match(issuefilter):
                    yield issue
        else:
            for issueuuid in self.__bugs:
                issue=self.__bugs[issueuuid]
                if issuefilter is None or issue._match(issuefilter):
                    yield issue

    def parseComments(self, issue_uuid, commentfilter=None):
        if not isinstance(issue_uuid, str):
            issue_uuid=str(issue_uuid)
        if issue_uuid not in self.__bugs:
            raise AssertionError, "Issue uuid '"+str(issue_uuid)+"' not found"
        issue=self.__bugs[issue_uuid]
        for commentuuid in issue.comments:
            yield issue.comments[commentuuid]

def instantiate(uri, **args):
    return BEXMLParser(uri, **args)
