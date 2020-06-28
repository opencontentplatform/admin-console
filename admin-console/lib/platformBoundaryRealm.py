"""Pane for Admin Console ribbon destination: Platform->Boundary->Realm."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx


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


class MyEvent(wx.PyCommandEvent):
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)
		self.myVal = None


class Main():
	def __init__(self, parentPanel, log, api):
		self.logger = log
		self.api = api
		self.parentPanel = parentPanel
		self.thisPanel = RawPanel(self.parentPanel, wx.ID_ANY)
		self.realms = []
		self.getRealms()
		self.scopes = {}
		self.getRealmScopes()
		self.currentRealm = None
		if len(self.realms) > 0:
			self.currentRealm = self.realms[0]
			self.currentRealmId = 0
		self.updateDataPanel()
		wx.EndBusyCursor()


	def getRealms(self):
		apiResults = self.api.getResource('config/Realm')
		for name in apiResults.get('realms', {}):
			self.realms.append(name)


	def getRealmScopes(self):
		apiResults = self.api.getResource('config/RealmScope')
		for entry in apiResults.get('scopes', []):
			name = entry.get('realm')
			count = entry.get('count')
			networks = entry.get('data')
			self.scopes[name] = {'ips': count, 'networks': networks}


	def updateDataPanel(self):
		self.logger.debug('updateDataPanel: starting')
		self.parentPanel.Freeze()
		self.thisPanel.Destroy()
		self.thisPanel = RawPanel(self.parentPanel, wx.ID_ANY)

		self.rb = wx.RadioBox(self.thisPanel, wx.ID_ANY, 'Realm Selection', wx.DefaultPosition, wx.DefaultSize, self.realms, 1, wx.RA_SPECIFY_COLS)
		self.thisPanel.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
		self.rb.SetToolTip(wx.ToolTip('Select a Realm'))
		self.rb.SetSelection(self.currentRealmId)
		self.insertRealmButton = wx.Button(self.thisPanel, wx.ID_ANY, 'Insert Realm')
		self.thisPanel.Bind(wx.EVT_BUTTON, self.OnInsertRealmButton, self.insertRealmButton)
		self.deleteRealmButton = wx.Button(self.thisPanel, wx.ID_ANY, 'Delete Realm')
		self.thisPanel.Bind(wx.EVT_BUTTON, self.OnDeleteRealmButton, self.deleteRealmButton)
		self.rawPanel = RawPanel(self.thisPanel, wx.ID_ANY)

		mainBox = wx.BoxSizer(wx.HORIZONTAL)
		vBox1 = wx.BoxSizer(wx.VERTICAL)
		vBox1.Add(self.rb, 0, wx.ALL, 20)
		vBox1.Add(self.insertRealmButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
		vBox1.AddSpacer(20)
		vBox1.Add(self.deleteRealmButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
		mainBox.Add(vBox1, 0, wx.EXPAND)

		vBox2 = wx.BoxSizer(wx.VERTICAL)
		self.rawPanel.Destroy()
		self.rawPanel = RawPanel(self.thisPanel, wx.ID_ANY)
		self.dataPanel = None

		if self.currentRealm is not None:
			vBox3 = wx.BoxSizer(wx.VERTICAL)
			realmLabel = wx.StaticText(self.rawPanel, wx.ID_ANY, 'Selected Realm:   ')
			realmName = wx.StaticText(self.rawPanel, wx.ID_ANY, self.currentRealm)
			hBox2  = wx.BoxSizer(wx.HORIZONTAL)
			hBox2.Add(realmLabel, 0, wx.LEFT, 20)
			hBox2.Add(realmName, 0)
			vBox3.Add(hBox2, 0, wx.EXPAND|wx.TOP, 20)
			ipsLabel = wx.StaticText(self.rawPanel, wx.ID_ANY, 'Total IP Count:    ')
			ipsTotal = wx.StaticText(self.rawPanel, wx.ID_ANY, str(self.scopes.get(self.currentRealm, {}).get('ips', 0)))
			hBox3  = wx.BoxSizer(wx.HORIZONTAL)
			hBox3.Add(ipsLabel, 0, wx.LEFT, 20)
			hBox3.Add(ipsTotal, 0)
			vBox3.Add(hBox3, 0, wx.EXPAND|wx.TOP, 10)
			netLabel = wx.StaticText(self.rawPanel, wx.ID_ANY, 'Networks:')
			vBox3.Add(netLabel, 0, wx.EXPAND|wx.TOP|wx.LEFT, 20)
			textString = None
			for net in self.scopes.get(self.currentRealm, {}).get('networks', []):
				if textString is None:
					textString = '{}'.format(net)
				else:
					textString = '{},\n{}'.format(textString, net)
			if textString is None:
				textString = ''
			textCtrl = wx.TextCtrl(self.rawPanel, wx.ID_ANY, textString, size=(200, -1), style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY)
			vBox3.Add(textCtrl, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 20)
		self.logger.debug('updateDataPanel: finishing...')
		self.rawPanel.SetSizer(vBox3)
		self.rawPanel.Show()
		self.rawPanel.SendSizeEvent()
		mainBox.Add(self.rawPanel, 0, wx.EXPAND)
		self.logger.debug('updateDataPanel: end')
		self.thisPanel.SetSizer(mainBox)
		self.thisPanel.Show()
		self.thisPanel.SendSizeEvent()
		## Box for the ribbon at the top and a data panel on the bottom
		parentBox = wx.BoxSizer()
		parentBox.Add(self.thisPanel, 1, wx.EXPAND)
		self.parentPanel.Layout()
		## Apply the layout
		self.parentPanel.SetSizer(parentBox)
		self.parentPanel.Thaw()
		self.parentPanel.SendSizeEvent()


	def EvtRadioBox(self, event):
		realmId = event.GetInt()
		# self.logger.debug('EvtRadioBox:     entry id : {}'.format(realmId))
		# self.logger.debug('EvtRadioBox: selectedRealm: {}'.format(self.realms[realmId]))
		# self.logger.debug('EvtRadioBox: currentRealm : {}'.format(self.currentRealm))
		if self.currentRealmId != realmId:
			try:
				self.currentRealm = self.realms[realmId]
				self.currentRealmId = realmId
				self.updateDataPanel()
			except:
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				self.logger.debug('Failure in EvtRadioBox: {stacktrace}'.format(stacktrace))


	def OnInsertRealmButton(self, event=None):
		self.logger.debug('OnInsertRealmButton: {}'.format(event.GetInt()))
		dlgInsert = wx.TextEntryDialog(self.thisPanel, 'Enter a new name', 'Insert Realm')
		name = None
		if dlgInsert.ShowModal() == wx.ID_OK:
			name = dlgInsert.GetValue()
			self.logger.debug('You entered: {}'.format(name))
		dlgInsert.Destroy()
		if name is not None:
			## Send to the API
			(responseCode, responseAsJson) = self.api.postResourceWithoutPayload('config/Realm/{}'.format(name))
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Insert realm {}'.format(name), wx.OK | wx.ICON_INFORMATION)
				dlgResult.ShowModal()
				dlgResult.Destroy()
				## Add to the local realms list
				self.realms.append(name)
				## Force a radio selection change
				evt = MyEvent(wx.NewEventType(), 0)
				self.EvtRadioBox(evt)
				self.updateDataPanel()
			else:
				## Ideally retrieve the value of the first/arbitrary element in
				## the dict; fall back to just printing the full JSON response.
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg , 'Insert realm {}'.format(name), wx.OK | wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()

	def OnDeleteRealmButton(self, event=None):
		self.logger.debug('OnDeleteRealmButton')
		name = self.currentRealm
		dlgDelete = wx.MessageDialog(self.thisPanel,
									 'Are you sure you want to delete the \'{}\' realm?'.format(name),
									 'Delete realm {}'.format(name),
									 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnDeleteRealmButton: value == OK')
			## If user pressed OK (and not Cancel), then call API to delete realm
			(responseCode, responseAsJson) = self.api.deleteResource('config/Realm/{}'.format(name))
			if responseCode == 200:
				self.logger.debug('OnDeleteRealmButton: removed realm: {}'.format(name))
				self.realms.remove(name)
				if len(self.realms) > 0:
					self.logger.debug('OnDeleteRealmButton: creating event for radio box')
					evt = MyEvent(wx.NewEventType(), 0)
					self.EvtRadioBox(evt)
				else:
					self.currentRealm = None
					self.updateDataPanel()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel,
											 errorMsg,
											 'Delete realm {}'.format(name),
											 wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnDeleteRealmButton: value == CANCEL')
