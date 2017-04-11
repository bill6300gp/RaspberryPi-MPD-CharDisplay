#!/usr/bin/python2
import subprocess
import socket
import fcntl
import struct
from mpd import MPDClient

class MPDInfo:
client = MPDClient()

def __init__(self):
client.connect("localhost", 6600)

def update(self):
_tmp=client.status()

class PlayerStatus():