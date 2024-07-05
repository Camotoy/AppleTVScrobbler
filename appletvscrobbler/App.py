import asyncio
import json

import pyatv
from pyatv import Protocol
from pyatv.storage.file_storage import FileStorage

from appletvscrobbler.AppleTvListener import AppleTvListener
from appletvscrobbler.MalojaInterface import MalojaServer


async def appstart(loop):
    abort_sem = asyncio.Semaphore(0)

    config_name = "../config.json"
    with open(config_name) as f:
        config = json.load(f)

    # Maloja
    maloja = MalojaServer(config)
    code = await maloja.test()
    print("Test code is " + str(code))
    code = await maloja.health()
    print("Health code is " + str(code))

    storage = FileStorage.default_storage(loop)

    results = await pyatv.scan(identifier=config["identifier"], loop=loop, storage=storage)
    if not results:
        raise IOError("Could not find device on network with identifier " + config["identifier"])

    # TODO ouch
    results[0].get_service(Protocol.AirPlay).credentials = config["credentials"]

    # TODO implement reconnecting
    atv = await pyatv.connect(results[0], loop=loop, storage=storage)

    print(atv.device_info)

    listener = AppleTvListener(config, atv, maloja)
    atv.push_updater.listener = listener
    atv.push_updater.start()
    await wait_for_input(abort_sem)


async def wait_for_input(abort_sem):
    """Wait for abort signal."""
    abort_sem_acquire = asyncio.create_task(abort_sem.acquire())
    await asyncio.wait(
        [abort_sem_acquire], return_when=asyncio.FIRST_COMPLETED
    )