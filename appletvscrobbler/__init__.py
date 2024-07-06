import asyncio

from appletvscrobbler import App
from appletvscrobbler.App import MainLoop


def main():
    """Application start here."""
    loop = asyncio.get_event_loop()
    try:
        app = MainLoop(loop)
        return loop.run_until_complete(app.start())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())