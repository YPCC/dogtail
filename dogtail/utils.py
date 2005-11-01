#!/usr/bin/env python
"""
Various utilities

Authors: Ed Rousseau <rousseau@redhat.com>, Zack Cerza <zcerza@redhat.com, David Malcolm <dmalcolm@redhat.com>
"""

__author__ = """Ed Rousseau <rousseau@redhat.com>,
Zack Cerza <zcerza@redhat.com, 
David Malcolm <dmalcolm@redhat.com>
"""

import os
from config import config
from time import sleep
from logging import debugLogger as logger
from logging import TimeStamp

def screenshot(windowname = 'root', file = 'screenshot.png', timeStamp = True, args = ''):
	"""
	This function wraps the ImageMagick import command to take a screenshot. 
	
	The file argument may be specified as 'foo', 'foo.png', or using any other 
	extension that ImageMagick supports. PNG is the default.
	
	By default, screenshot filenames are in the format of foo_YYYYMMDD-hhmmss.png .
	The timeStamp argument may be set to False to name the file foo.png.
	"""
	# config is supposed to create this for us. If it's not there, bail.
	assert os.path.isdir(config.scratchDir)
	
	if windowname == '':
		windowname = "root"

	baseName = ''.join(file.split('.')[0:-1])
	fileExt = file.split('.')[-1]
	if not baseName: 
		baseName = file
		fileExt = 'png'
	print baseName, fileExt
	
	if timeStamp:
		ts = TimeStamp()
		newFile = ts.fileStamp(baseName) + '.' + fileExt
		path = config.scratchDir + newFile
	else:
		newFile = baseName + '.' + fileExt
		path = config.scratchDir + newFile
	
	print path
	
	# Generate the command and redirect STDERR to STDOUT
	# This really needs window manipulation and pyspi state binding to be done
	# to actually be really useful
	answer = []
	cmd = "import -window '%s' %s %s 2>&1" % (windowname, path, args)
	answer = os.popen(cmd).readlines()

	# If successful we should get nothing back. If not something went wrong
	# and our mouse is now probably unusable
	if answer:
		raise ValueError, "Screenshot failed: " + answer[-1]
	assert os.path.exists(path)
	logger.log("Screenshot taken: " + path)
	return path

def run(string, timeout=config.runTimeout, interval=config.runInterval, desktop=None, dumb=False, appName=''):
	"""
	Runs an application. [For simple command execution such as 'rm *', use os.popen() or os.system()]
	If dumb is omitted or is False, polls at interval seconds until the application is finished starting, or until timeout is reached.
	If dumb is True, returns when timeout is reached.
	"""
	from os import environ, spawnvpe, P_NOWAIT
	if not desktop: from tree import root as desktop
	args = string.split()
	name = args[0]
	pid = spawnvpe (P_NOWAIT, name, args, environ)

	if not appName:
		appName=args[0]
	
	if dumb:
		# We're starting a non-AT-SPI-aware application. Disable startup detection.
		doDelay(timeout)
	else:
		# Startup detection code
		# The timing here is not totally precise, but it's good enough for now.
		time = 0
		while time < timeout:
			time = time + interval
			try:
				for child in desktop.children[::-1]:
					if child.name == appName:
						for grandchild in child.children:
							if grandchild.roleName == 'frame':
								from procedural import focus
								focus.application.node = child
								doDelay(interval)
								return pid
			except AttributeError: pass
			doDelay(interval)
	return pid

def doDelay(delay=None):
	"""
	Utility function to insert a delay (with logging and a configurable
	default delay)
	"""
	if delay is None:
		delay = config.defaultDelay
	if config.debugSleep:
		logger.log("sleeping for %f"%delay)
	sleep(delay)

