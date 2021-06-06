import tornado.ioloop
import tornado.web
from discord.discord import Discord
from currency_converter.converter import CurrencyConverter, CurrencyConverterApi
from version.version import Version


def make_app():
    return tornado.web.Application([
        ("/discord/?", Discord),
        ("/(waehrungs-)?rechner/?", CurrencyConverter),
        ("/(waehrungs-)?rechner/api/?", CurrencyConverterApi),
        ("/version/?", Version)
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()


