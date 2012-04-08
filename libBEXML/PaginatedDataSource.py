# PaginatedDataSource
# Provide a file-like object coalescing a paginated data source into a continuous stream
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

import urllib3, URI
from collections import Iterator

class PaginatedDataSource(Iterator):
    """Provide a file-like object coalescing a paginated data source into a continuous stream"""

    def __init__(self, uri, prefetch, http_op, num_pools):
        self.__uri=URI.URI(uri)
        if self.__uri.scheme!="http" and self.__uri.scheme!="https":
            raise Exception("Scheme '%s' is not currently supported" % uri.scheme)
        self.__closed=False
        self.__httppool=urllib3.PoolManager(num_pools)
        self.__http_op=http_op
        self.__prefetch=prefetch
        self.__data=[]
        self.__fillData(1)
        if self.__data[0].status!=200:
            raise Exception("HTTP error %d (%s)" % (self.__data[0].status, self.__data[0].reason))
        self.__page

    def __fillData(self, pages=99999):
        while len(self.__data)<self.__prefetch and pages>0:
            self.__data.append(self.__httppool.request(self.__http_op, self.__uri))
            pages-=1

    def close():
        pass

    def read(size=None):
        pass

    def readline(size=None):
        pass

    def readlines(sizehint=None):
        pass

    def tell():
        pass

    @property
    def closed(self):
        self.__closed

    @property
    def name(self):
        return str(self.__uri)

    def __iter__(self):
        return self

    def next(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

class AutoCount:
    """A callable returning a monotonic count. You can construct using the initial count"""

    def __init__(self, parametername, initialcount=1):
        self.parametername=parametername
        self.count=initialcount

    def __call__(self, dsobj, response):
        self.count+=1
        return (self.parametername, self.count)

def urlopen(uri, analysisfunct=AutoCount('page'), prefetch=5, http_op='GET', num_pools=10):
    """Opens the URI as a PaginatedDataSource. Returns a file-like object which returns the paginated source as a continuous stream, but prefetching
    in the background to try and hide latency.

    analysisfunct is a callable taking (dsobj, urllib3.response.HTTPResponse) and returning ('offsetparametername', nextoffsetvalue). For an offset
    source, you'll need to calculate the correct offset to request for the next page. For a paged source, use AutoCount(<pageparametername>) which
    returns a monotonically increasing count.

    Note that the iterator interface to PaginatedDataSource is rather different to what you might expect:
    for page in urlopen("https://api.github.com/repos/github/github-services/issues?per_page=100"):
        # page is a full page of data, not a single line

    readline() and readlines() do do what you'd expect though.

    You almost certainly don't want to do read() unless you're prepared to wait a while for all pages to be fetched. You can do read(1) which
    actually returns one page.
    """
    return PaginatedDataSource(uri, analysisfunct, prefetch, http_op, num_pools)
