# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

import urlparse, logging, os, urllib2, URI
try:
    import magic
    have_magic=True
except: have_magic=False
import parsers

log=logging.getLogger(__name__)

def BEXML(uri, storageparser=None, **args):
    """Initialises an issue tracking repository for use"""
    if storageparser is None:
        uri=URI.URI(uri)
        first256bytes=None
        mimetype=None
        if uri.scheme=="file":
            path=uri.pathname
            if os.path.isfile(path):
                with open(path, 'r') as ih:
                    first256bytes=ih.read(256)
        elif uri.scheme=="http" or uri.scheme=="https":
            try:
                response=urllib2.urlopen(urllib2.Request(str(uri), headers={"Accept" : "*", "Accept-Charset" : "utf-8", "Range" : "bytes=0-256"}))
                first256bytes=response.read(256)
                mimetype=response.headers['Content-Type']
            except Exception(e):
                log.warn("Failed to open '"+uri+"' because of "+e.message)
        if mimetype is None and first256bytes is not None:
            if have_magic:
                mimetype=magic.Magic(mime=True).from_buffer(first256bytes)
            elif first256bytes.startswith('<?xml'):
                mimetype="application/xml"
        log.info("From uri '"+str(uri)+"' determined mimetype "+str(mimetype)+" from data '"+str(first256bytes)+"'")

        parser_instances=[parsers.__dict__[parser_module].instantiate(uri, **args) for parser_module in parsers.__all__]
        parser_scores=[(instance.try_location(mimetype, first256bytes), instance) for instance in parser_instances]
        parser_scores.sort(reverse=True)
        if log.isEnabledFor(logging.INFO):
            log.info("Parser scoring of input returned:")
            for score in parser_scores:
                log.info("   %s" % repr(score))
        score=parser_scores[0][0]
        storageparser=parser_scores[0][1]
    else:
        storageparser=storageparser(uri, **args)
        score=storageparser.try_location()
    if score[0]<0:
        raise Exception("No storage parser matched the uri '"+str(uri)+"'. The best matching ("+str(storageparser)+" reported: "+score[1])
    return storageparser
