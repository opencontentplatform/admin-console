"""Pane for Admin Console ribbon destination: Platform->Config->DefaultConfig."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.agw.genericmessagedialog as GMD
import wx.html2


class InsertDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE,
				 name='InsertDialog', log=None):
		wx.Dialog.__init__(self, parent, id, 'Insert Default Config', pos, size, style, name)
		self.panel = self
		self.logger = log
		self.logger.debug('Inside InsertDialog')

		self.textCtrl = wx.TextCtrl(self.panel, wx.ID_ANY, '', size=(600, 700), style=wx.TE_MULTILINE|wx.TE_RICH|wx.EXPAND)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		mainBox.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 15)

		line = wx.StaticLine(self, -1, size=(300,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 20)

		btnsizer = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		mainBox.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 15)

		self.panel.SetSizer(mainBox)
		mainBox.Fit(self.panel)
		self.panel.Show()


class UpdateDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='UpdateDialog', log=None, textString=''):
		wx.Dialog.__init__(self, parent, id, 'Update Default Config', pos, size, style, name)
		self.panel = self
		self.logger = log
		self.logger.debug('Inside UpdateDialog')

		self.textCtrl = wx.TextCtrl(self.panel, wx.ID_ANY, textString, size=(600, 700), style=wx.TE_MULTILINE|wx.TE_RICH|wx.EXPAND)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		mainBox.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 15)

		line = wx.StaticLine(self, -1, size=(200,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 20)

		btnsizer = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		mainBox.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 15)

		self.panel.SetSizer(mainBox)
		mainBox.Fit(self.panel)
		self.panel.Show()


class MyEvent(wx.PyCommandEvent):
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)
		self.myVal = None


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

		self.realms = []
		self.realmData = {}
		self.getRealms()
		self.currentRealm = None
		if len(self.realms) > 0:
			self.currentRealm = self.realms[0]
			self.currentRealmId = 0
		self.textCtrl = None

		self.leftPanelStaticBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, "Default Config")
		self.rbRealm = wx.RadioBox(self.leftPanelStaticBox, wx.ID_ANY, 'Realm Selection', wx.DefaultPosition, wx.DefaultSize, self.realms, 1, wx.RA_SPECIFY_COLS)
		self.leftPanelStaticBox.Bind(wx.EVT_RADIOBOX, self.EvtRealmRadioBox, self.rbRealm)
		self.rbRealm.SetToolTip(wx.ToolTip('Select a Realm'))

		self.insertButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Insert')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnInsertButton, self.insertButton)
		self.updateButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Update')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnUpdateButton, self.updateButton)
		self.deleteButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Delete Realm')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnDeleteButton, self.deleteButton)

		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		self.mainQueryBox.AddSpacer(2)
		self.mainQueryBox.Add(self.leftPanelStaticBox, 2, wx.LEFT|wx.BOTTOM, 5)
		
		topBorder, otherBorder = self.leftPanelStaticBox.GetBordersForSizer()
		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.AddSpacer(topBorder + 3)
		self.leftSizer.Add(self.rbRealm, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(20)

		self.leftSizer.Add(self.insertButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.updateButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(20)
		self.leftSizer.Add(self.deleteButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		
		self.leftPanelStaticBox.SetSizer(self.leftSizer)
		## Placeholder for when we known how to create an TextCtrl
		self.textCtrl = RawPanel(self.thisPanel, wx.ID_ANY)
		
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainBox.Add(self.mainQueryBox, 0, wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 15)
		self.thisPanel.SetSizer(self.mainBox)
		self.logger.debug('Main.init')

		self.resetMainPanel()
		wx.EndBusyCursor()


	def resetMainPanel(self):
		## Create boxes to arrange the panels
		self.logger.debug('Start resetMainPanel')
		self.thisPanel.Freeze()
		
		## Replace the textCtrl pane on the right
		self.mainBox.Detach(self.textCtrl)
		self.textCtrl.Destroy()
		self.logger.debug('resetMainPanel: currentRealm: {}'.format(self.currentRealm))
		self.logger.debug('resetMainPanel: realmData: {}'.format(self.realmData))
		dataSet = self.realmData.get(self.currentRealm, {})
		self.logger.debug('resetMainPanel: dataSet: {}'.format(dataSet))
		if dataSet is not None:
			self.logger.debug('resetMainPanel: dataSet: {}'.format(dataSet))
			textString = json.dumps(dataSet, indent=8)
			self.textCtrl = wx.TextCtrl(self.thisPanel, wx.ID_ANY, textString, style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY|wx.EXPAND)
		else:
			self.textCtrl = RawPanel(self.thisPanel, wx.ID_ANY)
		self.mainBox.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 15)

		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()
		self.logger.debug('Stop resetMainPanel')


	def getRealms(self):
		apiResults = self.api.getResource('config/Realm')
		for name in apiResults.get('realms', {}):
			self.logger.debug('resetMainPanel: getRealms: realm {}'.format(name))
			self.realms.append(name)
			self.getData(name)

	def getData(self, realm):
		apiResults = self.api.getResource('config/ConfigDefault/{}'.format(realm))
		self.realmData[realm] = apiResults.get('content')
		self.logger.debug('resetMainPanel: getData: apiResults {}'.format(apiResults))

	def EvtRealmRadioBox(self, event):
		realmId = event.GetInt()
		self.logger.debug('EvtRealmRadioBox: currentRealm : {}'.format(self.currentRealm))
		if self.currentRealmId != realmId:
			try:
				self.currentRealm = self.realms[realmId]
				self.logger.debug('EvtRealmRadioBox: switching to realm {}'.format(self.currentRealm))
				self.currentRealmId = realmId
				wx.BeginBusyCursor()
				self.resetMainPanel()
				wx.EndBusyCursor()
			except:
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				self.logger.debug('Failure in EvtRealmRadioBox: {}'.format(stacktrace))

	def OnInsertButton(self, event=None):
		myDialog = InsertDialog(self.thisPanel, log=self.logger)
		myDialog.CenterOnScreen()
		value = myDialog.ShowModal()
		## Pull results out before destroying the window
		data = {}
		data['realm'] = self.currentRealm
		data['source'] = 'admin console'
		data['content'] = {}
		osData = myDialog.textCtrl.GetValue()
		myDialog.Destroy()
		if value == wx.ID_OK:
			if osData is None or osData == '':
				self.logger.debug('OnInsertButton: nothing to insert')
				return
			data['content'] = json.loads(osData)
			self.logger.debug('OnInsertButton: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/ConfigDefault', {'content' : data})
			if responseCode == 405:
				(responseCode, responseAsJson) = self.api.putResource('config/ConfigDefault/{}'.format(self.currentRealm), {'content' : data})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Inserted ConfigDefault for realm {}'.format(self.currentRealm), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnInsertButton: ConfigDefault added.')
				wx.BeginBusyCursor()
				self.realmData[self.currentRealm] = data['content']
				self.resetMainPanel()
				wx.EndBusyCursor()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'ConfigDefault insert error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnInsertButton: value == CANCEL')

	def OnUpdateButton(self, event=None):
		dataSet = self.realmData.get(self.currentRealm, {})
		dataSetString = json.dumps(dataSet, indent=8)
		myDialog = UpdateDialog(self.thisPanel, log=self.logger, textString=dataSetString)
		myDialog.CenterOnScreen()
		value = myDialog.ShowModal()
		## Pull results out before destroying the window
		data = {}
		data['realm'] = self.currentRealm
		data['source'] = 'admin console'
		#data['content'] = self.realmData[self.currentRealm]
		osData = myDialog.textCtrl.GetValue()
		myDialog.Destroy()
		if value == wx.ID_OK:
			data['content'] = json.loads(osData)
			self.logger.debug('OnUpdateButton: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.putResource('config/ConfigDefault/{}'.format(self.currentRealm), {'content' : data})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Updated ConfigDefault for realm {}'.format(self.currentRealm), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnUpdateButton: ConfigDefault added.')
				wx.BeginBusyCursor()
				self.realmData[self.currentRealm] = data['content']
				self.resetMainPanel()
				wx.EndBusyCursor()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'ConfigDefault update error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnUpdateButton: value == CANCEL')

	def OnDeleteButton(self, event=None):
		self.logger.debug('OnDeleteButton: removing params for {}'.format(self.currentRealm))
		wx.BeginBusyCursor()
		(responseCode, responseAsJson) = self.api.deleteResource('config/ConfigDefault/{}'.format(self.currentRealm))
		wx.EndBusyCursor()
		if responseCode == 200:
			dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Removed ConfigDefault for realm {}'.format(self.currentRealm), wx.OK|wx.ICON_INFORMATION)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()
			self.logger.debug('OnDeleteButton: ConfigDefault removed.')
			wx.BeginBusyCursor()
			self.realmData[self.currentRealm] = None
			self.resetMainPanel()
			wx.EndBusyCursor()
		else:
			errorMsg = json.dumps(responseAsJson)
			with suppress(Exception):
				errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
			dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'ConfigDefault delete error', wx.OK|wx.ICON_ERROR)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()
