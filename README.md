# multiCams

This software is used for storing streams for multiple web cameras that are on one computer.

Videos and timestamp files are stored simoutaneously

Developed based on Python3.7 and OpenCV


# Installation
Download and in the terminal ( inside the folder) run

$ conda env create -f multiCams.yaml

# Usage
After installation, inside the folder open the terminal and run

$ conda activate multiCams

$ python multiCams.py -n 2 --IO8Exist y # simoutanously record 2 webcams, IO8 exist

$ python multiCams.py -n 2 --IO8Exist n # simoutanously record 2 webcams, IO8 not exist
