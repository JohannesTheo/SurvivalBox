# SurvivalBox
A grid world game for deep reinforcement learning

## Installation

- Requires python 3.5

Four steps to install:

1. install PyGame-Learning-Environment from GitHub
2. clone SurvivalBox repository
3. install general dependencies from requirements.txt
4. optionally install SurvivalBox system/env wide

You can clone both, the SurvivalBox and the PLE repository to any place you want on your system. The install via '''pip install -e .''' will link those directories. To uninstall, just call '''pip uninstall <*>''' and simply delete the repository directories again.

### 1 - install PyGame-Learning-Environment from GitHub
```
git clone https://github.com/ntasfi/PyGame-Learning-Environment.git
cd PyGame-Learning-Environment/
pip install -e .
```

### 2 - clone SurvivalBox repository
```
git clone https://github.com/JohannesTheo/SurvivalBox.git
```
### 3 - install general dependencies from requirements.txt
```
cd SurvivalBox
pip install -r requirements.txt 
```

### 4 -  Optionally: install SurvivalBox system/env wide
```
pip install -e .
```

## Run Demo
```
python random_agent.py
python manual_game.py
```