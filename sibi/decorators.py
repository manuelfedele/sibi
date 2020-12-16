import json
from functools import wraps

import redis
from loguru import logger
from twisted.internet import defer

try:
    r = redis.StrictRedis(host="localhost", port=6379, db=0)
except Exception as e:
    logger.error(e)


def request(method=None, order=False):
    def _decorate(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            logger.info(f"Start processing {function.__name__}")
            if order:
                identifier = self.getNextOrderId()
                deferredDict = self.deferredOrdersRequests
            else:
                identifier = self.getNextReqId()
                deferredDict = self.deferredRequests
            deferredDict[identifier] = defer.Deferred()
            deferredDict[identifier].addCallbacks(json.dumps, self.error)
            _ = function(self, identifier, *args, **kwargs)
            return _

        return wrapper

    if method:
        return _decorate(method)
    return _decorate


def resolve(method=None, order=False):
    def _decorate(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            if order:
                deferredDict = self.deferredOrdersRequests
                deferredResultsDict = self.deferredOrdersResults
            else:
                deferredDict = self.deferredRequests
                deferredResultsDict = self.deferredResults
            _ = function(self, *args, **kwargs)
            identifier = args[0]
            deferredDict[identifier].callback(deferredResultsDict[identifier])
            del deferredDict[identifier]
            del deferredResultsDict[identifier]
            logger.info(f"Finish processing {function.__name__}")
            return _

        return wrapper

    if method:
        return _decorate(method)
    return _decorate


def publish(method=None, order=False):
    def _decorate(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            data = function(self, *args, **kwargs)
            if order:
                additionalInfoDict = self.additionalOrderInfo
            else:
                additionalInfoDict = self.additionalRequestInfo
            identifier = args[0]
            if additionalInfoDict.get(identifier):
                data = {**data, **additionalInfoDict[identifier]}
            data = json.dumps(data)
            r.publish(function.__name__, data)
            logger.debug(f"Pushing data on channel {function.__name__}")
            return data

        return wrapper

    if method:
        return _decorate(method)
    return _decorate


def append(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        data = method(self, *args, **kwargs)
        reqId = args[0]
        if reqId not in self.deferredResults.keys():
            self.deferredResults[reqId] = []
        self.deferredResults[reqId].append(data)

        logger.debug(f"Appending {reqId} from {method.__name__}")
        return data

    return wrapper
