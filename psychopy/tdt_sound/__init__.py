from typing import Dict

from psychopy.tdt_manager import TDTManager, TDTWorkingMode
import yaml


class TDTSound(object):
    def __init__(self, tdt_configfile_path, speaker_name, sound="A", duration=0.100, volume=0.0):

        self.tdt = TDTManager()
        self.tdt.syn.setMode(TDTWorkingMode.IDLE.value)

        self._multiplex_selector = None
        self._audio_gizmos_dict = None
        self._sound = None

        # read_config()
        # validate config with tdt gizmo information
        # complete sound setter and getter
        # set sound volume function

        self._set_audio_gizmo_list(tdt_configfile_path, speaker_name, self.tdt)

        self.play = self._play_single_tone

    def _play_single_tone(self):
        pass

    def _play_file(self):
        pass

    def _set_audio_gizmo_list(self, tdt_configfile_path, speaker_name, tdt):
        with open(tdt_configfile_path, "r") as stream:
            try:
                config_file = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        tdt_speaker_config = config_file["Speakers"][speaker_name]

        self._audio_gizmos_dict = dict()

        _valid_type: Dict[str, str] = {
            "Tone": "AudioStim",
            "Noise": "AudioStim",
            "File": "FileStim"
        }

        tdt_gizmos = tdt.syn.getGizmoNames()
        for key in tdt_speaker_config.keys():
            if key in _valid_type.keys():
                gizmo_name = tdt_speaker_config[key]
                if gizmo_name in tdt_gizmos:
                    info = tdt.syn.getGizmoInfo(gizmo_name)
                    if info["type"] == _valid_type[key]:
                        self._audio_gizmos_dict[key] = gizmo_name
                    else:
                        raise Exception(
                            f'Conflict between config file and tdt synapse configuration.\n {key} must'
                            f' be {_valid_type[key]} but is {info["type"]}')

        # if len(self._audio_gizmos_dict) > 1:
        #     if 'Selectors' in tdt_speaker_config.keys():
        #         selectors = tdt_speaker_config["Selectors"]
        #         for _selector in selectors:
        #             if _selector in tdt_gizmos:
        #                 info = tdt.syn.getGizmoInfo(gizmo_name)
        #                 if info["type"] == _valid_type[key]:
        #                     self._audio_gizmos_dict[key] = gizmo_name
        #                 else:
        #                     raise Exception(
        #                         f'Conflict between config file and tdt synapse configuration.\n {key} must be {_valid_type[key]} but is {info["type"]}')

    @property
    def sound(self):
        print("getter method called")
        return self._sound

    # a setter function
    @sound.setter
    def sound(self, _sound):
        pass
        # Set frequency, set volume, set multiplexers
        # if (a < 18):
        #     raise ValueError("Sorry you age is below eligibility criteria")
        # print("setter method called")
        # self._age = a


if __name__ == "__main__":
    temp = TDTSound("C:/Users/adm/Documents/Projects/psychopy/temp/tdt_config.yaml", speaker_name="Spk1")
    print("Hello")
