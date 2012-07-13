# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

import __builtin__
line_profiler=None
if 0:
    try:
        from line_profiler import LineProfiler
        line_profiler=LineProfiler()
        def runctx(cmd, globals, locals, file):
            return line_profiler.runctx(cmd, globals, locals)
        __builtin__.__dict__['lineprofile']=line_profiler
    except: pass

if line_profiler is None:
    from cProfile import runctx
    __builtin__.__dict__['lineprofile']=lambda x:x

from libBEXML import BEXML
import logging, time, unittest, cProfile, pstats, os, sys
from collections import namedtuple
from abc import ABCMeta, abstractmethod, abstractproperty

log=logging.getLogger(__name__)

# Figure out how long an empty loop takes
start=time.time()
while time.time()-start<2: pass # Prime SpeedStep
start=time.time()
for n in xrange(0, 100000):
    time.time()
end=time.time()
emptyloop=end-start
del start, end, n
emptyloop/=100000.0

def readRepo(parser, forceLoad=False, printSummaries=False, filter=None):
    issues=comments=0
    issueparsetaken=0
    issueloadtaken=0
    commentparsetaken=0
    commentloadtaken=0
    start=time.time()
    for issue in parser.parseIssues(issuefilter=filter):
        issues+=1
        if printSummaries:
            print(repr("  "+str(issue.uuid)+": "+issue.summary))
            for commentuuid in issue.comments:
                print(repr("    c "+str(commentuuid)+": "+issue.comments[commentuuid].body[:48]))
    end=time.time()
    issueparsetaken+=end-start-emptyloop
    if forceLoad:
        start=time.time()
        for issue in parser.parseIssues(issuefilter=filter):
            issue.status
        end=time.time()
        issueloadtaken+=end-start-emptyloop
    start=time.time()
    for issue in parser.parseIssues(issuefilter=filter):
        for commentuuid in issue.comments:
            comments+=1
    end=time.time()
    commentparsetaken+=end-start-emptyloop
    if forceLoad:
        start=time.time()
        for issue in parser.parseIssues(issuefilter=filter):
           for commentuuid in issue.comments:
                issue.comments[commentuuid].alt_id
        end=time.time()
        commentloadtaken+=end-start-emptyloop
    return namedtuple('ReadRepoTimings', ['issues', 'comments', 'issueparse', 'issueload', 'commentparse', 'commentload'])(issues=issues, comments=comments, issueparse=issueparsetaken, issueload=issueloadtaken, commentparse=commentparsetaken, commentload=commentloadtaken)

class TestParseWithLib():
    __metaclass__=ABCMeta
    profileEverything = True

    @abstractproperty
    def repoURI(self):
        """Returns the repo URI to use"""
        pass

    @property
    def profile(self):
        """True if we should profile the test"""
        return self.profileEverything

    @abstractproperty
    def filter(self):
        """Returns the name to search for"""
        pass

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        log.info("Timing overhead is %f secs" % emptyloop)

    def tearDown(self):
        if self.profile:
            try:
                if line_profiler is not None:
                    with open("lineProfile.txt", "a") as oh:
                        line_profiler.print_stats(oh)
                        oh.write("\n\n")
                else:
                    with open("cProfile.txt", "a") as oh:
                        p=pstats.Stats('cProfile', stream=oh)
                        p.sort_stats('cumulative').print_stats(30)
                        oh.write("\n\n")
            except:
                sys.stderr.write("Exception writing profiling stats: %s\n" % sys.exc_info()[1])

    def test(self):
        start=time.time()
        parser=BEXML(self.repoURI)
        end=time.time()
        print("Opening the repository took %f secs" % (end-start-emptyloop))
        start=time.time()
        parser.reload()
        end=time.time()
        print("Loading the repository took %f secs" % (end-start-emptyloop))

        if self.profile:
            global timings2, parser2
            parser2=parser
            if line_profiler is not None:
                log.info("Using line level profiler")
                line_profiler.add_function(readRepo)
            else:
                log.info("Using function level profiler")
            try:
                runctx("timings2=readRepo(parser2)", globals(), globals(), "cProfile")
            except:
                self.tearDown()
                raise
            timings=timings2
        else:
            timings=readRepo(parser)
        print("Reading %d issues from the repository for the first time took %f secs to parse and %f secs to load" % (timings.issues, timings.issueparse, timings.issueload))
        print("Reading %d comments from the repository for the first time took %f secs to parse and %f secs to load" % (timings.comments, timings.commentparse, timings.commentload))
        issuessec=timings.issues
        if timings.issueparse+timings.issueload!=0: issuessec/=(timings.issueparse+timings.issueload)
        else: issuessec=0
        commentssec=timings.comments
        if timings.commentparse+timings.commentload!=0: commentssec/=(timings.commentparse+timings.commentload)
        else: commentssec=0
        print("That's %f issues/sec and %f comments/sec" % (issuessec, commentssec))

        timings2=readRepo(parser)
        self.assertEqual(timings.issues, timings2.issues)
        self.assertEqual(timings.comments, timings2.comments)
        print("Reading %d issues from the repository for the second time took %f secs to parse and %f secs to load" % (timings2.issues, timings2.issueparse, timings2.issueload))
        print("Reading %d comments from the repository for the second time took %f secs to parse and %f secs to load" % (timings2.comments, timings2.commentparse, timings2.commentload))
        issuessec=timings2.issues
        if timings2.issueparse+timings2.issueload!=0: issuessec/=(timings2.issueparse+timings2.issueload)
        else: issuessec=0
        commentssec=timings2.comments
        if timings2.commentparse+timings2.commentload!=0: commentssec/=(timings2.commentparse+timings2.commentload)
        else: commentssec=0
        print("That's %f issues/sec and %f comments/sec" % (issuessec, commentssec))

        print("\nIssues reported by anyone called %s:" % self.filter)
        timings=readRepo(parser, filter="{{reporter}}:{{%s}}" % self.filter, printSummaries=True)
        print("Reading %d issues from the repository took %f secs to parse and %f secs to load" % (timings.issues, timings.issueparse, timings.issueload))


if TestParseWithLib.profileEverything:
    if os.path.exists("cProfile"):
        os.remove("cProfile")
    if line_profiler is None:
        if os.path.exists("cProfile.txt"):
            os.remove("cProfile.txt")
    else:
        if os.path.exists("lineProfile.txt"):
            os.remove("lineProfile.txt")
