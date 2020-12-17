import sys
from typing import List

from twisted.internet import reactor
from twisted.web import xmlrpc
from twisted.web.client import HTTPConnectionPool, Agent

from sibi.ibapi.common import BarData
from sibi.ibapi.contract import Contract, ComboLeg
from sibi.ibapi.order import Order


class XMLRPCServer(xmlrpc.XMLRPC):
    def __init__(self, factory):
        super(XMLRPCServer, self).__init__()
        pool = HTTPConnectionPool(reactor, persistent=True)
        pool.maxPersistentPerHost = 10
        self.agent = Agent(reactor, pool=pool)
        self.factory = factory

        xmlrpc.addIntrospection(self)

    def xmlrpc_reqContractDetails(
        self,
        symbol: str = "",
        secType: str = "STK",
        currency: str = "USD",
        exchange: str = "SMART",
        lastTradeDateOrContractMonth: str = "",
        strike: str = "",
        right: str = "",
    ):
        """This returns information about a contract's conID, symbol, local symbol, currency, etc.
         reqContractDetails takes as an argument a Contract object which may uniquely match one contract,
         and unlike other API functions it can also take a Contract object which matches multiple contracts
         in IB's database. When there are multiple matches, a list is returned

        Args:
            symbol (str): IB symbol (eg. SPY, AAPL, DAX)
            secType (str): The type of security (eg. IND, STK, OPT)
            currency (str): The currency of the security (eg. EUR, USD)
            exchange (str): The exchange (eg SMART, CBOE)
            lastTradeDateOrContractMonth (str): This is a date for OPTIONS (eg. 20210104) or a month for FUTURES (eg. 202103)
            strike (str): Strike price for options
            right (str): Right for options (eg. C or CALL, P or PUT)
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = secType
        contract.currency = currency
        contract.exchange = exchange
        contract.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
        contract.strike = strike
        contract.right = right
        contract.includeExpired = False
        result = self.factory.reqContractDetails(contract)

        return result

    def xmlrpc_reqHistoricalData(
        self,
        symbol: str = "",
        secType: str = "",
        currency: str = "",
        exchange: str = "",
        endDateTime: str = "",
        durationStr: str = "1 M",
        barSizeSetting: str = "1 day",
        whatToShow: str = "MIDPOINT",
        useRTH: int = 1,
        formatDate: int = 1,
        keepUpToDate: bool = False,
        chartOptions=None,
    ) -> List[BarData]:
        if chartOptions is None:
            chartOptions = []
        contract = Contract()
        contract.symbol = symbol
        contract.secType = secType
        contract.currency = currency
        contract.exchange = exchange
        result = self.factory.reqHistoricalData(
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
        return result

    def xmlrpc_reqMktData(
        self,
        conId: str = 0,
        symbol: str = "",
        secType: str = "",
        currency: str = "",
        exchange: str = "",
        lastTradeDateOrContractMonth: str = "",
        strike: float = 0.0,
        right: str = "",
    ):
        contract = Contract()
        contract.conId = conId
        contract.symbol = symbol
        contract.secType = secType
        contract.currency = currency
        contract.exchange = exchange
        contract.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
        contract.strike = strike
        contract.right = right
        contract.includeExpired = False
        result = self.factory.reqMktData(contract)
        return result

    def xmlrpc_cancelMktData(self, tickerId: int = -1):
        """Cancels market data subscriptions.

        Args:
            tickerId (int): The ticker ID which was specified in original market data request.
                Cancelling a subscription allows the user to make a subscription to a different contract and remain
                within the level 1 market data lines allowance.
        """
        result = self.factory.cancelMktData(tickerId)
        return result

    def xmlrpc_placeOrder(
        self,
        symbol: str = "",
        secType: str = "STK",
        currency: str = "USD",
        exchange: str = "SMART",
        lastTradeDateOrContractMonth: str = "",
        strike: str = "",
        right: str = "",
        orderType: str = "MKT",
        limitPrice: float = sys.float_info.max,
        totalQuantity: int = 1,
        action: str = "BUY",
        comboLegs=None,
        allOrNone: bool = True,
    ):
        """This procedure places an Order if a valid contract and a valid order are provided

        Args:
            symbol (str): IB symbol (eg. SPY, AAPL, DAX)
            secType (str): The type of security (eg. IND, STK, OPT)
            currency (str): The currency of the security (eg. EUR, USD)
            exchange (str): The exchange (eg SMART, CBOE)
            lastTradeDateOrContractMonth (str): This is a date for OPTIONS (eg. 20210104) or a month for FUTURES (eg. 202103)
            strike (str): Strike price for options
            right (str): Right for options (eg. C or CALL, P or PUT)
            orderType (str): Order's typlogy (eg. MKT, LMT)
            limitPrice (float): A limit price provided if LMT order
            totalQuantity (int): Quantity to buy
            action (int): Order's action (BUY/SELL)
            comboLegs (list): If provided, indentifies this order as a Combo order
            allOrNone (bool): Indicates whether or not all the order has to be filled on a single execution.
        """

        contract = Contract()
        contract.symbol = symbol
        contract.secType = secType
        contract.currency = currency
        contract.exchange = exchange
        if lastTradeDateOrContractMonth:
            contract.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
        if strike:
            contract.strike = strike
        if right:
            contract.right = right
        contract.comboLegs = []

        if comboLegs and secType == "BAG":
            for comboLeg in comboLegs:
                leg = ComboLeg()
                for key, value in comboLeg.items():
                    setattr(leg, key, value)
                contract.comboLegs.append(leg)

        order = Order()
        order.action = action
        order.orderType = orderType
        order.totalQuantity = totalQuantity
        order.lmtPrice = float(limitPrice)
        order.allOrNone = allOrNone
        order.smartComboRoutingParams = []

        result = self.factory.placeOrder(contract, order)
        return result

    def xmlrpc_cancelOrder(self, orderId: int):
        result = self.factory.cancelOrder(orderId)
        return result
