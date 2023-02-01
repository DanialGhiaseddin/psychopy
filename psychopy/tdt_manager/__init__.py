from enum import Enum


class TDTWorkingMode(Enum):
    IDLE = 0
    PREVIEW = 1
    RECORDING = 2


class TDTManager(object):
    syn = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(TDTManager, cls).__new__(cls)
            obj = cls.instance
            obj.syn = "Created"
        return cls.instance

    def set_state(self):
        self.syn = "set_state"

    def set_mode(self, mode: TDTWorkingMode):
        self.syn = mode.value
        pass

    def set_parameter_value(self, parameter_name, value):
        pass


if __name__ == "__main__":
    pass
