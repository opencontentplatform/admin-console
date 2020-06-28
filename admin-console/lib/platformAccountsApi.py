"""Pane for Admin Console ribbon destination: Platform->Accounts->API Users."""
import sys, traceback, os
import re, json, base64, uuid
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.dialogs


class UpdateDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='API Account', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='UpdateDialog', log=None, userDetails={}):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.userDetails = userDetails
		self.filterData = []
		self.logger.debug('Inside UpdateDialog')
		self.admin = False
		self.write = False
		self.delete = False
		self.active = True

		self.nameText = wx.StaticText(self.panel, wx.ID_ANY, 'Account Name:')
		self.name = wx.TextCtrl(self.panel, wx.ID_ANY, self.userDetails.get('name'), style=wx.TE_READONLY, size=(200, -1))
		self.ownerText = wx.StaticText(self.panel, wx.ID_ANY, 'Ownership:')
		self.owner = wx.TextCtrl(self.panel, wx.ID_ANY, self.userDetails.get('owner'), size=(200, -1))
		self.roleText = wx.StaticText(self.panel, wx.ID_ANY, 'Role:')
		self.role = wx.Choice(self.panel, wx.ID_ANY, (60, 50), choices=['user', 'admin'])
		self.role.SetSelection(0)
		if self.userDetails.get('access_admin', False):
			self.role.SetSelection(1)
			self.admin = True
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRole, self.role)
		self.accessText = wx.StaticText(self.panel, wx.ID_ANY, 'Access:')
		self.access = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=['read only', 'read/write', 'read/write/delete'])
		self.access.SetSelection(0)
		if self.userDetails.get('access_delete'):
			self.access.SetSelection(2)
			self.delete = True
			self.write = True
		elif self.userDetails.get('access_write'):
			self.access.SetSelection(1)
			self.write = True
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseAccess, self.access)
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		if not self.userDetails.get('active', True):
			self.activeChoice.SetSelection(1)
			self.active = False
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.token = self.userDetails.get('key')
		self.tokenText = wx.StaticText(self.panel, wx.ID_ANY, 'Token:')
		self.tokenEntry = wx.TextCtrl(self.panel, wx.ID_ANY, self.token, size=(210, -1))
		self.tokenEntry.Enable(False)
		self.newTokenButton = wx.Button(self.panel, wx.ID_ANY, 'New Token')
		self.panel.Bind(wx.EVT_BUTTON, self.OnNewTokenButton, self.newTokenButton)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.nameText, 0, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.ownerText, 0, wx.EXPAND)
		gBox1.Add(self.owner, 0, wx.EXPAND)
		gBox1.Add(self.roleText, 0, wx.EXPAND)
		gBox1.Add(self.role, 0, wx.EXPAND)
		gBox1.Add(self.accessText, 0, wx.EXPAND)
		gBox1.Add(self.access, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		gBox1.Add(self.tokenText, 0, wx.EXPAND|wx.TOP, 20)
		gBox1.Add(self.tokenEntry, 0, wx.EXPAND|wx.TOP, 20)
		gBox1.AddSpacer(1)
		gBox1.Add(self.newTokenButton, 0, wx.ALIGN_RIGHT)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.ALL, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 20)

		btnsizer = wx.StdDialogButtonSizer()
		if wx.Platform != "__WXMSW__":
			btn = wx.ContextHelpButton(self)
			btnsizer.AddButton(btn)
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

	def OnNewTokenButton(self, event):
		self.token = uuid.uuid4().hex
		self.tokenEntry.ChangeValue('{}'.format(self.token))

	def OnTokenCheck(self, event):
		if self.tokenCheck.Value == True:
			self.tokenEntry.Enable(True)
		else:
			self.tokenEntry.Enable(False)
		event.Skip()

	def EvtChooseRole(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'admin':
			self.admin = True
		else:
			self.admin = False

	def EvtChooseAccess(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'read/write':
			self.write = True
			self.delete = False
		elif event.GetString() == 'read/write/delete':
			self.write = True
			self.delete = True
		else:
			self.write = False
			self.delete = False

	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True


class InsertDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='API Account', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='InsertDialog', log=None):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.filterData = []
		self.name = None
		self.owner = None
		self.token = uuid.uuid4().hex
		self.admin = False
		self.write = False
		self.delete = False
		self.active = True
		self.logger.debug('Inside InsertDialog')

		self.nameText = wx.StaticText(self.panel, wx.ID_ANY, 'Account Name:')
		self.name = wx.TextCtrl(self.panel, wx.ID_ANY, size=(200, -1))
		self.ownerText = wx.StaticText(self.panel, wx.ID_ANY, 'Ownership:')
		self.owner = wx.TextCtrl(self.panel, wx.ID_ANY, size=(200, -1))
		self.roleText = wx.StaticText(self.panel, wx.ID_ANY, 'Role:')
		self.role = wx.Choice(self.panel, wx.ID_ANY, (60, 50), choices=['user', 'admin'])
		self.role.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseRole, self.role)
		self.accessText = wx.StaticText(self.panel, wx.ID_ANY, 'Access:')
		self.access = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=['read only', 'read/write', 'read/write/delete'])
		self.access.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseAccess, self.access)
		self.activeText = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.activeChoice = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=['True', 'False'])
		self.activeChoice.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.activeChoice)
		self.tokenText = wx.StaticText(self.panel, wx.ID_ANY, 'Token (32-bit hex value) is generated automatically,\nunless you choose to override and enter manually:')
		self.tokenCheck = wx.CheckBox(self.panel, -1, 'Manual:')
		self.tokenEntry = wx.TextCtrl(self.panel, wx.ID_ANY, size=(218, -1))
		self.tokenEntry.Enable(False)
		self.tokenCheck.Bind(wx.EVT_CHECKBOX, self.OnTokenCheck)

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.nameText, 0, wx.EXPAND)
		gBox1.Add(self.name, 0, wx.EXPAND)
		gBox1.Add(self.ownerText, 0, wx.EXPAND)
		gBox1.Add(self.owner, 0, wx.EXPAND)
		gBox1.Add(self.roleText, 0, wx.EXPAND)
		gBox1.Add(self.role, 0, wx.EXPAND)
		gBox1.Add(self.accessText, 0, wx.EXPAND)
		gBox1.Add(self.access, 0, wx.EXPAND)
		gBox1.Add(self.activeText, 0, wx.EXPAND)
		gBox1.Add(self.activeChoice, 0, wx.EXPAND)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		mainBox.Add(self.tokenText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		gBox2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox2.Add(self.tokenCheck, 0, wx.EXPAND)
		gBox2.Add(self.tokenEntry, 0, wx.EXPAND)
		mainBox.AddSpacer(5)
		mainBox.Add(gBox2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 20)

		btnsizer = wx.StdDialogButtonSizer()
		if wx.Platform != "__WXMSW__":
			btn = wx.ContextHelpButton(self)
			btnsizer.AddButton(btn)
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

	def OnTokenCheck(self, event):
		if self.tokenCheck.Value == True:
			self.tokenEntry.Enable(True)
		else:
			self.tokenEntry.Enable(False)
		event.Skip()


	def EvtChooseRole(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'admin':
			self.admin = True
		else:
			self.admin = False

	def EvtChooseAccess(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'read/write':
			self.write = True
			self.delete = False
		elif event.GetString() == 'read/write/delete':
			self.write = True
			self.delete = True
		else:
			self.write = False
			self.delete = False

	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.active = False
		else:
			self.active = True


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class ResultListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, accounts, headers, users, OutterUpdateUser, OutterDeleteUser):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.api = api
		self.accounts = accounts
		self.headers = headers
		self.userDetails = users
		self.OutterUpdateUser = OutterUpdateUser
		self.OutterDeleteUser = OutterDeleteUser
		self.logger.debug('Inside ResultListCtrlPanel: results: {}'.format(self.accounts))
		self.caption = wx.StaticText(self, label="API User Accounts:")
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.accounts
		listmix.ColumnSorterMixin.__init__(self, len(self.headers))
		mainBox = wx.BoxSizer(wx.VERTICAL)
		mainBox.Add(self.caption, 0, wx.EXPAND|wx.BOTTOM, 10)
		mainBox.Add(self.list, 1, wx.EXPAND|wx.ALL)
		self.SetSizer(mainBox)
		mainBox.Fit(self)
		self.Show()
		self.SendSizeEvent()
		self.Layout()
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
		self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
		self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
		self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		# for wxMSW
		self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
		# for wxGTK
		self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)


	def PopulateList(self, data=None):
		self.logger.debug('PopulateList... ')
		self.currentItem = 0
		self.list.ClearAll()
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		col = 0
		for header in self.headers:
			info.Align = wx.LIST_FORMAT_LEFT
			info.Text = header
			self.list.InsertColumn(col, info)
			col += 1

		self.logger.debug('inside PopulateList: data: {}'.format(self.accounts))
		self.logger.debug('inside PopulateList: count: {}'.format(self.list.GetItemCount()))
		for key,data in self.accounts.items():
			self.logger.debug('inside PopulateList: {} --> {}'.format(key, data))
			index = self.list.InsertItem(self.list.GetItemCount(), str(data[0]))
			for x in range(len(self.headers)-1):
				self.list.SetItem(index, x+1, str(data[x+1]))
			self.list.SetItemData(index, key)
		col = 0
		for header in self.headers:
			if col in [2, 3, 4, 5]:
				self.list.SetColumnWidth(col, 60)
			else:
				self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			col += 1
		self.currentItemId = None
		if self.accounts is not None and len(self.accounts) > 0:
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
			self.Bind(wx.EVT_MENU, self.OutterUpdateUser, id=self.updateID)
			self.deleteID = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, self.OutterDeleteUser, id=self.deleteID)
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
		message = ''
		pos = 0
		nameFromListItem = self.getColumnText(self.currentItem, 0)
		self.logger.debug("OnProperties: nameFromListItem: {}".format(nameFromListItem))
		originalData = self.userDetails.get(nameFromListItem, {})
		for attr,value in originalData.items():
			## Transform 'data' into JSON, and 'transformed' into visual list
			if attr == 'data':
				value = json.dumps(value, indent=4)
			elif attr == 'transformed':
				prettyValue = ""
				for entry in value.split(','):
					prettyValue = '{}\n    {}'.format(prettyValue, entry)
				value = prettyValue
			newEntry = '{}: {}\n'.format(attr, value)
			if message is None:
				message = newEntry
			else:
				message = '{}{}'.format(message, newEntry)
			pos += 1
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "Properties", size=(500, 300))
		dlg.ShowModal()
		dlg.Destroy()

	def OnUpdateUser(self, event=None):
		name = self.currentItemId
		self.logger.debug('OnUpdateUser: name: {}'.format(name))
		userDetails = self.userDetails[name]
		self.logger.debug('OnUpdateUser: {}'.format(event.GetInt()))
		dlgUser = UpdateDialog(self, log=self.logger, userDetails=userDetails)
		dlgUser.CenterOnScreen()
		value = dlgUser.ShowModal()
		needToRefreshData = False

		## Pull results out before destroying the window
		userData = {}
		if userDetails['owner'] != dlgUser.owner.GetValue():
			userData['owner'] = dlgUser.owner.GetValue()
		if userDetails['key'] != dlgUser.token:
			userData['key'] = dlgUser.token
		if userDetails['access_write'] != dlgUser.write:
			userData['access_write'] = dlgUser.write
		if userDetails['access_delete'] != dlgUser.delete:
			userData['access_delete'] = dlgUser.delete
		if userDetails['access_admin'] != dlgUser.admin:
			userData['access_admin'] = dlgUser.admin
		if userDetails['active'] != dlgUser.active:
			userData['active'] = dlgUser.active
		self.logger.debug('OnUpdateUser: userData: {}'.format(userData))
		dlgUser.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnUpdateUser: value == OK')
			self.logger.debug('OnUpdateUser: userData: {}'.format(userData))
			if len(userData) <= 0:
				dlgResult = wx.MessageDialog(self, 'No updates provided', 'Update user {}'.format(name), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
			else:
				wx.BeginBusyCursor()
				userData['source'] = 'admin console'
				(responseCode, responseAsJson) = self.api.putResource('config/ApiConsumerAccess/{}'.format(name), {'content' : userData})
				self.logger.debug('OnUpdateUser: response: {}'.format(responseAsJson))
				wx.EndBusyCursor()
				if responseCode == 200:
					dlgResult = wx.MessageDialog(self, 'SUCCESS', 'Updated user {}'.format(name), wx.OK|wx.ICON_INFORMATION)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
					self.logger.debug('OnUpdateUser: user updated.')
					needToRefreshData = True

				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self, errorMsg, 'API user error', wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
		else:
			self.logger.debug('OnUpdateUser: value == CANCEL')
		return needToRefreshData


	def OnDeleteUser(self, event=None):
		self.logger.debug('OnDeleteUserButton')
		name = self.currentItemId
		needToRefreshData = False
		self.logger.debug('OnDeleteUserButton: name: {}'.format(name))
		dlgDelete = wx.MessageDialog(self,
									 'Are you sure you want to delete user {}?'.format(name),
									 'Delete user {}'.format(name),
									 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnDeleteUserButton: value == OK')
			## If user pressed OK (and not Cancel), then call API to delete network
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.deleteResource('config/ApiConsumerAccess/{}'.format(name))
			wx.EndBusyCursor()
			if responseCode == 200:
				self.logger.debug('OnDeleteUserButton: removed user {}'.format(name))
				needToRefreshData = True
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self, errorMsg, 'Delete user {}'.format(name), wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnDeleteUserButton: value == CANCEL')
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
		## Placeholder for when we known how to create it
		self.usersPanel = RawPanel(self.parentPanel, wx.ID_ANY)

		self.insertUserButton = wx.Button(self.parentPanel, wx.ID_ANY, 'Insert Account')
		self.parentPanel.Bind(wx.EVT_BUTTON, self.OnInsertUserButton, self.insertUserButton)
		self.updateUserButton = wx.Button(self.parentPanel, wx.ID_ANY, 'Update Account')
		self.parentPanel.Bind(wx.EVT_BUTTON, self.OnUpdateUserButton, self.updateUserButton)
		self.deleteUserButton = wx.Button(self.parentPanel, wx.ID_ANY, 'Delete Account')
		self.parentPanel.Bind(wx.EVT_BUTTON, self.OnDeleteUserButton, self.deleteUserButton)
		
		self.mainBox = wx.BoxSizer(wx.VERTICAL)
		self.hBox1 = wx.BoxSizer(wx.HORIZONTAL)
		self.hBox1.Add(self.insertUserButton, 0, wx.EXPAND|wx.ALL, 10)
		self.hBox1.Add(self.updateUserButton, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
		self.hBox1.AddStretchSpacer(1)
		self.hBox1.Add(self.deleteUserButton, 0, wx.EXPAND|wx.ALL, 10)
		self.mainBox.Add(self.hBox1, 0, wx.EXPAND)
		
		self.updateDataPanel()
		wx.EndBusyCursor()


	def updateDataPanel(self):
		self.logger.debug('updateDataPanel: starting')
		self.parentPanel.Freeze()
		self.accounts = {}
		self.headers = []
		self.userDetails = {}
		self.getAccounts()
		self.logger.debug('updateDataPanel: after accounts')

		## Replace the textCtrl pane on the right
		self.mainBox.Detach(self.usersPanel)
		self.usersPanel.Destroy()
		self.usersPanel = ResultListCtrlPanel(self.parentPanel, self.logger, self.api, self.accounts, self.headers, self.userDetails, self.OnUpdateUserButton, self.OnDeleteUserButton)
		self.logger.debug('updateDataPanel: after ResultListCtrlPanel')

		self.mainBox.Add(self.usersPanel, 1, wx.EXPAND|wx.ALL, 10)

		self.mainBox.Layout()
		self.parentPanel.SetSizer(self.mainBox)
		self.parentPanel.Thaw()
		self.parentPanel.Show()
		self.parentPanel.SendSizeEvent()


	def getAccounts(self):
		apiResults = self.api.getResource('config/ApiConsumerAccess')
		objectId = 1
		self.userDetails.clear()
		self.accounts.clear()
		self.logger.debug('getAccounts: found user list: {}'.format(apiResults.get('Users', [])))
		for user in apiResults.get('Users', []):
			self.logger.debug('getAccounts: pulling user info: {}'.format(user))
			details = self.api.getResource('config/ApiConsumerAccess/{}'.format(user))
			for attr in ['object_id', 'password']:
				if attr in details:
					details.pop(attr)
			self.userDetails[user] = details
			attrList = []
			orderedList = ['name', 'owner', 'access_read', 'access_write', 'access_delete', 'access_admin', 'time_created', 'object_created_by', 'time_updated', 'object_updated_by']
			self.headers = ['name', 'owner', 'read', 'write', 'delete', 'admin', 'created', 'created by', 'last updated', 'updated by']
			for col in orderedList:
				value = details.get(col)
				if value is None:
					value = ''
				attrList.append(value)
			self.accounts[objectId] = attrList
			objectId += 1


	def OnInsertUserButton(self, event=None):
		self.logger.debug('OnInsertUserButton: {}'.format(event.GetInt()))
		dlgUser = InsertDialog(self.parentPanel, log=self.logger)
		dlgUser.CenterOnScreen()
		value = dlgUser.ShowModal()

		## Pull results out before destroying the window
		userData = {}
		userData['name'] = dlgUser.name.GetValue()
		userData['owner'] = dlgUser.owner.GetValue()
		token = uuid.uuid4().hex
		if dlgUser.tokenCheck.Value == True:
			token = dlgUser.tokenEntry.GetValue()
		userData['key'] = dlgUser.token
		userData['access_write'] = dlgUser.write
		userData['access_delete'] = dlgUser.delete
		userData['access_admin'] = dlgUser.admin
		userData['active'] = dlgUser.active
		userData['source'] = 'admin console'
		self.logger.debug('OnInsertUserButton: userData: {}'.format(userData))

		dlgUser.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnInsertUserButton: value == OK')
			if userData['name'] is None or userData['name'] == '':
				dlgResult = wx.MessageDialog(self.parentPanel, 'Did not provide a valid name', 'API user error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				return
			if userData['owner'] is None or userData['owner'] == '':
				dlgResult = wx.MessageDialog(self.parentPanel, 'Did not provide a valid owner', 'API user error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				return

			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/ApiConsumerAccess', {'content' : userData})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.parentPanel, 'SUCCESS', 'Insert user {}'.format(userData['name']), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnInsertUserButton: user added.')
				wx.BeginBusyCursor()
				self.updateDataPanel()
				wx.EndBusyCursor()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.parentPanel, errorMsg, 'API user error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnInsertUserButton: value == CANCEL')


	def OnUpdateUserButton(self, event=None):
		if (self.usersPanel.OnUpdateUser(event)):
			wx.BeginBusyCursor()
			self.updateDataPanel()
			wx.EndBusyCursor()


	def OnDeleteUserButton(self, event=None):
		if (self.usersPanel.OnDeleteUser(event)):
			wx.BeginBusyCursor()
			self.updateDataPanel()
			wx.EndBusyCursor()
