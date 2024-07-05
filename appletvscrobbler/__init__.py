import asyncio

from appletvscrobbler import App


def main():
    """Application start here."""
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(App.appstart(loop))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())