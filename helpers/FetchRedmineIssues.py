#!/bin/sh
# FetchRedmineIssues - Retrieves a complete XML dump of all the issues at some Redmine installation
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

import sys, urllib, copy, StringIO
from lxml import etree

if len(sys.argv)<2:
    sys.stderr.write("Usage: FetchRedmineIssues.py <url> [<output file>]\n")
    sys.exit(1)
url=sys.argv[1]
outpath=sys.argv[2] if len(sys.argv)>2 else None

def fetchIssues(url, **pars):
    """Fetch a page of issues from Redmine"""
    if url[-1:]!='/': url+='/'
    req=url+"issues.xml?status_id=*"+('&'+urllib.urlencode(pars) if len(pars)>0 else "")
    sys.stderr.write("Fetching '%s' ...\n" % req)
    return etree.parse(req)

issuesxml=fetchIssues(url)
try:
    issueselem=issuesxml.getroot()
    if 'total_count' in issueselem.attrib:
        total_count=int(issueselem.attrib['total_count'])
        sys.stderr.write("'%s' contains %d issues\n" % (url, total_count))
        offset=int(issueselem.attrib['limit'])
        while offset<total_count:
            pagexml=fetchIssues(url, limit=1000, offset=offset)
            sys.stderr.write("Page contains %s issues\n" % pagexml.getroot().attrib['limit'])
            for element in pagexml.getroot():
                issueselem.append(element)
            offset+=int(pagexml.getroot().attrib['limit'])
            issueselem.attrib['limit']=str(offset)
            #break
finally:
    if outpath is None:
        output=StringIO.StringIO()
        issuesxml.write(output, encoding='UTF-8', xml_declaration=True)
        print(output.getvalue())
    else:
        with open(outpath, 'w') as oh:
            issuesxml.write(oh, encoding='UTF-8', xml_declaration=True)
