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

    def __mapBodyToBE(self, xmlelem):
        """Maps a Redmine comment body"""
        self.content_type="text/plain"
        return xmlelem.text

    def __mapAuthorToBE(self, xmlelem):
        """Maps a Redmine author to BE reporter"""
        id=int(xmlelem.attrib['id'])
        if id in self.parentParser.issueauthorids:
            return self.parentParser.issueauthorids[id][1]
        name=xmlelem.attrib['name']
        BEname='"%s" (id:%d)' % (name, id)
        self.parentParser.issueauthorids[id]=(name, BEname)
        return BEname


    def __init__(self, parentIssue, commentelem):
        XMLComment.__init__(self, parentIssue, commentelem, mapToBE={'notes':       ('body',   self.__mapBodyToBE),              # From journal
                                                                     'description': ('body',   self.__mapBodyToBE),              # From issue
                                                                     'user':        ('Author', self.__mapAuthorToBE),            # From journal
                                                                     'author':      ('Author', self.__mapAuthorToBE),            # From issue
                                                                     'created_on':  ('Date',   lambda xmlelem:xmlelem.text),     # From journal and issue
                                                                     }, dontprocess=set())
        if commentelem.tag=="journal":
            self.__commentType=1
            self.redmine_id=int(commentelem.attrib['id'])
            self.parentParser.journalids[self.redmine_id]=self
            self.uuid=uuid.uuid5(self.uuid_namespace, str(self.redmine_id))
        elif commentelem.tag=="issue":
            self.__commentType=0
            self.redmine_id=int(commentelem.find("id").text)
            self.uuid=uuid.uuid5(parentIssue.uuid_namespace, str(self.redmine_id))
        else:
            raise Exception("Unknown comment type '"+commentelem.tag+"'")
        #print("Added comment "+str(self.uuid)+" type "+str(self.__commentType))


class RedmineXMLIssue(XMLIssue):
    """An issue loaded from an XML based Redmine repo"""
    uuid_namespace=uuid.UUID('{9b02c0ae-2b5a-44ca-856d-bef60cced435}') # Used to generated a unique UUID from unique issue id
    mapStatusToBE={'New':'unconfirmed', 'In Progress':'open', 'Resolved':'fixed', 'Feedback':'feedback', 'Closed':'closed', 'Rejected':'wontfix'}
    mapPriorityToBE={'Low':'minor', 'Normal':'major', 'High':'serious', 'Urgent':'critical', 'Immediate':'fatal'} # Missing wishlist, target

    def __mapIDToBE(self, xmlelem):
        """Maps a Redmine id to BE uuid"""
        self.redmine_id=int(xmlelem.text)
        assert self.redmine_id not in self.parentParser.issueids
        self.parentParser.issueids[self.redmine_id]=self
        return uuid.uuid5(self.uuid_namespace, str(self.redmine_id))

    def __mapStatusToBE(self, xmlelem):
        """Maps a Redmine status to BE status"""
        id=int(xmlelem.attrib['id'])
        if id in self.parentParser.issuestatusids:
            return self.parentParser.issuestatusids[id][1]
        name=xmlelem.attrib['name']
        BEname=self.mapStatusToBE[name] if name in self.mapStatusToBE else ""
        self.parentParser.issuestatusids[id]=(name, BEname)
        return BEname

    def __mapPriorityToBE(self, xmlelem):
        """Maps a Redmine priority to BE severity"""
        id=int(xmlelem.attrib['id'])
        if id in self.parentParser.issuepriorityids:
            return self.parentParser.issuepriorityids[id][1]
        name=xmlelem.attrib['name']
        BEname=self.mapPriorityToBE[name] if name in self.mapPriorityToBE else ""
        self.parentParser.issuepriorityids[id]=(name, BEname)
        return BEname

    def __mapAuthorToBE(self, xmlelem):
        """Maps a Redmine author to BE reporter"""
        id=int(xmlelem.attrib['id'])
        if id in self.parentParser.issueauthorids:
            return self.parentParser.issueauthorids[id][1]
        name=xmlelem.attrib['name']
        BEname='"%s" (id:%d)' % (name, id)
        self.parentParser.issueauthorids[id]=(name, BEname)
        return BEname

    def __init__(self, parser, bugelem):
        XMLIssue.__init__(self, parser, bugelem, mapToBE={'id'        :('uuid',     self.__mapIDToBE),
                                                          'status'    :('status',   self.__mapStatusToBE),
                                                          'priority'  :('severity', self.__mapPriorityToBE),
                                                          'author'    :('reporter', self.__mapAuthorToBE),
                                                          'subject'   :('summary',  lambda xmlelem:xmlelem.text),
                                                          'created_on':('time',     lambda xmlelem:xmlelem.text),
                                                          }, dontprocess=set(['description']))
        self.redmine_id=None

    @XMLIssue.element.setter
    def element(self, value):
        XMLIssue.element.fset(self, value)
        # In Redmine, each issue comes with a long description field. Map that to first comment in BE
        descriptionelem=self.element.find("description")
        if descriptionelem is not None and descriptionelem.text is not None:
            self.addComment(RedmineXMLComment(self, self.element))


class RedmineXMLParser(XMLParser):
    """Parses an XML based Redmine repo"""

    @classmethod
    def _schemapath(cls):
        return os.path.join(os.path.dirname(__file__), "redmine_issues.xsd")

    def _XMLIssue(self, bugelem, **pars):
        ret=copy(self.RedmineXMLIssue)
        ret.element=bugelem
        return ret

    def __init__(self, uri, encoding="utf-8"):
        XMLParser.__init__(self, uri, encoding, mapToBE={'bug':'issue'})
        self.issueids={}
        self.journalids={}
        self.issuestatusids={} # Keep a map of issue statuses to ids as these can vary between Redmines
        self.issuepriorityids={} # Ditto
        self.issueauthorids={} # Ditto
        self.RedmineXMLIssue=RedmineXMLIssue(self, None)

    def try_location(self, mimetype=None, first256bytes=None):
        score, errmsg=XMLParser.try_location(self, mimetype, first256bytes)
        if score>=0 and first256bytes is not None and '<issues' in first256bytes and 'type="array"' in first256bytes: score+=100
        return (score, errmsg)

def instantiate(uri, **args):
    return RedmineXMLParser(uri, **args)
