from psychopy.tdt_manager import TDTManager, TDTWorkingMode


class TDTSound(object):
    def __init__(self, config):
        tdt = TDTManager()
        tdt.set_mode(TDTWorkingMode.IDLE)
        self.play = self._play_single_tone

    def _play_single_tone(self):
        pass

    def _play_file(self):
        pass


if __name__ == "__main__":
    pass
