class IBException(Exception):
    def __init__(self, code, message, reqId=None):
        self.reqId = None
        self.code = code
        self.message = message

    def __repr__(self):
        return self.__dict__

    def __str__(self):
        return self.__dict__
