from loguru import logger
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.tcp import Connector
from twisted.python.failure import Failure

from sibi.decorators import append, publish, request, resolve
from sibi.exceptions import IBException
from sibi.ib_protocol import IBProtocol
from sibi.ibapi import decoder
from sibi.ibapi.client import EClient
from sibi.ibapi.common import TickerId, BarData, TagValueList, TickAttrib, OrderId
from sibi.ibapi.contract import Contract, ContractDetails
from sibi.ibapi.order import Order
from sibi.ibapi.order_state import OrderState
from sibi.ibapi.ticktype import TickType, TickTypeEnum
from sibi.ibapi.wrapper import EWrapper
from sibi.models import OrderStatus


class IBClientFactory(ReconnectingClientFactory, EClient, EWrapper):
    protocol = IBProtocol

    def __init__(self, clientId: int) -> None:
        """This is the Factory that instantiates the IBProtocols instance.

        Args:
            clientId (int): The clientId for TWS
        """
        EClient.__init__(self, wrapper=self)
        self.name = "IBClientFactory"
        self.decoder = decoder.Decoder(self, self.serverVersion())
        self.clientId = clientId
        self.currentReqId = 1
        self.nextValidOrderId = -1
        self.deferredRequests = {}
        self.deferredResults = {}
        self.additionalRequestInfo = {}

        self.deferredOrdersRequests = {}
        self.deferredOrdersResults = {}
        self.additionalOrderInfo = {}
        self.activeMktDataSubscriptions = []

    def clientConnectionLost(self, connector: Connector, reason: Failure) -> None:
        """ Internal reconnection method in case of connection lose """

        logger.warning(f"Lost connection.  Reason: {reason.getErrorMessage()}")
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector: Connector, reason: Failure) -> None:
        """ Internal reconnection method in case of connection fail """

        logger.warning(f"Connection failed.  Reason: {reason.getErrorMessage()}")
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def getNextReqId(self) -> int:
        """  Increments the reqId for TWS. This is automatically called by **@request** decorator """

        reqId = self.currentReqId
        self.currentReqId = self.currentReqId + 1
        return reqId

    def getNextOrderId(self):
        orderId = self.nextValidOrderId
        self.nextValidOrderId = self.nextValidOrderId + 1
        return orderId

    def nextValidId(self, orderId: int) -> int:
        """nextValidId event provides the next valid identifier needed to place an order.
        This is automatically called by TWS
        """

        logger.info(f"Next valid id initialized to {orderId}")
        super(IBClientFactory, self).nextValidId(orderId)
        self.nextValidOrderId = orderId
        return orderId

    @request(order=True)
    @resolve(order=True)
    def placeOrder(self, orderId: OrderId, contract: Contract, order: Order):
        """Places an order. Immediately after the order is submitted correctly, the TWS will start sending events
        concerning the order's activity via **openOrder** and **orderStatus** methods
        """

        super(IBClientFactory, self).placeOrder(orderId, contract, order)
        self.deferredOrdersResults[orderId] = {"orderId": orderId}
        return self.deferredOrdersRequests[orderId]

    @publish(order=True)
    def openOrder(
        self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState
    ):
        super(IBClientFactory, self).openOrder(orderId, contract, order, orderState)
        return order.__dict__

    @publish(order=True)
    def orderStatus(
        self,
        orderId: OrderId,
        status: str,
        filled: float,
        remaining: float,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
        mktCapPrice: float,
    ):

        super(IBClientFactory, self).orderStatus(
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )
        orderStatus = OrderStatus(
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )
        return orderStatus.__dict__

    @request
    def reqContractDetails(self, reqId: int, contract: Contract, **kwargs) -> Deferred:
        logger.debug(contract.__dict__)

        super(IBClientFactory, self).reqContractDetails(reqId, contract)
        return self.deferredRequests[reqId]

    @request
    def reqHistoricalData(
        self,
        reqId: int,
        contract: Contract,
        endDateTime: str,
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: int,
        formatDate: int,
        keepUpToDate: bool,
        chartOptions: TagValueList,
        **kwargs,
    ) -> Deferred:
        """ Requests historical data for contract. """

        super(IBClientFactory, self).reqHistoricalData(
            reqId,
            contract,
            endDateTime,
            durationStr,
            barSizeSetting,
            whatToShow,
            useRTH,
            formatDate,
            keepUpToDate,
            chartOptions,
        )

        return self.deferredRequests[reqId]

    @request
    @resolve
    def reqMktData(
        self,
        reqId: int,
        contract: Contract,
        genericTickList: str = "",
        snapshot: bool = False,
        regulatorySnapshot: bool = False,
        mktDataOptions=None,
        **kwargs,
    ) -> None:
        """ Starts live market data polling for specified contract """

        if mktDataOptions is None:
            mktDataOptions = []

        super(IBClientFactory, self).reqMktData(
            reqId,
            contract,
            genericTickList,
            snapshot,
            regulatorySnapshot,
            mktDataOptions,
        )
        self.deferredResults[reqId] = {"reqId": reqId}
        self.activeMktDataSubscriptions.append(reqId)
        self.additionalRequestInfo[reqId] = contract.__dict__
        return self.deferredRequests[reqId]

    @request
    @resolve
    def cancelMktData(self, reqId: int, tickerId: TickerId):
        canceledIDs = []
        if tickerId == -1:
            for _tickerId in self.activeMktDataSubscriptions:
                super(IBClientFactory, self).cancelMktData(int(_tickerId))
                canceledIDs.append(_tickerId)
            self.activeMktDataSubscriptions = []
            self.deferredResults[reqId] = {"reqId": canceledIDs}
        else:
            super(IBClientFactory, self).cancelMktData(tickerId)
            self.deferredResults[reqId] = {"reqId": reqId}
        return self.deferredRequests[reqId]

    @request(order=True)
    @resolve(order=True)
    def cancelOrder(self, orderId: OrderId):
        # TODO: Test this
        super(IBClientFactory, self).cancelOrder(orderId)

    @append
    def contractDetails(self, reqId: int, contractDetails: ContractDetails) -> dict:
        return contractDetails.contract.__dict__

    @append
    def historicalData(self, reqId: int, bar: BarData) -> dict:
        """ Adds a BAR to reqId deferred """

        return bar.__dict__

    @publish
    def tickPrice(
        self, reqId: int, tickType: TickType, price: float, attrib: TickAttrib
    ) -> dict:
        """ This method is called by IB server when a new tickPrice is available for active live data market lines """

        data = {
            "reqId": reqId,
            "tickType": TickTypeEnum.to_str(tickType),
            "price": price,
        }

        return data

    def tickSize(self, reqId: int, tickType: TickType, size: int) -> dict:
        data = {
            "reqId": reqId,
            "tickType": TickTypeEnum.to_str(tickType),
            "size": size,
        }
        return data

    def tickString(self, reqId: int, tickType: TickType, value: str) -> dict:
        data = {
            "reqId": reqId,
            "tickType": TickTypeEnum.to_str(tickType),
            "value": value,
        }
        return data

    def tickGeneric(self, reqId: int, tickType: TickType, value: float) -> dict:
        data = {
            "reqId": reqId,
            "tickType": TickTypeEnum.to_str(tickType),
            "value": value,
        }
        return data

    @publish
    def historicalDataUpdate(self, reqId: int, bar: BarData) -> dict:
        data = {"reqId": reqId, "barData": BarData.__dict__}
        return data

    @resolve
    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        pass

    @resolve
    def contractDetailsEnd(self, reqId: int) -> None:
        pass

    def error(
        self, reqId: TickerId, errorCode: int = -1, errorString: str = "GenericError"
    ) -> None:
        NON_ERROR_CODES = [2104, 2106, 2158]
        if errorCode in NON_ERROR_CODES:
            logger.info(errorString)
        else:
            logger.error(f"Error. Id: {reqId} Code: {errorCode} Msg: {errorString}")

        if reqId in self.deferredRequests.keys():
            self.deferredRequests[reqId].callback(
                IBException(errorCode, errorString, reqId).__dict__
            )
            del self.deferredRequests[reqId]
