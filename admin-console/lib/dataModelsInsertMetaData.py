"""Pane for Admin Console ribbon destination: Data->Models->Insert MetaData.

This pane enables management of Model MetaData through custom forms.
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
from wx.lib.scrolledpanel import ScrolledPanel
from operator import itemgetter


class CreateMatchSimpleDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Match Dialog', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='CreateMatchSimpleDialog', log=None):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.logger = log
		self.logger.debug('Inside CreateMatchSimpleDialog')

		regExText = wx.StaticText(self, wx.ID_ANY, 'Matching Regular Expression')
		self.regEx = wx.TextCtrl(self, wx.ID_ANY, size=(250, -1))

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=20, vgap=5)
		gBox1.Add(regExText, 1, wx.EXPAND)
		gBox1.Add(self.regEx, 0, wx.EXPAND)
		mainBox.Add(gBox1, 1, wx.EXPAND|wx.ALL, 20)

		btnsizer = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		mainBox.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
		self.SetSizer(mainBox)
		self.Layout()
		self.SendSizeEvent()

class CreateMatchDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Match Dialog', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='CreateMatchDialog', log=None):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.logger = log
		self.logger.debug('Inside CreateMatchDialog')

		nameText = wx.StaticText(self, wx.ID_ANY, 'Name To Assign')
		regExText = wx.StaticText(self, wx.ID_ANY, 'Matching Regular Expression')
		self.name = wx.TextCtrl(self, wx.ID_ANY, size=(150, -1))
		self.regEx = wx.TextCtrl(self, wx.ID_ANY, size=(250, -1))

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=20, vgap=5)
		gBox1.Add(nameText, 1, wx.EXPAND)
		gBox1.Add(regExText, 1, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.regEx, 0, wx.EXPAND)
		mainBox.Add(gBox1, 1, wx.EXPAND|wx.ALL, 20)
		mainBox.AddSpacer(20)
		self.constructSampleRegExPane(mainBox)
		mainBox.AddSpacer(20)
		# line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
		# mainBox.Add(line, 1, wx.ALL, 10)

		btnsizer = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		mainBox.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
		self.SetSizer(mainBox)
		self.Layout()
		self.SendSizeEvent()

	def constructSampleRegExPane(self, mainBox):
		samples_collapsible_panel = wx.CollapsiblePane(self, label='Sample regular expressions')
		## Add collapsible pane with zero proportion, to the sizer
		mainBox.Add(samples_collapsible_panel, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		samplesRefPanel = samples_collapsible_panel.GetPane()
		samples_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		panelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		panelBuffer.AddSpacer(10)
		panelSizer = wx.FlexGridSizer(cols=2, vgap=10, hgap=20)
		panelSizer.AddGrowableCol(1)

		regex5 = wx.StaticText(samplesRefPanel, wx.ID_ANY, '^[Nn][Yy][Cc]\d{1,3}[-]')
		descr5 = wx.StaticText(samplesRefPanel, wx.ID_ANY, 'name starting with NYC + 1-3 integers + a hyphen')
		panelSizer.Add(regex5, 0, wx.EXPAND)
		panelSizer.Add(descr5, 0, wx.EXPAND)
		regex1 = wx.StaticText(samplesRefPanel, wx.ID_ANY, '^(.*(?:dr\.|prod\.).*)$')
		descr1 = wx.StaticText(samplesRefPanel, wx.ID_ANY, 'domain containing \'dr.\' or \'prod.\'')
		panelSizer.Add(regex1, 0, wx.EXPAND)
		panelSizer.Add(descr1, 0, wx.EXPAND)
		regex2 = wx.StaticText(samplesRefPanel, wx.ID_ANY, '^((?:(?!dev\.|qa\.).)*)$')
		descr2 = wx.StaticText(samplesRefPanel, wx.ID_ANY, 'domain not containing \'dev.\' or \'qa.\'')
		panelSizer.Add(regex2, 0, wx.EXPAND)
		panelSizer.Add(descr2, 0, wx.EXPAND)
		regex4 = wx.StaticText(samplesRefPanel, wx.ID_ANY, '^13\.(?:107|9[0-9])\.')
		descr4 = wx.StaticText(samplesRefPanel, wx.ID_ANY, 'IP starting with \'13.107.\' or \'13.9x.\'')
		panelSizer.Add(regex4, 0, wx.EXPAND)
		panelSizer.Add(descr4, 0, wx.EXPAND)
		regex3 = wx.StaticText(samplesRefPanel, wx.ID_ANY, '^(?!192[.]|14[.])')
		descr3 = wx.StaticText(samplesRefPanel, wx.ID_ANY, 'IP not starting with \'192.\' or \'14.\'')
		panelSizer.Add(regex3, 0, wx.EXPAND)
		panelSizer.Add(descr3, 0, wx.EXPAND)

		panelBuffer.Add(panelSizer, 1, wx.EXPAND)
		samplesRefPanel.SetSizer(panelBuffer)

		## end constructSampleRegExPane

	def on_change(self, event):
		self.Freeze()
		self.Layout()
		self.Thaw()


class InsertForm(ScrolledPanel):
	def __init__(self, parent, logger, api, apps, classDefinitions):
		ScrolledPanel.__init__(self, parent)
		self.logger = logger
		self.api = api
		self.apps = apps
		self.appList = []
		self.appNames = []
		self.appData = None
		self.getAppList()
		self.envNames = []
		self.envClass = None
		self.envClassName = None
		self.envAttr = None
		self.locClass = None
		self.locClassName = None
		self.locAttr = None
		self.targetClass = None
		self.targetClassName = None
		self.targetAttr = None
		self.searchClass = None
		self.searchAttr = None
		self.searchResults = []
		self.envPatterns = {}
		self.locPatterns = {}
		self.targetPatterns = []
		self.targetPattern = None
		self.classDefinitions = classDefinitions

		mainBox = wx.BoxSizer(wx.HORIZONTAL)
		mainBox.AddSpacer(60)
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(20)

		## Header/banner text
		label = 'Insert model metadata'
		banner = wx.StaticText(self, label=label)
		f = banner.GetFont()
		f.SetPointSize(f.GetPointSize()+6)
		f.SetWeight(wx.FONTWEIGHT_BOLD)
		banner.SetFont(f)
		vbox.Add(banner, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(20)

		## Description section
		text = 'Complete this form and click Insert to save.'
		description = wx.StaticText(self, label=text)
		font = description.GetFont()
		font.SetPointSize(font.GetPointSize()+2)
		description.SetFont(font)
		vbox.Add(description, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(20)
		panesBox = wx.BoxSizer(wx.HORIZONTAL)
		vbox1 = wx.BoxSizer(wx.VERTICAL)  ## for the left pane
		vbox2 = wx.BoxSizer(wx.VERTICAL)  ## for the right pane

		## Left pane construction... main form for metadata
		self.constructFormPane(vbox1)

		## Right pane construction... helper forms for search validation
		self.constructSearchPane(vbox2)

		## Wrap up the sizer boxes
		panesBox.Add(vbox1, 1, wx.EXPAND)
		panesBox.AddSpacer(40)
		panesBox.Add(vbox2, 1, wx.EXPAND)
		vbox.Add(panesBox, 1, wx.LEFT|wx.EXPAND, 20)
		mainBox.Add(vbox, 1, wx.EXPAND|wx.RIGHT, 60)
		self.SetupScrolling()
		self.SetSizer(mainBox)


	def constructFormPane(self, vbox):
		## Tier 4 Group (top level):
		##   App
		self.constructTier4(vbox)
		## Tier 3 Group:
		##   App -> Environment
		self.constructTier3(vbox)
		## Tier 2 Group:
		##   App -> Environment -> Software
		self.constructTier2(vbox)
		## Tier 1 Group (bottom logical level):
		##   App -> Environment -> Software -> Location
		self.constructTier1(vbox)
		## Logical model object instance:
		##   App -> Environment -> Software -> Location -> ModelObject
		self.constructTier0(vbox)
		## Target 'discoverable' object, used to created the Model object
		self.constructTargetObject(vbox)
		vbox.AddSpacer(20)
		## Insert button
		btn = wx.Button(self, label='Insert')
		self.Bind(wx.EVT_BUTTON, self.onInsert, btn)
		vbox.Add(btn, 0, wx.ALIGN_RIGHT)
		btn.SetDefault()
		btn.SetFocus()

		## end constructFormPane


	def constructTier4(self, vbox):
		"""Tier 4 Group (top level):
		     App
		"""
		app_collapsible_panel = wx.CollapsiblePane(self, label='Application')
		## Add collapsible pane with zero proportion, to the sizer
		vbox.Add(app_collapsible_panel, 0, wx.EXPAND)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		appRefPanel = app_collapsible_panel.GetPane()
		app_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		appPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		appPanelBuffer.AddSpacer(40)
		appPanelSizer = wx.FlexGridSizer(cols=2, vgap=20, hgap=20)
		appPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(appRefPanel, label='Select the Application:')
		self.appChoice = wx.Choice(appRefPanel, wx.ID_ANY, (100, -1), choices=self.appNames)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseApp, self.appChoice)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		appPanelSizer.Add(self.appChoice, 0, wx.EXPAND)

		thisText = wx.StaticText(appRefPanel, label='Application ID:')
		self.appCtrlId = wx.TextCtrl(appRefPanel, wx.ID_ANY, style=wx.TE_READONLY)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		appPanelSizer.Add(self.appCtrlId, 0, wx.EXPAND)

		thisText = wx.StaticText(appRefPanel, label='Short Name:')
		self.appCtrlName = wx.TextCtrl(appRefPanel, wx.ID_ANY, style=wx.TE_READONLY)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		appPanelSizer.Add(self.appCtrlName, 0, wx.EXPAND)
		appPanelBuffer.Add(appPanelSizer, 1, wx.EXPAND)
		appPanelBuffer.AddSpacer(40)

		appRefPanel.SetSizer(appPanelBuffer)
		vbox.AddSpacer(20)
		app_collapsible_panel.Expand()

		## end constructTier4


	def constructTier3(self, vbox):
		"""Tier 3 Group (top level):
		     App -> Environment
		"""
		env_collapsible_panel = wx.CollapsiblePane(self, label='Environment')
		## Add collapsible pane with zero proportion, to the sizer
		vbox.Add(env_collapsible_panel, 0, wx.EXPAND)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		envRefPanel = env_collapsible_panel.GetPane()
		env_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		envPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		envPanelBuffer.AddSpacer(40)
		envPanelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		envPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(envRefPanel, label='Matching Class:')
		classList = list(self.classDefinitions.keys())
		self.envClassChoice = wx.Choice(envRefPanel, wx.ID_ANY, (100, -1), choices=classList)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseEnvClass, self.envClassChoice)
		envPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		envPanelSizer.Add(self.envClassChoice, 0, wx.EXPAND)

		thisText = wx.StaticText(envRefPanel, label='Matching Attribute:')
		self.envAttrChoice = wx.Choice(envRefPanel, wx.ID_ANY, (100, -1), choices=[])
		self.Bind(wx.EVT_CHOICE, self.EvtChooseEnvAttr, self.envAttrChoice)
		envPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		envPanelSizer.Add(self.envAttrChoice, 0, wx.EXPAND)

		## Insert pattern button
		bvSizer = wx.BoxSizer(wx.VERTICAL)
		btn = wx.Button(envRefPanel, label='Add Pattern')
		self.Bind(wx.EVT_BUTTON, self.onEnvPattern, btn)
		btnClear = wx.Button(envRefPanel, label='Clear')
		self.Bind(wx.EVT_BUTTON, self.onEnvClear, btnClear)
		bvSizer.Add(btn, 0, wx.ALIGN_RIGHT)
		bvSizer.AddSpacer(5)
		bvSizer.Add(btnClear, 0, wx.ALIGN_RIGHT)
		envPanelSizer.Add(bvSizer, 0, wx.ALIGN_RIGHT)
		## Patterns panel
		self.envPanel = wx.TextCtrl(envRefPanel, wx.ID_ANY, size=(-1, 75), style=wx.EXPAND|wx.TE_READONLY|wx.TE_MULTILINE)
		envPanelSizer.Add(self.envPanel, 0, wx.EXPAND)

		envPanelBuffer.Add(envPanelSizer, 1, wx.EXPAND)
		envPanelBuffer.AddSpacer(40)

		envRefPanel.SetSizer(envPanelBuffer)
		vbox.AddSpacer(20)

		## end constructTier3


	def constructTier2(self, vbox):
		"""Tier 2 Group:
		     App -> Environment -> Software
		"""
		sw_collapsible_panel = wx.CollapsiblePane(self, label='Logical Group')
		## Add collapsible pane with zero proportion, to the sizer
		vbox.Add(sw_collapsible_panel, 0, wx.EXPAND)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		swRefPanel = sw_collapsible_panel.GetPane()
		sw_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		swPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		swPanelBuffer.AddSpacer(40)
		swPanelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		swPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(swRefPanel, label='Name:')
		self.swCtrlName = wx.TextCtrl(swRefPanel, wx.ID_ANY)
		swPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		swPanelSizer.Add(self.swCtrlName, 0, wx.EXPAND)

		swPanelBuffer.Add(swPanelSizer, 1, wx.EXPAND)
		swPanelBuffer.AddSpacer(40)

		swRefPanel.SetSizer(swPanelBuffer)
		vbox.AddSpacer(20)

		## end constructTier2


	def constructTier1(self, vbox):
		"""Tier 1 Group (bottom logical level):
		     App -> Environment -> Software -> Location
		"""
		loc_collapsible_panel = wx.CollapsiblePane(self, label='Location')
		## Add collapsible pane with zero proportion, to the sizer
		vbox.Add(loc_collapsible_panel, 0, wx.EXPAND)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		locRefPanel = loc_collapsible_panel.GetPane()
		loc_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		locPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		locPanelBuffer.AddSpacer(40)
		locPanelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		locPanelSizer.AddGrowableCol(1)


		thisText = wx.StaticText(locRefPanel, label='Matching Class:')
		classList = list(self.classDefinitions.keys())
		self.locClassChoice = wx.Choice(locRefPanel, wx.ID_ANY, (100, -1), choices=classList)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseLocClass, self.locClassChoice)
		locPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		locPanelSizer.Add(self.locClassChoice, 0, wx.EXPAND)

		thisText = wx.StaticText(locRefPanel, label='Matching Attribute:')
		self.locAttrChoice = wx.Choice(locRefPanel, wx.ID_ANY, (100, -1), choices=[])
		self.Bind(wx.EVT_CHOICE, self.EvtChooseLocAttr, self.locAttrChoice)
		locPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		locPanelSizer.Add(self.locAttrChoice, 0, wx.EXPAND)

		## Insert pattern button
		bvSizer = wx.BoxSizer(wx.VERTICAL)
		btn = wx.Button(locRefPanel, label='Add Pattern')
		self.Bind(wx.EVT_BUTTON, self.onLocPattern, btn)
		btnClear = wx.Button(locRefPanel, label='Clear')
		self.Bind(wx.EVT_BUTTON, self.onLocClear, btnClear)
		bvSizer.Add(btn, 0, wx.ALIGN_RIGHT)
		bvSizer.AddSpacer(5)
		bvSizer.Add(btnClear, 0, wx.ALIGN_RIGHT)
		locPanelSizer.Add(bvSizer, 0, wx.ALIGN_RIGHT)
		## Patterns panel
		self.locPanel = wx.TextCtrl(locRefPanel, wx.ID_ANY, size=(-1, 75), style=wx.EXPAND|wx.TE_READONLY|wx.TE_MULTILINE)
		locPanelSizer.Add(self.locPanel, 0, wx.EXPAND)

		locPanelBuffer.Add(locPanelSizer, 1, wx.EXPAND)
		locPanelBuffer.AddSpacer(40)

		locRefPanel.SetSizer(locPanelBuffer)
		vbox.AddSpacer(20)

		## end constructTier1


	def constructTier0(self, vbox):
		"""Model object:
		     App -> Environment -> Software -> Location -> ModelObject
		"""
		instance_collapsible_panel = wx.CollapsiblePane(self, label='Logical Object')
		## Add collapsible pane with zero proportion, to the sizer
		vbox.Add(instance_collapsible_panel, 0, wx.EXPAND)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		instanceRefPanel = instance_collapsible_panel.GetPane()
		instance_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		instancePanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		instancePanelBuffer.AddSpacer(40)
		instancePanelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		instancePanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(instanceRefPanel, label='Name:')
		self.objectCtrlName = wx.TextCtrl(instanceRefPanel, wx.ID_ANY)
		instancePanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		instancePanelSizer.Add(self.objectCtrlName, 0, wx.EXPAND)

		instancePanelBuffer.Add(instancePanelSizer, 1, wx.EXPAND)
		instancePanelBuffer.AddSpacer(40)

		instanceRefPanel.SetSizer(instancePanelBuffer)
		vbox.AddSpacer(20)

		## end constructTier0


	def constructTargetObject(self, vbox):
		"""Target object, used to created the Model object:
		     App -> Environment -> Software -> Location -> ModelObject
		"""
		target_collapsible_panel = wx.CollapsiblePane(self, label='Discoverable Object')
		## Add collapsible pane with zero proportion, to the sizer
		vbox.Add(target_collapsible_panel, 0, wx.EXPAND)
		## Create a reference to access the pane, used for adding controls since
		## we can't add controls directly into the wx.CollapsiblePane itself.
		targetRefPanel = target_collapsible_panel.GetPane()
		target_collapsible_panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)

		targetPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		targetPanelBuffer.AddSpacer(40)
		targetPanelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		targetPanelSizer.AddGrowableCol(1)


		thisText = wx.StaticText(targetRefPanel, label='Matching Class:')
		classList = list(self.classDefinitions.keys())
		self.targetClassChoice = wx.Choice(targetRefPanel, wx.ID_ANY, (100, -1), choices=classList)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseTargetClass, self.targetClassChoice)
		targetPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		targetPanelSizer.Add(self.targetClassChoice, 0, wx.EXPAND)

		thisText = wx.StaticText(targetRefPanel, label='Matching Attribute:')
		self.targetAttrChoice = wx.Choice(targetRefPanel, wx.ID_ANY, (100, -1), choices=[])
		self.Bind(wx.EVT_CHOICE, self.EvtChooseTargetAttr, self.targetAttrChoice)
		targetPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		targetPanelSizer.Add(self.targetAttrChoice, 0, wx.EXPAND)

		## Insert pattern button
		bvSizer = wx.BoxSizer(wx.VERTICAL)
		btn = wx.Button(targetRefPanel, label='Add Pattern')
		self.Bind(wx.EVT_BUTTON, self.onTargetPattern, btn)
		btnClear = wx.Button(targetRefPanel, label='Clear')
		self.Bind(wx.EVT_BUTTON, self.onTargetClear, btnClear)
		bvSizer.Add(btn, 0, wx.ALIGN_RIGHT)
		bvSizer.AddSpacer(5)
		bvSizer.Add(btnClear, 0, wx.ALIGN_RIGHT)

		targetPanelSizer.Add(bvSizer, 0, wx.ALIGN_RIGHT)
		## Patterns panel
		self.targetPanel = wx.TextCtrl(targetRefPanel, wx.ID_ANY, size=(-1, 75), style=wx.EXPAND|wx.TE_READONLY|wx.TE_MULTILINE)
		targetPanelSizer.Add(self.targetPanel, 0, wx.EXPAND)

		targetPanelBuffer.Add(targetPanelSizer, 1, wx.EXPAND)
		targetPanelBuffer.AddSpacer(40)

		targetRefPanel.SetSizer(targetPanelBuffer)
		vbox.AddSpacer(20)

		## end constructTargetObject


	def constructSearchPane(self, vbox):
		"""Search Pane on right"""
		vbox.AddSpacer(8)
		self.searchPanelStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Search Database')
		topBorder, otherBorder = self.searchPanelStaticBox.GetBordersForSizer()
		staticSizer = wx.BoxSizer()
		staticSizer.AddSpacer(topBorder + 5)
		searchPanelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		searchPanelSizer.AddGrowableCol(1)
		searchPanelSizer.AddSpacer(1)
		searchPanelSizer.AddSpacer(1)

		thisText = wx.StaticText(self.searchPanelStaticBox, label='Matching Class:')
		classList = list(self.classDefinitions.keys())
		self.searchClassChoice = wx.Choice(self.searchPanelStaticBox, wx.ID_ANY, (100, -1), choices=classList)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseSearchClass, self.searchClassChoice)
		searchPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		searchPanelSizer.Add(self.searchClassChoice, 0, wx.EXPAND)

		thisText = wx.StaticText(self.searchPanelStaticBox, label='Matching Attribute:')
		self.searchAttrChoice = wx.Choice(self.searchPanelStaticBox, wx.ID_ANY, (100, -1), choices=[])
		self.Bind(wx.EVT_CHOICE, self.EvtChooseSearchAttr, self.searchAttrChoice)
		searchPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		searchPanelSizer.Add(self.searchAttrChoice, 0, wx.EXPAND)

		thisText = wx.StaticText(self.searchPanelStaticBox, label='Target Match Pattern:')
		self.searchCtrlPattern = wx.TextCtrl(self.searchPanelStaticBox, wx.ID_ANY)
		searchPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		searchPanelSizer.Add(self.searchCtrlPattern, 0, wx.EXPAND)

		## Search button
		btn = wx.Button(self.searchPanelStaticBox, label='Search')
		self.Bind(wx.EVT_BUTTON, self.onSearch, btn)
		searchPanelSizer.AddSpacer(1)
		searchPanelSizer.Add(btn, 0, wx.LEFT|wx.RIGHT, 20)

		thisText = wx.StaticText(self.searchPanelStaticBox, label='Search Results:')
		self.searchResultsChoice = wx.Choice(self.searchPanelStaticBox, wx.ID_ANY, size=(100, -1), choices=[])
		self.Bind(wx.EVT_CHOICE, self.EvtChooseSearchResult, self.searchResultsChoice)
		searchPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		searchPanelSizer.Add(self.searchResultsChoice, 1, wx.EXPAND)

		## Unique checkbox
		self.uniqueCheckBox = wx.CheckBox(self.searchPanelStaticBox, wx.ID_ANY, 'Unique results')
		self.Bind(wx.EVT_CHECKBOX, self.EvtUniqueSearchResults, self.uniqueCheckBox)
		searchPanelSizer.AddSpacer(1)
		searchPanelSizer.Add(self.uniqueCheckBox, 0, wx.LEFT|wx.RIGHT, 20)
		searchPanelSizer.AddSpacer(10)

		staticSizer.Add(searchPanelSizer, 1, wx.ALL, 10)
		self.searchPanelStaticBox.SetSizer(staticSizer)
		vbox.Add(self.searchPanelStaticBox, 0, wx.EXPAND)

		## end constructSearchPane


	def on_change(self, event):
		self.Freeze()
		self.Layout()
		self.FitInside()
		self.Thaw()

	def getAppList(self):
		unsortedList = []
		for appId,appDict in self.apps.items():
			unsortedList.append(appDict)
		## After creating a list of dicts, now sort the list by the 'name' key
		self.appData = sorted(unsortedList, key=itemgetter('name'))
		## Now get the list of names from the positional dicts in our list; all
		## this is so that when the user selects a positional name from a list,
		## we have the handle of it's positional dictionary value
		for entry in self.appData:
			self.appNames.append(entry.get('name', 'NA'))

	def EvtChooseApp(self, event):
		place = event.GetInt()
		selection = event.GetString()
		self.logger.debug('EvtChooseApp: selection: {}'.format(selection))
		self.app = self.appData[place]
		self.appCtrlId.SetValue(self.app.get('element_id'))
		self.appCtrlName.SetValue(self.app.get('short_name'))

	def EvtChooseEnvClass(self, event):
		self.envClassName = event.GetString()
		self.envClass = self.classDefinitions.get(self.envClassName, {}).get('class_name')
		envClassAttrList = self.classDefinitions.get(self.envClassName, {}).get('attrs', [])
		self.logger.debug('EvtChooseEnvClass: attrList: {}'.format(envClassAttrList))
		self.envAttrChoice.Clear()
		self.envAttrChoice.AppendItems(envClassAttrList)

	def EvtChooseEnvAttr(self, event):
		self.envAttr = event.GetString()
		self.logger.debug('EvtChooseEnvAttr: {}'.format(self.envAttr))

	def EvtChooseLocClass(self, event):
		self.locClassName = event.GetString()
		self.locClass = self.classDefinitions.get(self.locClassName, {}).get('class_name')
		locClassAttrList = self.classDefinitions.get(self.locClassName, {}).get('attrs', [])
		self.logger.debug('EvtChooseEnvClass: attrList: {}'.format(locClassAttrList))
		self.locAttrChoice.Clear()
		self.locAttrChoice.AppendItems(locClassAttrList)

	def EvtChooseLocAttr(self, event):
		self.locAttr = event.GetString()
		self.logger.debug('EvtChooseEnvAttr: {}'.format(self.locAttr))

	def EvtChooseTargetClass(self, event):
		self.targetClassName = event.GetString()
		self.targetClass = self.classDefinitions.get(self.targetClassName, {}).get('class_name')
		targetClassAttrList = self.classDefinitions.get(self.targetClassName, {}).get('attrs', [])
		self.logger.debug('EvtChooseTargetClass: attrList: {}'.format(targetClassAttrList))
		self.targetAttrChoice.Clear()
		self.targetAttrChoice.AppendItems(targetClassAttrList)

	def EvtChooseTargetAttr(self, event):
		self.targetAttr = event.GetString()
		self.logger.debug('EvtChooseTargetAttr: {}'.format(self.targetAttr))

	def EvtChooseSearchClass(self, event):
		self.searchClass = event.GetString()
		searchClassAttrList = self.classDefinitions.get(self.searchClass, {}).get('attrs', [])
		self.logger.debug('EvtChooseSearchClass: attrList: {}'.format(searchClassAttrList))
		self.searchAttrChoice.Clear()
		self.searchAttrChoice.AppendItems(searchClassAttrList)

	def EvtChooseSearchAttr(self, event):
		self.searchAttr = event.GetString()
		self.logger.debug('EvtChooseSearchAttr: {}'.format(self.searchAttr))

	def EvtChooseSearchResult(self, event):
		pass

	def EvtUniqueSearchResults(self, event):
		wx.BeginBusyCursor()
		#self.searchResultsChoice.GetSelection()
		self.searchResultsChoice.Clear()
		if self.uniqueCheckBox.IsChecked():
			## Set to a filtered/unique set
			self.searchResultsChoice.AppendItems(sorted(list(set(self.searchResults))))
		else:
			## Set to the original raw result (perhaps with dups)
			self.searchResultsChoice.AppendItems(self.searchResults)
		self.searchResultsChoice.SetSelection(0)
		wx.EndBusyCursor()

	def onEnvPattern(self, event):
		dlgMatchPattern = CreateMatchDialog(self, title='Environment Match Pattern', log=self.logger)
		dlgMatchPattern.CenterOnScreen()
		value = dlgMatchPattern.ShowModal()
		## Pull results out before destroying the window
		thisName = dlgMatchPattern.name.GetValue()
		thisRegEx = dlgMatchPattern.regEx.GetValue()
		self.logger.debug('onEnvPattern: retrieving results. name: {}  regEx: {}'.format(thisName, thisRegEx))
		dlgMatchPattern.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('onEnvPattern: value == OK')
			if ((thisName is not None and thisName != '') and
				(thisRegEx is not None and thisRegEx != '')):
				self.envPatterns[thisName] = thisRegEx
				self.envPanel.Clear()
				for key,value in self.envPatterns.items():
					self.envPanel.WriteText('{} : {}\n'.format(key, value))
		else:
			self.logger.debug('onEnvPattern: value == CANCEL')

	def onEnvClear(self, event):
		self.envPatterns.clear()
		self.envPanel.Clear()

	def onLocPattern(self, event):
		dlgMatchPattern = CreateMatchDialog(self, title='Location Match Pattern', log=self.logger)
		dlgMatchPattern.CenterOnScreen()
		value = dlgMatchPattern.ShowModal()
		## Pull results out before destroying the window
		thisName = dlgMatchPattern.name.GetValue()
		thisRegEx = dlgMatchPattern.regEx.GetValue()
		self.logger.debug('onLocPattern: retrieving results. name: {}  regEx: {}'.format(thisName, thisRegEx))
		dlgMatchPattern.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('onLocPattern: value == OK')
			if ((thisName is not None and thisName != '') and
				(thisRegEx is not None and thisRegEx != '')):
				self.locPatterns[thisName] = thisRegEx
				self.locPanel.Clear()
				for key,value in self.locPatterns.items():
					self.locPanel.WriteText('{} : {}\n'.format(key, value))
		else:
			self.logger.debug('onLocPattern: value == CANCEL')

	def onLocClear(self, event):
		self.locPatterns.clear()
		self.locPanel.Clear()

	def onTargetPattern(self, event):
		dlgMatchPattern = CreateMatchSimpleDialog(self, title='Target Match Pattern', log=self.logger)
		dlgMatchPattern.CenterOnScreen()
		value = dlgMatchPattern.ShowModal()
		thisRegEx = dlgMatchPattern.regEx.GetValue()
		self.logger.debug('onTargetPattern: retrieving regEx: {}'.format(thisRegEx))
		dlgMatchPattern.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('onTargetPattern: value == OK')
			if (thisRegEx is not None and thisRegEx != ''):
				self.targetPatterns.append(thisRegEx)
				self.targetPanel.Clear()
				for value in self.targetPatterns:
					self.targetPanel.WriteText('{}\n'.format(value))
		else:
			self.logger.debug('onTargetPattern: value == CANCEL')

	def onTargetClear(self, event):
		self.targetPatterns.clear()
		self.targetPanel.Clear()

	def onSearch(self, event):
		searchPattern = self.searchCtrlPattern.GetValue()
		## Construct the corresponding API query
		className = self.classDefinitions.get(self.searchClass, {}).get('class_name')
		payload = {
			"objects": [{
				"class_name": className,
				"attributes": ["caption", self.searchAttr],
				"minimum": "1",
				"maximum": "",
				"filter": [{
					"condition": {
						"attribute": self.searchAttr,
						"operator": "regex",
						"value": searchPattern
					}
				}],
				"linchpin": True
			}],
			"links": []
		}
		wx.BeginBusyCursor()
		(responseCode, responseAsJson) = self.api.taskQuery(payload)
		wx.EndBusyCursor()
		if responseCode == 200:
			self.logger.debug('onSearch: parse results: {}'.format(responseAsJson))
			wx.BeginBusyCursor()
			results = []
			for entry in responseAsJson.get('objects', []):
				try:
					attributes = entry.get('data')
					value = attributes.get(self.searchAttr)
					caption = attributes.get('caption')
					self.logger.debug('  onSearch: matched value {} ... associated object\'s caption: {}'.format(value, caption))
					if (value is None or value == 'None'):
						continue
					results.append(value)
				except:
					stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
					self.logger.error('Failure in getSearchResults: {}'.format(stacktrace))
			self.searchResults = sorted(results)
			self.EvtUniqueSearchResults(event)
			wx.EndBusyCursor()
		else:
			errorMsg = json.dumps(responseAsJson)
			with suppress(Exception):
				errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
			dlgResult = wx.MessageDialog(self, errorMsg, 'Object insert error', wx.OK|wx.ICON_ERROR)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()

		## end onSearch

	def onInsert(self, event=None):
		self.logger.debug('Attempting to construct object for manual insert')
		attributes = {}
		## Tier 4 Group (top level):
		##   App
		self.logger.info('='*80)
		self.logger.info('Tier 4 : App')
		self.logger.info('-'*40)
		attributes['tier4_name'] = self.app.get('name')[:256]
		attributes['tier4_alias'] = self.app.get('short_name')[:32]
		attributes['tier4_id'] = self.app.get('element_id')[:32]
		attributes['tier4_create_class'] = 'BusinessApplication'
		self.logger.info('name: {}'.format(self.app.get('name')))
		self.logger.info('element_id: {}'.format(self.app.get('element_id')))
		self.logger.info('short_name: {}'.format(self.app.get('short_name')))

		## Tier 3 Group:
		##   App -> Environment
		self.logger.info('='*80)
		self.logger.info('Tier 3 : App -> Environment')
		self.logger.info('-'*40)
		self.logger.info('class: {}'.format(self.envClass))
		self.logger.info('attr : {}'.format(self.envAttr))
		self.logger.info('patterns: {}'.format(self.envPatterns))
		attributes['tier3_match_class'] = self.envClass
		attributes['tier3_match_attribute'] = self.envAttr
		attributes['tier3_match_patterns'] = self.envPatterns
		attributes['tier3_create_class'] = 'EnvironmentGroup'

		## Tier 2 Group:
		##   App -> Environment -> Software
		self.logger.info('='*80)
		self.logger.info('Tier 2 : App -> Environment -> Software')
		self.logger.info('-'*40)
		self.logger.info('name: {}'.format(self.swCtrlName.GetValue()))
		attributes['tier2_name'] = self.swCtrlName.GetValue()
		attributes['tier2_create_class'] = 'SoftwareGroup'

		## Tier 1 Group (bottom logical level):
		##   App -> Environment -> Software -> Location
		self.logger.info('='*80)
		self.logger.info('Tier 1 : App -> Environment -> Software -> Location')
		self.logger.info('-'*40)
		self.logger.info('class: {}'.format(self.locClass))
		self.logger.info('attr : {}'.format(self.locAttr))
		self.logger.info('patterns: {}'.format(self.locPatterns))
		attributes['tier1_match_class'] = self.locClass
		attributes['tier1_match_attribute'] = self.locAttr
		attributes['tier1_match_patterns'] = self.locPatterns
		attributes['tier1_create_class'] = 'LocationGroup'

		## Model object:
		##   App -> Environment -> Software -> Location -> ModelObject
		self.logger.info('='*80)
		self.logger.info('Tier 0 :App -> Environment -> Software -> Location -> ModelObject')
		self.logger.info('-'*40)
		self.logger.info('name: {}'.format(self.objectCtrlName.GetValue()))
		attributes['model_object_name'] = self.objectCtrlName.GetValue()[:512]

		## Target object, used to created the Model object:
		self.logger.info('='*80)
		self.logger.info('Target object')
		self.logger.info('-'*40)
		self.logger.info('class: {}'.format(self.targetClass))
		self.logger.info('attr : {}'.format(self.targetAttr))
		self.logger.info('pattern: {}'.format(self.targetPatterns))
		attributes['target_match_class'] = self.targetClass
		attributes['target_match_attribute'] = self.targetAttr
		attributes['target_match_patterns'] = self.targetPatterns

		self.logger.info('attributes to insert: {}'.format(attributes))
		self.insertMetaData(attributes)

		## end onInsert
		return

	def insertMetaData(self, attributes):
		self.logger.debug('insertMetaData: value == OK')
		wx.BeginBusyCursor()
		content = {}
		content['source'] = 'admin console'
		content['data'] = attributes
		(responseCode, responseAsJson) = self.api.postResource('data/ModelMetaData', {'content': content})
		wx.EndBusyCursor()
		if responseCode == 200:
			dlgResult = wx.MessageDialog(self, 'SUCCESS', 'Inserted MetaData', wx.OK|wx.ICON_INFORMATION)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()
			self.logger.debug('insertMetaData: metadata added.')
		else:
			errorMsg = json.dumps(responseAsJson)
			with suppress(Exception):
				errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
			dlgResult = wx.MessageDialog(self, errorMsg, 'Insert failed', wx.OK|wx.ICON_ERROR)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()



class Main():
	def __init__(self, thisPanel, log, api):
		self.logger = log
		self.api = api
		self.apps = {}
		self.getApps()
		self.getObjectDefinitions()

		thisPanel.Freeze()
		insertForm = InsertForm(thisPanel, self.logger, self.api, self.apps, self.classDefinitions)

		mainBox = wx.BoxSizer()
		mainBox.Add(insertForm, 1, wx.EXPAND)
		thisPanel.Layout()
		thisPanel.SetSizer(mainBox)
		thisPanel.Show()
		thisPanel.SendSizeEvent()
		thisPanel.Thaw()
		wx.EndBusyCursor()

	def getApps(self):
		apiResults = self.api.getResource('data/BusinessApplication')
		for result in apiResults.get('objects', []):
			self.logger.debug('--> App found: {}'.format(result))
			appId = result.get('identifier')
			if appId is not None:
				self.apps[appId] = result.get('data', {})

	def getObjectDefinitions(self):
		self.classDefinitions = {
			'Node': {
				'class_name': 'Node',
				'attrs': ['hostname', 'domain', 'vendor', 'platform', 'version', 'hardware_is_virtual', 'hardware_provider']
			},
			'Linux': {
				'class_name': 'Linux',
				'attrs': ['hostname', 'domain', 'vendor', 'platform', 'version', 'hardware_is_virtual', 'hardware_provider']
			},
			'Windows': {
				'class_name': 'Windows',
				'attrs': ['hostname', 'domain', 'vendor', 'platform', 'version', 'hardware_is_virtual', 'hardware_provider']
			},
			'IP Address': {
				'class_name': 'IpAddress',
				'attrs': ['address', 'realm']
			},
			'TCP/IP Port': {
				'class_name': 'TcpIpPort',
				'attrs': ['name', 'ip', 'port_type', 'label']
			},
			'DNS Record': {
				'class_name': 'NameRecord',
				'attrs': ['name', 'value', 'description']
			},
			'Process': {
				'class_name': 'ProcessFingerprint',
				'attrs': ['name', 'process_hierarchy', 'process_owner', 'process_args', 'path_from_process', 'path_from_filesystem', 'path_from_analysis', 'path_working_dir']
			},
			'Software': {
				'class_name': 'SoftwareFingerprint',
				'attrs': ['name', 'software_id', 'software_info', 'vendor']
			}
		}
