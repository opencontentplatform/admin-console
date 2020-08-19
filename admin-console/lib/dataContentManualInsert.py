"""Pane for Admin Console ribbon destination: Data->Content->Insert Object."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.agw.genericmessagedialog as GMD
import wx.html2
from wx.lib.pubsub import pub
## pip install pysubpub
#from subpub import sub, pub


class Page2(wx.Panel):
	def __init__(self, parent, logger, onNextPage, onBackPage, page1, data, api):
		wx.Panel.__init__(self, parent)
		self.logger = logger
		self.data = data
		self.api = api
		self.onNextPage = onNextPage
		self.onBackPage = onBackPage
		#self.realms = self.data['realms']
		self.SetBackgroundColour('white')
		self.ctrlTracker = {}
		self.boolValue = True
		self.listValue = None
		self.objectType = self.data['objectType']
		self.objectDefinition = self.data['objects'][self.objectType]

		## pubsub stuff
		pub.subscribe(self.__onObjectSelection, 'object.definition')

	def __onObjectSelection(self, objType, objDef=None):
		self.logger.debug('Page2: __onObjectSelection: received objType {} and objDef {}'.format(objType, objDef))
		self.objectType = objType
		self.objectDefinition = objDef
		if objDef is None:
			self.objectDefinition = {}

		mainBox = wx.BoxSizer(wx.HORIZONTAL)
		mainBox.AddSpacer(60)
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(20)

		self.logger.debug(' Page2 objectType from page1: {}'.format(self.objectType))
		label = 'Manually insert an object'
		## Let's be grammatically correct
		if self.objectType in ['IpAddress']:
			label = 'Manually insert an {} object'.format(self.objectType)
		else:
			label = 'Manually insert a {} object'.format(self.objectType)

		banner = wx.StaticText(self, label=label)
		f = banner.GetFont()
		f.SetPointSize(f.GetPointSize()+6)
		f.SetWeight(wx.FONTWEIGHT_BOLD)
		banner.SetFont(f)
		vbox.Add(banner, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(20)

		text = 'Complete this form and click Next to insert the object.'
		description = wx.StaticText(self, label=text)
		font = description.GetFont()
		font.SetPointSize(font.GetPointSize()+2)
		description.SetFont(font)
		vbox.Add(description, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(20)

		bufferSizer = wx.BoxSizer(wx.HORIZONTAL)
		bufferSizer.AddSpacer(20)

		panelSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=20)
		panelSizer.AddGrowableCol(1)

		for attrName,attrType in self.objectDefinition.items():
			self.logger.debug(' ... working on {} : {} : {}'.format(attrName, attrType, type(attrType)))
			thisText = wx.StaticText(self, -1, '{} :'.format(attrName))
			thisText.SetFont(font)
			thisControl = None
			if isinstance(attrType, str):
				self.logger.debug('    ... found string')
				thisControl = wx.TextCtrl(self, wx.ID_ANY, "")
				thisControl.SetFont(font)
			elif isinstance(attrType, bool):
				self.logger.debug('    ... found boolean')
				thisControl = wx.Choice(self, wx.ID_ANY, (120, 50), choices=['True', 'False'])
				thisControl.SetSelection(0)
				thisControl.SetFont(font)
				self.boolValue = True
				self.Bind(wx.EVT_CHOICE, self.EvtChooseBool, thisControl)
			elif isinstance(attrType, list):
				self.logger.debug('    ... found list')
				thisControl = wx.Choice(self, wx.ID_ANY, (120, 50), choices=attrType)
				thisControl.SetSelection(0)
				thisControl.SetFont(font)
				self.listValue = attrType[0]
				self.Bind(wx.EVT_CHOICE, self.EvtChooseList, thisControl)
			else:
				self.logger.debug('Unsupported instance {} type {}'.format(attrType, type(attrType)))
				continue
			self.ctrlTracker[attrName] = thisControl
			panelSizer.Add(thisText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
			panelSizer.Add(thisControl, 0, wx.EXPAND)

		bufferSizer.Add(panelSizer, 0)
		vbox.Add(bufferSizer, 0)
		vbox.AddSpacer(20)

		btn = wx.Button(self, label="Insert")
		btn.SetFont(font)
		self.Bind(wx.EVT_BUTTON, self.onInsert, btn)
		vbox.Add(btn, 0, wx.LEFT|wx.RIGHT, 20)
		btn.SetDefault()
		btn.SetFocus()

		vbox.AddStretchSpacer()
		mainBox.Add(vbox, 1, wx.EXPAND|wx.RIGHT, 60)
		self.SetSizer(mainBox)

	def onInsert(self, event=None):
		self.logger.debug('Attempting to construct object for manual insert')
		jsonObject = {}
		## Get data from the page
		for attrName,attrType in self.objectDefinition.items():
			self.logger.debug(' working on {} : {}'.format(attrName, attrType))
			thisControl = self.ctrlTracker.get(attrName)
			thisValue = None
			if isinstance(attrType, str):
				#self.logger.debug('    ... found string')
				thisValue = thisControl.GetValue()
			elif isinstance(attrType, bool):
				#self.logger.debug('    ... found boolean')
				thisValue = self.boolValue
			elif isinstance(attrType, list):
				#self.logger.debug('    ... found list')
				thisValue = self.listValue
			else:
				continue
			if thisValue is not None:
				jsonObject[attrName] = thisValue
		content = {}
		content['source'] = 'admin console'
		content['data'] = jsonObject
		self.logger.debug('onInsert: call api to insert {} object: {}'.format(self.objectType, jsonObject))
		self.logger.debug('onInsert: content: {}'.format(content))

		## Call API to insert
		wx.BeginBusyCursor()
		(responseCode, responseAsJson) = self.api.postResource('data/{}'.format(self.objectType), {'content': content})
		wx.EndBusyCursor()
		if responseCode == 200 or responseCode == 201:
			self.logger.debug('onInsert: {} object added.'.format(self.objectType))
			wx.BeginBusyCursor()
			self.clearPanel()
			wx.EndBusyCursor()
		else:
			errorMsg = json.dumps(responseAsJson)
			with suppress(Exception):
				errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
			dlgResult = wx.MessageDialog(self, errorMsg, 'Object insert error', wx.OK|wx.ICON_ERROR)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()

	def clearPanel(self):
		for attrName,attrType in self.objectDefinition.items():
			self.logger.debug(' ===> clearing out {} : {}'.format(attrName, attrType))
			thisControl = self.ctrlTracker.get(attrName)
			thisValue = None
			if isinstance(attrType, str):
				self.logger.debug('    ===> found string')
				thisControl.Clear()
			elif isinstance(attrType, bool):
				self.logger.debug('    ===> found boolean')
				thisControl.SetSelection(0)
				self.boolValue = True
			elif isinstance(attrType, list):
				self.logger.debug('    ===> found list')
				thisControl.SetSelection(0)
				self.listValue = attrType[0]
			else:
				continue

	def EvtChooseBool(self, event):
		selection = event.GetString()
		self.logger.debug('EvtChooseBool: {}'.format(selection))
		if event.GetString() == 'False':
			self.boolValue = False
		else:
			self.boolValue = True

	def EvtChooseList(self, event):
		selection = event.GetString()
		self.logger.debug('EvtChooseList: {}'.format(selection))
		self.listValue = selection


class Page1(wx.Panel):
	def __init__(self, parent, logger, onNextPage, data):
		wx.Panel.__init__(self, parent)
		self.logger = logger
		self.onNextPage = onNextPage
		self.data = data
		self.SetBackgroundColour('white')
		self.objectTypes = list(self.data.get('objects', {}).keys())
		self.objectType = self.objectTypes[0]

		mainBox = wx.BoxSizer(wx.HORIZONTAL)
		mainBox.AddSpacer(60)
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(20)

		banner = wx.StaticText(self, label='Manually insert an object')
		f = banner.GetFont()
		f.SetPointSize(f.GetPointSize()+6)
		f.SetWeight(wx.FONTWEIGHT_BOLD)
		banner.SetFont(f)
		vbox.Add(banner, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(40)

		text1 = 'This page enables the manual creation of select object types in the database.\n'
		description = wx.StaticText(self, label=text1)
		font = description.GetFont()
		font.SetPointSize(font.GetPointSize()+2)
		description.SetFont(font)
		vbox.Add(description, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(10)

		text2 = 'After selecting the object type and clicking Next, the form enters a self-referencing cycle for the selected type. This is intended to expedite the creation of many objects of the same type, with minimal clicks. To return to this screen and change the type, simply click the \'Insert Object\' icon in the ribbon above.\n\n\n'
		description = wx.StaticText(self, label=text2)
		font = description.GetFont()
		font.SetPointSize(font.GetPointSize()+2)
		description.SetFont(font)
		vbox.Add(description, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(10)

		text3 = 'Note: The intent here is not to support all class types. This is simply a utility exposed to expedite testing and validation.\n\n'
		description = wx.StaticText(self, label=text3)
		font = description.GetFont()
		font.SetPointSize(font.GetPointSize()+2)
		description.SetFont(font)
		vbox.Add(description, 0, wx.LEFT|wx.EXPAND, 20)
		vbox.AddSpacer(10)

		hbox = wx.BoxSizer()
		selection = wx.StaticText(self, label='Select object type:')
		selection.SetFont(font)
		hbox.Add(selection, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 20)
		self.activeChoice = wx.Choice(self, wx.ID_ANY, (100, -1), choices=self.objectTypes)
		self.activeChoice.SetFont(font)
		self.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		hbox.Add(self.activeChoice)
		vbox.Add(hbox, 0)
		mainBox.Add(vbox, 1, wx.EXPAND|wx.RIGHT, 60)
		self.SetSizer(mainBox)

	def EvtChooseEnabled(self, event):
		self.objectType = event.GetString()
		#self.data['objectType'] = objectType
		self.logger.debug('Object type selected: {}'.format(self.objectType))
		pub.sendMessage('object.definition', objType=self.objectType, objDef=self.data.get('objects', {}).get(self.objectType))
		self.onNextPage(event)
		#pub('objectDefinition', self.objectType, self.data.get('objects', {}).get(self.objectType))


class InsertObjectBook(wx.Simplebook):
	def __init__(self, parent, log, api):
		wx.Simplebook.__init__(self, parent)
		self.showEffect = wx.SHOW_EFFECT_NONE
		self.hideEffect = wx.SHOW_EFFECT_NONE
		self.showTimeout = 0
		self.hideTimeout = 0
		self.logger = log
		self.api = api
		self.data = {}
		self.getRealms()
		self.getObjectDefinitions()
		self.data['objectType'] = list(self.data['objects'].keys())[0]
		self.DoSetEffects()
		page1 = Page1(self, self.logger, self.OnNextPage, self.data)
		self.AddPage(page1, '')
		page2 = Page2(self, self.logger, self.OnNextPage, self.OnBackPage, page1, self.data, self.api)
		self.AddPage(page2, '')


	def getRealms(self):
		apiResults = self.api.getResource('config/Realm')
		self.data['realms'] = []
		self.realms = []
		for name in apiResults.get('realms', {}):
			self.data['realms'].append(name)
			self.realms.append(name)

	def getObjectDefinitions(self):
		self.data['objects'] = {
			'IpAddress': {
				'address': str(),
				'realm': self.realms,
				'is_ipv4': bool()
			},
			'Node': {
				'hostname': str(),
				'domain': str(),
				'vendor': str(),
				'platform': str(),
				'version': str(),
				'hardware_is_virtual': bool(),
				'hardware_provider': str()
			},
			'Linux': {
				'hostname': str(),
				'domain': str(),
				'vendor': str(),
				'platform': str(),
				'version': str(),
				'hardware_is_virtual': bool(),
				'hardware_provider': str()
			},
			'Windows': {
				'hostname': str(),
				'domain': str(),
				'vendor': str(),
				'platform': str(),
				'version': str(),
				'hardware_is_virtual': bool(),
				'hardware_provider': str()
			},
			'BusinessApplication': {
				'name': str(),
				'element_id': str(),
				'element_owner': str(),
				'support_team': str(),
				'short_name': str()
			}
		}

	def MakeBackHomeButton(self, panel, vbox):
		btn = wx.Button(panel, -1, 'Back to page 1')
		self.Bind(wx.EVT_BUTTON, self.OnBackHome, btn)
		vbox.AddSpacer(75)
		vbox.Add(btn)


	def OnNextPage(self, evt):
		current = self.GetSelection()
		current += 1
		if current >= self.GetPageCount():
			current = 0
		self.ChangeSelection(current)

	def OnBackPage(self, evt):
		current = self.GetSelection()
		current -= 1
		if current < 0:
			current = 0
		self.ChangeSelection(current)

	def OnBackHome(self, evt):
		self.ChangeSelection(0)

	def OnShowEffectChoice(self, evt):
		self.showEffect = eval(evt.GetString())
		self.DoSetEffects()

	def OnHideEffectChoice(self, evt):
		self.hideEffect = eval(evt.GetString())
		self.DoSetEffects()

	def OnShowTimeoutSpin(self, evt):
		self.showTimeout = evt.GetEventObject().GetValue()
		self.DoSetEffects()

	def OnHideTimeoutSpin(self, evt):
		self.hideTimeout = evt.GetEventObject().GetValue()
		self.DoSetEffects()

	def DoSetEffects(self):
		self.SetEffects(self.showEffect, self.hideEffect)
		self.SetEffectsTimeouts(self.showTimeout, self.hideTimeout)


class RawPanel(wx.Panel):
	def __init__(self, parent, log):
		#wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(780, 920), style=wx.EXPAND|wx.CLIP_CHILDREN, name="rawPanel")
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, style=wx.EXPAND|wx.CLIP_CHILDREN, name="rawPanel")
		self.Layout()
	def Freeze(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(RawPanel, self).Freeze()
	def Thaw(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(RawPanel, self).Thaw()


class Main():
	def __init__(self, thisPanel, log, api):
		self.logger = log
		self.api = api
		self.thisPanel = thisPanel

		book = InsertObjectBook(thisPanel, self.logger, self.api)
		mainBox = wx.BoxSizer()
		mainBox.Add(book, 1, wx.EXPAND)

		thisPanel.Layout()
		thisPanel.SetSizer(mainBox)
		thisPanel.Show()
		thisPanel.SendSizeEvent()
		wx.EndBusyCursor()
