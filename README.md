**Solid** is an XMLRPC interface to Interactive Brokers API.

The main purpose of this library is to transform the `async` world of tws api into `sync` procedures, in order to develop custom applications easily.

It needs TWS **9.76.1** or greater python api to work.

---

## Example
* Create a file `testxmlrpc.py` with:

```Python
import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:7080')

bars = s.reqHistoricalData("EUR", "CASH", "GBP", "IDEALPRO")

print(bars)
```

And that's it.