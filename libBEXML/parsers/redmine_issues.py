# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

from ..xmlparserbase import XMLComment, XMLIssue, XMLParser

import os, logging, uuid
from copy import copy, deepcopy

log=logging.getLogger(__name__)


class RedmineXMLComment(XMLComment):
    """A comment loaded from an XML based Redmine repo"""
    uuid_namespace=uuid.UUID('{63913f93-2c8d-4f95-9619-f54f52514ef4}') # Used to generated a unique UUID from unique comment id

    def __init__(self, parentIssue, commentelem):
        XMLComment.__init__(self, parentIssue, commentelem)


class RedmineXMLIssue(XMLIssue):
    """An issue loaded from an XML based Redmine repo"""
    uuid_namespace=uuid.UUID('{9b02c0ae-2b5a-44ca-856d-bef60cced435}') # Used to generated a unique UUID from unique issue id
    mapStatusToBE={'New':'unconfirmed', 'In Progress':'open', 'Resolved':'fixed', 'Feedback':'feedback', 'Closed':'closed', 'Rejected':'wontfix'}
    mapPriorityToBE={'Low':'minor', 'Normal':'major', 'High':'serious', 'Urgent':'critical', 'Immediate':'fatal'} # Missing wishlist, target

    def __mapIDToBE(self, xmlelem):
        """Maps a Redmine id to BE uuid"""
        self.redmine_id=int(xmlelem.text)
        assert self.redmine_id not in self.__parentparser.issueids
        self.__parentparser.issueids[self.redmine_id]=self
        return uuid.uuid5(self.uuid_namespace, str(self.redmine_id))

    def __mapStatusToBE(self, xmlelem):
        """Maps a Redmine status to BE status"""
        id=int(xmlelem.attrib['id'])
        if id in self.__parentparser.issuestatusids:
            return self.__parentparser.issuestatusids[id][1]
        name=xmlelem.attrib['name']
        BEname=self.mapStatusToBE[name] if name in self.mapStatusToBE else ""
        self.__parentparser.issuestatusids[id]=(name, BEname)
        return BEname

    def __mapPriorityToBE(self, xmlelem):
        """Maps a Redmine priority to BE severity"""
        id=int(xmlelem.attrib['id'])
        if id in self.__parentparser.issuepriorityids:
            return self.__parentparser.issuepriorityids[id][1]
        name=xmlelem.attrib['name']
        BEname=self.mapPriorityToBE[name] if name in self.mapPriorityToBE else ""
        self.__parentparser.issuepriorityids[id]=(name, BEname)
        return BEname

    def __mapAuthorToBE(self, xmlelem):
        """Maps a Redmine author to BE reporter"""
        id=int(xmlelem.attrib['id'])
        if id in self.__parentparser.issueauthorids:
            return self.__parentparser.issueauthorids[id][1]
        name=xmlelem.attrib['name']
        BEname='"%s" (id:%d)' % (name, id)
        self.__parentparser.issueauthorids[id]=(name, BEname)
        return BEname

    def __init__(self, parentparser, bugelem):
        self.__parentparser=parentparser
        XMLIssue.__init__(self, bugelem, mapToBE={'id'        :('uuid',     self.__mapIDToBE),
                                                  'status'    :('status',   self.__mapStatusToBE),
                                                  'priority'  :('severity', self.__mapPriorityToBE),
                                                  'author'    :('reporter', self.__mapAuthorToBE),
                                                  'subject'   :('summary',  lambda xmlelem:xmlelem.text),
                                                  'created_on':('time',     lambda xmlelem:xmlelem.text),
                                                  }, dontprocess=set(['description']))
        self.redmine_id=None


class RedmineXMLParser(XMLParser):
    """Parses an XML based Redmine repo"""

    @classmethod
    def _schemapath(cls):
        return os.path.join(os.path.dirname(__file__), "redmine_issues.xsd")

    def _XMLIssue(self, bugelem, **pars):
        ret=copy(self.RedmineXMLIssue)
        ret.element=bugelem
        #assert self.RedmineXMLIssueHash==hash(self.RedmineXMLIssue)
        #ret=RedmineXMLIssue(self, bugelem, **pars)
        return ret

    def __init__(self, uri, encoding="utf-8"):
        XMLParser.__init__(self, uri, encoding, mapToBE={'bug':'issue'})
        self.issueids={}
        self.issuestatusids={} # Keep a map of issue statuses to ids as these can vary between Redmines
        self.issuepriorityids={} # Ditto
        self.issueauthorids={} # Ditto
        self.RedmineXMLIssue=RedmineXMLIssue(self, None)
        #self.RedmineXMLIssueHash=hash(self.RedmineXMLIssue)

    def try_location(self, mimetype=None, first256bytes=None):
        score, errmsg=XMLParser.try_location(self, mimetype, first256bytes)
        if score>=0 and first256bytes is not None and '<issues' in first256bytes and 'type="array"' in first256bytes: score+=100
        return (score, errmsg)

def instantiate(uri, **args):
    return RedmineXMLParser(uri, **args)
