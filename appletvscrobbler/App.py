import asyncio
import json
from asyncio import AbstractEventLoop

import pyatv
from pyatv.interface import BaseConfig
from pyatv.storage.file_storage import FileStorage

from appletvscrobbler.AppleTvListener import AppleTvListener
from appletvscrobbler.MalojaInterface import MalojaServer


class MainLoop():

    def __init__(self, loop: AbstractEventLoop):
        self.abort_sem = asyncio.Semaphore(0)
        self.loop = loop

        config_name = "../config.json"
        with open(config_name) as f:
            self.config = json.load(f)

    async def start(self):
        # Maloja
        self.maloja = MalojaServer(self.config)
        code = await self.maloja.test()
        print("Test code is " + str(code))
        code = await self.maloja.health()
        print("Health code is " + str(code))

        self.storage = FileStorage.default_storage(self.loop)
        await self.storage.load()

        results = await pyatv.scan(identifier=self.config["identifier"], loop=self.loop, storage=self.storage)
        if not results:
            raise IOError("Could not find device on network with identifier " + self.config["identifier"])

        try:
            while True:
                await self.initializeAndHold(results)
                results = await self.reconnect()
        except KeyboardInterrupt:
            return 0

    async def initializeAndHold(self, results: list[BaseConfig]):
        atv = await pyatv.connect(results[0], loop=self.loop, storage=self.storage)
        print(atv.device_info)

        # Note: you have to define these as separate variables before setting them as listeners.
        # Coming from Java, I have absolutely zero idea why.
        connect_listener = ConnectListener(self)
        listener = AppleTvListener(self.config, atv, self.maloja)

        atv.listener = connect_listener
        atv.push_updater.listener = listener
        atv.push_updater.start()

        await self.wait_for_input()

    async def reconnect(self):
        while True:
            results = await pyatv.scan(identifier=self.config["identifier"], loop=self.loop)
            if len(results) == 0:
                print("Could not find Apple TV. Trying again in five seconds...")
                await asyncio.sleep(5)
            else:
                break

        return results

    async def wait_for_input(self):
        """Wait for abort signal."""
        abort_sem_acquire = asyncio.create_task(self.abort_sem.acquire())
        await asyncio.wait(
            [abort_sem_acquire], return_when=asyncio.FIRST_COMPLETED
        )


class ConnectListener(pyatv.interface.DeviceListener):

    def __init__(self, parent: MainLoop):
        self.parent = parent

    def connection_lost(self, exception: Exception) -> None:
        print("Connection lost.")
        self.parent.abort_sem.release()

    def connection_closed(self) -> None:
        print("Connection closed.")
        self.parent.abort_sem.release()