# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

from libBEXML import BEXML
import logging, time, unittest, cProfile, pstats
from collections import namedtuple
from abc import ABCMeta, abstractmethod, abstractproperty

log=logging.getLogger(__name__)

# Figure out how long an empty loop takes
start=time.time()
while time.time()-start<2: pass # Prime SpeedStep
start=time.time()
for n in xrange(0, 100):
    time.time()
end=time.time()
emptyloop=end-start
del start, end, n
emptyloop/=100
log.info("Timing overhead is %f secs" % emptyloop)


def readRepo(parser, forceLoad=True, printSummaries=False, filter=None):
    issues=comments=0
    issueparsetaken=0
    issueloadtaken=0
    commentparsetaken=0
    commentloadtaken=0
    start=time.time()
    for issue in parser.parseIssues(issuefilter=filter):
        end=time.time()
        issueparsetaken+=end-start-emptyloop
        issues+=1
        if forceLoad:
            start=time.time()
            issue.status
            end=time.time()
            issueloadtaken+=end-start-emptyloop
        if printSummaries: print(repr("  "+str(issue.uuid)+": "+issue.summary))
        start=time.time()
        for commentuuid in issue.comments:
            end=time.time()
            commentparsetaken+=end-start-emptyloop
            comments+=1
            if forceLoad:
                start=time.time()
                issue.comments[commentuuid].alt_id
                end=time.time()
                commentloadtaken+=end-start-emptyloop
            start=time.time()
        start=time.time()
    return namedtuple('ReadRepoTimings', ['issues', 'comments', 'issueparse', 'issueload', 'commentparse', 'commentload'])(issues=issues, comments=comments, issueparse=issueparsetaken, issueload=issueloadtaken, commentparse=commentparsetaken, commentload=commentloadtaken)

class TestParseWithLib():
    __metaclass__=ABCMeta

    @abstractproperty
    def repoURI(self):
        """Returns the repo URI to use"""
        pass

    @abstractproperty
    def profile(self):
        """True if we should profile the test"""
        pass

    @abstractproperty
    def filter(self):
        """Returns the name to search for"""
        pass

    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    def tearDown(self):
        if self.profile:
            with open("cProfile.txt", "w") as oh:
                p=pstats.Stats('cProfile', stream=oh)
                p.sort_stats('time').print_stats()

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
            cProfile.run("timings2=readRepo(parser2)", "cProfile")
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

        timings=readRepo(parser)
        print("Reading %d issues from the repository for the second time took %f secs to parse and %f secs to load" % (timings.issues, timings.issueparse, timings.issueload))
        print("Reading %d comments from the repository for the second time took %f secs to parse and %f secs to load" % (timings.comments, timings.commentparse, timings.commentload))
        issuessec=timings.issues
        if timings.issueparse+timings.issueload!=0: issuessec/=(timings.issueparse+timings.issueload)
        else: issuessec=0
        commentssec=timings.comments
        if timings.commentparse+timings.commentload!=0: commentssec/=(timings.commentparse+timings.commentload)
        else: commentssec=0
        print("That's %f issues/sec and %f comments/sec" % (issuessec, commentssec))

        print("\nIssues reported by anyone called %s:" % self.filter)
        timings=readRepo(parser, filter="{{reporter}}:{{%s}}" % self.filter)
        print("Reading %d issues from the repository took %f secs to parse and %f secs to load" % (timings.issues, timings.issueparse, timings.issueload))

