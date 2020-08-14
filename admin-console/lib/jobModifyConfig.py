"""Pane for Admin Console ribbon destination: Jobs->Modify->Config.

This pane presents details of jobs by service.
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix

class InsertDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE,
				 name='InsertDialog', log=None):
		wx.Dialog.__init__(self, parent, id, 'Create Job', pos, size, style, name)
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
				 name='UpdateDialog', log=None, jobName=None, textString=''):
		wx.Dialog.__init__(self, parent, id, 'Update {}'.format(jobName), pos, size, style, name)
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


class ResultListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, jobDetails, columns, headers, columnStaticWidthDict={}):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.logger.debug('Inside ResultListCtrlPanel')
		self.SetAutoLayout(1)
		self.jobDetails = jobDetails
		self.dataToPopulate = {}
		self.columns = columns
		self.headers = headers
		self.columnStaticWidthDict = columnStaticWidthDict
		self.formatDataForView()
		self.list = ObjectListCtrl(self, wx.ID_ANY)
		self.list.SetAutoLayout(1)
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.dataToPopulate
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


	def formatDataForView(self):
		## Only put specific keys in the view, and in a natural order
		objectId = 1
		self.dataToPopulate.clear()
		for entry in self.jobDetails:
			attrList = []
			for col in self.columns:
				value = entry.get(col)
				if value is None:
					value = ''
				attrList.append(value)
			self.dataToPopulate[objectId] = attrList
			objectId += 1


	def PopulateList(self):
		self.logger.debug('PopulateList... ')
		self.list.ClearAll()
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		col = 0
		## Insert the headers
		for header in self.headers:
			info.Align = wx.LIST_FORMAT_LEFT
			info.Text = header
			self.list.InsertColumn(col, info)
			col += 1
		## Now insert the jobs
		for key,value in self.dataToPopulate.items():
			index = self.list.InsertItem(self.list.GetItemCount(), str(value[0]))
			for x in range(len(self.headers)-1):
				self.list.SetItem(index, x+1, str(value[x+1]))
			self.list.SetItemData(index, key)
		col = 0
		## Set column widths
		for header in self.headers:
			if col in self.columnStaticWidthDict:
				self.list.SetColumnWidth(col, self.columnStaticWidthDict[col])
			else:
				self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			col += 1
		self.currentItemId = None
		self.currentItem = 0
		self.logger.debug('PopulateList... data: {}'.format(self.dataToPopulate))
		if self.dataToPopulate is not None and len(self.dataToPopulate) > 0:
			self.logger.debug('               self.currentItem: {}'.format(self.currentItem))
			self.currentItemId = self.getColumnText(self.currentItem, 0)
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
		message = None
		lineId = self.currentItem + 1
		self.logger.debug("OnPropertiesPopup: lineId: {}".format(lineId))
		self.logger.debug("OnPropertiesPopup: self.dataToPopulate size: {}".format(len(self.dataToPopulate)))
		self.logger.debug("OnPropertiesPopup: self.dataToPopulate: {}".format(self.dataToPopulate))

		originalData = self.dataToPopulate[lineId]
		self.logger.debug("OnPropertiesPopup: originalData: {}".format(originalData))
		objectId = 0
		for attr in self.columns:
			value = originalData[objectId]
			self.logger.debug("  {} value: {}".format(objectId, value))
			## Transform 'content' into JSON
			if attr == 'count_per_client' or attr == 'count_per_status' or attr == 'result_count':
				value = json.dumps(value, indent=4)
			newEntry = '{}: {}\n'.format(attr, value)
			if message is None:
				message = newEntry
			else:
				message = '{}{}'.format(message, newEntry)
			objectId += 1
		self.logger.debug('OnPropertiesPopup: 3: message: {}'.format(message))
		self.logger.debug('OnPropertiesPopup: 3: size: {}'.format(len(message)))
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "Properties", size=(500, 500))
		dlg.ShowModal()
		dlg.Destroy()


class MyEvent(wx.PyCommandEvent):
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)
		self.myVal = None


class JobListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, dataPanelRef):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(250, 300), style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY)
		sizer.Add(self.list, 1, wx.EXPAND)
		## Initialize the data
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
		jobs = self.owner.packageList[self.owner.packageType]
		objectId = 1
		for job in jobs:
			self.data[objectId] = job
			objectId += 1

	def PopulateList(self):
		self.currentItem = 0
		self.list.ClearAll()
		data = self.data
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Job short name"
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
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
		self.owner.currentJob = self.owner.packageList[self.owner.packageType][name]
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
		self.owner.OnStatsButton()

	def OnRightClick(self, event):
		self.logger.debug("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))


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

		self.jobFilterBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Manage Job')
		self.getServices()
		self.jobDetails = {}
		self.packageList = {}
		self.packages = []
		self.packageType = None
		self.currentJob = None
		self.getJobsForThisService()
		self.serviceText = wx.StaticText(self.jobFilterBox, wx.ID_ANY, 'Select Service:')
		self.serviceChoice = wx.Choice(self.jobFilterBox, wx.ID_ANY, (120, 50), choices=self.services)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChooseServiceType, self.serviceChoice)
		self.packageText = wx.StaticText(self.jobFilterBox, wx.ID_ANY, 'Select Package:')
		self.packageChoice = wx.Choice(self.jobFilterBox, wx.ID_ANY, (120, 50), choices=self.packages)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChoosePackageType, self.packageChoice)
		self.packageChoice.SetSelection(0)
		self.serviceChoice.SetSelection(0)
		## Job List for selected package
		self.jobListPanel = JobListCtrlPanel(self.jobFilterBox, self.logger, self)
		self.jobListPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.jobListPanelSizer.Add(self.jobListPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
		## Buttons
		self.insertButton = wx.Button(self.jobFilterBox, wx.ID_ANY, 'Insert new job')
		self.jobFilterBox.Bind(wx.EVT_BUTTON, self.OnInsertButton, self.insertButton)
		self.updateButton = wx.Button(self.jobFilterBox, wx.ID_ANY, 'Update selected job')
		self.jobFilterBox.Bind(wx.EVT_BUTTON, self.OnUpdateButton, self.updateButton)
		self.deleteButton = wx.Button(self.jobFilterBox, wx.ID_ANY, 'Delete selected job')
		self.jobFilterBox.Bind(wx.EVT_BUTTON, self.OnDeleteGroupButton, self.deleteButton)

		## Right side
		self.jobConfigBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Job Configuration')
		## Placeholder for when we known how to create an TextCtrl
		self.jobConfigPanel = RawPanel(self.jobConfigBox, wx.ID_ANY)
		self.jobConfigSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.jobConfigSizerV = wx.BoxSizer(wx.VERTICAL)
		self.jobConfigSizerV.AddSpacer(10)
		self.jobConfigSizerV.Add(self.jobConfigPanel, 1, wx.EXPAND|wx.ALL, 10)
		self.jobConfigSizer.Add(self.jobConfigSizerV)
		self.jobConfigBox.SetSizer(self.jobConfigSizer)

		self.resultPanelSizer = wx.BoxSizer(wx.VERTICAL)
		self.resultPanelSizer.Add(self.jobConfigBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

		## Create boxes to arrange the panels
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		topBorder, otherBorder = self.jobFilterBox.GetBordersForSizer()
		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.AddSpacer(topBorder + 5)
		self.leftSizer.Add(self.serviceText, 0, wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(5)
		self.leftSizer.Add(self.serviceChoice, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(5)
		self.leftSizer.Add(self.packageText, 0, wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(5)
		self.leftSizer.Add(self.packageChoice, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(15)
		self.leftSizer.Add(self.jobListPanelSizer, 1, wx.EXPAND)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.insertButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.updateButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(20)
		self.leftSizer.Add(self.deleteButton, 0, wx.EXPAND|wx.ALL, 10)

		self.jobFilterBox.SetSizer(self.leftSizer)
		self.mainQueryBox.Add(self.jobFilterBox, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.resultPanelSizer, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 5)

		self.leftSizer.Layout()
		self.jobFilterBox.Layout()

		self.logger.debug('Main.init')
		self.thisPanel.SetSizer(self.mainBox)
		self.mainBox.Layout()
		self.jobListPanel.setCurrentItem()
		wx.EndBusyCursor()


	def resetMainPanel(self, preserve=True):
		self.logger.debug('Start resetMainPanel')
		self.thisPanel.Freeze()

		self.logger.debug('resetMainPanel: currentJob: {}'.format(self.currentJob))
		## Get current dataSet to display in the textCtl pane on the right
		dataSet = self.jobDetails.get(self.currentJob)

		## Cleanup previous data sets
		self.mainBox.Detach(self.resultPanelSizer)
		self.jobConfigSizerV.Detach(self.jobConfigPanel)
		self.jobConfigSizerV = None
		self.jobConfigSizer = None

		self.jobConfigPanel.Destroy()
		self.resultPanelSizer = None
		self.resultPanelSizer = wx.BoxSizer(wx.VERTICAL)
		self.jobConfigSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.jobConfigSizerV = wx.BoxSizer(wx.VERTICAL)
		self.jobConfigBox.Destroy()
		self.jobConfigBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Job Configuration')
		## Static texts
		self.text1 = wx.StaticText(self.jobConfigBox, label="Active: ")
		self.text2 = wx.StaticText(self.jobConfigBox, label="Created: ")
		self.text3 = wx.StaticText(self.jobConfigBox, label="Created by: ")
		self.text4 = wx.StaticText(self.jobConfigBox, label="Updated: ")
		self.text5 = wx.StaticText(self.jobConfigBox, label="Updated by: ")
		self.value1 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(dataSet.get('active', '')), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)
		self.value2 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(dataSet.get('time_created', '')), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)
		self.value3 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(dataSet.get('object_created_by', '')), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)
		self.value4 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(dataSet.get('time_updated', '')), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)
		self.value5 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(dataSet.get('object_updated_by', '')), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)

		## Replace the result panes on the right
		if dataSet is not None:
			self.logger.debug('resetMainPanel: dataSet: {}'.format(dataSet))
			textString = json.dumps(dataSet.get('content', {}), indent=8)
			self.jobConfigPanel = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, textString, style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY|wx.EXPAND)
		else:
			self.jobConfigPanel = RawPanel(self.jobConfigBox, wx.ID_ANY)

		## Put back in the sizers and refresh
		self.jobConfigSizerV.AddSpacer(30)

		self.dataSizer1 = wx.BoxSizer(wx.HORIZONTAL)
		self.dataSizer1.Add(self.text1, 0, wx.LEFT, 5)
		self.dataSizer1.Add(self.value1, 0, wx.EXPAND)
		self.jobConfigSizerV.Add(self.dataSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		self.dataSizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.dataSizer2.Add(self.text2, 0, wx.LEFT, 5)
		self.dataSizer2.Add(self.value2, 0, wx.EXPAND)
		self.jobConfigSizerV.Add(self.dataSizer2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		self.dataSizer3 = wx.BoxSizer(wx.HORIZONTAL)
		self.dataSizer3.Add(self.text3, 0, wx.LEFT, 5)
		self.dataSizer3.Add(self.value3, 0, wx.EXPAND)
		self.jobConfigSizerV.Add(self.dataSizer3, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		self.dataSizer4 = wx.BoxSizer(wx.HORIZONTAL)
		self.dataSizer4.Add(self.text4, 0, wx.LEFT, 5)
		self.dataSizer4.Add(self.value4, 0, wx.EXPAND)
		self.jobConfigSizerV.Add(self.dataSizer4, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		self.dataSizer5 = wx.BoxSizer(wx.HORIZONTAL)
		self.dataSizer5.Add(self.text5, 0, wx.LEFT, 5)
		self.dataSizer5.Add(self.value5, 0, wx.EXPAND)
		self.jobConfigSizerV.Add(self.dataSizer5, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		self.jobConfigSizerV.AddSpacer(10)
		self.jobConfigSizerV.Add(self.jobConfigPanel, 1, wx.EXPAND|wx.ALL, 10)
		self.jobConfigSizer.Add(self.jobConfigSizerV, 1, wx.EXPAND)
		self.jobConfigBox.SetSizer(self.jobConfigSizer)
		self.resultPanelSizer.Add(self.jobConfigBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.mainBox.Add(self.resultPanelSizer, 1, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
		self.jobConfigSizer.Layout()
		self.resultPanelSizer.Layout()

		if not preserve:
			## Conditionally replace the job list on the left
			newListPanel = JobListCtrlPanel(self.jobFilterBox, self.logger, self)
			self.leftSizer.Detach(self.jobListPanelSizer)
			self.jobListPanel.Destroy()
			self.jobListPanel = newListPanel
			self.jobListPanelSizer = None
			self.jobListPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
			self.jobListPanelSizer.Add(self.jobListPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
			self.leftSizer.Insert(9, self.jobListPanelSizer, wx.EXPAND)
			self.leftSizer.Layout()
			self.jobFilterBox.Layout()
			## setCurrentItem will call resetMainPanel again, for force resizing
			self.jobListPanel.setCurrentItem()

		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()
		self.logger.debug('Stop resetMainPanel')

	def getServices(self):
		self.services = ['contentGathering', 'universalJob']
		self.serviceType = self.services[0]


	def getJobsForThisService(self):
		self.logger.debug('getJobs')
		self.jobDetails.clear()
		self.packageList.clear()
		apiResults = self.api.getResource('job/config/{}'.format(self.serviceType))
		jobList = apiResults.get('Jobs', [])
		for jobName in jobList:
			jobConfig = self.api.getResource('job/config/{}/{}'.format(self.serviceType, jobName))
			jobData = jobConfig.get(jobName, {})
			self.jobDetails[jobName] = jobData
			pkgName = jobData.get('package', 'Unknown')
			## Fancy way of spliting to get the last part (better performance),
			## which is similar to:  shortName = jobName.split('.')[1]
			shortName = jobName.partition('{}.'.format(pkgName))[2]
			if pkgName not in self.packageList:
				self.packageList[pkgName] = {}
			self.packageList[pkgName][shortName] = jobName

		self.packages.clear()
		for key in self.packageList:
			self.packages.append(key)
		self.packageType = self.packages[0]
		self.currentJob = self.packageList[self.packageType][next(iter(self.packageList[self.packageType]))]


	def EvtChooseServiceType(self, event):
		self.serviceType = event.GetString()
		self.getJobsForThisService()
		## When we change the service, update the package choices
		self.logger.debug('EvtChooseServiceType: update variables')
		self.packageChoice.Clear()
		self.packages.clear()
		flag = True
		for key in self.packageList.keys():
			if flag:
				self.packageType = key
				flag = False
			self.packages.append(key)
			self.packageChoice.Append(key)
		self.packageChoice.SetSelection(0)

		self.currentJob = self.packageList[self.packageType][next(iter(self.packageList[self.packageType]))]
		self.logger.debug('EvtChooseServiceType: packageType: {}'.format(self.packageType))
		self.logger.debug('EvtChooseServiceType: currentJob: {}'.format(self.currentJob))
		self.resetMainPanel(preserve=False)


	def EvtChoosePackageType(self, event):
		self.packageType = event.GetString()
		self.resetMainPanel(preserve=False)


	def refreshCachedJobData(self):
		## Pull new version from API
		jobConfig = self.api.getResource('job/config/{}/{}'.format(self.serviceType, self.currentJob))
		jobData = jobConfig.get(self.currentJob, {})
		## Overwrite cached version
		self.jobDetails[self.currentJob] = jobData


	def OnUpdateButton(self, event=None):
		dataSet = self.jobDetails[self.currentJob].get('content', {})
		dataSetString = json.dumps(dataSet, indent=8)
		self.logger.debug('OnUpdateButton: dataSetString before: {}'.format(dataSetString))
		myDialog = UpdateDialog(self.thisPanel, log=self.logger, jobName=self.currentJob, textString=dataSetString)
		myDialog.CenterOnScreen()
		value = myDialog.ShowModal()
		## Pull results out before destroying the window
		newData = myDialog.textCtrl.GetValue()
		self.logger.debug('OnUpdateButton: dataSetString after : {}'.format(json.dumps(newData, indent=8)))
		myDialog.Destroy()
		if value == wx.ID_OK:
			if newData is None or newData == '':
				self.logger.debug('OnUpdateButton: nothing to insert')
				return
			dataAsDict = json.loads(newData)
			#data = {}
			#data['content'] = dataAsDict
			#data['source'] = 'admin console'
			self.logger.debug('OnUpdateButton: value == OK')
			wx.BeginBusyCursor()
			#(responseCode, responseAsJson) = self.api.putResource('job/config/{}/{}'.format(self.serviceType, self.currentJob), {'content' : data})
			(responseCode, responseAsJson) = self.api.putResource('job/config/{}/{}'.format(self.serviceType, self.currentJob), {'content' : dataAsDict})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Updated job {}'.format(self.currentJob), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnUpdateButton: job updated: {}'.format(self.currentJob))
				## Update the local cached data
				self.refreshCachedJobData()
				self.resetMainPanel()
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'Job update error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnUpdateButton: value == CANCEL')


	def OnInsertButton(self, event=None):
		myDialog = InsertDialog(self.thisPanel, log=self.logger)
		myDialog.CenterOnScreen()
		value = myDialog.ShowModal()
		## Pull results out before destroying the window
		jobData = myDialog.textCtrl.GetValue()
		myDialog.Destroy()
		if value == wx.ID_OK:
			self.logger.debug('OnInsertButton: value == OK')
			if jobData is None or jobData == '':
				self.logger.debug('OnInsertButton: nothing to insert')
				return
			dataAsDict = json.loads(jobData)
			data = {}
			data['source'] = 'admin console'
			data['package'] = self.packageType
			data['content'] = dataAsDict
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.postResource('job/config/{}'.format(self.serviceType), {'content' : data})
			wx.EndBusyCursor()
			if responseCode == 200:
				#dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', 'Inserted Job '.format('{}.{}'.format(self.packageType, dataAsDict.get('jobName'))), wx.OK|wx.ICON_INFORMATION)
				dlgResult = wx.MessageDialog(self.thisPanel, 'SUCCESS', responseAsJson.get('Response'), wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnInsertButton: Job created.')

				wx.BeginBusyCursor()
				self.currentJob = '{}.{}'.format(self.packageType, dataAsDict.get('jobName'))
				self.logger.debug('OnInsertButton: requesting job from API: {}'.format(self.currentJob))
				jobConfig = self.api.getResource('job/config/{}/{}'.format(self.serviceType, self.currentJob))
				jobData = jobConfig.get(self.currentJob, {})
				self.jobDetails[self.currentJob] = jobData
				self.packageList[self.packageType][dataAsDict.get('jobName')] = self.currentJob
				wx.EndBusyCursor()

				## Don't preserve; need to rebuild the items
				self.refreshCachedJobData()
				self.resetMainPanel(preserve=False)
			else:
				errorMsg = json.dumps(responseAsJson)
				with suppress(Exception):
					errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
				dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'Job insert error', wx.OK|wx.ICON_ERROR)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
		else:
			self.logger.debug('OnInsertButton: value == CANCEL')


	def OnDeleteGroupButton(self, event=None):
		self.logger.debug('OnDeleteGroupButton: currentJob: {}'.format(self.currentJob))
		dlgDelete = wx.MessageDialog(self.thisPanel, 'Are you sure you want to delete this job: {}?'.format(self.currentJob), 'Delete job', wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		dlgDelete.CenterOnScreen()
		value = dlgDelete.ShowModal()
		dlgDelete.Destroy()
		wx.BeginBusyCursor()
		try:
			if value == wx.ID_OK:
				self.logger.debug('OnDeleteGroupButton: value == OK')
				## If user pressed OK (and not Cancel), then call API to delete
				(responseCode, responseAsJson) = self.api.deleteResource('job/config/{}/{}'.format(self.serviceType, self.currentJob))
				if responseCode == 200:
					self.logger.debug('OnDeleteGroupButton: removed job: {}'.format(self.currentJob))
				else:
					errorMsg = json.dumps(responseAsJson)
					with suppress(Exception):
						errorMsg = str(responseAsJson[list(responseAsJson.keys())[0]])
					dlgResult = wx.MessageDialog(self.thisPanel, errorMsg, 'Delete job {}'.format(self.currentGroup), wx.OK|wx.ICON_ERROR)
					dlgResult.CenterOnScreen()
					dlgResult.ShowModal()
					dlgResult.Destroy()
				## Probably can just use cache, but let's pull updated data, in
				## case there is some backend failure that didn't remove job...
				## the user would still see it and then troubleshoot.
				self.getJobsForThisService()
				## Don't preserve; need to rebuild the items
				self.resetMainPanel(preserve=False)
			else:
				self.logger.debug('OnDeleteGroupButton: value == CANCEL')
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in OnDeleteGroupButton: {}'.format(stacktrace))
		wx.EndBusyCursor()
