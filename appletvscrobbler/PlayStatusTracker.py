import asyncio
from asyncio import Task
from typing import Optional

from pyatv.const import DeviceState
from pyatv.interface import Playing

from appletvscrobbler import AppleTvListener


class PlayStatusTracker():

    def __init__(self, parent: AppleTvListener, playstatus: Playing):
        self.parent = parent
        self.time = None
        self.playstatus = None
        self.playing: bool = False
        self.task: Optional[Task] = None
        self.duration_played = 0
        self.update_playstatus(playstatus)

    def update_playstatus(self, playstatus: Playing):
        if self.task is not None:
            # We always want to cancel the existing task, so the time can be updated to the current state
            # and then resumed in sync.
            self.task.cancel()

        should_reset_duration = self.should_reset_duration(self.playstatus, playstatus)
        is_new_song = self.is_new_song(self.playstatus, playstatus)
        if (is_new_song or should_reset_duration) and self.can_submit_as_scrobble():
            print("Is new song?: " + str(is_new_song) + " Should reset duration?: " + str(should_reset_duration))
            print("Uploading scrobble.")
            asyncio.ensure_future(self.parent.maloja_server.upload_scrobble(self.playstatus, self.duration_played))

        self.playstatus: Playing = playstatus
        self.time = playstatus.position
        self.playing = playstatus.device_state == DeviceState.Playing

        if is_new_song:
            print("Resetting duration played. Was " + str(self.duration_played))
            self.duration_played = 0

        if self.playing:
            self.task = asyncio.ensure_future(self.update_time())
        else:
            self.task = None

    def should_reset_duration(self, old_playstatus: Optional[Playing], new_playstatus: Playing) -> bool:
        if old_playstatus is None:
            return False
        # Should account for latency while allowing repeats?
        if abs(new_playstatus.position - self.time) <= 5:
            return False
        # If time is greater than current position, then we reset the song.
        return new_playstatus.position < self.time and new_playstatus.device_state == DeviceState.Playing

    def is_new_song(self, old_playstatus: Optional[Playing], new_playstatus: Playing) -> bool:
        if old_playstatus is None:
            return False
        return old_playstatus.title != new_playstatus.title or old_playstatus.artist != new_playstatus.artist or old_playstatus.album != new_playstatus.album

    def can_submit_as_scrobble(self) -> bool:
        # Playtime was more than 50%
        if (self.duration_played / self.playstatus.total_time) > .50:
            return True
        # More than four minutes were played
        return (self.duration_played / 60) > 4

    async def update_time(self):
        # Should not need to check if playing - the task will be cancelled in this case.
        while self.time <= self.playstatus.total_time:
            self.time += 1
            self.duration_played += 1
            # print("Incrementing time to " + str(self.time))
            await asyncio.sleep(1)
