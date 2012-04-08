# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

from abc import ABCMeta, abstractmethod, abstractproperty
import logging, URI

log=logging.getLogger(__name__)

class ParserBase():
    """Abstract base class for parsers"""
    __metaclass__=ABCMeta

    def __init__(self, uri):
        self.uri=URI.URI(uri)

    def _pathFromURI(self):
        """Returns a local filing system path from a URI"""
        # Windows can pass a drive letter through, unfortunately this causes urlparse to misparse
        if self.uri.scheme!="file":
            return None
        return (up.netloc+up.path) if up.netloc[-1]==':' else up.netloc

    @abstractmethod
    def try_location(self, mimetype=None, first256bytes=None):
        """Returns (integer score, msg) for how much this parser likes the given uri"""
        pass

    @abstractmethod
    def reload(self):
        """Reloads any cached data."""
        pass

    @abstractmethod
    def parseIssues(self, issuefilter=None):
        """Coroutine parsing the issues at the uri filtering out anything not matching issuefilter"""
        pass

    @abstractmethod
    def parseComments(self, issue_uuid, commentfilter=None):
        """Coroutine parsing the comments for issue_uuid filtering out anything not matching commentfilter"""
        pass
