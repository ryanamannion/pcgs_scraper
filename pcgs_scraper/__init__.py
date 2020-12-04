import os

__version__ = "0.0.2-dev"

if not os.path.isdir('./data'):
    os.mkdir('data/')
