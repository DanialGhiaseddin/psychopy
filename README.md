# PsychoPy

[![PyPI version](https://img.shields.io/pypi/v/psychopy.svg)](https://pypi.python.org/pypi/PsychoPy)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v1.4%20adopted-ff69b4.svg)](code-of-conduct.md)  

PsychoPy is an open-source package for creating experiments in behavioral science. It aims to provide a single package that is:

* precise enough for psychophysics
* easy enough for teaching
* flexible enough for everything else
* able to run experiments in a local Python script or online in JavaScript

To meet these goals PsychoPy provides a choice of interface - you can use a
simple graphical user interface called Builder, or write your experiments in
Python code. The entire application and library are written in Python and is
platform independent.

There is a range of documentation at:

* [PsychoPy Homepage](https://www.psychopy.org)
* [Youtube](https://www.youtube.com/playlist?list=PLFB5A1BE51964D587)
* The textbook, [Building Experiments in PsychoPy](https://uk.sagepub.com/en-gb/eur/building-experiments-in-psychopy/book253480)
* [The discourse user forum](https://discourse.psychopy.org)

## Contributions

To contribute, please fork the repository, hack in a feature branch, and send a
pull request.  For more, see [CONTRIBUTING.md](CONTRIBUTING.md)
and the developers documentation at [https://www.psychopy.org/developers](https://psychopy.org/developers)

## Code Status

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/psychopy/psychopy.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/psychopy/psychopy/context:python)  
Dev branch tests: [![GH tests](https://github.com/psychopy/psychopy/actions/workflows/pytests.yaml/badge.svg?branch=dev)](https://github.com/psychopy/psychopy/actions/workflows/pytests.yaml?query=branch%3Adev)  
Release tests: [![GH tests](https://github.com/psychopy/psychopy/actions/workflows/pytests.yaml/badge.svg?branch=release)](https://github.com/psychopy/psychopy/actions/workflows/pytests.yaml?query=branch%3Arelease)

## More information

* Homepage: https://www.psychopy.org
* Forum: https://discourse.psychopy.org
* Issue tracker: https://github.com/psychopy/psychopy/issues
* Changelog: https://www.psychopy.org/changelog.html

## Download Instruction

### open the terminal and change to your desired directory

```git clone https://github.com/DanialGhiaseddin/psychopy.git```
```cd psychopy```

### Create new virtual environment and activate the environment

```python -m venv venv```

```.\venv\Scripts\activate```

### Install psychopy

```python -m pip install --upgrade pip```

```pip install -e .```

```pip3 install -r requirements.txt```