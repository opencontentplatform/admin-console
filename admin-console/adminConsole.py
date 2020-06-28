"""Entry for the Open Content Platform's (OCP) Admin Console.

The OCP Admin Console extends common administrator functions through a graphical
interface for quicker interaction, instead of requiring direct JSON manipulation
through a REST API utility. It leverages wxPython for the GUI toolkit.

According to the xwPython site (wxpython.org), wxPython is a "cross-platform GUI
toolkit for the Python language. With wxPython software developers can create
truly native user interfaces for their Python applications, that run with little
or no modifications on Windows, Macs and Linux or other unix-like systems."

Author: Chris Satterthwaite (CS)
Contributors:
Version info:
  1.0 : (CS) Created Apr 11, 2019

"""
import sys, os, traceback
import re, platform, importlib

## Load the lib directory into sys.path, so we can import the main module
basePath = os.path.dirname(os.path.abspath(__file__))
libPath = os.path.join(basePath, 'lib')
if libPath not in sys.path:
	sys.path.append(libPath)
import main


def checkModule(moduleName):
	"""Check if a module exists, without actually loading it yet."""
	## This version works on Python3.5+, but requires importlib
	spec = importlib.util.find_spec(moduleName)
	found = spec is not None
	if not found:
		print('\nModule not found: {}.  Please run \'pip install {}\' first.\n'.format(moduleName, moduleName))
		raise OSError('Module not found: {}.  Please run \'pip install {}\' first.'.format(moduleName, moduleName))

	## end checkModule
	return found


def verifyAvailableModules(osType):
	"""Check to see if the required packages are loaded."""
	import importlib
	checkModule('wx')
	if re.search('windows', osType, re.I):
		checkModule('winreg')

	## end verifyAvailableModules
	return


def verifyBrowserEmulation(osType):
	"""Enable Reg key for python to use browser emulation (html/javascript).

	Add a DWORD value for an executable, according to this site:
	https://docs.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/general-info/ee330730(v=vs.85)#browser_emulation

	For this Registry location:
	Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION

	Without compiling an single executable for the console, we added python.exe,
	with value 11001 (at the time it was the IE11 default using IE11 Edge mode).
	"""
	if re.search('windows', osType, re.I):
		print('Checking browser emulation setting in registry')
		import winreg
		try:
			fileName = 'python.exe'
			key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Internet Explorer\\Main\\FeatureControl\\FEATURE_BROWSER_EMULATION")
			result = winreg.QueryValueEx(key, fileName)
			print('Key already found with value: {}. Leaving key unchanged.'.format(result))
		except FileNotFoundError:
			try:
				print('Attempting to set browser emulation key in registry')
				key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Internet Explorer\\Main\\FeatureControl\\FEATURE_BROWSER_EMULATION")
				winreg.SetValueEx(key, fileName, 0, winreg.REG_DWORD, 11001)
				print('Registry key set')
			except:
				print('\mFailed to set registry key.  You may need to start the shell with \'Run as Administrator\'.\n')
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				print('Failure in verifyBrowserEmulation: {}'.format(stacktrace))
		except:
			raise

	## end verifyBrowserEmulation
	return


if __name__ == '__main__':
	try:
		osType = platform.system()
		verifyAvailableModules(osType)
		verifyBrowserEmulation(osType)
		main.main()
	except:
		stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		print('Failure in adminConsole wrapper: {}'.format(stacktrace))
