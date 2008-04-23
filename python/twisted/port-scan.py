#!/usr/bin/env python

import sys
from twisted.internet import reactor, defer, protocol

class CallbackAndDisconnectProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.deferred.callback("Connected")
        self.transport.loseConnection()

class ConnectionTestFactory(protocol.ClientFactory):
    protocol = CallbackAndDisconnectProtocol

    def __init__(self):
        self.deferred = defer.Deferred()

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)

def testConnect(host, port):
    testFactory = ConnectionTestFactory()
    reactor.connectTCP(host, port, testFactory)
    return testFactory.deferred

def handleAllResults(results, ports):
    for port, resultInfo in zip(ports, results):
        success, result = resultInfo
        if success:
            print "Connected to port %i" % port
    reactor.stop()

host = sys.argv[1]
ports = range(1,64000)
print ports
testers = [testConnect(host, port) for port in ports]
defer.DeferredList(testers, consumeErrors=True).addCallback(
                   handleAllResults, ports)
reactor.run()
