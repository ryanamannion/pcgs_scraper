import os

__version__ = "0.0.5-dev"

if not os.path.isdir('./data'):
    os.mkdir('data/')
