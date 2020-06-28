"""Pane for Admin Console ribbon destination: Data->Models->Delete MetaData."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
from wx.lib.scrolledpanel import ScrolledPanel
from operator import itemgetter


class MyEvent(wx.PyCommandEvent):
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)
		self.myVal = None


class RawPanel(wx.Panel):
	def __init__(self, parent, log):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, style=wx.EXPAND|wx.CLIP_CHILDREN, name="rawPanel")
		self.Layout()
	def Freeze(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(RawPanel, self).Freeze()
	def Thaw(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(RawPanel, self).Thaw()


class UpdateForm(ScrolledPanel):
	def __init__(self, parent, logger, api, apps, appsWithMetaData, metadata, classDefinitions):
		ScrolledPanel.__init__(self, parent)
		self.logger = logger
		self.api = api
		self.apps = apps
		self.appsWithMetaData = appsWithMetaData
		self.metadata = metadata
		self.appList = []
		self.appNames = []
		self.appData = None
		self.metaDataList = []
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
		label = 'Delete model metadata'
		banner = wx.StaticText(self, label=label)
		f = banner.GetFont()
		f.SetPointSize(f.GetPointSize()+6)
		f.SetWeight(wx.FONTWEIGHT_BOLD)
		banner.SetFont(f)
		vbox.Add(banner, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(20)

		## Description section
		text = 'Select the Application and metadata object, and click Delete to remove.'
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
		## App and metadata selection
		self.constructAppSection(vbox)
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
		btn = wx.Button(self, label='Delete')
		self.Bind(wx.EVT_BUTTON, self.onDelete, btn)
		vbox.Add(btn, 0, wx.ALIGN_RIGHT)
		btn.SetDefault()
		btn.SetFocus()

		## end constructFormPane


	def constructAppSection(self, vbox):
		"""Tier 4 Group (top level):
		     App
		"""
		self.appStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Application')
		topBorder, otherBorder = self.appStaticBox.GetBordersForSizer()

		appPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		appPanelBuffer.AddSpacer(40)
		appPanelSizer = wx.FlexGridSizer(cols=2, vgap=10, hgap=20)
		appPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(self.appStaticBox, label='Select Application:')
		self.appChoice = wx.Choice(self.appStaticBox, wx.ID_ANY, (100, -1), choices=self.appNames)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseApp, self.appChoice)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, (topBorder+5))
		appPanelSizer.Add(self.appChoice, 0, wx.EXPAND|wx.TOP, (topBorder+5))

		thisText = wx.StaticText(self.appStaticBox, label='Application ID:')
		self.appCtrlId = wx.TextCtrl(self.appStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		appPanelSizer.Add(self.appCtrlId, 0, wx.EXPAND)

		thisText = wx.StaticText(self.appStaticBox, label='Short Name:')
		self.appCtrlName = wx.TextCtrl(self.appStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		appPanelSizer.Add(self.appCtrlName, 0, wx.EXPAND)

		thisText = wx.StaticText(self.appStaticBox, label='Select MetaData:')
		self.mdChoice = wx.Choice(self.appStaticBox, wx.ID_ANY, (100, -1), choices=[])
		self.Bind(wx.EVT_CHOICE, self.EvtChooseMetaData, self.mdChoice)
		appPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, (topBorder))
		appPanelSizer.Add(self.mdChoice, 0, wx.EXPAND|wx.BOTTOM, (topBorder))

		appPanelBuffer.Add(appPanelSizer, 1, wx.EXPAND)
		appPanelBuffer.AddSpacer(40)

		self.appStaticBox.SetSizer(appPanelBuffer)
		vbox.Add(self.appStaticBox, 0, wx.EXPAND)
		vbox.AddSpacer(20)

		## end constructAppSection


	def constructTier3(self, vbox):
		"""Tier 3 Group (top level):
		     App -> Environment
		"""
		self.envStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Environment')
		topBorder, otherBorder = self.envStaticBox.GetBordersForSizer()

		envPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		envPanelBuffer.AddSpacer(40)
		envPanelSizer = wx.FlexGridSizer(cols=2, vgap=10, hgap=20)
		envPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(self.envStaticBox, label='Matching Class:')
		self.envObjectClass = wx.TextCtrl(self.envStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		envPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, (topBorder+5))
		envPanelSizer.Add(self.envObjectClass, 0, wx.EXPAND|wx.TOP, (topBorder+5))

		thisText = wx.StaticText(self.envStaticBox, label='Matching Attribute:')
		self.envObjectAttr = wx.TextCtrl(self.envStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		envPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		envPanelSizer.Add(self.envObjectAttr, 0, wx.EXPAND)

		thisText = wx.StaticText(self.envStaticBox, label='RegEx Patterns:')
		self.envObjectPatterns = wx.TextCtrl(self.envStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		envPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, (topBorder))
		envPanelSizer.Add(self.envObjectPatterns, 0, wx.EXPAND|wx.BOTTOM, (topBorder))

		envPanelBuffer.Add(envPanelSizer, 1, wx.EXPAND)
		envPanelBuffer.AddSpacer(40)

		self.envStaticBox.SetSizer(envPanelBuffer)
		vbox.Add(self.envStaticBox, 0, wx.EXPAND)
		vbox.AddSpacer(20)

		## end constructTier3


	def constructTier2(self, vbox):
		"""Tier 2 Group:
		     App -> Environment -> Software
		"""
		self.groupStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Logical Group')
		topBorder, otherBorder = self.groupStaticBox.GetBordersForSizer()
		groupPanelBuffer = wx.BoxSizer(wx.VERTICAL)
		groupPanelBuffer.AddSpacer(topBorder)

		self.groupCtrlName = wx.TextCtrl(self.groupStaticBox, wx.ID_ANY, style=wx.TE_READONLY)

		groupPanelBuffer.Add(self.groupCtrlName, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		groupPanelBuffer.AddSpacer(5)
		self.groupStaticBox.SetSizer(groupPanelBuffer)
		vbox.Add(self.groupStaticBox, 0, wx.EXPAND)
		vbox.AddSpacer(20)

		## end constructTier2


	def constructTier1(self, vbox):
		"""Tier 1 Group (bottom logical level):
		     App -> Environment -> Software -> Location
		"""
		self.locStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Location')
		topBorder, otherBorder = self.locStaticBox.GetBordersForSizer()

		locPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		locPanelBuffer.AddSpacer(40)
		locPanelSizer = wx.FlexGridSizer(cols=2, vgap=10, hgap=20)
		locPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(self.locStaticBox, label='Matching Class:')
		self.locObjectClass = wx.TextCtrl(self.locStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		locPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, (topBorder+5))
		locPanelSizer.Add(self.locObjectClass, 0, wx.EXPAND|wx.TOP, (topBorder+5))

		thisText = wx.StaticText(self.locStaticBox, label='Matching Attribute:')
		self.locObjectAttr = wx.TextCtrl(self.locStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		locPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		locPanelSizer.Add(self.locObjectAttr, 0, wx.EXPAND)

		thisText = wx.StaticText(self.locStaticBox, label='RegEx Patterns:')
		self.locObjectPatterns = wx.TextCtrl(self.locStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		locPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, (topBorder))
		locPanelSizer.Add(self.locObjectPatterns, 0, wx.EXPAND|wx.BOTTOM, (topBorder))

		locPanelBuffer.Add(locPanelSizer, 1, wx.EXPAND)
		locPanelBuffer.AddSpacer(40)

		self.locStaticBox.SetSizer(locPanelBuffer)
		vbox.Add(self.locStaticBox, 0, wx.EXPAND)
		vbox.AddSpacer(20)

		## end constructTier1


	def constructTier0(self, vbox):
		"""Model object:
		     App -> Environment -> Software -> Location -> ModelObject
		"""
		self.objectStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Logical Object')
		topBorder, otherBorder = self.objectStaticBox.GetBordersForSizer()
		objectPanelBuffer = wx.BoxSizer(wx.VERTICAL)
		objectPanelBuffer.AddSpacer(topBorder)

		self.objectCtrlName = wx.TextCtrl(self.objectStaticBox, wx.ID_ANY, style=wx.TE_READONLY)

		objectPanelBuffer.Add(self.objectCtrlName, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		objectPanelBuffer.AddSpacer(5)
		self.objectStaticBox.SetSizer(objectPanelBuffer)
		vbox.Add(self.objectStaticBox, 0, wx.EXPAND)
		vbox.AddSpacer(20)

		## end constructTier0


	def constructTargetObject(self, vbox):
		"""Target object, used to created the Model object:
		     App -> Environment -> Software -> Location -> ModelObject
		"""
		self.targetStaticBox = wx.StaticBox(self, wx.ID_ANY, 'Discoverable Object')
		topBorder, otherBorder = self.targetStaticBox.GetBordersForSizer()

		targetPanelBuffer = wx.BoxSizer(wx.HORIZONTAL)
		targetPanelBuffer.AddSpacer(40)
		targetPanelSizer = wx.FlexGridSizer(cols=2, vgap=10, hgap=20)
		targetPanelSizer.AddGrowableCol(1)

		thisText = wx.StaticText(self.targetStaticBox, label='Matching Class:')
		self.discoverableObjectClass = wx.TextCtrl(self.targetStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		targetPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, (topBorder+5))
		targetPanelSizer.Add(self.discoverableObjectClass, 0, wx.EXPAND|wx.TOP, (topBorder+5))

		thisText = wx.StaticText(self.targetStaticBox, label='Matching Attribute:')
		self.discoverableObjectAttr = wx.TextCtrl(self.targetStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		targetPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		targetPanelSizer.Add(self.discoverableObjectAttr, 0, wx.EXPAND)

		thisText = wx.StaticText(self.targetStaticBox, label='RegEx Patterns:')
		self.discoverableObjectPatterns = wx.TextCtrl(self.targetStaticBox, wx.ID_ANY, style=wx.TE_READONLY)
		targetPanelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, (topBorder))
		targetPanelSizer.Add(self.discoverableObjectPatterns, 0, wx.EXPAND|wx.BOTTOM, (topBorder))

		targetPanelBuffer.Add(targetPanelSizer, 1, wx.EXPAND)
		targetPanelBuffer.AddSpacer(40)

		self.targetStaticBox.SetSizer(targetPanelBuffer)
		vbox.Add(self.targetStaticBox, 0, wx.EXPAND)
		vbox.AddSpacer(20)

		## end constructTargetObject

	def constructSearchPane(self, vbox):
		"""Filler pane on right, so the delete page is similar to insert/update"""
		thisPanel = RawPanel(self, wx.ID_ANY)
		vbox.Add(thisPanel, 0, wx.EXPAND)

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
		self.metaDataList = self.appsWithMetaData.get(selection, [])
		self.logger.debug('EvtChooseApp: metaDataList: {}'.format(self.metaDataList))
		self.mdChoice.Clear()
		self.mdChoice.AppendItems(self.metaDataList)
		self.mdChoice.SetSelection(0)
		evt = MyEvent(wx.NewEventType(), 0)
		self.EvtChooseMetaData(evt)

	def EvtChooseMetaData(self, event):
		place = event.GetInt()
		selection = event.GetString()
		self.logger.debug('EvtChooseMetaData: selection: {}'.format(selection))
		if len(self.metaDataList) > 0:
			self.metaDataId = self.metaDataList[place]
			self.metaData = self.metadata[self.metaDataId]
		else:
			self.metaData = {}
		self.populateFormWithMetaData()

	def populateFormWithMetaData(self):
		## Populate metadata attributes into the form sections
		## Tier 3 Group:
		##   App -> Environment
		self.envClass = self.metaData.get('tier3_match_class', '')
		self.envClassName = ''
		for entry,val in self.classDefinitions.items():
			if val.get('class_name') == self.envClass:
				self.envClassName = entry
				break
		self.envObjectClass.SetValue(self.envClassName)
		self.envAttr = self.metaData.get('tier3_match_attribute', '')
		self.envObjectAttr.SetValue(self.envAttr)
		self.envPatterns = self.metaData.get('tier3_match_patterns', '')
		self.envObjectPatterns.SetValue(str(self.envPatterns))
		## Tier 2 Group:
		##   App -> Environment -> Software
		self.groupCtrlName.SetValue(self.metaData.get('tier2_name', ''))
		## Tier 1 Group (bottom logical level):
		##   App -> Environment -> Software -> Location
		self.locClass = self.metaData.get('tier1_match_class', '')
		self.locClassName = ''
		for entry,val in self.classDefinitions.items():
			if val.get('class_name') == self.locClass:
				self.locClassName = entry
				break
		self.locObjectClass.SetValue(self.locClassName)
		self.locAttr = self.metaData.get('tier1_match_attribute', '')
		self.locObjectAttr.SetValue(self.locAttr)
		self.locPatterns = self.metaData.get('tier1_match_patterns', '')
		self.locObjectPatterns.SetValue(str(self.locPatterns))
		## Model object:
		##   App -> Environment -> Software -> Location -> ModelObject
		self.objectCtrlName.SetValue(self.metaData.get('model_object_name', ''))
		## Target object, used to created the Model object:
		self.targetClass = self.metaData.get('target_match_class', '')
		self.targetClassName = ''
		for entry,val in self.classDefinitions.items():
			if val.get('class_name') == self.targetClass:
				self.targetClassName = entry
				break
		self.discoverableObjectClass.SetValue(self.targetClassName)
		self.targetAttr = self.metaData.get('target_match_class', '')
		self.discoverableObjectAttr.SetValue(self.targetAttr)
		self.targetPatterns = self.metaData.get('target_match_patterns', '')
		self.discoverableObjectPatterns.SetValue(str(self.targetPatterns))


	def onDelete(self, event=None):
		self.logger.debug('onDelete: refId: {}'.format(self.metaDataId))
		dlgDelete = wx.MessageDialog(self,
									 'Are you sure you want to delete this MetaData entry?',
									 'Delete MetaData {}'.format(self.metaDataId),
									 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('onDelete: value == OK')

			self.logger.debug('onDelete: Attempting to remove metadata id: {}'.format(self.metaDataId))
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.deleteResource('data/ModelMetaData/{}'.format(self.metaDataId))
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self, 'SUCCESS', 'Deleted MetaData', wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('onDelete: metadata removed.')
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.parentPanel, errorMsg, 'Delete failed', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()

		## end onDelete
		return


class Main():
	def __init__(self, thisPanel, log, api):
		self.logger = log
		self.api = api
		self.apps = {}
		self.getApps()
		self.metadata = {}
		self.appsWithMetaData = {}
		self.getMetaData()
		self.getObjectDefinitions()
		self.logger.debug('MAIN: appsWithMetaData: {}'.format(self.appsWithMetaData))

		thisPanel.Freeze()
		form = UpdateForm(thisPanel, self.logger, self.api, self.apps, self.appsWithMetaData, self.metadata, self.classDefinitions)

		mainBox = wx.BoxSizer()
		mainBox.Add(form, 1, wx.EXPAND)
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

	def getMetaData(self):
		apiResults = self.api.getResource('data/ModelMetaData')
		for result in apiResults.get('objects', []):
			metaDataId = result.get('identifier')
			if metaDataId is not None:
				metaData = result.get('data', {})
				self.logger.debug('--> MetaData found: {}'.format(metaData))
				self.metadata[metaDataId] = metaData
				appName = metaData.get('tier4_name')
				self.logger.debug('   --> name found: {}'.format(appName))
				if appName not in self.appsWithMetaData:
					self.appsWithMetaData[appName] = []
				self.appsWithMetaData[appName].append(metaDataId)

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
