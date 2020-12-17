import struct
from typing import Optional

from loguru import logger
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import Int32StringReceiver
from twisted.protocols.policies import TimeoutMixin

from sibi.ibapi.server_versions import MIN_CLIENT_VER, MAX_CLIENT_VER

PROTOCOL_TIMEOUT = 10
(DISCONNECTED, CONNECTING, CONNECTED, REDIRECT) = range(4)


class IBProtocol(Int32StringReceiver, TimeoutMixin):
    def __init__(self):
        self.setTimeout(PROTOCOL_TIMEOUT)

    def sendMsg(self, msg):
        self.setTimeout(PROTOCOL_TIMEOUT)
        self.transport.write(msg)

    def stringReceived(self, text):
        self.setTimeout(None)
        fields = self.split_fields(text)

        if self.factory.connState == CONNECTING:
            if len(fields) == 2:
                logger.debug(f"Consolidating connection for {text}")
                self.finalize_connection(fields)
            else:
                logger.error(f"Error while connecting")
            return
        else:
            self.factory.decoder.interpret(fields)

    def connectionLost(self, reason=connectionDone):
        """
        This just sets the IB EClient connection state when disconnected.
        """

        logger.warning("Closing connection")
        if self.factory.connState == CONNECTING:
            logger.warning("Reconnecting")

        self.factory.setConnState(DISCONNECTED)
        logger.warning(reason.getErrorMessage())

    def isConnected(self):
        """
        Determines if we are connected to TWS
        """
        return self.factory.connState == CONNECTED

    def connectionMade(self):
        """
        As soon as connection is made, we need to send a message containing API version to TWS.
        This is the first part of IB's connection procedure.
        """
        logger.info("Connecting to TWS")
        self.factory.setConnState(CONNECTING)
        self.factory.conn = self
        v100prefix = "API\0"
        v100version = "v%d..%d" % (MIN_CLIENT_VER, MAX_CLIENT_VER)
        msg = self.make_msg(v100version)

        msg2 = str.encode(v100prefix, "ascii") + msg

        self.sendMsg(msg2)

    def finalize_connection(self, fields):
        """
        Finalizes connection with TWS
        """
        (server_version, conn_time) = fields
        server_version = int(server_version)
        logger.info(
            f"{self.factory.name}: ANSWER Version:{server_version} time:{conn_time}"
        )
        self.factory.connTime = conn_time
        self.factory.serverVersion_ = server_version
        self.factory.decoder.serverVersion = self.factory.serverVersion()

        logger.debug(f"{self.factory.name}: sent startApi")
        self.factory.setConnState(CONNECTED)
        self.factory.startApi()

    @staticmethod
    def split_fields(buffer: bytes, separator: Optional[bytes] = b"\0") -> tuple:
        """
        Payload is made of fields terminated/separated by NULL chars.
        We split the bytes using the null b"\0" separator and return a tuple containing fields.
        """

        fields = buffer.split(separator)

        return tuple(fields[:-1])  # Last is always empty

    @staticmethod
    def make_field(value: str) -> str:
        """
        IB detects different fields by splitting a string using a null separator (\0)
        This just adds the NULL string terminator to a common string
        """

        if value is None:
            raise ValueError("Cannot send None to TWS")

        # bool type is encoded as int
        if type(value) is bool:
            value = int(value)

        # we add the null terminator and return
        field = str(value) + "\0"
        return field

    @staticmethod
    def make_msg(text) -> bytes:
        """ adds the length prefix """
        msg = struct.pack("!I%ds" % len(text), len(text), str.encode(text))
        return msg
