"""Pane for Admin Console ribbon destination: Platform->Config->ConfigGroups."""
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
				 name='InsertDialog', log=None, osType=None):
		wx.Dialog.__init__(self, parent, id, 'Insert {} Parameters'.format(osType), pos, size, style, name)
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
				 name='UpdateDialog', log=None, osType=None, textString=''):
		wx.Dialog.__init__(self, parent, id, 'Update {} Parameters'.format(osType), pos, size, style, name)
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


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)


class ListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, dataPanelRef):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(300, 300), style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		self.api = api
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY)
		sizer.Add(self.list, 1, wx.EXPAND)
		## Pull object count from API
		self.data = dict()
		self.getData()
		self.logger.debug('Data found: {}'.format(self.data))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.data
		listmix.ColumnSorterMixin.__init__(self, 1)
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
		# for wxMSW
		self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
		# for wxGTK
		self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)

	def getData(self):
		groups = self.owner.groupNames[self.owner.currentRealm]
		objectId = 1
		for group in groups:
			self.data[objectId] = group
			objectId += 1

	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.data
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Config Group"
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
			#self.list.SetItem(index, 0, name)
			self.list.SetItemData(index, key)
		#self.list.SetColumnWidth(0, 200)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	def getCurrentItem(self):
		return self.currentItem

	def setCurrentItem(self, value=0):
		self.currentItem = value
		self.list.Select(value)

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def OnItemSelected(self, event):
		self.currentItem = event.Index
		name = self.list.GetItemText(self.currentItem)
		self.logger.debug("OnItemSelected: %s, %s" % (self.currentItem, name))
		self.owner.currentGroup = name
		self.owner.resetMainPanel()
		event.Skip()

	def OnItemDeselected(self, evt):
		item = evt.GetItem()
		self.logger.debug("OnItemDeselected: %d" % evt.Index)

	def OnItemActivated(self, event):
		self.currentItem = event.Index
		self.logger.debug("OnItemActivated: %s\nTopItem: %s" %
						   (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))

	def OnColClick(self, event):
		self.logger.debug("OnColClick: %d\n" % event.GetColumn())
		#self.owner.resetMainPanel
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
		self.logger.debug("OnColBeginDrag")

	def OnColDragging(self, event):
		self.logger.debug("OnColDragging")

	def OnColEndDrag(self, event):
		self.logger.debug("OnColEndDrag")

	def OnDoubleClick(self, event):
		self.logger.debug("OnDoubleClick item %s\n" % self.list.GetItemText(self.currentItem))
		event.Skip()

	def OnRightClick(self, event):
		self.logger.debug("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))


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


class Main():
	def __init__(self, thisPanel, log, api):
		self.logger = log
		self.api = api
		self.thisPanel = thisPanel

		self.mainBox = None
		self.mainQueryBox = None
		self.leftSizer = None
		self.listPanel = None
		self.rbRealm = None
		self.insertButton = None
		self.updateButton = None
		self.deleteButton = None
		self.leftPanelStaticBox = None
		self.logger.debug('Main.init: 1')

		self.groupNames = {}
		self.groupData = {}
		self.realms = []
		self.realmData = {}
		self.currentGroup = None
		self.currentGroupId = None
		self.getRealms()
		self.currentRealm = None
		if len(self.realms) > 0:
			self.currentRealm = self.realms[0]
			self.currentRealmId = 0
			if len(self.groupNames.get(self.currentRealm, [])) > 0:
				self.currentGroup = self.groupNames.get(self.currentRealm)[0]

		self.logger.debug('Main.init: 2')

		self.leftPanelStaticBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, "Config Groups")

		self.rbRealm = wx.RadioBox(self.leftPanelStaticBox, wx.ID_ANY, 'Realm Selection', wx.DefaultPosition, wx.DefaultSize, self.realms, 1, wx.RA_SPECIFY_COLS)
		self.leftPanelStaticBox.Bind(wx.EVT_RADIOBOX, self.EvtRealmRadioBox, self.rbRealm)
		self.rbRealm.SetToolTip(wx.ToolTip('Select a Realm'))

		self.insertButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Insert')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnInsertButton, self.insertButton)
		self.updateButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Update')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnUpdateButton, self.updateButton)
		self.deleteGroupButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Delete Group')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnDeleteGroupButton, self.deleteGroupButton)
		self.deleteRealmButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Delete Realm')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnDeleteRealmButton, self.deleteRealmButton)

		self.listPanel = ListCtrlPanel(self.leftPanelStaticBox, self.logger, self.api, self)

		self.listPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.listPanelSizer.Add(self.listPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		#self.leftSizer.Insert(3, self.listPanelSizer, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		self.mainQueryBox.AddSpacer(2)
		self.mainQueryBox.Add(self.leftPanelStaticBox, 2, wx.LEFT|wx.BOTTOM, 5)

		topBorder, otherBorder = self.leftPanelStaticBox.GetBordersForSizer()
		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.AddSpacer(topBorder + 3)
		self.leftSizer.Add(self.rbRealm, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(8)

		self.leftSizer.Add(self.listPanelSizer, 1, wx.EXPAND)
		self.leftSizer.AddSpacer(20)

		self.leftSizer.Add(self.insertButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.updateButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.deleteGroupButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(20)
		self.leftSizer.Add(self.deleteRealmButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)

		self.leftPanelStaticBox.SetSizer(self.leftSizer)
		## Placeholder for when we known how to create an TextCtrl
		self.textCtrl = RawPanel(self.thisPanel, wx.ID_ANY)

		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainBox.Add(self.mainQueryBox, 0, wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 15)
		self.thisPanel.SetSizer(self.mainBox)
		#self.listPanel.setCurrentItem()
		self.logger.debug('Main.init: 3')
		self.resetMainPanel()

		wx.EndBusyCursor()


	def resetMainPanel(self, preserve=True):
		self.logger.debug('Start resetMainPanel')
		self.thisPanel.Freeze()

		## Get current dataSet to display in the textCtl pane on the right
		self.logger.debug('resetMainPanel: currentRealm: {}'.format(self.currentRealm))
		self.logger.debug('resetMainPanel: currentGroup: {}'.format(self.currentGroup))
		self.logger.debug('resetMainPanel: groupData: {}'.format(self.groupData))
		dataSet = self.groupData.get(self.currentRealm, {}).get(self.currentGroup)

		## Replace the textCtrl pane on the right
		self.mainBox.Detach(self.textCtrl)
		self.textCtrl.Destroy()
		if dataSet is not None:
			self.logger.debug('resetMainPanel: dataSet: {}'.format(dataSet))
			textString = json.dumps(dataSet, indent=8)
			self.textCtrl = wx.TextCtrl(self.thisPanel, wx.ID_ANY, textString, style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY|wx.EXPAND)
		else:
			self.textCtrl = RawPanel(self.thisPanel, wx.ID_ANY)
		self.mainBox.Add(self.textCtrl, 1, wx.EXPAND|wx.ALL, 15)

		if not preserve:
			## Conditionally replace the config group list on the left
			newListPanel = ListCtrlPanel(self.leftPanelStaticBox, self.logger, self.api, self)
			self.leftSizer.Detach(self.listPanelSizer)
			self.listPanel.Destroy()
			self.listPanel = newListPanel
			self.listPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
			self.listPanelSizer.Add(self.listPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
			self.leftSizer.Insert(3, self.listPanelSizer, wx.EXPAND)
			self.leftSizer.Layout()
			self.leftPanelStaticBox.Layout()
			## setCurrentItem will call resetMainPanel again, for force resizing
			self.listPanel.setCurrentItem()

		self.logger.debug('Main.resetMainPanel: 1')
		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()
		self.logger.debug('Stop resetMainPanel')


	def getRealms(self):
		apiResults = self.api.getResource('config/Realm')
		for name in apiResults.get('realms', {}):
			self.logger.debug('getRealms: getRealms: realm {}'.format(name))
			self.realms.append(name)
			self.getData(name)

	def getData(self, realm):
		apiResults = self.api.getResource('config/ConfigGroups/{}'.format(realm))
		realmData = apiResults.get('content', {})
		self.groupNames[realm] = []
		self.groupData[realm] = {}
		self.logger.debug('getData: getData: apiResults {}'.format(apiResults))
		for entry in realmData:
			name = entry.get('name')
			self.groupNames[realm].append(name)
			self.groupData[realm][name] = entry
		self.logger.debug('getData: getData: groupNames {}'.format(self.groupNames))

	def EvtRealmRadioBox(self, event):
		realmId = event.GetInt()
		self.logger.debug('EvtRealmRadioBox: currentRealm : {}'.format(self.currentRealm))
		if self.currentRealmId != realmId:
			try:
				self.currentRealm = self.realms[realmId]
				self.logger.debug('EvtRealmRadioBox: switching to realm {}'.format(self.currentRealm))
				self.currentRealmId = realmId
				wx.BeginBusyCursor()
				self.logger.debug('EvtRealmRadioBox: ListCtrlPanel rebuild')
				self.resetMainPanel(preserve=False)
				wx.EndBusyCursor()
			except:
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				self.logger.debug('Failure in EvtRealmRadioBox: {}'.format(stacktrace))


	def OnInsertButton(self, event=None):
		myDialog = InsertDialog(self.thisPanel, log=self.logger, osType=self.currentGroup)
		myDialog.CenterOnScreen()
		value = myDialog.ShowModal()
		## Pull results out before destroying the window
		data = {}
		data['realm'] = self.currentRealm
		groupData = myDialog.textCtrl.GetValue()
		myDialog.Destroy()
		if value == wx.ID_OK:
			if groupData is None or groupData == '':
				self.logger.debug('OnInsertButton: nothing to insert')
				return
			dataAsDict = json.loads(groupData)
			## POST operations update a list of entries in one fell swoop
			data['content'] = []
			data['content'].append(dataAsDict)
			data['source'] = 'admin console'
			self.logger.debug('OnInsertButton: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/ConfigGroups', {'content' : data})
			if responseCode == 405:
				## PUT operations only update one entry at a time
				data['content'] = dataAsDict
				data['source'] = 'admin console'
				(responseCode, responseAsJson) = self.api.putResource('config/ConfigGroups/{}'.format(self.currentRealm), {'content' : data})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Inserted ConfigGroups for realm '.format(self.currentRealm), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnInsertButton: ConfigGroups added.')
				wx.BeginBusyCursor()
				thisGroupName = dataAsDict.get('name')

				## Update the local cached data
				self.groupData[self.currentRealm][thisGroupName] = dataAsDict
				self.groupNames[self.currentRealm].append(thisGroupName)
				self.logger.debug('EvtRealmRadioBox: ListCtrlPanel rebuild')

				## Don't preserve; need to rebuild the items
				self.resetMainPanel(preserve=False)
				wx.EndBusyCursor()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'ConfigGroups insert error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnInsertButton: value == CANCEL')

	def OnUpdateButton(self, event=None):
		dataSet = self.groupData[self.currentRealm][self.currentGroup]
		dataSetString = json.dumps(dataSet, indent=8)
		self.logger.debug('OnUpdateButton: dataSetString: {}'.format(dataSetString))
		myDialog = UpdateDialog(self.thisPanel, log=self.logger, osType=self.currentGroup, textString=dataSetString)
		myDialog.CenterOnScreen()
		value = myDialog.ShowModal()
		## Pull results out before destroying the window
		data = {}
		groupData = myDialog.textCtrl.GetValue()
		myDialog.Destroy()
		if value == wx.ID_OK:
			if groupData is None or groupData == '':
				self.logger.debug('OnInsertButton: nothing to insert')
				return
			dataAsDict = json.loads(groupData)
			data['content'] = dataAsDict
			data['source'] = 'admin console'
			self.logger.debug('OnUpdateButton: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.putResource('config/ConfigGroups/{}'.format(self.currentRealm), {'content' : data})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Updated ConfigGroups for realm '.format(self.currentRealm), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnUpdateButton: ConfigGroups added.')
				## Update the local cached data
				thisGroupName = dataAsDict.get('name')
				self.groupData[self.currentRealm][thisGroupName] = dataAsDict
				self.resetMainPanel()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'ConfigGroups update error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnUpdateButton: value == CANCEL')


	def OnDeleteGroupButton(self, event=None):
		dataSet = self.groupData[self.currentRealm][self.currentGroup]
		dataSetString = json.dumps(dataSet, indent=8)
		self.logger.debug('OnDeleteGroupButton: dataSetString: {}'.format(dataSetString))
		self.logger.debug('OnDeleteGroupButton: currentRealm: {}'.format(self.currentRealm))
		self.logger.debug('OnDeleteGroupButton: currentGroup: {}'.format(self.currentGroup))
		self.logger.debug('OnDeleteGroupButton: realm data: {}'.format(self.groupData[self.currentRealm]))


		dlgDelete = wx.MessageDialog(self.thisPanel, 'Are you sure you want to delete group {}?'.format(self.currentGroup), 'Delete cred {}'.format(self.currentGroup), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		wx.BeginBusyCursor()
		try:
			if value == wx.ID_OK:
				self.logger.debug('OnDeleteGroupButton: value == OK')
				## If user pressed OK (and not Cancel), then call API to delete
				(responseCode, responseAsJson) = self.api.deleteResource('config/ConfigGroups/{}/{}'.format(self.currentRealm, self.currentGroup))
				if responseCode == 200:
					self.logger.debug('OnDeleteGroupButton: removed ConfigGroup {}'.format(self.currentGroup))
					needToRefreshData = True
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'Delete ConfigGroup {}'.format(self.currentGroup), wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
				## Probably can just use cache, but let's pull updated data
				self.getRealms()
				## Don't preserve; need to rebuild the items
				self.resetMainPanel(preserve=False)
			else:
				self.logger.debug('OnDeleteGroupButton: value == CANCEL')
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in OnDeleteGroupButton: {}'.format(stacktrace))
		wx.EndBusyCursor()


	def OnDeleteRealmButton(self, event=None):

		dlgDelete = wx.MessageDialog(self.thisPanel, 'Are you sure you want to delete all entries in the {} realm?'.format(self.currentRealm), 'Delete realm {}'.format(self.currentRealm), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		wx.BeginBusyCursor()
		try:
			if value == wx.ID_OK:
				self.logger.debug('OnDeleteGroupButton: value == OK')
				## If user pressed OK (and not Cancel), then call API to delete
				self.logger.debug('OnDeleteRealmButton: removing {}'.format(self.currentRealm))
				(responseCode, responseAsJson) = self.api.deleteResource('config/ConfigGroups/{}'.format(self.currentRealm))
				if responseCode == 200:
					dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Removed ConfigGroups for realm '.format(self.currentRealm), wx.OK|wx.ICON_INFORMATION)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
					self.logger.debug('OnDeleteRealmButton: ConfigGroups removed.')
					## Update the local cached data
					self.groupData[self.currentRealm] = {}
					self.groupNames[self.currentRealm] = []
					self.logger.debug('OnDeleteRealmButton: ListCtrlPanel rebuild')
					## Don't preserve; need to rebuild the items
					self.resetMainPanel(preserve=False)
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'ConfigGroups delete error', wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in OnDeleteRealmButton: {}'.format(stacktrace))
		wx.EndBusyCursor()

