from typing import Optional

import pyatv.interface
from pyatv.const import FeatureName, FeatureState
from pyatv.interface import Playing

from appletvscrobbler.MalojaInterface import MalojaServer
from appletvscrobbler.PlayStatusTracker import PlayStatusTracker


class AppleTvListener(pyatv.interface.PushListener):
    """Listen for push updates and print changes."""

    def __init__(self, config, atv: pyatv.interface.AppleTV, maloja_server: MalojaServer):
        """Initialize a new listener."""
        self.config = config
        self.atv = atv
        self.maloja_server = maloja_server
        self.playstatus_tracker: Optional[PlayStatusTracker] = None

    def playstatus_update(self, updater, playstatus: Playing) -> None:
        """Inform about changes to what is currently playing."""
        app = (
            self.atv.metadata.app
            if not self.atv.features.in_state(FeatureState.Unavailable, FeatureName.App)
            else None
        )
        # TODO find out when app can be None
        if app is None or app.identifier == self.config["app"]:
            print(playstatus)
            if not self.playstatus_tracker:
                self.playstatus_tracker = PlayStatusTracker(self, playstatus)
            else:
                self.playstatus_tracker.update_playstatus(playstatus)

    def playstatus_error(self, updater, exception: Exception) -> None:
        """Inform about an error when updating play status."""
        print(exception)
