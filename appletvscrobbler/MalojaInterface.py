import aiohttp
from pyatv.interface import Playing


class MalojaServer():

    def __init__(self, config):
        self._url = config["maloja_url"]
        self._api_key = config["maloja_api_key"]

    async def upload_scrobble(self, playstatus: Playing, duration_played, time_started):
        json_data = {
            'artist': playstatus.artist,
            'title': playstatus.title,
            'album': playstatus.album,
            'duration': duration_played,
            'length': playstatus.total_time,
            'time': time_started
        }

        params: dict = {"key": self._api_key}
        async with aiohttp.ClientSession() as session:
            async with session.post(url = self._url + "/apis/mlj_1/newscrobble", json = json_data, params = params) as response:
                print("Submitted scrobble: " + str(json_data) + " and got code " + str(response.status))

    async def test(self):
        params: dict = {"key": self._api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url = self._url + "/apis/mlj_1/test", params = params) as response:
                return response.status

    async def health(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url = self._url + "/apis/mlj_1/serverinfo") as response:
                return response.status
