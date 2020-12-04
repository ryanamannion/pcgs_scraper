import os

__version__ = "0.0.1"

if not os.path.isdir('./data'):
    os.mkdir('data/')
