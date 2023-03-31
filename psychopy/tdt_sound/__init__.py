from typing import Dict

from psychopy.tdt_manager import TDTManager, TDTWorkingMode
import yaml
import numpy as np


class TDTSound(object):
    def __init__(self, tdt_configfile_path, speaker_name, sound="C5", duration=1.100, volume=35.0):

        self.tdt = TDTManager()
        self.tdt.syn.setMode(TDTWorkingMode.IDLE.value)

        self._multiplex_selector = []
        self._audio_gizmos_dict = None
        self._standard_tones = self._get_piano_notes()
        self._sound = None
        self._stim_gizmo = None
        self.duration = duration
        self.volume = volume

        # read_config()
        # validate config with tdt gizmo information
        # complete sound setter and getter
        # set sound volume function

        self._set_audio_gizmo_list(tdt_configfile_path, speaker_name, self.tdt)

        self.tdt.syn.setMode(TDTWorkingMode.RECORDING.value)

        self.sound = sound

    def _play_single_tone(self):
        pass

    def _play_file(self):
        pass

    def play(self):
        self.tdt.syn.setParameterValue(self._stim_gizmo, 'Strobe', 1)

    def _set_audio_gizmo_list(self, tdt_configfile_path, speaker_name, tdt):
        with open(tdt_configfile_path, "r") as stream:
            try:
                config_file = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self.tdt_speaker_config = config_file["Speakers"][speaker_name]

        self._audio_gizmos_dict = dict()

        _valid_type: Dict[str, str] = {
            "Tone": "AudioStim",
            "Noise": "AudioStim",
            "File": "FileStim"
        }

        tdt_gizmos = tdt.syn.getGizmoNames()
        for key in self.tdt_speaker_config.keys():
            if key in _valid_type.keys():
                gizmo_name = self.tdt_speaker_config[key]
                if gizmo_name in tdt_gizmos:
                    info = tdt.syn.getGizmoInfo(gizmo_name)
                    if info["type"] == _valid_type[key]:
                        self._audio_gizmos_dict[key] = gizmo_name
                    else:
                        raise Exception(
                            f'Conflict between config file and tdt synapse configuration.\n {key} must'
                            f' be {_valid_type[key]} but is {info["type"]}')
                else:
                    raise Exception(
                        f'Conflict between config file and tdt synapse configuration.\n {key} not found')

        if len(self._audio_gizmos_dict) > 1:
            if 'Selectors' in self.tdt_speaker_config.keys():
                selectors = self.tdt_speaker_config["Selectors"]
                for _selector in selectors:
                    if _selector in tdt_gizmos:
                        info = tdt.syn.getGizmoInfo(_selector)
                        if info["type"] == "SigSelector":
                            self._multiplex_selector.append(_selector)
                        else:
                            raise Exception(
                                f'Conflict between config file and tdt synapse configuration.\n Selectors must be '
                                f'SigSelector but is {info["type"]}')

    @staticmethod
    def _get_piano_notes():
        # White keys are in Uppercase and black keys (sharps) are in lowercase
        octave = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        base_freq = 440  # Frequency of Note A4
        keys = np.array([x + str(y) for y in range(0, 9) for x in octave])
        # Trim to standard 88 keys
        start = np.where(keys == 'A0')[0][0]
        end = np.where(keys == 'C8')[0][0]
        keys = keys[start:end + 1]
        note_freqs = dict(zip(keys, [2 ** ((n + 1 - 49) / 12) * base_freq for n in range(len(keys))]))
        note_freqs[''] = 0.0  # stop
        return note_freqs

    @property
    def sound(self):
        return self._sound

    # a setter function
    @sound.setter
    def sound(self, _sound):
        if _sound in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']:
            _sound = _sound + "4"
        if _sound in self._standard_tones.keys():
            freq = self._standard_tones[_sound]
        elif _sound == "noise":
            freq = "wn"
        else:
            freq = float(_sound)

        self._sound = freq

        if type(freq) is float:
            self._stim_gizmo = self.tdt_speaker_config['Tone']
            selector_index = 1
        elif freq == "wn":
            self._stim_gizmo = self.tdt_speaker_config['Noise']
            selector_index = 2
        else:
            self._stim_gizmo = None
            selector_index = 0

        for _selector_gizmo in self._multiplex_selector:
            self.tdt.syn.setParameterValue(_selector_gizmo, 'ChanSel-1', selector_index)

        # self.tdt.syn.setParameterValue(self._stim_gizmo, 'ChanSel-1', selector_index)
        self.tdt.syn.setParameterValue(self._stim_gizmo, 'WaveFreq', self._sound)

        self.tdt.syn.setParameterValue(self._stim_gizmo, 'WaveAmp', self.volume)
        self.tdt.syn.setParameterValue(self._stim_gizmo, 'PulseDur', self.duration * 1000)

        # Set frequency, set volume, set multiplexers
        # if (a < 18):
        #     raise ValueError("Sorry you age is below eligibility criteria")
        # print("setter method called")
        # self._age = a


if __name__ == "__main__":
    temp = TDTSound("C:/Users/adm/Documents/Projects/psychopy/temp/tdt_config.yaml", speaker_name="Spk1")
    print(temp.sound)
