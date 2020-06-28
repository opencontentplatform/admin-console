"""Pane for Admin Console ribbon destination: Platform->Boundary->Networks."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress
from ipaddress import IPv4Network

import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.dialogs

provider = wx.SimpleHelpProvider()
wx.HelpProvider.Set(provider)



class ScopeDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Network Scope', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='ScopeDialog', log=None):
		wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.focusPane = 0
		self.logger.debug('Inside ScopeDialog')

		mainBox = wx.BoxSizer(wx.VERTICAL)
		txt = 'Fill out one of the following sections:'
		staticText1 = 'The first section accepts a network entry, entered as either a CIDR format\n(e.g. 10.2.1.0/24) or an IP/mask format (e.g. 10.2.1.0/255.255.255.0).'
		staticText2 = 'The second section accepts a single IP address.'
		staticText3 = 'The last section accepts two IPs for a start/stop range (10.2.1.32 - 10.2.1.57).'
		self.text = wx.StaticText(self.panel, wx.ID_ANY, txt)
		mainBox.AddSpacer(10)
		mainBox.Add(self.text, 0, wx.EXPAND|wx.ALL, 15)
		mainBox.AddSpacer(20)

		## Network section
		self.text1 = wx.StaticText(self.panel, wx.ID_ANY, staticText1)
		mainBox.Add(self.text1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
		self.cidrPane = wx.CollapsiblePane(self.panel, label='Network/CIDR', style=wx.CP_DEFAULT_STYLE, name='cidrPane')
		self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCidrPaneChanged, self.cidrPane)
		self.MakeCidrPaneContent(self.cidrPane.GetPane())
		mainBox.Add(self.cidrPane, 0, wx.EXPAND|wx.ALL, 10)

		## Single IP section
		mainBox.AddSpacer(20)
		self.text2 = wx.StaticText(self.panel, wx.ID_ANY, staticText2)
		mainBox.Add(self.text2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
		self.ipPane = wx.CollapsiblePane(self.panel, label='Single IP', style=wx.CP_DEFAULT_STYLE, name='ipPane')
		self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnIpPaneChanged, self.ipPane)
		self.MakeIpPaneContent(self.ipPane.GetPane())
		mainBox.Add(self.ipPane, 0, wx.EXPAND|wx.ALL, 10)

		## IP Range section
		mainBox.AddSpacer(20)
		self.text2 = wx.StaticText(self.panel, wx.ID_ANY, staticText2)
		mainBox.Add(self.text2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
		self.ipRangePane = wx.CollapsiblePane(self.panel, label='IP Range', style=wx.CP_DEFAULT_STYLE, name='ipRangePane')
		self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnIpRangePaneChanged, self.ipRangePane)
		self.MakeIpRangePaneContent(self.ipRangePane.GetPane())
		mainBox.Add(self.ipRangePane, 0, wx.EXPAND|wx.ALL, 10)

		## OK / Cancel buttons
		mainBox.AddSpacer(20)
		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.TOP, 5)
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
		mainBox.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)

		## Layout
		self.panel.Layout()
		self.panel.SetSizer(mainBox)
		mainBox.Fit(self.panel)
		self.panel.Show()


	def OnCidrPaneChanged(self, evt=None):
		if evt:
			self.logger.debug('OnPaneChanged: wx.EVT_COLLAPSIBLEPANE_CHANGED: %s' % evt.Collapsed)
		self.focusPane = 0
		self.ipPane.Collapse(True)
		self.ipRangePane.Collapse(True)
		self.Layout()

	def OnIpPaneChanged(self, evt=None):
		if evt:
			self.logger.debug('OnPaneChanged: wx.EVT_COLLAPSIBLEPANE_CHANGED: %s' % evt.Collapsed)
		self.focusPane = 1
		self.cidrPane.Collapse(True)
		self.ipRangePane.Collapse(True)
		self.Layout()

	def OnIpRangePaneChanged(self, evt=None):
		if evt:
			self.logger.debug('OnPaneChanged: wx.EVT_COLLAPSIBLEPANE_CHANGED: %s' % evt.Collapsed)
		self.focusPane = 2
		self.cidrPane.Collapse(True)
		self.ipPane.Collapse(True)
		self.Layout()

	def MakeCidrPaneContent(self, pane):
		'''Just make a few controls to put on the collapsible pane'''
		entry1Lbl = wx.StaticText(pane, -1, "Network:")
		self.CidrEntry = wx.TextCtrl(pane, -1, "");
		panelSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		panelSizer.AddGrowableCol(1)
		panelSizer.Add(entry1Lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		panelSizer.Add(self.CidrEntry, 0, wx.EXPAND)
		border = wx.BoxSizer()
		border.Add(panelSizer, 1, wx.EXPAND|wx.ALL, 5)
		pane.SetSizer(border)

	def MakeIpPaneContent(self, pane):
		'''Just make a few controls to put on the collapsible pane'''
		entry1Lbl = wx.StaticText(pane, -1, "Single IP:")
		self.IpEntry = wx.TextCtrl(pane, -1, "")
		panelSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		panelSizer.AddGrowableCol(1)
		panelSizer.Add(entry1Lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		panelSizer.Add(self.IpEntry, 0, wx.EXPAND)
		border = wx.BoxSizer()
		border.Add(panelSizer, 1, wx.EXPAND|wx.ALL, 5)
		pane.SetSizer(border)

	def MakeIpRangePaneContent(self, pane):
		'''Just make a few controls to put on the collapsible pane'''
		entry1Lbl = wx.StaticText(pane, -1, "Starting IP:")
		self.IpRangeEntry1 = wx.TextCtrl(pane, -1, "")
		entry2Lbl = wx.StaticText(pane, -1, "Ending IP:")
		self.IpRangeEntry2 = wx.TextCtrl(pane, -1, "")
		panelSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		panelSizer.AddGrowableCol(1)
		panelSizer.Add(entry1Lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		panelSizer.Add(self.IpRangeEntry1, 0, wx.EXPAND)
		panelSizer.Add(entry2Lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		panelSizer.Add(self.IpRangeEntry2, 0, wx.EXPAND)
		border = wx.BoxSizer()
		border.Add(panelSizer, 1, wx.EXPAND|wx.ALL, 5)
		pane.SetSizer(border)


class NetworkDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='Network Scope', size=wx.DefaultSize,
				 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
				 name='NetworkDialog', log=None, api=None, realm=None):
		## Instead of calling default Dialog constructor; set Context Help...
		##wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
		wx.Dialog.__init__(self)
		self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		self.Create(parent, id, title, pos, size, style, name)
		self.panel = self
		self.logger = log
		self.api = api
		self.realm = realm
		self.filterData = []
		self.scopeData = None
		self.description = None
		self.scopeIsEnabled = True
		self.logger.debug('Inside NetworkDialog')

		self.text1 = wx.StaticText(self.panel, wx.ID_ANY, 'Realm:')
		self.text1.SetHelpText("Realm where this scope will be applied")
		self.entry1 = wx.TextCtrl(self.panel, wx.ID_ANY, self.realm, style=wx.TE_READONLY)
		self.entry1.SetHelpText("Realm where this scope will be applied")
		self.text2 = wx.StaticText(self.panel, wx.ID_ANY, 'Active:')
		self.text2.SetHelpText("Is this scope active? When set to False, the scope is disabled/ignored in this realm.")
		self.entry2 = wx.Choice(self.panel, wx.ID_ANY, (120, 50), choices=['True', 'False'])
		self.entry2.SetHelpText("Is this scope active? When set to False, the scope is disabled and ignored in this realm.")
		self.entry2.SetSelection(0)
		self.panel.Bind(wx.EVT_CHOICE, self.EvtChooseEnabled, self.entry2)

		self.text3 = wx.StaticText(self.panel, wx.ID_ANY, 'Description:')
		self.text3.SetHelpText("Description for the network entry for future reference")
		self.description = wx.TextCtrl(self.panel, wx.ID_ANY, size=(200, -1))
		self.description.SetHelpText("Description for the network entry for future reference")

		self.scopeButton = wx.Button(self.panel, wx.ID_ANY, "Define Scope", (50,50))
		self.scopeButton.SetHelpText("Required: define a Network Scope for this domain")
		self.panel.Bind(wx.EVT_BUTTON, self.OnScopeButton, self.scopeButton)
		self.scopePanel = wx.TextCtrl(self.panel, wx.ID_ANY, size=(-1, 25), style=wx.EXPAND|wx.TE_READONLY)
		self.scopePanel.SetHelpText("Newly defined scope is visable here")

		self.filterButton = wx.Button(self.panel, wx.ID_ANY, "Define Filter", (50,50))
		self.filterButton.SetHelpText("Optional: define an exclusion for the above scope")
		self.panel.Bind(wx.EVT_BUTTON, self.OnFilterButton, self.filterButton)
		self.filterPanel = wx.TextCtrl(self.panel, wx.ID_ANY, size=(-1, 75), style=wx.EXPAND|wx.TE_READONLY|wx.TE_MULTILINE)
		self.filterPanel.Enable(False)
		self.filterPanel.SetHelpText("Defined filters are visible here")

		mainBox = wx.BoxSizer(wx.VERTICAL)
		gBox1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
		gBox1.Add(self.text1, 0, wx.EXPAND)
		gBox1.Add(self.entry1, 0, wx.EXPAND)
		gBox1.Add(self.text2, 0, wx.EXPAND)
		gBox1.Add(self.entry2, 0, wx.EXPAND)
		gBox1.Add(self.text3, 0, wx.EXPAND)
		gBox1.Add(self.description, 0, wx.EXPAND|wx.BOTTOM, 20)
		mainBox.Add(gBox1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
		mainBox.Add(self.scopeButton, 0, wx.LEFT|wx.RIGHT, 20)
		mainBox.AddSpacer(5)
		mainBox.Add(self.scopePanel, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)
		mainBox.Add(self.filterButton, 0, wx.LEFT|wx.RIGHT, 20)
		mainBox.AddSpacer(5)
		mainBox.Add(self.filterPanel, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		mainBox.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 20)

		btnsizer = wx.StdDialogButtonSizer()
		if wx.Platform != "__WXMSW__":
			btn = wx.ContextHelpButton(self)
			btnsizer.AddButton(btn)
		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("Submit the network scope")
		btn.SetDefault()
		btnsizer.AddButton(btn)
		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("Cancel dialog and discard the scope")
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		mainBox.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 15)

		self.panel.SetSizer(mainBox)
		mainBox.Fit(self.panel)
		self.panel.Show()


	def EvtChooseEnabled(self, event):
		self.logger.debug('EvtChoice: %s\n' % event.GetString())
		if event.GetString() == 'False':
			self.scopeIsEnabled = False
		else:
			self.scopeIsEnabled = True

	def OnScopeButton(self, event=None):
		self.logger.debug('OnScopeButton')
		dlgScope = ScopeDialog(self, log=self.logger)
		dlgScope.CenterOnScreen()
		value = dlgScope.ShowModal()
		## Pull results out before destroying the window
		result = {}
		if dlgScope.focusPane == 0:
			result['entry'] = dlgScope.CidrEntry.GetValue()
		elif dlgScope.focusPane == 1:
			result['entry'] = dlgScope.IpEntry.GetValue()
		elif dlgScope.focusPane == 2:
			result['entry'] = dlgScope.IpRangeEntry1.GetValue()
			result['entryStop'] = dlgScope.IpRangeEntry2.GetValue()
		dlgScope.Destroy()
		## If OK and not CANCEL, then keep the results
		if value == wx.ID_OK:
			self.logger.debug('OnScopeButton: value == OK')
			self.logger.debug('OnScopeButton: result: {}'.format(result))
			self.scopePanel.SetValue(str(result))
			self.scopeData = result
		else:
			self.logger.debug('OnScopeButton: value == CANCEL')

	def OnFilterButton(self, event=None):
		self.logger.debug('OnFilterButton')
		dlgScope = ScopeDialog(self, log=self.logger)
		dlgScope.CenterOnScreen()
		value = dlgScope.ShowModal()
		## Pull results out before destroying the window
		result = {}
		if dlgScope.focusPane == 0:
			result['entry'] = dlgScope.CidrEntry.GetValue()
		elif dlgScope.focusPane == 1:
			result['entry'] = dlgScope.IpEntry.GetValue()
		elif dlgScope.focusPane == 2:
			result['entry'] = dlgScope.IpRangeEntry1.GetValue()
			result['entryStop'] = dlgScope.IpRangeEntry2.GetValue()
		dlgScope.Destroy()
		## If OK and not CANCEL, then keep the results
		if value == wx.ID_OK:
			self.logger.debug('OnFilterButton: value == OK')
			self.logger.debug('OnFilterButton: result: {}'.format(result))
			self.filterPanel.WriteText('{}\n'.format(str(result)))
			self.filterData.append(result)
		else:
			self.logger.debug('OnFilterButton: value == CANCEL')


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class ResultListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, networkScopes, currentRealm):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.api = api
		self.SetAutoLayout(1)
		self.networkScopes = networkScopes
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		self.list.SetAutoLayout(1)
		self.logger.debug('Inside ResultListCtrlPanel')
		## Pull object count from API
		self.resultsActive = dict()
		self.results = dict()
		self.headersActive = None
		self.headers = []
		self.getResults(currentRealm)
		self.resultAttrs = list(range(0,len(self.headersActive)))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.resultsActive
		listmix.ColumnSorterMixin.__init__(self, len(self.headers))
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


	def getResults(self, realm):
		self.logger.debug('Inside ResultListCtrlPanel.getResults ...')
		results = self.networkScopes.get(realm, {})
		createdHeaders = False
		objectId = 0
		for entryId,entry in results.items():
			attrList = []
			if not createdHeaders:
				#self.headers = []
				for attr,value in entry.items():
					if value is None:
						value = ''
					attrList.append(value)
					self.headers.append(attr)
				createdHeaders = True
			else:
				for attr,value in entry.items():
					if value is None:
						value = ''
					attrList.append(value)
			self.results[entryId] = attrList
			## Shallow copy to allow deleting columns from the active version
			self.resultsActive[entryId] = attrList[:]
			objectId += 1
		self.logger.debug('getResults: {}'.format(self.results))
		## Shallow copy to manage filters/searches without new API queries
		self.headersActive = self.headers[:]
		return

	def OnUpdateColumns(self):
		self.logger.info('OnUpdateColumns: {}'.format(self.resultsActive))
		for key,data in self.resultsActive.items():
			self.logger.info('OnUpdateColumns looking at {} : {}'.format(key, data))
			self.logger.info('OnUpdateColumns range           : {}'.format(list(range(0, len(self.headers)))))
			self.logger.info('OnUpdateColumns self.resultAttrs: {}'.format(self.resultAttrs))
			## Go in reverse since we're deleting in place
			for x in reversed(range(0, len(self.headers))):
				self.logger.info('OnUpdateColumns x: {}'.format(x))
				if x not in self.resultAttrs:
					self.logger.info('OnUpdateColumns removing index {} with value {}'.format(x, data[x]))
					del data[x]
			self.resultsActive[key] = data

	def initResultsActive(self):
		self.resultsActive.clear()
		for resultId,resultValue in self.results.items():
			## Shallow copy to allow deleting columns from the active version
			self.resultsActive[resultId] = resultValue[:]

	def PopulateList(self, data=None):
		self.logger.debug('PopulateList... ')
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.resultsActive
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		col = 0
		for header in self.headersActive:
			info.Align = wx.LIST_FORMAT_LEFT
			info.Text = header
			self.list.InsertColumn(col, info)
			col += 1
		items = data.items()

		for key,data in items:
			index = self.list.InsertItem(self.list.GetItemCount(), str(data[0]))
			for x in range(len(self.headersActive)-1):
				self.list.SetItem(index, x+1, str(data[x+1]))
			self.list.SetItemData(index, key)
		col = 0
		for header in self.headersActive:
			if col in [0, 2, 6]:
				self.list.SetColumnWidth(col, 60)
			else:
				self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			col += 1
		self.currentItemId = None
		if data is not None and len(data) > 0:
			self.currentItemId = int(self.getColumnText(self.currentItem, 0))
		#self.list.FitInside()
		self.list.Fit()



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
		self.currentItemId = int(self.getColumnText(self.currentItem, 0))
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
		self.currentItemId = int(self.getColumnText(self.currentItem, 0))
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
		self.OnPropertiesPopup(None)
		event.Skip()

	def OnRightClick(self, event):
		self.logger.debug("OnRightClick %s" % self.list.GetItemText(self.currentItem))
		# only do this part the first time so the events are only bound once
		if not hasattr(self, "propertiesID"):
			self.propertiesID = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, self.OnPropertiesPopup, id=self.propertiesID)
		menu = wx.Menu()
		menu.Append(self.propertiesID, "Properties")
		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		self.PopupMenu(menu)
		menu.Destroy()

	def OnPropertiesPopup(self, event):
		self.logger.debug("OnPropertiesPopup: currentItem: {}".format(self.currentItem))
		message = ''
		pos = 0
		objectIdFromListItem = int(self.getColumnText(self.currentItem, 0))
		realmFromListItem = self.getColumnText(self.currentItem, 1)
		self.logger.debug("OnPropertiesPopup: objectIdFromListItem: {}".format(objectIdFromListItem))
		self.logger.debug("OnPropertiesPopup: realmFromListItem: {}".format(realmFromListItem))
		self.logger.debug("OnPropertiesPopup: realm data: {}".format(self.networkScopes[realmFromListItem]))
		originalData = self.networkScopes[realmFromListItem][objectIdFromListItem]
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
		self.logger.debug('OnPropertiesPopup: 3: message: {}'.format(message))
		self.logger.debug('OnPropertiesPopup: 3: size: {}'.format(len(message)))
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "Properties", size=(500, 300))
		dlg.ShowModal()
		dlg.Destroy()


class ResultObjects():
	def __init__(self, thisPanel, log, api, networkScopes, currentRealm):
		self.thisPanel = thisPanel
		self.logger = log
		self.api = api
		self.networkScopes = networkScopes
		self.logger.debug('Inside ResultObjects')

		self.resultList = ResultListCtrlPanel(thisPanel, self.logger, self.api, self.networkScopes, currentRealm)
		self.filter = wx.SearchCtrl(thisPanel, style=wx.TE_PROCESS_ENTER)
		self.filter.ShowCancelButton(True)
		self.filter.Bind(wx.EVT_TEXT, self.OnSearch)
		self.filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: self.filter.SetValue(''))
		self.filter.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
		## Create boxes to arrange the panels
		mainBox = wx.BoxSizer(wx.VERTICAL)
		## Box on top for the search and attribute controls
		hBox1 = wx.BoxSizer(wx.HORIZONTAL)
		hBox1.Add(self.filter, 1, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
		if 'wxMac' in wx.PlatformInfo:
			hBox1.Add((5,5))  # Make sure there is room for the focus ring
		self.attributeButton = wx.Button(thisPanel, -1, "Select Columns", (50,50))
		thisPanel.Bind(wx.EVT_BUTTON, self.OnAttributeButton, self.attributeButton)
		hBox1.Add(self.attributeButton, 0, wx.EXPAND)
		mainBox.Add(hBox1, 0, wx.EXPAND|wx.ALL, 10)
		hBox2 = wx.BoxSizer(wx.HORIZONTAL)
		vBox1 = wx.BoxSizer(wx.VERTICAL)
		boxLabel = wx.StaticText(self.thisPanel, wx.ID_ANY, 'Network Configurations:')
		vBox1.Add(boxLabel, 0, wx.EXPAND)
		vBox1.AddSpacer(5)
		vBox1.Add(self.resultList, 1, wx.EXPAND|wx.ALL)
		hBox2.Add(vBox1, 1, wx.EXPAND)

		mainBox.Add(hBox2, 1, wx.EXPAND|wx.ALL, 10)
		thisPanel.SetSizer(mainBox)
		thisPanel.Show()
		thisPanel.SendSizeEvent()


	def OnAttributeButton(self, event=None):
		dlg = wx.MultiChoiceDialog(self.thisPanel, "Only selected attributes will be displayed", "Object Attributes", self.resultList.headers)
		## Pre-select what is currently displayed
		dlg.SetSelections(self.resultList.resultAttrs)
		if (dlg.ShowModal() == wx.ID_OK):
			self.resultList.resultAttrs = dlg.GetSelections()
			self.resultList.headersActive = [self.resultList.headers[x] for x in self.resultList.resultAttrs]
			self.logger.debug("New attribute list for headers: {}".format(self.resultList.headersActive))
		dlg.Destroy()
		## Force the resultsActive to get all column values before updating; do
		## this in case a new column was shown instead of just hid; need to
		## update the dataset given to the MixIn that enables column sorting.
		self.UpdateResultsActive()
		self.resultList.OnUpdateColumns()
		self.resultList.PopulateList()
		## Now update the ColumnSorterMixin references for future column touches
		self.resultList.SetColumnCount(len(self.resultList.headersActive))
		self.resultList.itemDataMap = self.resultList.resultsActive
		## Send a size event to refresh the scroll bar
		self.resultList.list.SendSizeEvent()
		self.thisPanel.SendSizeEvent()


	def UpdateResultsActive(self):
		value = self.filter.GetValue()
		if not value:
			self.logger.info('UpdateResultsActive: fill all')
			self.logger.info('UpdateResultsActive: results      : {}'.format(self.resultList.results))
			self.resultList.resultsActive.clear()
			for prevId,data in self.resultList.results.items():
				self.resultList.resultsActive[prevId] = data[:]
		else:
			self.logger.info('UpdateResultsActive: filter fill')
			self.resultList.resultsActive.clear()
			newId = 1
			for prevId,data in self.resultList.results.items():
				for entry in data:
					if re.search(str(value), str(entry), re.I):
						self.resultList.resultsActive[newId] = data[:]
						newId += 1
						break
		self.logger.info('UpdateResultsActive: resultsActive: {}'.format(self.resultList.resultsActive))


	def OnSearch(self, event=None):
		value = self.filter.GetValue()
		if not value:
			self.resultList.initResultsActive()
			self.resultList.OnUpdateColumns()
			self.resultList.PopulateList()
			self.resultList.SendSizeEvent()
			return
		wx.BeginBusyCursor()
		newId = 1
		self.resultList.resultsActive.clear()
		for prevId,data in self.resultList.results.items():
			for entry in data:
				if re.search(str(value), str(entry), re.I):
					self.resultList.resultsActive[newId] = data[:]
					newId += 1
					break
		self.resultList.OnUpdateColumns()
		self.resultList.PopulateList()
		self.resultList.SendSizeEvent()
		wx.EndBusyCursor()


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

		self.realms = []
		self.getRealms()
		self.currentRealm = None
		if len(self.realms) > 0:
			self.currentRealm = self.realms[0]
			self.currentRealmId = 0

		self.leftPanelStaticBox = wx.StaticBox(self.parentPanel, wx.ID_ANY, "Networks")
		self.rb = wx.RadioBox(self.leftPanelStaticBox, wx.ID_ANY, 'Realm Selection', wx.DefaultPosition, wx.DefaultSize, self.realms, 1, wx.RA_SPECIFY_COLS)
		self.leftPanelStaticBox.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
		self.rb.SetToolTip(wx.ToolTip('Select a Realm'))
		self.insertNetworkButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Insert Network')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnInsertNetworkButton, self.insertNetworkButton)
		self.deleteNetworkButton = wx.Button(self.leftPanelStaticBox, wx.ID_ANY, 'Delete Network')
		self.leftPanelStaticBox.Bind(wx.EVT_BUTTON, self.OnDeleteNetworkButton, self.deleteNetworkButton)
		self.thisPanel = RawPanel(self.parentPanel, wx.ID_ANY)
		
		topBorder, otherBorder = self.leftPanelStaticBox.GetBordersForSizer()
		self.staticSizer = wx.BoxSizer(wx.VERTICAL)
		self.staticSizer.AddSpacer(topBorder + 3)
		self.staticSizer.Add(self.rb, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
		self.staticSizer.Add(self.insertNetworkButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.staticSizer.AddSpacer(20)
		self.staticSizer.Add(self.deleteNetworkButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.staticSizer.AddSpacer(10)
		
		self.leftPanelStaticBox.SetSizer(self.staticSizer)
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		self.mainQueryBox.AddSpacer(3)
		self.mainQueryBox.Add(self.leftPanelStaticBox, 2, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
		self.mainBox.Add(self.mainQueryBox, 0, wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		
		self.thisPanel = RawPanel(self.parentPanel, wx.ID_ANY)
		self.vBox2 = wx.BoxSizer(wx.VERTICAL)
		self.vBox2.Add(self.thisPanel, 1, wx.EXPAND)
		self.mainBox.Add(self.vBox2, 1, wx.EXPAND)
		
		self.updateDataPanel()
		wx.EndBusyCursor()


	def getRealms(self):
		apiResults = self.api.getResource('config/Realm')
		for name in apiResults.get('realms', {}):
			self.realms.append(name)


	def getNetworkScopes(self):
		apiResults = self.api.getResource('config/NetworkScope')
		for entry in apiResults.get('scopes', []):
			privateData = {}
			objectId = entry.get('object_id', '')
			realm = entry.get('realm', '')
			privateData['object_id'] = objectId
			privateData['realm'] = realm
			privateData['active'] = entry.get('active', '')
			privateData['object_created_by'] = entry.get('object_created_by', '')
			privateData['time_created'] = entry.get('time_created', '')
			privateData['description'] = entry.get('description', '')
			privateData['count'] = entry.get('count', 0)
			privateData['data'] = entry.get('data', {})
			transformedString = entry.get('transformed', {})
			privateData['transformed'] = transformedString
			if self.networkScopes.get(realm) is None:
				self.networkScopes[realm] = {}
			self.networkScopes[realm][objectId] = privateData


	def updateDataPanel(self):
		self.logger.debug('updateDataPanel: starting')
		self.parentPanel.Freeze()
		self.networkScopes = {}
		self.getNetworkScopes()

		self.vBox2.Detach(self.thisPanel)
		self.thisPanel.Destroy()
		self.thisPanel = RawPanel(self.parentPanel, wx.ID_ANY)
		self.dataPanel = ResultObjects(self.thisPanel, self.logger, self.api, self.networkScopes, self.currentRealm)
		self.vBox2.Add(self.thisPanel, 1, wx.EXPAND)

		self.parentPanel.SetSizer(self.mainBox)
		self.parentPanel.Thaw()
		self.parentPanel.Show()
		self.parentPanel.SendSizeEvent()


	def EvtRadioBox(self, event):
		realmId = event.GetInt()
		self.logger.debug('EvtRadioBox:     entry id : {}'.format(realmId))
		self.logger.debug('EvtRadioBox: selectedRealm: {}'.format(self.realms[realmId]))
		self.logger.debug('EvtRadioBox: currentRealm : {}'.format(self.currentRealm))
		if self.currentRealmId != realmId:
			try:
				self.currentRealm = self.realms[realmId]
				self.currentRealmId = realmId
				wx.BeginBusyCursor()
				self.updateDataPanel()
				wx.EndBusyCursor()
			except:
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				self.logger.debug('Failure in EvtRadioBox: {}'.format(stacktrace))


	def OnInsertNetworkButton(self, event=None):
		self.logger.debug('OnInsertNetworkButton: {}'.format(event.GetInt()))
		dlgNetScope = NetworkDialog(self.parentPanel, log=self.logger, api=self.api, realm=self.currentRealm)
		dlgNetScope.CenterOnScreen()
		value = dlgNetScope.ShowModal()

		## Pull results out before destroying the window
		content = {}
		networkConfig = {}
		networkConfig['realm'] = self.currentRealm
		networkConfig['active'] = dlgNetScope.scopeIsEnabled
		networkConfig['description'] = dlgNetScope.description.GetValue()
		networkConfig['source'] = 'admin console'
		#networkConfig['object_updated_by'] = 'admin console'
		data = dlgNetScope.scopeData
		filters = dlgNetScope.filterData
		if data is not None:
			data['exclusion'] = filters
		networkConfig['data'] = data
		self.logger.debug('OnInsertNetworkButton: networkConfig: {}'.format(networkConfig))

		dlgNetScope.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnInsertNetworkButton: value == OK')
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('config/NetworkScope', {'content' : networkConfig})
			wx.EndBusyCursor()
			if responseCode == 200:
				self.logger.debug('OnInsertNetworkButton: network scope added.')
				wx.BeginBusyCursor()
				self.updateDataPanel()
				wx.EndBusyCursor()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'Network scope error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()

		else:
			self.logger.debug('OnInsertNetworkButton: value == CANCEL')


	def OnDeleteNetworkButton(self, event=None):
		self.logger.debug('OnDeleteNetworkButton')
		realm = self.currentRealm
		scopeId = self.dataPanel.resultList.currentItemId
		self.logger.debug('OnDeleteNetworkButton: scopeId: {}'.format(scopeId))
		dlgDelete = wx.MessageDialog(self.thisPanel,
									 'Are you sure you want to delete network {}?'.format(scopeId),
									 'Delete network {}'.format(scopeId),
									 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnDeleteNetworkButton: value == OK')
			## If user pressed OK (and not Cancel), then call API to delete network
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.deleteResource('config/NetworkScope/{}/{}'.format(realm, scopeId))
			wx.EndBusyCursor()
			if responseCode == 200:
				self.logger.debug('OnDeleteNetworkButton: removed network {}'.format(scopeId))
				del self.networkScopes[realm][scopeId]
				wx.BeginBusyCursor()
				self.updateDataPanel()
				wx.EndBusyCursor()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'Delete network with scopeId {}'.format(scopeId), wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnDeleteNetworkButton: value == CANCEL')
