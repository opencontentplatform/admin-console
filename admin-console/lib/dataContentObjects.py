"""Pane for Admin Console ribbon destination: Data->Content->Objects."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.agw.genericmessagedialog as GMD


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)


class ObjectListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, dataPanelRef):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		self.api = api
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		sizer.Add(self.list, 1, wx.EXPAND)
		## Pull object count from API
		self.objectCounts = dict()
		self.getObjectCounts()
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.objectCounts
		listmix.ColumnSorterMixin.__init__(self, 2)
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


	def getObjectCounts(self):
		apiResults = self.api.count()
		objectId = 1
		for obj,count in apiResults.items():
			self.objectCounts[objectId] = (obj, count)
			objectId += 1
		return

	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.objectCounts
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Object Type"
		self.list.InsertColumn(0, info)
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Count"
		self.list.InsertColumn(1, info)

		items = data.items()
		for key, data in items:
			index = self.list.InsertItem(self.list.GetItemCount(), data[0])
			self.list.SetItem(index, 1, str(data[1]))
			self.list.SetItemData(index, key)

		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.list.SetColumnWidth(1, 100)

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

	def resetDataPanel(self, selection):
		self.logger.debug("ObjectListCtrlPanel: resetDataPanel...")
		self.owner.thisPanel.Freeze()
		self.owner.vBox2.Detach(self.owner.rawPanel)
		if self.owner.dataPanel is not None:
			self.owner.rawPanel.Destroy()
			self.owner.rawPanel = RawPanel(self.owner.thisPanel, wx.ID_ANY)
		self.owner.dataPanel = ResultObjects(self.owner.rawPanel, self.logger, self.api, selection)
		## Create boxes to arrange the panels
		self.owner.mainBox.Detach(self.owner.staticBox)
		self.owner.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		## Box on left for the Tree
		self.owner.staticBox.SetSizer(self.owner.vBox1)
		self.owner.mainBox.Add(self.owner.staticBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 10)
		## Box on the right for the data
		self.owner.vBox2 = wx.BoxSizer(wx.VERTICAL)
		self.owner.vBox2.Add(self.owner.rawPanel, 1, wx.EXPAND|wx.ALL, 5)
		self.owner.mainBox.Add(self.owner.vBox2, 1, wx.EXPAND)
		self.owner.thisPanel.SetSizer(self.owner.mainBox)
		self.owner.thisPanel.Thaw()
		self.owner.thisPanel.Show()
		self.owner.thisPanel.SendSizeEvent()
		self.owner.rawPanel.SendSizeEvent()
		self.logger.debug("ObjectListCtrlPanel: resetDataPanel... DONE")


	def OnItemSelected(self, event):
		self.currentItem = event.Index
		self.logger.debug("OnItemSelected: %s, %s, %s\n" % (self.currentItem, self.list.GetItemText(self.currentItem), self.getColumnText(self.currentItem, 1)))
		self.resetDataPanel(self.getColumnText(self.currentItem, 0))
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


class ResultListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, context, log, api):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.api = api
		self.SetAutoLayout(1)
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		self.list.SetAutoLayout(1)
		#self.list.SetupScrolling()
		## Pull object count from API
		self.resultsActive = dict()
		self.results = dict()
		self.headersActive = None
		self.headers = []
		self.resultAttrs = []
		self.objectType = context
		self.getResults()
		self.sizer = wx.BoxSizer()
		#self.resultAttrs = list(range(0,len(self.headersActive)))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.resultsActive
		listmix.ColumnSorterMixin.__init__(self, len(self.headers))

		self.sizer.Add(self.list, 1, wx.EXPAND)
		self.SetSizer(self.sizer)
		self.sizer.Fit(self)
		self.sizer.Layout()

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


	def getResults(self):
		self.resultsActive.clear()
		self.results.clear()
		self.headersActive = None
		self.headers.clear()
		self.resultAttrs.clear()
		apiResults = self.api.objectEntries(self.objectType)
		objectId = 1
		createdHeaders = False
		for result in apiResults.get('objects', {}):
			attrList = []
			if not createdHeaders:
				for attr,value in result.get('data',{}).items():
					if value is None:
						value = ''
					attrList.append(value)
					self.headers.append(attr)
				createdHeaders = True
			else:
				for attr,value in result.get('data',{}).items():
					if value is None:
						value = ''
					attrList.append(value)
			self.results[objectId] = attrList
			## Shallow copy to allow deleting columns from the active version
			self.resultsActive[objectId] = attrList[:]
			objectId += 1
		## Shallow copy to manage filters/searches without new API queries
		self.headersActive = self.headers[:]
		self.resultAttrs = list(range(0,len(self.headers)))
		## Remove headers to hide & trim the key/values from the active results
		baseAttrsToHide = ['object_id', 'reference_id', 'object_type', 'time_created', 'time_updated', 'time_gathered', 'object_created_by', 'object_updated_by', 'description', 'caption']
		for x in reversed(range(0, len(self.headers))):
			headerName = self.headers[x]
			if headerName in baseAttrsToHide:
				self.logger.info('Trying to remove header name {} with index {}'.format(headerName, x))
				self.logger.info('  self.headersActive : {}'.format(self.headersActive))
				self.headersActive.remove(headerName)
				self.logger.info('  self.headersActive : {}'.format(self.headersActive))
				self.resultAttrs.pop(x)
		for key,data in self.resultsActive.items():
			self.logger.info('  self.resultsActive key {} value: {}'.format(key, data))
			## Go in reverse since we're deleting in place
			for x in reversed(range(0, len(self.headers))):
				headerName = self.headers[x]
				if headerName in baseAttrsToHide:
					del data[x]
			self.resultsActive[key] = data
		return

	def deselectItem(self):
		## Deselect all, since the selected one has just moved it's place. If I
		## don't do this, a click on the column will sort the objects, but the
		## previous selection is still highlighted. If I try to right click and
		## delete or show properties... the "current" item is at the same position
		## as the one the highlighted one was at previously. The position isn't
		## updated in the sort mixin.  So here I deselect everything here so the
		## user doesn't see that issue.
		self.logger.debug("deselectItem: {}".format(self.currentItem))
		#self.list.SetItemState(self.currentItem, 0, wx.LIST_STATE_SELECTED)
		for x in range(0, self.list.GetItemCount()):
			self.list.Select(x, on=0)
		self.currentItem = 0

	def OnUpdateColumns(self):
		self.logger.info('OnUpdateColumns: {}'.format(self.resultsActive))
		for key,data in self.resultsActive.items():
			#self.logger.info('OnUpdateColumns looking at {} : {}'.format(key, data))
			#self.logger.info('OnUpdateColumns range           : {}'.format(list(range(0, len(self.headers)))))
			#self.logger.info('OnUpdateColumns self.resultAttrs: {}'.format(self.resultAttrs))
			## Go in reverse since we're deleting in place
			for x in reversed(range(0, len(self.headers))):
				#self.logger.info('OnUpdateColumns x: {}'.format(x))
				if x not in self.resultAttrs:
					#self.logger.info('OnUpdateColumns removing index {} with value {}'.format(x, data[x]))
					del data[x]
			self.logger.info('OnUpdateColumns: set {} : {}'.format(key, data))
			self.resultsActive[key] = data
		self.deselectItem()

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
			if len(data) <= 0:
				continue
			index = self.list.InsertItem(self.list.GetItemCount(), data[0])
			for x in range(len(self.headersActive)-1):
				self.list.SetItem(index, x+1, str(data[x+1]))
			self.list.SetItemData(index, key)
		col = 0
		for header in self.headersActive:
			self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			col += 1
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
		self.logger.debug("OnItemActivated: %s\nTopItem: %s" %
						   (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))

	def OnColClick(self, event):
		self.logger.debug("OnColClick: %d\n" % event.GetColumn())
		event.Skip()
		self.deselectItem()

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
			self.deleteID  = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, self.OnDeleteAction, id=self.deleteID)
		menu = wx.Menu()
		menu.Append(self.propertiesID, "Properties")
		menu.Append(self.deleteID, "Delete Object")
		self.PopupMenu(menu)
		menu.Destroy()

	def OnPropertiesPopup(self, event):
		self.logger.debug("OnPropertiesPopup: currentItem: {}".format(self.currentItem))	
		message = ''
		pos = 0
		for header in self.headersActive:
			newEntry = '{}: {}\n'.format(header, self.getColumnText(self.currentItem, pos))
			if message is None:
				message = newEntry
			else:
				message = '{}{}'.format(message, newEntry)
			pos += 1
		
		## This uses a static window, which looks more native across OS types,
		## but it doesn't let a user copy/paste out of it... which is sorta the
		## point to opening up the properties of an object.
		# dlg = wx.GenericMessageDialog(self, message, "{} Properties".format(self.objectType), wx.ICON_INFORMATION)
		# dlg.ShowModal()
		# dlg.Destroy()
		
		## This uses a plain scrollable window with selectable text
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "{} Properties".format(self.objectType), size=(500, 400))
		dlg.ShowModal()
		dlg.Destroy()
		
		

	def OnDeleteAction(self, event=None):
		self.logger.debug("OnDeleteAction: currentItem: {}".format(self.currentItem))
		self.logger.debug("OnDeleteAction: resultsActive: {}".format(self.resultsActive))
		#objectInfo = self.resultsActive[self.currentItem]
		#self.logger.debug("OnDeleteAction: objectInfo: {}".format(objectInfo))
		objectId = None
		message = 'Do you want to permanently delete this {} object?\n\n'.format(self.objectType)
		pos = 0
		for header in self.headersActive:
			newEntry = '    {}: {}\n'.format(header, self.getColumnText(self.currentItem, pos))
			message = '{}{}'.format(message, newEntry)
			if header == 'object_id':
				objectId = self.getColumnText(self.currentItem, pos)
			pos += 1
		if objectId is None:
			dlgDelete = wx.MessageDialog(self,
										 'In order to delete an object, you must have the \'object_id\' column added to the results. Click the \'Select Columns\' button at the top right of this screen to add explicitely, or click the \'Show All Columns\' button to add all hidden columns, and then retry the Delete action.',
										 'Add the object_id column',
										 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
			dlgDelete.CenterOnScreen()
			value = dlgDelete.ShowModal()
			dlgDelete.Destroy()
		else:
			dlgDelete = wx.MessageDialog(self,
										 message,
										 'Delete {}'.format(self.objectType),
										 wx.OK|wx.CANCEL|wx.ICON_QUESTION)
			dlgDelete.CenterOnScreen()
			value = dlgDelete.ShowModal()
			dlgDelete.Destroy()
			if value == wx.ID_OK:
				self.logger.debug('OnDeleteAction: value == OK')
				## If user pressed OK (and not Cancel), then call API to delete network
				wx.BeginBusyCursor()
				(responseCode, responseAsJson) = self.api.deleteResource('data/{}/{}'.format(self.objectType, objectId))
				wx.EndBusyCursor()
				if responseCode == 200:
					self.logger.debug('OnDeleteAction: removed object {}'.format(objectId))
					self.updateData()
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self, errorMsg, 'Delete Failed on object'.format(objectId), wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
			else:
				self.logger.debug('OnDeleteAction: value == CANCEL')

	def updateData(self):
		wx.BeginBusyCursor()

		savedHeadersActive = self.headersActive[:]
		#self.logger.debug(' =======> updateData 0: {}'.format(self.headersActive))
		#self.logger.debug(' =======> updateData 1: {}'.format(savedHeadersActive))
		self.getResults()
		## Reset the active headers and the resultAttrs (positions)
		self.headersActive = savedHeadersActive
		self.resultAttrs = list(range(0,len(self.headers)))
		for x in reversed(range(0, len(self.headers))):
			headerName = self.headers[x]
			if headerName not in self.headersActive:
				self.resultAttrs.pop(x)
		#self.logger.debug(' =======> updateData 2: {}'.format(self.headersActive))
		self.resultsActive.clear()
		for prevId,data in self.results.items():
			self.resultsActive[prevId] = data[:]
		self.OnUpdateColumns()
		self.PopulateList()
		self.Layout()
		wx.EndBusyCursor()


class ResultObjects():
	def __init__(self, thisPanel, log, api, context):
		self.thisPanel = thisPanel
		self.logger = log
		self.api = api
		wx.BeginBusyCursor()
		self.resultList = ResultListCtrlPanel(thisPanel, context, self.logger, self.api)
		wx.EndBusyCursor()
		self.filter = wx.SearchCtrl(thisPanel, style=wx.TE_PROCESS_ENTER)
		self.filter.ShowCancelButton(True)
		self.filter.Bind(wx.EVT_TEXT, self.OnSearch)
		self.filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: self.filter.SetValue(''))
		self.filter.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
		## Create boxes to arrange the panels
		mainBox = wx.BoxSizer(wx.VERTICAL)
		## Box on top for the search and attribute controls
		hBox1 = wx.BoxSizer(wx.HORIZONTAL)
		hBox1.Add(self.filter, 1, wx.EXPAND|wx.ALL, 5)
		if 'wxMac' in wx.PlatformInfo:
			hBox1.Add((5,5))  # Make sure there is room for the focus ring

		self.allAttrsButton = wx.Button(thisPanel, -1, "Show All Columns", (50,50))
		thisPanel.Bind(wx.EVT_BUTTON, self.OnShowAllAttributes, self.allAttrsButton)
		hBox1.Add(self.allAttrsButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		self.attributeButton = wx.Button(thisPanel, -1, "Select Columns", (50,50))
		thisPanel.Bind(wx.EVT_BUTTON, self.OnAttributeButton, self.attributeButton)
		hBox1.Add(self.attributeButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		mainBox.Add(hBox1, 0, wx.EXPAND)
		mainBox.Add(self.resultList, 1, wx.EXPAND|wx.ALL, 5)
		thisPanel.SetSizer(mainBox)
		thisPanel.Show()
		thisPanel.SendSizeEvent()

	def OnShowAllAttributes(self, event=None):
		self.logger.debug('OnShowBaseAttributes: old attribute list for headers: {}'.format(self.resultList.headersActive))
		self.resultList.headersActive = self.resultList.headers[:]
		self.resultList.resultAttrs = list(range(0,len(self.resultList.headers)))
		for key,data in self.resultList.results.items():
			self.resultList.resultsActive[key] = data[:]
		self.logger.debug('OnShowBaseAttributes: new attribute list for headers: {}'.format(self.resultList.headersActive))
		self.onButtonFunctions()

	def OnAttributeButton(self, event=None):
		dlg = wx.MultiChoiceDialog(self.thisPanel, "Only selected attributes will be displayed", "Object Attributes", self.resultList.headers)
		## Pre-select what is currently displayed
		dlg.SetSelections(self.resultList.resultAttrs)
		if (dlg.ShowModal() == wx.ID_OK):
			self.resultList.resultAttrs = dlg.GetSelections()
			self.logger.debug("New selection list for headers: {}".format(self.resultList.resultAttrs))
			self.resultList.headersActive = [self.resultList.headers[x] for x in self.resultList.resultAttrs]
			self.logger.debug("New attribute list for headers: {}".format(self.resultList.headersActive))
		dlg.Destroy()
		self.onButtonFunctions()

	def onButtonFunctions(self):
		## Force the resultsActive to get all column values before updating; do
		## this in case a new column was shown instead of just hid; need to
		## update the dataset given to the MixIn that enables column sorting.
		self.UpdateResultsActive()
		self.resultList.OnUpdateColumns()
		self.resultList.PopulateList()
		## Now update the ColumnSorterMixin references for future column touches
		self.resultList.SetColumnCount(len(self.resultList.headersActive))
		self.resultList.itemDataMap = self.resultList.resultsActive
		#listmix.ColumnSorterMixin.__init__(self.resultList, len(self.resultList.headers))
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
		self.logger.info('OnSearch: done')
		wx.EndBusyCursor()


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

		thisPanel.Freeze()
		self.staticBox = wx.StaticBox(thisPanel, wx.ID_ANY, 'Objects in the database')
		self.topBorder, self.otherBorder = self.staticBox.GetBordersForSizer()
		self.thisPanel = thisPanel
		self.rawPanel = RawPanel(thisPanel, wx.ID_ANY)
		self.dataPanel = None
		self.objectList = ObjectListCtrlPanel(self.staticBox, self.logger, self.api, self)
		self.filter = wx.SearchCtrl(self.staticBox, style=wx.TE_PROCESS_ENTER)
		self.filter.ShowCancelButton(True)
		self.filter.Bind(wx.EVT_TEXT, self.OnSearch)
		self.filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: self.filter.SetValue(''))
		self.filter.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)

		## Create boxes to arrange the panels
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		## Box on left for the Tree
		self.vBox1 = wx.BoxSizer(wx.VERTICAL)
		#label_font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT)
		self.vBox1.AddSpacer(self.topBorder)
		self.caption2 = wx.StaticText(self.staticBox, label="Filter Objects:")
		self.vBox1.Add(self.caption2, 0, wx.TOP|wx.LEFT, 5)
		self.vBox1.Add(self.filter, 0, wx.EXPAND|wx.ALL, 5)
		if 'wxMac' in wx.PlatformInfo:
			self.vBox1.Add((5,5))  # Make sure there is room for the focus ring
		self.vBox1.AddSpacer(5)
		self.vBox1.Add(self.objectList, 1, wx.EXPAND|wx.ALL, 5)
		self.staticBox.SetSizer(self.vBox1)
		self.mainBox.Add(self.staticBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 10)
		## Box on the right for the data
		# vBox2 = wx.BoxSizer(wx.VERTICAL)
		# hBox2 = wx.BoxSizer()
		# hBox2.Add(self.rawPanel, 1, wx.EXPAND|wx.ALL, 5)
		# vBox2.Add(hBox2, 4, flag=wx.EXPAND)
		# mainBox.Add(vBox2, 4, wx.EXPAND)
		self.vBox2 = wx.BoxSizer(wx.VERTICAL)
		self.vBox2.Add(self.rawPanel, 1, wx.EXPAND|wx.ALL, 5)
		self.mainBox.Add(self.vBox2, 4, wx.EXPAND)

		thisPanel.SetSizer(self.mainBox)
		thisPanel.Thaw()
		thisPanel.SendSizeEvent()
		wx.EndBusyCursor()


	def OnSearch(self, event=None):
		value = self.filter.GetValue()
		if not value:
			self.objectList.PopulateList()
			return
		wx.BeginBusyCursor()
		newData = dict()
		newId = 1
		for prevId,data in self.objectList.objectCounts.items():
			for entry in data:
				if re.search(str(value), str(entry), re.I):
					newData[newId] = data
					newId += 1
					break
		self.objectList.PopulateList(newData)
		## Send a size event to refresh the scroll bar
		# self.objectList.list.SendSizeEvent()
		# self.dataPanel.SendSizeEvent()
		# self.onButtonFunctions()
		wx.EndBusyCursor()
