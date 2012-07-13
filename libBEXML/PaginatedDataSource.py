# PaginatedDataSource
# Provide a file-like object coalescing a paginated data source into a continuous stream
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

import urllib3, URI, logging, traceback
from collections import Iterator
from multiprocessing.pool import ThreadPool, ApplyResult
from lxml import etree

log=logging.getLogger(__name__)

class AutoPageCount:
    """A callable returning a monotonic count. You can construct using the initial count"""

    def __init__(self, parametername='page', initialcount=1):
        self.__parametername=parametername
        self.__count=initialcount

    def __call__(self, response):
        self.__count+=1
        return {self.__parametername: self.__count}

class PaginatedDataSource(Iterator):
    """Provide a file-like object coalescing a paginated data source into a continuous stream"""

    def __init__(self, uri, analysis, schema, timeout, prefetch, http_op, num_pools):
        self.__uri=URI.URI(uri)
        if self.__uri.scheme!="http" and self.__uri.scheme!="https":
            raise Exception("Scheme '%s' is not currently supported" % uri.scheme)
        self.__host=str(self.__uri)
        self.__request=self.__uri.path
        self.__host=self.__host[:self.__host.find(self.__request)]
        self.__fields=dict(self.__uri.query)
        self.__analysisfunct=analysis
        self.__parser=etree.XMLParser(schema=schema)
        self.__timeout=timeout
        self.__prefetch=prefetch
        self.__http_op=http_op

        self.__httppool=urllib3.connection_from_url(self.__host, maxsize=num_pools)
        # AutoPageCount doesn't rely on earlier pages, so we can skip a thread pool
        if isinstance(self.__analysisfunct, AutoPageCount):
            self.__threadpool=None
        else:
            self.__threadpool=ThreadPool(1)
        self.__page=0
        self.__data=[]
        for slot in xrange(0, self.__prefetch):
            self.__dataptr=slot
            self.__data.append(None)
            self.__fillData()
        # Wait for the first page in case it was a bad URL        
        if self.__getData(0).status!=200:
            raise Exception("HTTP error %d (%s)" % (self.__data[0].status, self.__data[0].reason))

    def __nextData(self, slot): # WARNING: MAY BE CALLED IN DIFFERENT THREAD
        try:
            fields=self.__fields.copy()
            prevdata=self.__data[slot-1] if slot>0 else None
            # Should never happen, but be defensive anyway ...
            if isinstance(prevdata, ApplyResult):
                prevdata.wait() # deliberately not get() to not throw exceptions
                assert prevdata.ready()
                prevdata=self.__data[slot-1]
            offset=self.__analysisfunct(prevdata)
            if offset is not None:
                fields.update(offset)
                self.__data[slot]=self.__httppool.request(self.__http_op, self.__request, fields)
            else:
                self.__data[slot]=None
        except Exception as e:
            log.error("Error in thread: %s" % traceback.format_exc())
            self.__data[slot]=e

    def __fillData(self):
        if self.__threadpool is not None:
            self.__data[self.__dataptr]=self.__threadpool.apply_async(self.__nextData, [int(self.__dataptr)])
        else:
            self.__data[self.__dataptr]=self.__nextData(self.__dataptr)
        self.__dataptr+=1
        if self.__dataptr>=self.__prefetch: self.__dataptr=0

    def __getData(self, idxoffset=0):
        idx=self.__dataptr+idxoffset
        ret=self.__data[idx]
        while isinstance(ret, ApplyResult):
            ret.get(self.__timeout)
            ret=self.__data[idx]
        if isinstance(ret, Exception):
            raise ret
        return ret

    def close(*args):
        # lxml seems to call us as close(self, ...) rather than self.close(...)
        self=args[0]
        self.__page=-1
        self.__threadpool.close()
        self.__threadpool.join()
        self.__data=[]
        self.__threadpool=None

    def read(*args):
        # lxml seems to call us as read(self, ...) rather than self.read(...)
        try:
            return args[0].next()
        except StopIteration:
            return ""

    def readline(size=None):
        raise NotImplementedError()

    def readlines(sizehint=None):
        raise NotImplementedError()

    def tell():
        raise NotImplementedError()

    @property
    def closed(self):
        return self.__page==-1

    @property
    def name(self):
        return str(self.__uri)

    def __iter__(self):
        return self

    def next(self):
        if self.__page<0: raise StopIteration
        response=self.__getData()
        if response is None:
            raise StopIteration
        if response.status!=200:
            raise Exception("HTTP error %d (%s)" % (response.status, response.reason))
        self.__fillData()
        xml=etree.fromstring(response.data, self.__parser)
        ret=etree.tostring(xml)
        if self.__page>0:
            # Not the first page, so strip header
            firstchild=xml[0]
            firstchildstr=etree.tostring(firstchild)
            ret=ret[ret.find(firstchildstr[:64]):]
        # Am I on the last page?
        if self.__analysisfunct(response) is not None:
            # Not last page, so strip tail
            ret=ret[:ret.rfind('</')]
        self.__page+=1
        return ret

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

def urlopen(uri, analysisfunct=AutoPageCount('page'), schema=None, timeout=10000, prefetch=3, http_op='GET', num_pools=3):
    """Opens the URI as a PaginatedDataSource. Returns a file-like object which returns the paginated source as a continuous stream, but prefetching
    in the background to try and hide latency.

    analysisfunct is a callable taking (None|urllib3.response.HTTPResponse) and returning None|{'offsetparametername': 0|nextoffsetvalue}. For an offset
    source, you'll need to calculate the correct offset to request for the next page. For a paged source, use AutoPageCount(<pageparametername>) which
    returns a monotonically increasing count.

    Note that the iterator interface to PaginatedDataSource is rather different to what you might expect:
    for page in urlopen("https://api.github.com/repos/github/github-services/issues?per_page=100"):
        # page is a full page of data, not a single line

    readline() and readlines() do do what you'd expect though.

    You almost certainly don't want to do read() unless you're prepared to wait a while for all pages to be fetched. You can do read(1) which
    actually returns one page.
    """
    return PaginatedDataSource(uri, analysisfunct, schema, timeout, prefetch, http_op, num_pools)
