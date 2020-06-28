import os, sys

basePath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

## ./conf
configPath = os.path.join(basePath, 'conf')
## ./docs
libPath = os.path.join(basePath, 'lib')
## ./external
logPath = os.path.join(basePath, 'log')

def addLibPath():
	if libPath not in sys.path:
		sys.path.append(libPath)