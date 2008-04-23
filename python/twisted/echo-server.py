#!/usr/bin/env python
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

class Echo(Protocol):
    def dataReceived(self, data):
        # Once data is received, echo it back
        self.transport.write(data)

# Create a factory to handle any connction errors
f = Factory()
# Create an Echo protocol instance once connection is successful
f.protocol = Echo
reactor.listenTCP(9999, f)
reactor.run()
