#!/usr/bin/python
from twisted.internet import reactor, protocol

class EchoClient(protocol.Protocol):
    def connectionMade(self):
        print "Connected to %s." % self.transport.getPeer().host
        self.transport.write("hello world")

    def dataReceived(self, data):
        print "Server said:", data
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print "Connection lost:", reason

class EchoClientFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionLost(self, connector, reason):
        print "Lost connection: %s" % reason.getErrorMessage()
        reactor.stop()

    def clientConnectFailed(self, connector, reason):
        print "Connection failed: %s" % reason.getErrorMessage()
        reactor.stop()

reactor.connectTCP('192.168.1.77', 9999, EchoClientFactory())
reactor.run()
