#!/usr/bin/env python
"""Play"""
import sys
from itertools import chain
from time import sleep

from urllib.request import urlopen

from simplejson import loads

from vestaboard import Board
from vestaboard.formatter import Formatter

# This is hokey but works for now to nix personal data out of here
from credentials import *
# provides vestaboard and alphavantage keys, along with stocks and etfs to quote

def get_quote(ticker):
    """ds"""
    ret = {}
    use_fields=["sym", "open", "high", "low", "price", "vol", "day", "prev", "change", "change%"]
    url = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}".format(ticker, ticker_apikey)

    res = loads(urlopen(url).read())
    raw = res["Global Quote"]
    for i, k in enumerate(sorted(raw.keys())):
        ret[use_fields[i]] = raw[k]

    # small fixup - drop % symbol
    ret["change%"] = ret["change%"][:-1]

    return ret


def get_tickers(limit=6):
    count = 0
    ret = []
    for t in list(chain(stocks, etfs)):
        count += 1

        if count <= limit:
            ret.append(t)
        else:
            count=0
            yield ret
            ret = []

    yield ret


def get_quotes(tickers, limit=5, sleep_secs=65):
    """Get all quotes we need but don't exceed API limits"""
    quotes = {}
    i = 0
    slept = 0
    for t in tickers:
        quotes[t] = get_quote(t)
        i += 1
        if i >= limit:
            sleep(sleep_secs)
            slept += sleep_secs
            i = 0

    return quotes, slept


def format_line(q):
    """Format single quote line"""

    if q.get("price", None) is None:
        # return blank line
        return Formatter().convertLine("")

    convert =" {:<5} {:>6.2f} {:>+5.2f}% ".format(q["sym"], float(q["price"]), float(q["change%"]))
    print(convert)
    line = Formatter().convertLine(convert, justify="left")

    #Default green
    line[0] = 66
    line[-1] = 66
    if float(q["change%"]) < 0:
        # red
        line[0] = 63
        line[-1] = 63

    return line


def verify_lines(lines):
    """Verify we have right number of lines"""

    # Too few, append blank lines
    for _ in range(6-len(lines)):
        lines.append(Formatter().convertLine(""))

    # If too many, truncate
    return lines[:6]


def main():
    """You know, for main()"""

    #installable = vestaboard.Installable(key, secret)
    vboard = Board(apiKey=key, apiSecret=secret, subscriptionId=sub)
    #vboard.post('Love is all you need')

    interval=120
    while(True):
        ticker_lists = get_tickers()
        for l in ticker_lists:
            quotes = []
            lines = []
        #lines.append(Formatter().convertLine("")) # blank top line
            quotes, slept = get_quotes(l)
            for q in quotes.values():
                lines.append(format_line(q))
            vboard.raw(verify_lines(lines))
            print(lines)
            sleep(interval-slept)

    return 0


if __name__ == "__main__":
    sys.exit(main())
