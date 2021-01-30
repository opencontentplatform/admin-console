"""Pane for Admin Console ribbon destination: Platform->Accounts->Credentials."""
import sys, traceback, os
import re, json, uuid, base64
import logging, logging.handlers
from contextlib import suppress
import encryptionModule
import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.dialogs


def getStaticListForType(protocolType, credHeaders):
	orderedList = None
	staticHeaders = None
	if protocolType == 'snmp':
		orderedList = ['id', 'version', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'version', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'wmi':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'ssh':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'token', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'token', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'powershell':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'rest':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'postgres':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'mssql':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'oracle':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'mariadb':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'mysql':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	elif protocolType == 'db2':
		orderedList = ['id', 'user', 'realm', 'credential_group', 'description', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
		staticHeaders = ['id', 'user', 'realm', 'credential group', 'description', 'created', 'created by', 'last updated', 'updated by']
	else:
		raise EnvironmentError('TODO: Protocol type not instrumented')
	## Don't overwrite; reuse the header structure
	credHeaders.clear()
	for header in staticHeaders:
		credHeaders.append(header)
	return orderedList


def cleanAttr(value):
	if value is None:
		value = ''
	return value

class UpdateGenericDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Update Credential', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='UpdateGenericDialog', log=None, credDetails={}, realms=[]):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.credDetails = credDetails
		self.logger.debug('Inside UpdateGenericDialog')
		self.realms = realms
		self.port = None
		self.realm = self.credDetails.get('realm')
		## In case user created cred without a realm initially - fix their oops
		if self.realm is None and len(self.realms) > 0:
			self.realm = self.realms[0]
		self.active = True
		self.passwordShown = False

		self.nameText = wx.StaticText(self.panel, wx.ID_ANY, 'Account Name:')
		self.name = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('user')), style=wx.TE_READONLY, size=(200, -1))
		self.passwordText1 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
		self.passwordText2 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.passwordText2.Hide()
		self.passwordClear = wx.TextCtrl(self.panel)
		self.passwordClear.Hide()
		self.toggleVisible = wx.Button(self.panel, wx.ID_ANY, 'Toggle Password')
		self.toggleVisible.Bind(wx.EVT_BUTTON, self.OnTogglePassButton)
		self.realmText = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.realmChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=self.realms)
		self.realmChoice.SetSelection(0)
		entryId = 0
		for entry in self.realms:
			if self.credDetails.get('realm') == entry:
				self.realmChoice.SetSelection(entryId)
				break
			entryId += 1
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRealm, self.realmChoice)
		self.descriptionText = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('description')), size=(200, -1))
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		if not self.credDetails.get('active', True):
			self.activeChoice.SetSelection(1)
			self.active = False
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.portCheck = wx.CheckBox(self.panel, -1, 'Custom Port:')
		if self.port is not None and self.port != '':
			self.portEntry = wx.TextCtrl(self.panel, wx.ID_ANY, self.port)
		else:
			self.portEntry = wx.TextCtrl(self.panel, wx.ID_ANY)
		self.portEntry.Enable(False)
		self.portCheck.Bind(wx.EVT_CHECKBOX, self.EvtOnPortCheck)
		self.credGroupText = wx.StaticText(self.panel, wx.ID_ANY, 'Credential Group is set to \'default\' unless overriden:')
		self.credGroupCheck = wx.CheckBox(self.panel, -1, 'Override:')
		self.credGroupEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.credGroupEntry.Enable(False)
		self.credGroupCheck.Bind(wx.EVT_CHECKBOX, self.OnCredGroupCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.nameText, 0, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.passwordText1, 0, wx.EXPAND)
		gBox1.Add(self.password, 0, wx.EXPAND)
		gBox1.Add(self.passwordText2, 0, wx.EXPAND)
		gBox1.Add(self.passwordClear, 0, wx.EXPAND)
		gBox1.AddSpacer(1)
		gBox1.Add(self.toggleVisible, 0, wx.ALIGN_RIGHT)
		gBox1.Add(self.realmText, 0, wx.EXPAND)
		gBox1.Add(self.realmChoice, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.descriptionText, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND)
		gBox1.Add(self.portCheck, 0, wx.EXPAND)
		gBox1.Add(self.portEntry, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)
		mainBox.Add(self.credGroupText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.credGroupCheck, 0, wx.EXPAND)
		gBox2.Add(self.credGroupEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
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

	def OnTogglePassButton(self, event):
		self.passwordText1.Show(self.passwordShown)
		self.password.Show(self.passwordShown)
		self.passwordText2.Show(not self.passwordShown)
		self.passwordClear.Show(not self.passwordShown)
		if not self.passwordShown:
			self.passwordClear.SetValue(self.password.GetValue())
			self.passwordClear.SetFocus()
		else:
			self.password.SetValue(self.passwordClear.GetValue())
			self.password.SetFocus()
		self.password.GetParent().Layout()
		self.passwordShown = not self.passwordShown

	def EvtOnPortCheck(self, event):
		if self.portCheck.Value == True:
			self.portEntry.Enable(True)
		else:
			self.portEntry.Enable(False)
		event.Skip()

	def EvtChooseRealm(self, event):
		entryId = 0
		self.realm = event.GetString()

	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True

	def OnCredGroupCheck(self, event):
		if self.credGroupCheck.Value == True:
			self.credGroupEntry.Enable(True)
		else:
			self.credGroupEntry.Enable(False)
		event.Skip()


class UpdateSnmpDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Update SNMP Credential', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='UpdateSnmpDialog', log=None, credDetails={}, realms=[]):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.credDetails = credDetails
		self.logger.debug('Inside UpdateSnmpDialog')
		self.realms = realms
		self.realm = self.credDetails.get('realm')
		## In case user created cred without a realm initially - fix their oops
		if self.realm is None and len(self.realms) > 0:
			self.realm = self.realms[0]
		self.community_string = None
		self.version = None
		self.active = True
		self.commShown = False

		self.versionText = wx.StaticText(self.panel, wx.ID_ANY, 'Version:')
		self.versionChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=['1', '2', '3'])
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseVersion, self.versionChoice)
		self.version = self.credDetails.get('version', '1')
		self.versionChoice.SetSelection(int(self.version)-1)
		self.commText1 = wx.StaticText(self.panel, wx.ID_ANY, 'Community String:')
		self.comm = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
		self.commText2 = wx.StaticText(self.panel, wx.ID_ANY, 'Community String:')
		self.commText2.Hide()
		self.commClear = wx.TextCtrl(self.panel)
		self.commClear.Hide()
		self.toggleVisible = wx.Button(self.panel, wx.ID_ANY, 'Toggle Visible')
		self.toggleVisible.Bind(wx.EVT_BUTTON, self.OnTogglePassButton)
		self.realmText = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.realmChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=self.realms)
		self.realmChoice.SetSelection(0)
		entryId = 0
		for entry in self.realms:
			if self.credDetails.get('realm') == entry:
				self.realmChoice.SetSelection(entryId)
				break
			entryId += 1
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRealm, self.realmChoice)
		self.descriptionText = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('description')), size=(185, -1))
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		if not self.credDetails.get('active', True):
			self.activeChoice.SetSelection(1)
			self.active = False
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.credGroupText = wx.StaticText(self.panel, wx.ID_ANY, 'Credential Group is set to \'default\' unless overriden:')
		self.credGroupCheck = wx.CheckBox(self.panel, -1, 'Override:')
		self.credGroupEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.credGroupEntry.Enable(False)
		self.credGroupCheck.Bind(wx.EVT_CHECKBOX, self.OnCredGroupCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.versionText, 0, wx.EXPAND)
		gBox1.Add(self.versionChoice, 0, wx.EXPAND)
		gBox1.Add(self.commText1, 0, wx.EXPAND)
		gBox1.Add(self.comm, 0, wx.EXPAND)
		gBox1.Add(self.commText2, 0, wx.EXPAND)
		gBox1.Add(self.commClear, 0, wx.EXPAND)
		gBox1.AddSpacer(1)
		gBox1.Add(self.toggleVisible, 0, wx.ALIGN_RIGHT)
		gBox1.Add(self.realmText, 0, wx.EXPAND)
		gBox1.Add(self.realmChoice, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.descriptionText, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)
		mainBox.Add(self.credGroupText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.credGroupCheck, 0, wx.EXPAND)
		gBox2.Add(self.credGroupEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
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

	def OnTogglePassButton(self, event):
		self.commText1.Show(self.commShown)
		self.comm.Show(self.commShown)
		self.commText2.Show(not self.commShown)
		self.commClear.Show(not self.commShown)
		if not self.commShown:
			self.commClear.SetValue(self.comm.GetValue())
			self.commClear.SetFocus()
		else:
			self.comm.SetValue(self.commClear.GetValue())
			self.comm.SetFocus()
		self.comm.GetParent().Layout()
		self.commShown = not self.commShown

	def EvtChooseRealm(self, event):
		entryId = 0
		self.realm = event.GetString()

	def EvtChooseVersion(self, event):
		self.version = event.GetString()
		self.logger.debug('Version Choice: %s\n' % self.version)

	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True

	def OnCredGroupCheck(self, event):
		if self.credGroupCheck.Value == True:
			self.credGroupEntry.Enable(True)
		else:
			self.credGroupEntry.Enable(False)
		event.Skip()

class UpdateRestDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Update Rest Credential', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='UpdateRestDialog', log=None, credDetails={}, realms=[]):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.credDetails = credDetails
		self.logger.debug('Inside UpdateRestDialog')
		self.realms = realms
		self.port = None
		self.realm = self.credDetails.get('realm')
		## In case user created cred without a realm initially - fix their oops
		if self.realm is None and len(self.realms) > 0:
			self.realm = self.realms[0]
		self.active = True
		self.passwordShown = False

		self.nameText = wx.StaticText(self.panel, wx.ID_ANY, 'Account Name:')
		self.name = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('user')), style=wx.TE_READONLY, size=(200, -1))
		self.passwordText1 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
		self.passwordText2 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.passwordText2.Hide()
		self.passwordClear = wx.TextCtrl(self.panel)
		self.passwordClear.Hide()
		self.toggleVisible = wx.Button(self.panel, wx.ID_ANY, 'Toggle Password')
		self.toggleVisible.Bind(wx.EVT_BUTTON, self.OnTogglePassButton)
		self.tokenText = wx.StaticText(self.panel, wx.ID_ANY, 'Token:')
		## Can't show the token because it's encrypted by now
		#self.token = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('token')), style=wx.TE_READONLY, size=(200, -1))
		self.token = wx.TextCtrl(self.panel, wx.ID_ANY, size=(200, -1))
		self.clientIdText = wx.StaticText(self.panel, wx.ID_ANY, 'Client ID:')
		self.clientId = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('client_id')))
		self.clientSecretText = wx.StaticText(self.panel, wx.ID_ANY, 'Client Secret:')
		self.clientSecret = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('client_secret')))
		self.realmText = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.realmChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=self.realms)
		self.realmChoice.SetSelection(0)
		entryId = 0
		for entry in self.realms:
			if self.credDetails.get('realm') == entry:
				self.realmChoice.SetSelection(entryId)
				break
			entryId += 1
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRealm, self.realmChoice)
		self.descriptionText = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, cleanAttr(self.credDetails.get('description')), size=(200, -1))
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		if not self.credDetails.get('active', True):
			self.activeChoice.SetSelection(1)
			self.active = False
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.credGroupText = wx.StaticText(self.panel, wx.ID_ANY, 'Credential Group is set to \'default\' unless overriden:')
		self.credGroupCheck = wx.CheckBox(self.panel, -1, 'Override:')
		self.credGroupEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.credGroupEntry.Enable(False)
		self.credGroupCheck.Bind(wx.EVT_CHECKBOX, self.OnCredGroupCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.nameText, 0, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.passwordText1, 0, wx.EXPAND)
		gBox1.Add(self.password, 0, wx.EXPAND)
		gBox1.Add(self.passwordText2, 0, wx.EXPAND)
		gBox1.Add(self.passwordClear, 0, wx.EXPAND)
		gBox1.AddSpacer(1)
		gBox1.Add(self.toggleVisible, 0, wx.ALIGN_RIGHT)
		gBox1.Add(self.tokenText, 0, wx.EXPAND)
		gBox1.Add(self.token, 0, wx.EXPAND)
		gBox1.Add(self.clientIdText, 0, wx.EXPAND)
		gBox1.Add(self.clientId, 0, wx.EXPAND)
		gBox1.Add(self.clientSecretText, 0, wx.EXPAND)
		gBox1.Add(self.clientSecret, 0, wx.EXPAND)
		gBox1.Add(self.realmText, 0, wx.EXPAND)
		gBox1.Add(self.realmChoice, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.descriptionText, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)
		mainBox.Add(self.credGroupText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.credGroupCheck, 0, wx.EXPAND)
		gBox2.Add(self.credGroupEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
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

	def OnTogglePassButton(self, event):
		self.passwordText1.Show(self.passwordShown)
		self.password.Show(self.passwordShown)
		self.passwordText2.Show(not self.passwordShown)
		self.passwordClear.Show(not self.passwordShown)
		if not self.passwordShown:
			self.passwordClear.SetValue(self.password.GetValue())
			self.passwordClear.SetFocus()
		else:
			self.password.SetValue(self.passwordClear.GetValue())
			self.password.SetFocus()
		self.password.GetParent().Layout()
		self.passwordShown = not self.passwordShown

	def EvtChooseRealm(self, event):
		entryId = 0
		self.realm = event.GetString()

	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True

	def OnCredGroupCheck(self, event):
		if self.credGroupCheck.Value == True:
			self.credGroupEntry.Enable(True)
		else:
			self.credGroupEntry.Enable(False)
		event.Skip()


class InsertGenericDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Insert Credential', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='InsertGenericDialog', log=None, realms=[]):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.realms = realms
		self.realm = None
		if len(self.realms) > 0:
			self.realm = self.realms[0]
		self.name = None
		self.password = None
		self.active = True
		self.port = None
		self.passwordShown = False
		self.logger.debug('Inside InsertGenericDialog')

		self.nameText = wx.StaticText(self.panel, wx.ID_ANY, 'Account Name:')
		self.name = wx.TextCtrl(self.panel, wx.ID_ANY, size=(100, -1))
		self.passwordText1 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
		self.passwordText2 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.passwordText2.Hide()
		self.passwordClear = wx.TextCtrl(self.panel)
		self.passwordClear.Hide()
		self.toggleVisible = wx.Button(self.panel, wx.ID_ANY, 'Toggle Password')
		self.toggleVisible.Bind(wx.EVT_BUTTON, self.OnTogglePassButton)
		self.realmText = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.realmChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=self.realms)
		self.realmChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRealm, self.realmChoice)
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.descriptionText = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, size=(200, -1))
		self.portCheck = wx.CheckBox(self.panel, -1, 'Custom Port:')
		self.portEntry = wx.TextCtrl(self.panel, wx.ID_ANY)
		self.portEntry.Enable(False)
		self.portCheck.Bind(wx.EVT_CHECKBOX, self.EvtOnPortCheck)
		self.credGroupText = wx.StaticText(self.panel, wx.ID_ANY, 'Credential Group is set to \'default\' unless overriden:')
		self.credGroupCheck = wx.CheckBox(self.panel, -1, 'Override:')
		self.credGroupEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.credGroupEntry.Enable(False)
		self.credGroupCheck.Bind(wx.EVT_CHECKBOX, self.OnCredGroupCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.nameText, 0, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.passwordText1, 0, wx.EXPAND)
		gBox1.Add(self.password, 0, wx.EXPAND)
		gBox1.Add(self.passwordText2, 0, wx.EXPAND)
		gBox1.Add(self.passwordClear, 0, wx.EXPAND)
		gBox1.AddSpacer(1)
		gBox1.Add(self.toggleVisible, 0, wx.ALIGN_RIGHT)
		gBox1.Add(self.realmText, 0, wx.EXPAND)
		gBox1.Add(self.realmChoice, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.descriptionText, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND)
		gBox1.Add(self.portCheck, 0, wx.EXPAND)
		gBox1.Add(self.portEntry, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)
		mainBox.Add(self.credGroupText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.credGroupCheck, 0, wx.EXPAND)
		gBox2.Add(self.credGroupEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 20)

		btnsizer = wx.StdDialogButtonSizer()
		# if wx.Platform != "__WXMSW__":
		# 	btn = wx.ContextHelpButton(self)
		# 	btnsizer.AddButton(btn)
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

	def OnTogglePassButton(self, event):
		self.passwordText1.Show(self.passwordShown)
		self.password.Show(self.passwordShown)
		self.passwordText2.Show(not self.passwordShown)
		self.passwordClear.Show(not self.passwordShown)
		if not self.passwordShown:
			#self.passwordText2.SetFocus()
			self.passwordClear.SetValue(self.password.GetValue())
			self.passwordClear.SetFocus()
		else:
			#self.passwordText1.SetFocus()
			self.password.SetValue(self.passwordClear.GetValue())
			self.password.SetFocus()
		self.password.GetParent().Layout()
		self.passwordShown = not self.passwordShown

	def EvtOnPortCheck(self, event):
		if self.portCheck.Value == True:
			self.portEntry.Enable(True)
		else:
			self.portEntry.Enable(False)
		event.Skip()

	def EvtChooseRealm(self, event):
		entryId = 0
		self.realm = event.GetString()

	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True

	def OnCredGroupCheck(self, event):
		if self.credGroupCheck.Value == True:
			self.credGroupEntry.Enable(True)
		else:
			self.credGroupEntry.Enable(False)
		event.Skip()


class InsertSnmpDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Insert SNMP Credential', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='InsertSnmpDialog', log=None, realms=[]):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.realms = realms
		self.realm = None
		if len(self.realms) > 0:
			self.realm = self.realms[0]
		self.community_string = None
		self.active = True
		self.commShown = False
		self.logger.debug('Inside InsertSnmpDialog')

		self.versionText = wx.StaticText(self.panel, wx.ID_ANY, 'Version:')
		self.versionChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['1', '2', '3'])
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseVersion, self.versionChoice)
		self.versionChoice.SetSelection(1)
		self.version = '2'
		self.commText1 = wx.StaticText(self.panel, wx.ID_ANY, 'Community String:')
		self.comm = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
		self.commText2 = wx.StaticText(self.panel, wx.ID_ANY, 'Community String:')
		self.commText2.Hide()
		self.commClear = wx.TextCtrl(self.panel)
		self.commClear.Hide()
		self.toggleVisible = wx.Button(self.panel, wx.ID_ANY, 'Toggle Visible')
		self.toggleVisible.Bind(wx.EVT_BUTTON, self.OnTogglePassButton)
		self.realmText = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.realmChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=self.realms)
		self.realmChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRealm, self.realmChoice)
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.descriptionText = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, size=(185, -1))
		self.credGroupText = wx.StaticText(self.panel, wx.ID_ANY, 'Credential Group is set to \'default\' unless overriden:')
		self.credGroupCheck = wx.CheckBox(self.panel, -1, 'Override:')
		self.credGroupEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.credGroupEntry.Enable(False)
		self.credGroupCheck.Bind(wx.EVT_CHECKBOX, self.OnCredGroupCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.versionText, 0, wx.EXPAND)
		gBox1.Add(self.versionChoice, 0, wx.EXPAND)
		gBox1.Add(self.commText1, 0, wx.EXPAND)
		gBox1.Add(self.comm, 0, wx.EXPAND)
		gBox1.Add(self.commText2, 0, wx.EXPAND)
		gBox1.Add(self.commClear, 0, wx.EXPAND)
		gBox1.AddSpacer(1)
		gBox1.Add(self.toggleVisible, 0, wx.ALIGN_RIGHT)
		gBox1.Add(self.realmText, 0, wx.EXPAND)
		gBox1.Add(self.realmChoice, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.descriptionText, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)
		mainBox.Add(self.credGroupText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.credGroupCheck, 0, wx.EXPAND)
		gBox2.Add(self.credGroupEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
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

	def OnTogglePassButton(self, event):
		self.commText1.Show(self.commShown)
		self.comm.Show(self.commShown)
		self.commText2.Show(not self.commShown)
		self.commClear.Show(not self.commShown)
		if not self.commShown:
			self.commClear.SetValue(self.comm.GetValue())
			self.commClear.SetFocus()
		else:
			self.comm.SetValue(self.commClear.GetValue())
			self.comm.SetFocus()
		self.comm.GetParent().Layout()
		self.commShown = not self.commShown

	def EvtChooseRealm(self, event):
		entryId = 0
		self.realm = event.GetString()

	def EvtChooseVersion(self, event):
		self.version = event.GetString()
		self.logger.debug('Version Choice: %s\n' % self.version)

	def EvtChooseEnabled(self, event):
		self.logger.debug('Enabled Choice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True

	def OnCredGroupCheck(self, event):
		if self.credGroupCheck.Value == True:
			self.credGroupEntry.Enable(True)
		else:
			self.credGroupEntry.Enable(False)
		event.Skip()


class InsertRestDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Insert SNMP Credential', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='InsertRestDialog', log=None, realms=[]):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.realms = realms
		self.realm = None
		if len(self.realms) > 0:
			self.realm = self.realms[0]
		self.name = None
		self.active = True
		self.passwordShown = False
		self.logger.debug('Inside InsertRestDialog')

		self.nameText = wx.StaticText(self.panel, wx.ID_ANY, 'Account Name:')
		self.name = wx.TextCtrl(self.panel, wx.ID_ANY, size=(100, -1))
		self.passwordText1 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
		self.passwordText2 = wx.StaticText(self.panel, wx.ID_ANY, 'Password:')
		self.passwordText2.Hide()
		self.passwordClear = wx.TextCtrl(self.panel)
		self.passwordClear.Hide()
		self.toggleVisible = wx.Button(self.panel, wx.ID_ANY, 'Toggle Password')
		self.toggleVisible.Bind(wx.EVT_BUTTON, self.OnTogglePassButton)
		self.tokenText = wx.StaticText(self.panel, wx.ID_ANY, 'Token:')
		self.token = wx.TextCtrl(self.panel, wx.ID_ANY, size=(100, -1))
		self.clientIdText = wx.StaticText(self.panel, wx.ID_ANY, 'Client ID:')
		self.clientId = wx.TextCtrl(self.panel, wx.ID_ANY, size=(100, -1))
		self.clientSecretText = wx.StaticText(self.panel, wx.ID_ANY, 'Client Secret:')
		self.clientSecret = wx.TextCtrl(self.panel, wx.ID_ANY, size=(100, -1))
		self.realmText = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.realmChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=self.realms)
		self.realmChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRealm, self.realmChoice)
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (100, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.descriptionText = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, size=(185, -1))
		self.credGroupText = wx.StaticText(self.panel, wx.ID_ANY, 'Credential Group is set to \'default\' unless overriden:')
		self.credGroupCheck = wx.CheckBox(self.panel, -1, 'Override:')
		self.credGroupEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.credGroupEntry.Enable(False)
		self.credGroupCheck.Bind(wx.EVT_CHECKBOX, self.OnCredGroupCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.nameText, 0, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.passwordText1, 0, wx.EXPAND)
		gBox1.Add(self.password, 0, wx.EXPAND)
		gBox1.Add(self.passwordText2, 0, wx.EXPAND)
		gBox1.Add(self.passwordClear, 0, wx.EXPAND)
		gBox1.AddSpacer(1)
		gBox1.Add(self.toggleVisible, 0, wx.ALIGN_RIGHT)
		gBox1.Add(self.tokenText, 0, wx.EXPAND)
		gBox1.Add(self.token, 0, wx.EXPAND)
		gBox1.Add(self.clientIdText, 0, wx.EXPAND)
		gBox1.Add(self.clientId, 0, wx.EXPAND)
		gBox1.Add(self.clientSecretText, 0, wx.EXPAND)
		gBox1.Add(self.clientSecret, 0, wx.EXPAND)
		gBox1.Add(self.realmText, 0, wx.EXPAND)
		gBox1.Add(self.realmChoice, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.descriptionText, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)
		mainBox.Add(self.credGroupText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.credGroupCheck, 0, wx.EXPAND)
		gBox2.Add(self.credGroupEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
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

	def OnTogglePassButton(self, event):
		self.passwordText1.Show(self.passwordShown)
		self.password.Show(self.passwordShown)
		self.passwordText2.Show(not self.passwordShown)
		self.passwordClear.Show(not self.passwordShown)
		if not self.passwordShown:
			#self.passwordText2.SetFocus()
			self.passwordClear.SetValue(self.password.GetValue())
			self.passwordClear.SetFocus()
		else:
			#self.passwordText1.SetFocus()
			self.password.SetValue(self.passwordClear.GetValue())
			self.password.SetFocus()
		self.password.GetParent().Layout()
		self.passwordShown = not self.passwordShown

	def EvtChooseRealm(self, event):
		entryId = 0
		self.realm = event.GetString()

	def EvtChooseVersion(self, event):
		self.version = event.GetString()
		self.logger.debug('Version Choice: %s\n' % self.version)

	def EvtChooseEnabled(self, event):
		self.logger.debug('Enabled Choice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True

	def OnCredGroupCheck(self, event):
		if self.credGroupCheck.Value == True:
			self.credGroupEntry.Enable(True)
		else:
			self.credGroupEntry.Enable(False)
		event.Skip()


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class ResultListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, credType, credDetails, credView, credHeaders, realms, OutterUpdateCred, OutterDeleteCred):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.api = api
		self.credType = credType
		self.credDetails = credDetails
		self.credView = credView
		self.credHeaders = credHeaders
		self.realms = realms
		self.OutterUpdateCred = OutterUpdateCred
		self.OutterDeleteCred = OutterDeleteCred
		self.logger.debug('Inside ResultListCtrlPanel')
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		self.currentItemId = None
		self.resultAttrs = list(range(0,len(self.credHeaders)))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.credView
		listmix.ColumnSorterMixin.__init__(self, len(self.credHeaders))
		sizer = wx.BoxSizer()
		sizer.Add(self.list, 1, wx.EXPAND)
		self.SetSizer(sizer)
		sizer.Fit(self)
		self.Layout()
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
		self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
		self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self.list)
		self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self.list)
		self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self.list)
		self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
		self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		# for wxMSW
		self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
		# for wxGTK
		self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)


	def OnUpdateColumns(self):
		self.logger.info('OnUpdateColumns: {}'.format(self.credView))
		for key,data in self.credView.items():
			self.logger.info('OnUpdateColumns looking at {} : {}'.format(key, data))
			self.logger.info('OnUpdateColumns range           : {}'.format(list(range(0, len(self.credHeaders)))))
			self.logger.info('OnUpdateColumns self.resultAttrs: {}'.format(self.resultAttrs))
			## Go in reverse since we're deleting in place
			for x in reversed(range(0, len(self.credHeaders))):
				self.logger.info('OnUpdateColumns x: {}'.format(x))
				if x not in self.resultAttrs:
					self.logger.info('OnUpdateColumns removing index {} with value {}'.format(x, data[x]))
					del data[x]
			self.credView[key] = data

	def PopulateList(self, data=None):
		self.logger.debug('PopulateList... ')
		self.currentItem = 0
		self.list.ClearAll()
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		col = 0
		for header in self.credHeaders:
			info.Align = wx.LIST_FORMAT_LEFT
			info.Text = header
			self.list.InsertColumn(col, info)
			col += 1
		for key,data in self.credView.items():
			index = self.list.InsertItem(self.list.GetItemCount(), str(data[0]))
			for x in range(len(self.credHeaders)-1):
				self.list.SetItem(index, x+1, str(data[x+1]))
			self.list.SetItemData(index, key)
		col = 0
		for header in self.credHeaders:
			self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			if col == 0:
				self.list.SetColumnWidth(col, 40)
			elif col <= 3:
				self.list.SetColumnWidth(col, 120)
			else:
				self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			col += 1
		self.currentItemId = None
		if self.credView is not None and len(self.credView) > 0:
			self.currentItemId = self.getColumnText(self.currentItem, 0)


	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	def OnRightDown(self, event):
		x = event.GetX()
		y = event.GetY()
		self.logger.debug("x, y = %s\n" % str((x, y)))
		item, flags = self.list.HitTest((x, y))
		if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
			self.list.Select(item)
		event.Skip()

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def OnItemSelected(self, event):
		self.currentItem = event.Index
		self.currentItemId = self.getColumnText(self.currentItem, 0)
		self.logger.debug("OnItemSelected: %s, %s, %s, %s\n" %
						   (self.currentItem,
							self.list.GetItemText(self.currentItem),
							self.getColumnText(self.currentItem, 1),
							self.getColumnText(self.currentItem, 2)))
		event.Skip()

	def OnItemDeselected(self, evt):
		item = evt.GetItem()
		self.logger.debug("OnItemDeselected: %d" % evt.Index)

	def OnItemActivated(self, event):
		self.currentItem = event.Index
		self.currentItemId = self.getColumnText(self.currentItem, 0)
		self.logger.debug("OnItemActivated: %s\nTopItem: %s" %
						   (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))

	def OnColClick(self, event):
		self.logger.debug("OnColClick: %d\n" % event.GetColumn())
		event.Skip()

	def OnColRightClick(self, event):
		item = self.list.GetColumn(event.GetColumn())
		self.logger.debug("OnColRightClick: %d %s\n" %
						   (event.GetColumn(), (item.GetText(), item.GetAlign(),
												item.GetWidth(), item.GetImage())))
		if self.list.HasColumnOrderSupport():
			self.logger.debug("OnColRightClick: column order: %d\n" %
							   self.list.GetColumnOrder(event.GetColumn()))

	def OnColBeginDrag(self, event):
		self.logger.debug("OnColBeginDrag\n")

	def OnColDragging(self, event):
		self.logger.debug("OnColDragging")

	def OnColEndDrag(self, event):
		self.logger.debug("OnColEndDrag")

	def OnDoubleClick(self, event):
		self.logger.debug("OnDoubleClick item %s" % self.list.GetItemText(self.currentItem))
		self.OnProperties(None)
		event.Skip()

	def OnRightClick(self, event):
		self.logger.debug("OnRightClick %s" % self.list.GetItemText(self.currentItem))
		# only do this part the first time so the events are only bound once
		if not hasattr(self, "propertiesID"):
			self.propertiesID = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, self.OnProperties, id=self.propertiesID)
			self.updateID = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, self.OutterUpdateCred, id=self.updateID)
			self.deleteID = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, self.OutterDeleteCred, id=self.deleteID)
		menu = wx.Menu()
		menu.Append(self.propertiesID, "Properties")
		menu.Append(self.updateID, "Update")
		menu.Append(self.deleteID, "Delete")
		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		self.PopupMenu(menu)
		menu.Destroy()

	def OnProperties(self, event):
		self.logger.debug("OnProperties: currentItem: {}".format(self.currentItem))
		self.logger.debug("OnProperties: credDetails: {}".format(self.credDetails))
		message = ''
		pos = 0
		refId = self.getColumnText(self.currentItem, 0)
		#refId = self.getColumnText(self.currentItem, 1)
		originalData = self.credDetails[refId]
		for attr,value in originalData.items():
			newEntry = '{}: {}\n'.format(attr, value)
			if message is None:
				message = newEntry
			else:
				message = '{}{}'.format(message, newEntry)
			pos += 1
		self.logger.debug('OnProperties: 3: message: {}'.format(message))
		self.logger.debug('OnProperties: 3: size: {}'.format(len(message)))
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "Properties", size=(500, 300))
		dlg.ShowModal()
		dlg.Destroy()


	def updateGenericCred(self, titleName):
		needToRefreshData = False
		refId = self.currentItemId
		self.logger.debug('updateGenericCred: refId: {}'.format(refId))
		self.logger.debug("updateGenericCred: credDetails: {}".format(self.credDetails))
		credDetails = self.credDetails[refId]
		dlgCred = UpdateGenericDialog(self, title='{} credential'.format(titleName), log=self.logger, credDetails=credDetails, realms=self.realms)
		dlgCred.CenterOnScreen()
		value = dlgCred.ShowModal()

		## Pull results out before destroying the window
		credData = {}
		credData['source'] = 'admin console'
		if dlgCred.password.GetValue() is not None and dlgCred.password.GetValue() != '':
			credData['password'], credData['wrench'] = encryptionModule.transform(dlgCred.password.GetValue(), generateToken=True)
		elif dlgCred.passwordClear.GetValue() is not None and dlgCred.passwordClear.GetValue() != '':
			credData['password'], credData['wrench'] = encryptionModule.transform(dlgCred.passwordClear.GetValue(), generateToken=True)

		if credDetails['active'] != dlgCred.active:
			credData['active'] = dlgCred.active
		thisPort = None
		if dlgCred.portCheck.Value == True:
			thisPort = dlgCred.portEntry.GetValue()
		if credDetails['port'] != thisPort:
			credData['port'] = thisPort
		if credDetails['realm'] != dlgCred.realm and dlgCred.realm is not None and dlgCred.realm != '':
			credData['realm'] = dlgCred.realm
		thisCredGroup = 'default'
		if dlgCred.credGroupCheck.Value == True:
			thisCredGroup = dlgCred.credGroupEntry.GetValue()
		if credDetails['credential_group'] != thisCredGroup:
			credData['credential_group'] = thisCredGroup
		thisDescr = dlgCred.description.GetValue()
		if credDetails['description'] != thisDescr and thisDescr is not None and thisDescr != '':
			credData['description'] = thisDescr
		dlgCred.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('updateGenericCred: value == OK')
			self.logger.debug('updateGenericCred: credData: {}'.format(credData))
			if len(credData) <= 0:
				dlgResult = wx.MessageDialog(self, 'No updates provided', 'Update credential {}'.format(refId), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
			else:
				wx.BeginBusyCursor()
				(responseCode, responseAsJson) = self.api.putResource('config/cred/{}/{}'.format(self.credType, refId), {'content' : credData})
				wx.EndBusyCursor()
				if responseCode == 200:
					dlgResult = wx.MessageDialog(self, 'SUCCESS', 'Updated cred {}'.format(refId), wx.OK|wx.ICON_INFORMATION)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
					self.logger.debug('updateGenericCred: cred updated.')
					needToRefreshData = True
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self, errorMsg, 'Credentials error', wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
		else:
			self.logger.debug('updateGenericCred: value == CANCEL')
		return needToRefreshData

	def updateSnmpCred(self, titleName):
		needToRefreshData = False
		refId = self.currentItemId
		self.logger.debug('updateSnmpCred: refId: {}'.format(refId))
		self.logger.debug("updateSnmpCred: credDetails: {}".format(self.credDetails))
		credDetails = self.credDetails[refId]
		dlgCred = UpdateSnmpDialog(self, title='{} credential'.format(titleName), log=self.logger, credDetails=credDetails, realms=self.realms)
		dlgCred.CenterOnScreen()
		value = dlgCred.ShowModal()

		## Pull results out before destroying the window
		credData = {}
		credData['source'] = 'admin console'
		if dlgCred.comm.GetValue() is not None and dlgCred.comm.GetValue() != '':
			credData['community_string'], credData['wrench'] = encryptionModule.transform(dlgCred.comm.GetValue(), generateToken=True)
		elif dlgCred.commClear.GetValue() is not None and dlgCred.commClear.GetValue() != '':
			credData['community_string'], credData['wrench'] = encryptionModule.transform(dlgCred.commClear.GetValue(), generateToken=True)
		if credDetails['version'] != dlgCred.version:
			credData['version'] = dlgCred.version
		if credDetails['active'] != dlgCred.active:
			credData['active'] = dlgCred.active
		if credDetails['realm'] != dlgCred.realm and dlgCred.realm is not None and dlgCred.realm != '':
			credData['realm'] = dlgCred.realm
		thisCredGroup = 'default'
		if dlgCred.credGroupCheck.Value == True:
			thisCredGroup = dlgCred.credGroupEntry.GetValue()
		if credDetails['credential_group'] != thisCredGroup:
			credData['credential_group'] = thisCredGroup
		thisDescr = dlgCred.description.GetValue()
		if credDetails['description'] != thisDescr and thisDescr is not None and thisDescr != '':
			credData['description'] = thisDescr
		dlgCred.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('updateSnmpCred: value == OK')
			self.logger.debug('updateSnmpCred: credData: {}'.format(credData))
			if len(credData) <= 0:
				dlgResult = wx.MessageDialog(self, 'No updates provided', 'Update credential {}'.format(refId), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
			else:
				wx.BeginBusyCursor()
				(responseCode, responseAsJson) = self.api.putResource('config/cred/{}/{}'.format(self.credType, refId), {'content' : credData})
				wx.EndBusyCursor()
				if responseCode == 200:
					dlgResult = wx.MessageDialog(self, 'SUCCESS', 'Updated cred {}'.format(refId), wx.OK|wx.ICON_INFORMATION)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
					self.logger.debug('updateSnmpCred: cred updated.')
					needToRefreshData = True
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self, errorMsg, 'Credentials error', wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
		else:
			self.logger.debug('updateSnmpCred: value == CANCEL')
		return needToRefreshData

	def updateRestCred(self, titleName):
		needToRefreshData = False
		refId = self.currentItemId
		self.logger.debug('updateRestCred: refId: {}'.format(refId))
		#self.logger.debug("updateRestCred: credDetails: {}".format(self.credDetails))
		credDetails = self.credDetails[refId]
		dlgCred = UpdateRestDialog(self, title='{} credential'.format(titleName), log=self.logger, credDetails=credDetails, realms=self.realms)
		dlgCred.CenterOnScreen()
		value = dlgCred.ShowModal()

		## Pull results out before destroying the window
		credData = {}
		credData['source'] = 'admin console'
		if dlgCred.password.GetValue() is not None and dlgCred.password.GetValue() != '':
			credData['password'], credData['wrench'] = encryptionModule.transform(dlgCred.password.GetValue(), generateToken=True)
		elif dlgCred.passwordClear.GetValue() is not None and dlgCred.passwordClear.GetValue() != '':
			credData['password'], credData['wrench'] = encryptionModule.transform(dlgCred.passwordClear.GetValue(), generateToken=True)
		thisToken = dlgCred.token.GetValue()
		if thisToken is not None and thisToken != '':
			if credData.get('wrench') is not None and credData.get('wrench' != ''):
				## reuse the wrench value used with the password
				credData['token'] = encryptionModule.encode(thisToken, credData['wrench'])
			else:
				## no password provided; we still need to create the wrench
				credData['token'], credData['wrench'] = encryptionModule.transform(thisToken, generateToken=True)
		clientId = dlgCred.clientId.GetValue()
		if clientId:
			credData['client_id'] = clientId
		clientSecret = dlgCred.clientSecret.GetValue()
		if clientSecret:
			credData['client_secret'] = clientSecret
		if credDetails['active'] != dlgCred.active:
			credData['active'] = dlgCred.active
		if credDetails['realm'] != dlgCred.realm and dlgCred.realm is not None and dlgCred.realm != '':
			credData['realm'] = dlgCred.realm
		thisCredGroup = 'default'
		if dlgCred.credGroupCheck.Value == True:
			thisCredGroup = dlgCred.credGroupEntry.GetValue()
		if credDetails['credential_group'] != thisCredGroup:
			credData['credential_group'] = thisCredGroup
		thisDescr = dlgCred.description.GetValue()
		if credDetails['description'] != thisDescr and thisDescr is not None and thisDescr != '':
			credData['description'] = thisDescr
		dlgCred.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('updateRestCred: value == OK')
			self.logger.debug('updateRestCred: credData: {}'.format(credData))
			if len(credData) <= 0:
				dlgResult = wx.MessageDialog(self, 'No updates provided', 'Update REST credential {}'.format(refId), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
			else:
				wx.BeginBusyCursor()
				(responseCode, responseAsJson) = self.api.putResource('config/cred/{}/{}'.format(self.credType, refId), {'content' : credData})
				wx.EndBusyCursor()
				if responseCode == 200:
					dlgResult = wx.MessageDialog(self, 'SUCCESS', 'Updated cred {}'.format(refId), wx.OK|wx.ICON_INFORMATION)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
					self.logger.debug('updateRestCred: cred updated.')
					needToRefreshData = True
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self, errorMsg, 'Credentials error', wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
		else:
			self.logger.debug('updateRestCred: value == CANCEL')
		return needToRefreshData

	def updateSNMP(self, titleName):
		self.logger.debug('updateSNMP...')
		return self.updateSnmpCred(titleName)

	def updateWMI(self, titleName):
		self.logger.debug('updateWMI...')
		return self.updateGenericCred(titleName)

	def updateSSH(self, titleName):
		self.logger.debug('updateSSH...')
		return self.updateGenericCred(titleName)

	def updatePowerShell(self, titleName):
		self.logger.debug('updatePowerShell...')
		return self.updateGenericCred(titleName)

	def updateRest(self, titleName):
		self.logger.debug('updateRest...')
		return self.updateRestCred(titleName)


	def OnDeleteCred(self, event=None):
		self.logger.debug('OnDeleteCred')
		refId = self.currentItemId
		needToRefreshData = False
		self.logger.debug('OnDeleteCred: refId: {}'.format(refId))
		dlgDelete = wx.MessageDialog(self,
									 'Are you sure you want to delete cred {}?'.format(refId),
									 'Delete cred {}'.format(refId),
									 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnDeleteCred: value == OK')
			## If user pressed OK (and not Cancel), then call API to delete network
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.deleteResource('config/cred/{}/{}'.format(self.credType, refId))
			wx.EndBusyCursor()
			if responseCode == 200:
				self.logger.debug('OnDeleteCred: removed cred {}'.format(refId))
				needToRefreshData = True
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self, errorMsg, 'Delete cred {}'.format(refId), wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnDeleteCred: value == CANCEL')
		return needToRefreshData


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
		self.credsPanel = None

		self.realms = []
		self.protocolNames = []
		self.credDetails = {}
		self.credView = {}
		self.credHeaders = {}
		try:
			self.getRealms()
			self.getProtocols()
			self.getAllCredentials()
			self.currentProtocol = None
			self.currentProtocolId = None
			if len(self.protocolNames) > 0:
				self.currentProtocol = self.protocolNames[0]
				self.currentProtcolId = 0
	
			self.leftPanelStaticBox = wx.StaticBox(self.parentPanel, wx.ID_ANY, "Credentials")
			self.rb = wx.RadioBox(self.leftPanelStaticBox, wx.ID_ANY, 'Protocol Type', wx.DefaultPosition, wx.DefaultSize, self.protocolNames, 1, wx.RA_SPECIFY_COLS)
			self.leftPanelStaticBox.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
			self.rb.SetToolTip(wx.ToolTip('Select a Protocol'))
			self.insertCredButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Insert')
			self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnInsertCredButton, self.insertCredButton)
			self.updateCredButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Update')
			self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnUpdateCredButton, self.updateCredButton)
			self.deleteCredButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Delete')
			self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnDeleteCredButton, self.deleteCredButton)
			#self.panelLabel = wx.StaticText(self.parentPanel, wx.ID_ANY, 'Credential Entries:')
			
			self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
			self.mainQueryBox.AddSpacer(2)
			self.mainQueryBox.Add(self.leftPanelStaticBox, 2, wx.LEFT|wx.BOTTOM, 5)
			
			topBorder, otherBorder = self.leftPanelStaticBox.GetBordersForSizer()
			self.leftSizer = wx.BoxSizer(wx.VERTICAL)
			self.leftSizer.AddSpacer(topBorder + 3)
			self.leftSizer.Add(self.rb, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
			self.leftSizer.AddSpacer(20)
	
			self.leftSizer.Add(self.insertCredButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
			self.leftSizer.AddSpacer(10)
			self.leftSizer.Add(self.updateCredButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
			self.leftSizer.AddSpacer(20)
			self.leftSizer.Add(self.deleteCredButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
			self.leftSizer.AddSpacer(10)
			
			self.leftPanelStaticBox.SetSizer(self.leftSizer)
			## Placeholder for when we known how to create this
			self.credsPanel = RawPanel(self.parentPanel, wx.ID_ANY)
			
			self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
			self.mainBox.Add(self.mainQueryBox, 0, wx.TOP|wx.LEFT|wx.BOTTOM, 5)
			self.mainBox.Add(self.credsPanel, 1, wx.EXPAND|wx.ALL, 15)
			self.parentPanel.SetSizer(self.mainBox)
			
			wx.EndBusyCursor()
			self.updateDataPanel()
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in init: {}'.format(stacktrace))


	def updateDataPanel(self):
		try:
			wx.BeginBusyCursor()
			self.logger.debug('updateDataPanel: starting')
			self.parentPanel.Freeze()

			## Replace the credsPanel pane on the right
			self.mainBox.Detach(self.credsPanel)
			self.credsPanel.Destroy()
			self.credsPanel = ResultListCtrlPanel(self.parentPanel, self.logger,
												  self.api, self.currentProtocol,
												  self.credDetails[self.currentProtocol],
												  self.credView[self.currentProtocol],
												  self.credHeaders[self.currentProtocol],
												  self.realms,
												  self.OnUpdateCredButton,
												  self.OnDeleteCredButton)
			self.mainBox.Add(self.credsPanel, 1, wx.EXPAND|wx.ALL, 15)
			self.parentPanel.SetSizer(self.mainBox)
			self.parentPanel.Thaw()
			self.parentPanel.Show()
			self.parentPanel.SendSizeEvent()
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in updateDataPanel: {}'.format(stacktrace))
		wx.EndBusyCursor()


	def getRealms(self):
		apiResults = self.api.getResource('config/Realm')
		for name in apiResults.get('realms', {}):
			self.realms.append(name)

	def getProtocols(self):
		apiResults = self.api.getResource('config/cred')
		for protocolType in apiResults.get('Types', []):
			self.protocolNames.append(protocolType)
			self.credDetails[protocolType] = {}
			self.credView[protocolType] = {}
			self.credHeaders[protocolType] = []

	def getAllCredentials(self):
		for protocolType in self.protocolNames:
			self.getCredentialsForType(protocolType)

	def getCredentialsForType(self, protocolType):
		self.logger.debug('getCredentialsForType: looking at protocolType: {}'.format(protocolType))
		## Leaving the original structure (dict/list) and emptying for reuse
		credDetails = self.credDetails[protocolType]
		credView = self.credView[protocolType]
		credHeaders = self.credHeaders[protocolType]
		credDetails.clear()
		credView.clear()
		credHeaders.clear()
		objectId = 1
		apiResults = self.api.getResource('config/cred/{}'.format(protocolType))
		for ref,details in apiResults.items():
			self.logger.debug('getCredentialsForType: ref {}: {}'.format(ref, details))
			credDetails[ref] = {}
			## Remove keys we just don't care about
			for attr in ['object_id', 'password']:
				if attr in details:
					details.pop(attr)
			details['id'] = ref
			## Put most keys on credDetails
			for key,value in details.items():
				credDetails[ref][key] = value
			## Only put specific keys on credView, and in a natural order
			attrList = []
			orderedList = getStaticListForType(protocolType, credHeaders)
			for col in orderedList:
				value = details.get(col)
				if value is None:
					value = ''
				attrList.append(value)
			credView[objectId] = attrList
			objectId += 1


	def EvtRadioBox(self, event):
		protocolId = event.GetInt()
		self.logger.debug('EvtRadioBox:     entry id : {}'.format(protocolId))
		self.logger.debug('EvtRadioBox: selection: {}'.format(self.protocolNames[protocolId]))
		if self.currentProtocolId != protocolId:
			try:
				self.currentProtocol = self.protocolNames[protocolId]
				self.currentProtocolId = protocolId
				wx.BeginBusyCursor()
				self.updateDataPanel()
				wx.EndBusyCursor()
			except:
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				self.logger.debug('Failure in EvtRadioBox: {}'.format(stacktrace))


	def OnInsertCredButton(self, event=None):
		self.logger.debug('OnInsertCredButton: {}'.format(event.GetInt()))
		if self.currentProtocol == 'snmp':
			self.insertSNMP('SNMP')
		elif self.currentProtocol == 'wmi':
			self.insertWMI('WMI')
		elif self.currentProtocol == 'ssh':
			self.insertSSH('SSH')
		elif self.currentProtocol == 'powershell':
			self.insertPowerShell('PowerShell')
		elif self.currentProtocol == 'rest':
			self.insertRest('Rest API')
		else:
			raise NotImplementedError('Protocol type not supported: {}'.format(self.currentProtocol))

	def insertGenericCred(self, titleName):
		dlgCred = InsertGenericDialog(self.parentPanel, title='{} credential'.format(titleName), log=self.logger, realms=self.realms)
		dlgCred.CenterOnScreen()
		value = dlgCred.ShowModal()
		## Pull results out before destroying the window
		credData = {}
		credData['source'] = 'admin console'
		credData['user'] = dlgCred.name.GetValue()
		credData['password'] = None
		if dlgCred.password.GetValue() is not None and dlgCred.password.GetValue() != '':
			credData['password'] = dlgCred.password.GetValue()
		elif dlgCred.passwordClear.GetValue() is not None and dlgCred.passwordClear.GetValue() != '':
			credData['password'] = dlgCred.passwordClear.GetValue()
		credData['active'] = dlgCred.active
		credData['port'] = dlgCred.port
		credData['realm'] = dlgCred.realm
		credData['description'] = dlgCred.description.GetValue()
		credData['credential_group'] = 'default'
		if dlgCred.credGroupCheck.Value == True:
			credData['credential_group'] = dlgCred.credGroupEntry.GetValue()
		self.logger.debug('insertGenericCred: credData: {}'.format(credData))
		dlgCred.Destroy()
		if value == wx.ID_OK:
			thisPort = None
			if dlgCred.portCheck.Value == True:
				thisPort = dlgCred.portEntry.GetValue()
			## Remove invalid entries
			if thisPort is None or thisPort == '':
				credData.pop('port')
			if credData['description'] is None or credData['description'] == '':
				credData.pop('description')
			## Convert the password
			credData['password'], credData['wrench'] = encryptionModule.transform(credData['password'], generateToken=True)

			self.logger.debug('insertGenericCred: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/cred/{}'.format(self.currentProtocol), {'content' : credData})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.parentPanel, 'SUCCESS', 'Insert credential {}'.format(credData['user']), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('insertGenericCred: cred added.')
				wx.BeginBusyCursor()
				self.getCredentialsForType(self.currentProtocol)
				wx.EndBusyCursor()
				self.updateDataPanel()
				
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.parentPanel, errorMsg, 'Credentials error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('insertGenericCred: value == CANCEL')

	def insertSnmpCred(self, titleName):
		dlgCred = InsertSnmpDialog(self.parentPanel, title='{} credential'.format(titleName), log=self.logger, realms=self.realms)
		dlgCred.CenterOnScreen()
		value = dlgCred.ShowModal()
		## Pull results out before destroying the window
		credData = {}
		credData['source'] = 'admin console'
		credData['community_string'] = None
		if dlgCred.comm.GetValue() is not None and dlgCred.comm.GetValue() != '':
			credData['community_string'] = dlgCred.comm.GetValue()
		elif dlgCred.commClear.GetValue() is not None and dlgCred.commClear.GetValue() != '':
			credData['community_string'] = dlgCred.commClear.GetValue()
		credData['version'] = dlgCred.version
		credData['active'] = dlgCred.active
		credData['realm'] = dlgCred.realm
		credData['description'] = dlgCred.description.GetValue()
		credData['credential_group'] = 'default'
		if dlgCred.credGroupCheck.Value == True:
			credData['credential_group'] = dlgCred.credGroupEntry.GetValue()
		self.logger.debug('insertSnmpCred: credData: {}'.format(credData))
		dlgCred.Destroy()
		if value == wx.ID_OK:
			if credData['description'] is None or credData['description'] == '':
				credData.pop('description')
			## Convert the password
			credData['community_string'], credData['wrench'] = encryptionModule.transform(credData['community_string'], generateToken=True)

			self.logger.debug('insertSnmpCred: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/cred/{}'.format(self.currentProtocol), {'content' : credData})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.parentPanel, 'SUCCESS', 'Inserted {} credential'.format(titleName), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('insertSnmpCred: cred added.')
				wx.BeginBusyCursor()
				self.getCredentialsForType(self.currentProtocol)
				wx.EndBusyCursor()
				self.updateDataPanel()
				
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.parentPanel, errorMsg, 'Credentials error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('insertSnmpCred: value == CANCEL')

	def insertRestCred(self, titleName):
		dlgCred = InsertRestDialog(self.parentPanel, title='{} credential'.format(titleName), log=self.logger, realms=self.realms)
		dlgCred.CenterOnScreen()
		value = dlgCred.ShowModal()
		## Pull results out before destroying the window
		credData = {}
		credData['source'] = 'admin console'
		credData['user'] = dlgCred.name.GetValue()
		credData['password'] = None
		if dlgCred.password.GetValue() is not None and dlgCred.password.GetValue() != '':
			credData['password'] = dlgCred.password.GetValue()
		elif dlgCred.passwordClear.GetValue() is not None and dlgCred.passwordClear.GetValue() != '':
			credData['password'] = dlgCred.passwordClear.GetValue()
		credData['token'] = None
		credData['token'] = dlgCred.token.GetValue()
		clientId = dlgCred.clientId.GetValue()
		if clientId:
			credData['client_id'] = clientId
		clientSecret = dlgCred.clientSecret.GetValue()
		if clientSecret:
			credData['client_secret'] = clientSecret
		credData['active'] = dlgCred.active
		credData['realm'] = dlgCred.realm
		credData['description'] = dlgCred.description.GetValue()
		credData['credential_group'] = 'default'
		if dlgCred.credGroupCheck.Value == True:
			credData['credential_group'] = dlgCred.credGroupEntry.GetValue()
		self.logger.debug('insertRestCred: credData: {}'.format(credData))
		dlgCred.Destroy()
		if value == wx.ID_OK:
			if credData['description'] is None or credData['description'] == '':
				credData.pop('description')
			if credData['password'] is None or credData['password'] == '':
				credData.pop('password')
			else:
				## Convert the password
				credData['password'], credData['wrench'] = encryptionModule.transform(credData['password'], generateToken=True)
			if credData['token'] is None or credData['token'] == '':
				credData.pop('token')
			else:
				if credData.get('wrench') is not None and credData.get('wrench') != '':
					## reuse the wrench value used with the password
					credData['token'] = encryptionModule.encode(credData['token'], credData['wrench'])
				else:
					## no password provided; we still need to create a wrench
					credData['token'], credData['wrench'] = encryptionModule.transform(credData['token'], generateToken=True)

			self.logger.debug('insertRestCred: value == OK')
			self.logger.debug('insertRestCred: credData: {}'.format(credData))
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/cred/{}'.format(self.currentProtocol), {'content' : credData})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.parentPanel, 'SUCCESS', 'Insert REST credential {}'.format(credData['user']), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('insertRestCred: cred added.')
				wx.BeginBusyCursor()
				self.getCredentialsForType(self.currentProtocol)
				wx.EndBusyCursor()
				self.updateDataPanel()
				
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.parentPanel, errorMsg, 'Credentials error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('insertRestCred: value == CANCEL')


	def insertSNMP(self, titleName):
		self.logger.debug('insertSNMP...')
		self.insertSnmpCred(titleName)

	def insertWMI(self, titleName):
		self.logger.debug('insertWMI...')
		self.insertGenericCred(titleName)

	def insertSSH(self, titleName):
		self.logger.debug('insertSSH...')
		self.insertGenericCred(titleName)

	def insertPowerShell(self, titleName):
		self.logger.debug('insertPowerShell...')
		self.insertGenericCred(titleName)

	def insertRest(self, titleName):
		self.logger.debug('insertRest...')
		self.insertRestCred(titleName)

	def OnUpdateCredButton(self, event=None):
		needToRefreshData = False
		self.logger.debug('OnUpdateCred: {}'.format(event.GetInt()))
		if self.currentProtocol == 'snmp':
			needToRefreshData = self.credsPanel.updateSNMP('SNMP')
		elif self.currentProtocol == 'wmi':
			needToRefreshData = self.credsPanel.updateWMI('WMI')
		elif self.currentProtocol == 'ssh':
			needToRefreshData = self.credsPanel.updateSSH('SSH')
		elif self.currentProtocol == 'powershell':
			needToRefreshData = self.credsPanel.updatePowerShell('PowerShell')
		elif self.currentProtocol == 'rest':
			needToRefreshData = self.credsPanel.updateRest('Rest API')
		else:
			raise NotImplementedError('Protocol type not supported: {}'.format(self.currentProtocol))
		if needToRefreshData:
			wx.BeginBusyCursor()
			self.getCredentialsForType(self.currentProtocol)
			wx.EndBusyCursor()
			self.updateDataPanel()

	def OnDeleteCredButton(self, event=None):
		if (self.credsPanel.OnDeleteCred(event)):
			wx.BeginBusyCursor()
			self.getCredentialsForType(self.currentProtocol)
			wx.EndBusyCursor()
			self.updateDataPanel()
