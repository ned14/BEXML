# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

from parserbase import ParserBase
from issue import Issue as IssueBase
from comment import Comment as CommentBase

import os, logging, urlparse, urllib2
from abc import ABCMeta, abstractmethod, abstractproperty
try:
    from abc import abstractclassmethod
except:
    from abstract3kmethodsfor2k import abstractclassmethod
from lxml import etree
from encodings import utf_8 as ironpython_utf8_override
from collections import namedtuple
from uuid import UUID

log=logging.getLogger(__name__)


class XMLComment(CommentBase):
    """A comment loaded from an XML based repo"""

    def __init__(self, parentIssue, commentelem, mapToBE={}, dontprocess=set(), mapFromBE=None):
        """Initialises a new comment taken from an XML backing. mapToBE should be a dictionary
        mapping the source XML element tags to BE element names and outputs if necessary i.e
        mapToBE={'xmltag':('befield', lambda xmlelem:xmlelem.text)}
        Current BE comment fields:

        uuid: UUID
        [alt-id]: string
        [short-name]: string
        [in-reply-to]: UUID
        Author: string
        Date: datetime string
        Content-type: mimetype string
        Body: string
        """
        if mapFromBE is None: mapFromBe={v[0]:(k, v[1]) for k, v in mapToBE.iteritems()}
        CommentBase.__init__(self, parentIssue)
        self.__element=commentelem
        self.__elementhash=0
        self.__mapToBE=mapToBE
        self.__dontprocess=dontprocess
        self.__mapFromBE=mapFromBE

    @property
    def isStale(self):
        """True if the XML backing for this comment is newer than us"""
        if not self.isLoaded or not self.tracksStaleness:
            return None
        return self.__elementhash!=hash(self.__element)

    @property
    def element(self):
        """Returns the lxml element representing this XML backed comment"""
        return self.__element
    @element.setter
    def element(self, value):
        self.__element=value

    def load(self, reload=False):
        """Loads in the comment from XML"""
        if not reload and self.isLoaded:
            return
        values={}
        for valueelem in self.__element:
            if valueelem.tag not in self.__dontprocess:
                if valueelem.tag not in self.__mapToBE :
                    k=valueelem.tag
                    v=valueelem.text
                else:
                    m=self.__mapToBE[valueelem.tag]
                    k=m[0]
                    v=m[1](valueelem)
                values[k]=v
        notloaded=self._load_mostly(values)
        self.isLoaded=True
        if len(notloaded)>0:
            #log.warn("The following values from comment "+str(self.uuid)+" were not recognised: "+repr(notloaded))
            self.extraFields=notloaded
        self.isDirty=False
        if self.tracksStaleness:
            self.__elementhash=hash(self.__element)

class XMLIssue(IssueBase):
    """An issue loaded from an XML based repo"""

    def __init__(self, bugelem, mapToBE={}, dontprocess=set(), mapFromBE=None):
        """Initialises a new issue taken from an XML backing. mapToBE should be a dictionary
        mapping the source XML element tags to BE element names and outputs if necessary i.e
        mapToBE={'xmltag':('befield', lambda xmlelem:xmlelem.text)}
        Current BE issue fields:

        uuid: UUID
        [short-name]: string
        severity: string from ["minor", "wishlist", "serious", "major", "critical", "fatal", "target"]
        status: string from ["unconfirmed", "open", "test", "closed", "fixed", "feedback", "wontfix"]
        [assigned]: string
        [reporter]: string
        [creator]: string
        time: datetime string (e.g. Tue, 21 Jul 2009 18:32:12 +0000)
        summary: string
        [extra-strings]: list of strings
        """
        if mapFromBE is None: mapFromBe={v[0]:(k, v[1]) for k, v in mapToBE.iteritems()}
        IssueBase.__init__(self)
        self.__element=bugelem
        self.__elementhash=0
        self.__mapToBE=mapToBE
        self.__dontprocess=dontprocess
        self.__mapFromBE=mapFromBE

    @property
    def isStale(self):
        """True if the XML backing for this issue is newer than us"""
        if not self.isLoaded or not self.tracksStaleness:
            return None
        return self.__elementhash!=hash(self.__element)

    @property
    def element(self):
        """Returns the lxml element representing this XML backed issue"""
        return self.__element
    @element.setter
    def element(self, value):
        self.__element=value

    def load(self, reload=False):
        """Loads in the issue from XML"""
        if not reload and self.isLoaded:
            return
        values={}
        for valueelem in self.__element:
            if valueelem.tag not in self.__dontprocess:
                if valueelem.tag not in self.__mapToBE :
                    k=valueelem.tag
                    v=valueelem.text
                else:
                    m=self.__mapToBE[valueelem.tag]
                    k=m[0]
                    v=m[1](valueelem)
                values[k]=v
        notloaded=self._load_mostly(values)
        self.isLoaded=True
        if len(notloaded)>0:
            #log.warn("The following values from issue "+str(self.uuid)+" were not recognised: "+repr(notloaded))
            self.extraFields=notloaded
        self.isDirty=False
        if self.tracksStaleness:
            self.__elementhash=hash(self.__element)


class XMLParser(ParserBase):
    """Parses an XML based repo"""
    xml_schema=None

    @abstractclassmethod
    def _schemapath(cls):
        """Returns the schema file used to validate and key this XML repo. Return something like:

        return os.path.join(os.path.dirname(__file__), "bexml.xsd")
        """
        pass

    @abstractmethod
    def _XMLIssue(self, bugelem, **pars):
        """Returns the XML issue implementation used by this implementation. Note that constructing
        an XMLIssue is typically fairly heavy, so for speed consider instantiating a static copy and
        returning a clone like this:
        
        def _XMLIssue(self, bugelem, **pars):
            ret=copy(self.MyEmptyXMLIssue)
            ret.element=bugelem
            return ret
        """
        pass

    def __init__(self, uri, encoding="utf-8", mapToBE={}, mapFromBE=None):
        """Initialises a new XML repo parser. mapToBE should be a dictionary mapping the source
        XML element tags to BE element names if necessary. Current BE bug
        fields:

        bug: XMLIssue
        """
        if mapFromBE is None: mapFromBe={v:k for k, v in mapToBE.iteritems()}
        ParserBase.__init__(self, uri)
        self.__mapToBE=mapToBE
        self.__mapFromBE=mapFromBE
        self.source=None
        self.bugs={}
        # Save creating an XMLSchema per instance by poking this into the derived class as a static variable
        if self.xml_schema is None:
            self.__class__.xml_schema=etree.XMLSchema(file=self._schemapath())

    @abstractmethod
    def try_location(self, mimetype=None, first256bytes=None):
        up=urlparse.urlparse(self.uri)
        data=None
        score=0
        if up.scheme=="file":
            path=self._pathFromURI()
            if path[-4:]!='.xml':
                return (-999, "'"+path+"' is not an XML file")
            if not os.path.isfile(path):
                return (-998, "'"+path+"' is not a file")
            score+=1

        # Is this a mimetype I can live with?
        if mimetype=="text/xml" or mimetype=="application/xml": score+=5
        return (score, None)

    def reload(self):
        """Start parsing a XML source"""
        if self.source is None:
            assert self.try_location()[0]>0
        if self.source is not None:
            self.source.close()
            self.source=None
        self.bugs={}
        if self.uri[:4]=="file":
            self.source=open(self._pathFromURI(), 'r')
        else:
            self.source=urllib2.urlopen(self.uri)

    def parseIssues(self, issuefilter=None):
        if self.source is None:
            self.reload()
        if len(self.bugs)==0:
            tag='bug' if 'bug' not in self.__mapToBE else self.__mapToBE['bug']
            for _, bugelem in etree.iterparse(self.source, tag=tag, schema=self.xml_schema):
                issue=self._XMLIssue(bugelem)
                self.bugs[issue.uuid]=issue
                if issuefilter is None or issue._match(issuefilter):
                    yield issue
        else:
            for issueuuid in self.bugs:
                issue=self.bugs[issueuuid]
                if issuefilter is None or issue._match(issuefilter):
                    yield issue

    def parseComments(self, issue_uuid, commentfilter=None):
        if not isinstance(issue_uuid, str):
            issue_uuid=str(issue_uuid)
        if issue_uuid not in self.bugs:
            raise AssertionError("Issue uuid '"+str(issue_uuid)+"' not found")
        issue=self.bugs[issue_uuid]
        for commentuuid in issue.comments:
            yield issue.comments[commentuuid]
