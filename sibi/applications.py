from twisted.internet import reactor, endpoints
from twisted.protocols.policies import ThrottlingFactory
from twisted.web import server

from sibi.ib_factory import IBClientFactory
from sibi.xmlrpc_server import XMLRPCServer
import sys


class Sibi:
    def __init__(
        self,
        client_id: int,
        tws_host: str,
        tws_port: int,
        tws_max_connections: int,
        xmlrpc_port: int,
    ):
        ib_factory = IBClientFactory(client_id)
        reactor.connectTCP(tws_host, tws_port, ib_factory)

        # create XMLRPC SERVER ENDPOINT
        xmlrpc_resource = XMLRPCServer(ib_factory)
        xmlrpc_factory = ThrottlingFactory(
            server.Site(xmlrpc_resource), tws_max_connections
        )

        endpoint = endpoints.TCP4ServerEndpoint(reactor, xmlrpc_port)
        endpoint.listen(xmlrpc_factory)

    @staticmethod
    def run():
        reactor.run()

    @staticmethod
    def stop():
        reactor.stop()
