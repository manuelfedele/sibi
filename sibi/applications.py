from twisted.internet import reactor, endpoints
from twisted.protocols.policies import ThrottlingFactory
from twisted.web import server

from sibi.ib_factory import IBClientFactory
from sibi.xmlrpc_server import XMLRPCServer
from sibi.settings import logger


class Solid:

    def __init__(self,
                 client_id: int = 0,
                 tws_host: str = '192.168.74.130',
                 tws_port: int = 7498,
                 tws_max_connections: int = 49,
                 xmlrpc_port: int = 7080):
        logger.info("Creating APP")
        ib_factory = IBClientFactory(client_id)
        reactor.connectTCP(tws_host, tws_port, ib_factory)

        # create XMLRPC SERVER ENDPOINT
        xmlrpc_resource = XMLRPCServer(ib_factory)
        xmlrpc_factory = ThrottlingFactory(server.Site(xmlrpc_resource), tws_max_connections)

        endpoint = endpoints.TCP4ServerEndpoint(reactor, xmlrpc_port)
        endpoint.listen(xmlrpc_factory)

    def run(self):
        reactor.run()
