from enum import Enum
import numpy as np
import tdt


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
            obj.syn = tdt.SynapseAPI('localhost')
        return cls.instance

    def set_state(self):
        pass

    # def get_gizmo_list(self):
    #     return self.syn.getGizmoNames()
    #     # loop over gizmos, looking for 'AudioStim' gizmo
    #
    # def set_mode(self, mode: TDTWorkingMode):
    #     self.syn.setMode(mode.value)
    #
    # def set_parameter_value(self, gizmo, parameter_name, value):
    #     pass
    #
    # def get_parameter_value(self):
    #     pass


if __name__ == "__main__":
    pass

# # get all info on the 'MyArray' parameter
# GIZMO = 'TagTest1'
# PARAMETER = 'MyArray'
# info = syn.getParameterInfo(GIZMO, PARAMETER)
# # get the array size (should be 100)
# sz = syn.getParameterSize(GIZMO, PARAMETER)
# # write values 1 to 50 in second half of buffer
# result = syn.setParameterValues(GIZMO, PARAMETER, np.arange(1, 51), 50)
# # read all values from buffer
# syn.getParameterValues(GIZMO, PARAMETER, sz)
# # get all info on the 'Go' parameter
# PARAMETER = 'Go'
# info = syn.getParameterInfo(GIZMO, PARAMETER)
# # flip the switch
# result = syn.setParameterValue(GIZMO, PARAMETER, 1)
# # check the value
# value = syn.getParameterValue(GIZMO, PARAMETER)
# print('value =', value)
# # also verify visually that the switch slipped in the run
# # time interface. This state change will be logged just
# # like any other variable change and saved with the runtime
# # state.
