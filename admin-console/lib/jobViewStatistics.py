"""Pane for Admin Console ribbon destination: Jobs->View->Statistics.

This pane presents details of jobs by service.
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix


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

		self.jobFilterBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Job Statistics')
		self.getServices()
		self.reviewOrderedColumns = ['job_completed', 'completed_count', 'endpoint_count',
							   'time_started', 'time_finished', 'time_elapsed',
							   'active_client_count',
							   'count_per_client', 'count_per_status']
		self.reviewOrderedHeaders = ['Completed', 'Total', 'Invoked',
							   'Started', 'Finished', 'Elapsed',
							   'Clients', 'Count By Client', 'Status By Client']
		self.reviewColumnWidthDict = {0:80, 1:50, 2:60, 6:50}
		self.runtimeOrderedColumns = ['status', 'endpoint', 'client_name', 'messages',
							   'time_started', 'time_finished', 'time_elapsed',
							   'result_count', 'date_first_invocation',
							   'date_last_invocation', 'date_last_success',
							   'date_last_failure', 'consecutive_jobs_passed',
							   'consecutive_jobs_failed', 'total_jobs_passed',
							   'total_jobs_failed', 'total_job_invocations']
		self.runtimeOrderedHeaders = ['Status', 'Endpoint', 'Client', 'Messages',
							   'Started', 'Finished', 'Elapsed',
							   'Results', 'First Invocation',
							   'Last Invocation', 'Last Success',
							   'Last Failure', 'Consecutive Passes',
							   'Consecutive Failures', 'Total Passes',
							   'Total Failures', 'Total Invocations']
		self.runtimeColumnWidthDict = {3:200, 7:200, 12:120, 13:120, 14:80, 15:80, 16:100}
		self.jobDetails = {}
		self.packageList = {}
		self.packageTypes = []
		self.packageType = None
		self.currentJob = None
		self.getAllJobsWithStatsForSelectedService()
		self.serviceText = wx.StaticText(self.jobFilterBox, wx.ID_ANY, 'Select Service:')
		self.serviceChoice = wx.Choice(self.jobFilterBox, wx.ID_ANY, (120, 50), choices=self.serviceTypes)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChooseServiceType, self.serviceChoice)
		self.packageText = wx.StaticText(self.jobFilterBox, wx.ID_ANY, 'Select Package:')
		self.packageChoice = wx.Choice(self.jobFilterBox, wx.ID_ANY, (120, 50), choices=self.packageTypes)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChoosePackageType, self.packageChoice)
		self.packageChoice.SetSelection(0)
		self.serviceChoice.SetSelection(0)
		## Job List for selected package
		self.jobListPanel = JobListCtrlPanel(self.jobFilterBox, self.logger, self)
		self.jobListPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.jobListPanelSizer.Add(self.jobListPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
		## Job statistical breakdown button
		self.statsButton = wx.Button(self.jobFilterBox, wx.ID_ANY, 'Statistics on Client Details')
		self.jobFilterBox.Bind(wx.EVT_BUTTON, self.OnStatsButton, self.statsButton)

		## Placeholders for the Runtime and Review panels
		self.reviewBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Service Summary (one row per execution cycle)')
		self.reviewListPanel = RawPanel(self.reviewBox, wx.ID_ANY)
		self.reviewSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.reviewSizerV = wx.BoxSizer(wx.VERTICAL)
		self.reviewSizerV.AddSpacer(10)
		self.reviewSizerV.Add(self.reviewListPanel, 1, wx.EXPAND|wx.ALL, 10)
		self.reviewSizer.Add(self.reviewSizerV)
		self.reviewBox.SetSizer(self.reviewSizer)

		self.runtimeBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Client Details (one row per endpoint)')
		self.runtimeListPanel = RawPanel(self.runtimeBox, wx.ID_ANY)
		self.runtimeSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.runtimeSizerV = wx.BoxSizer(wx.VERTICAL)
		self.runtimeSizerV.AddSpacer(10)
		self.runtimeSizerV.Add(self.runtimeListPanel, 1, wx.EXPAND|wx.ALL, 10)
		self.runtimeSizer.Add(self.runtimeSizerV)
		self.runtimeBox.SetSizer(self.runtimeSizer)

		self.resultPanelSizer = wx.BoxSizer(wx.VERTICAL)
		self.resultPanelSizer.Add(self.reviewBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.resultPanelSizer.AddSpacer(20)
		self.resultPanelSizer.Add(self.runtimeBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

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
		self.leftSizer.Add(self.statsButton, 0, wx.EXPAND|wx.ALL, 10)
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
		runtimeDataSet = self.jobDetails[self.currentJob].get('runtime')
		reviewDataSet = self.jobDetails[self.currentJob].get('review')

		## Cleanup previous data sets
		self.mainBox.Detach(self.resultPanelSizer)
		self.reviewSizerV.Detach(self.reviewListPanel)
		self.reviewSizerV = None
		self.reviewSizer = None
		self.runtimeSizerV.Detach(self.runtimeListPanel)
		self.runtimeSizerV = None
		self.runtimeSizer = None
		self.reviewListPanel.Destroy()
		self.runtimeListPanel.Destroy()
		self.resultPanelSizer = None
		self.resultPanelSizer = wx.BoxSizer(wx.VERTICAL)
		self.runtimeSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.runtimeSizerV = wx.BoxSizer(wx.VERTICAL)
		self.reviewSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.reviewSizerV = wx.BoxSizer(wx.VERTICAL)
		self.reviewBox.Destroy()
		self.runtimeBox.Destroy()
		self.reviewBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Service Summary (one row per execution cycle)')
		self.runtimeBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Client Details (one row per endpoint)')

		## Replace the result panes on the right
		if reviewDataSet is not None:
			self.reviewListPanel = ResultListCtrlPanel(self.reviewBox, self.logger, reviewDataSet, self.reviewOrderedColumns, self.reviewOrderedHeaders, self.reviewColumnWidthDict)
		else:
			self.reviewListPanel = RawPanel(self.reviewBox, wx.ID_ANY)
		if runtimeDataSet is not None:
			self.runtimeListPanel = ResultListCtrlPanel(self.runtimeBox, self.logger, runtimeDataSet, self.runtimeOrderedColumns, self.runtimeOrderedHeaders, self.runtimeColumnWidthDict)
		else:
			self.runtimeListPanel = RawPanel(self.reviewBox, wx.ID_ANY)

		## Put back in the sizers and refresh
		self.reviewSizerV.AddSpacer(20)
		self.reviewSizerV.Add(self.reviewListPanel, 1, wx.EXPAND|wx.ALL, 10)
		self.reviewSizer.Add(self.reviewSizerV, 1, wx.EXPAND)
		self.reviewBox.SetSizer(self.reviewSizer)
		self.runtimeSizerV.AddSpacer(20)
		self.runtimeSizerV.Add(self.runtimeListPanel, 1, wx.EXPAND|wx.ALL, 10)
		self.runtimeSizer.Add(self.runtimeSizerV, 1, wx.EXPAND)
		self.runtimeBox.SetSizer(self.runtimeSizer)
		self.resultPanelSizer.Add(self.reviewBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.resultPanelSizer.AddSpacer(20)
		self.resultPanelSizer.Add(self.runtimeBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.mainBox.Add(self.resultPanelSizer, 1, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
		self.reviewSizer.Layout()
		self.runtimeSizer.Layout()
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
		self.serviceTypes = ['contentGathering', 'universalJob']
		self.serviceType = self.serviceTypes[0]

	def getAllJobsWithStatsForSelectedService(self):
		self.logger.debug('getAllJobsWithStatsForSelectedService')
		self.jobDetails.clear()
		self.packageList.clear()

		apiResults = self.api.getResource('job/review/{}'.format(self.serviceType))
		jobList = apiResults.get('Jobs', [])
		self.logger.debug('getAllJobsWithStatsForSelectedService: review result count: {}.  results: {}'.format(len(jobList), jobList))
		for jobName in jobList:
			self.jobDetails[jobName] = {}
			## Just doing a string split to get package name, which works unless
			## someone puts a period in a job name; more thorough method (though
			## heavier on resources) is to query the package from job/config.
			tmpList = jobName.split('.')
			pkgName = tmpList[0]
			shortName = tmpList[1]
			if pkgName not in self.packageList:
				self.packageList[pkgName] = {}
			self.packageList[pkgName][shortName] = jobName
			jobResults = self.api.getResource('job/review/{}/{}'.format(self.serviceType, jobName))
			jobData = jobResults.get(jobName, [])
			self.jobDetails[jobName]['review'] = jobData

		apiResults = self.api.getResource('job/runtime/{}'.format(self.serviceType))
		jobList = apiResults.get('Jobs', [])
		self.logger.debug('getAllJobsWithStatsForSelectedService: runtime result count: {}.  results: {}'.format(len(jobList), jobList))
		for jobName in jobList:
			## It's possible to have runtime but not review results
			if jobName not in self.jobDetails:
				self.jobDetails[jobName] = {}
				tmpList = jobName.split('.')
				pkgName = tmpList[0]
				shortName = tmpList[1]
			if pkgName not in self.packageList:
				self.packageList[pkgName] = {}
			self.packageList[pkgName][shortName] = jobName

			jobResults = self.api.getResource('job/runtime/{}/{}'.format(self.serviceType, jobName))
			## The result is a dictionary with the keys being endpoints (IPs)
			listFormat = []
			for key,value in jobResults.items():
				listFormat.append(value)
			self.jobDetails[jobName]['runtime'] = listFormat

		self.packageTypes.clear()
		for key in self.packageList:
			self.packageTypes.append(key)
		self.packageType = self.packageTypes[0]
		self.currentJob = self.packageList[self.packageType][next(iter(self.packageList[self.packageType]))]

	def EvtChooseServiceType(self, event):
		self.serviceType = event.GetString()
		self.getAllJobsWithStatsForSelectedService()
		#self.updateVariables()
		## When we change the service, update the package choices
		self.logger.debug('EvtChooseServiceType: update variables')
		self.packageChoice.Clear()
		self.packageTypes.clear()
		flag = True
		for key in self.packageList.keys():
			if flag:
				self.packageType = key
				flag = False
			self.packageTypes.append(key)
			self.packageChoice.Append(key)
		self.packageChoice.SetSelection(0)

		self.currentJob = self.packageList[self.packageType][next(iter(self.packageList[self.packageType]))]
		self.logger.debug('getAllJobsWithStatsForSelectedService: packageType: {}'.format(self.packageType))
		self.logger.debug('getAllJobsWithStatsForSelectedService: currentJob: {}'.format(self.currentJob))
		self.resetMainPanel(preserve=False)


	def EvtChoosePackageType(self, event):
		self.packageType = event.GetString()
		self.resetMainPanel(preserve=False)


	def OnStatsButton(self, event=None):
		apiResults = self.api.getResource('job/runtime/{}/{}/stats'.format(self.serviceType, self.currentJob))
		message = json.dumps(apiResults, indent=8)
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self.thisPanel, message, "Runtime statistics for {}".format(self.currentJob), size=(500, 500))
		dlg.ShowModal()
		dlg.Destroy()
