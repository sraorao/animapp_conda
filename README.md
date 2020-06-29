[![Build Status](https://travis-ci.org/sraorao/animapp_conda.svg?branch=master)](https://travis-ci.org/sraorao/animapp_conda)
[![Documentation Status](https://readthedocs.org/projects/animapp/badge/?version=latest)](https://animapp.readthedocs.io/en/latest/?badge=latest)

A package to track the movement of an object (a small animal) in a video.

See https://animapp.readthedocs.io/en/latest/ for detailed documentation.

To install:

```bash
conda create -n animapp_env
conda activate animapp_env
conda install pyqt opencv
pip install animapp
```
To run:

1. First set thresholds (creates settings.yaml file)
```bash
threshold
```

2. Run analysis module
```bash
animapp
```

