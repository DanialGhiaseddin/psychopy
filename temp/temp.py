import tdt
syn = tdt.SynapseAPI()
print(syn.getModeStr())
print(syn.getGizmoNames())
syn.setParameterValue('gizmo', 'parameter', new_value)