"""Pane for Admin Console ribbon destination: Jobs->View->Listing.

This pane presents details of jobs by service.
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)


class ResultListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, jobDetails, jobView, headers):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.logger.debug('Inside ResultListCtrlPanel')
		self.api = api
		self.SetAutoLayout(1)
		self.jobDetails = jobDetails
		self.jobView = jobView
		self.headers = headers
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		self.list.SetAutoLayout(1)
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.jobView
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
		for key,value in self.jobView.items():
			index = self.list.InsertItem(self.list.GetItemCount(), str(value[0]))
			for x in range(len(self.headers)-1):
				self.list.SetItem(index, x+1, str(value[x+1]))
			self.list.SetItemData(index, key)
		col = 0
		## Set column widths
		for header in self.headers:
			self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
			col += 1
		self.currentItemId = None
		self.currentItem = 0
		self.logger.debug('PopulateList... data: {}'.format(self.jobView))
		if self.jobView is not None and len(self.jobView) > 0:
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
		message = ''
		pos = 0
		name = self.getColumnText(self.currentItem, 0)
		#realm = self.getColumnText(self.currentItem, 1)
		self.logger.debug("OnPropertiesPopup: name: {}".format(name))
		self.logger.debug("OnPropertiesPopup: job data: {}".format(self.jobDetails[name]))
		originalData = self.jobDetails[name]
		for attr,value in originalData.items():
			## Transform 'content' into JSON
			if attr == 'content':
				value = json.dumps(value, indent=4)
			newEntry = '{}: {}\n'.format(attr, value)
			if message is None:
				message = newEntry
			else:
				message = '{}{}'.format(message, newEntry)
			pos += 1
		self.logger.debug('OnPropertiesPopup: 3: message: {}'.format(message))
		self.logger.debug('OnPropertiesPopup: 3: size: {}'.format(len(message)))
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "Properties", size=(500, 800))
		dlg.ShowModal()
		dlg.Destroy()


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

		self.jobFilterBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Job Listing')
		self.model = {}
		self.modelListTracker = {}
		self.modelList = []
		self.metaDataSnapshots = {}
		self.getServices()
		self.getFilters()
		self.orderedColumns = ['name', 'package', 'realm', 'active', 'object_created_by', 'object_updated_by', 'time_created', 'time_updated']
		self.orderedHeaders = ['name', 'package', 'realm', 'active', 'created by', 'updated by', 'created', 'last updated']
		self.jobDetails = {}
		self.jobView = {}
		self.serviceText = wx.StaticText(self.jobFilterBox, wx.ID_ANY, 'Select Service:')
		self.serviceChoice = wx.Choice(self.jobFilterBox, wx.ID_ANY, (120, 50), choices=self.serviceTypes)
		self.serviceChoice.SetSelection(0)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChooseServiceType, self.serviceChoice)
		self.rb = wx.RadioBox(self.jobFilterBox, wx.ID_ANY, 'Show', wx.DefaultPosition, wx.DefaultSize, self.showFilters, 1, wx.RA_SPECIFY_COLS)
		self.thisPanel.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
		self.rb.SetToolTip(wx.ToolTip('Select a filter'))

		## Placeholder for the JobList
		self.jobListPanel = RawPanel(thisPanel, wx.ID_ANY)
		self.getAllJobs()
		self.getFilteredJobs()

		## Create boxes to arrange the panels
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		self.thisPanel.Freeze()
		topBorder, otherBorder = self.jobFilterBox.GetBordersForSizer()
		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.AddSpacer(topBorder)
		self.leftSizer.Add(self.serviceText, 0, wx.TOP|wx.LEFT, 5)
		self.leftSizer.Add(self.serviceChoice, 0, wx.EXPAND|wx.ALL, 5)
		self.leftSizer.AddSpacer(topBorder + 3)
		self.leftSizer.Add(self.rb, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.jobFilterBox.SetSizer(self.leftSizer)
		self.mainQueryBox.Add(self.jobFilterBox, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.jobListPanel, 1, wx.EXPAND|wx.TOP, 7)

		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()

		wx.EndBusyCursor()
		self.updateDataPanel()


	def updateDataPanel(self):
		try:
			wx.BeginBusyCursor()
			self.logger.debug('updateDataPanel: starting')
			self.thisPanel.Freeze()

			## Replace the jobListPanel pane on the right
			self.mainBox.Detach(self.jobListPanel)
			self.jobListPanel.Destroy()
			self.jobListPanel = ResultListCtrlPanel(self.thisPanel, self.logger,
													self.api, self.jobDetails,
													self.jobView, self.orderedHeaders)
			self.mainBox.Add(self.jobListPanel, 1, wx.EXPAND|wx.ALL, 15)
			self.thisPanel.SetSizer(self.mainBox)
			self.thisPanel.Thaw()
			self.thisPanel.Show()
			self.thisPanel.SendSizeEvent()
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in updateDataPanel: {}'.format(stacktrace))
		wx.EndBusyCursor()


	def getServices(self):
		self.serviceTypes = ['contentGathering', 'universalJob']
		self.serviceType = self.serviceTypes[0]

	def getFilters(self):
		self.showFilters = ['Active', 'Disabled', 'All']
		self.filterId = 0
		self.currentFilter = self.showFilters[0]

	def getAllJobs(self):
		self.logger.debug('getJobs')
		self.jobDetails.clear()
		apiResults = self.api.getResource('job/config/{}'.format(self.serviceType))
		jobList = apiResults.get('Jobs', [])
		for jobName in jobList:
			jobResults = self.api.getResource('job/config/{}/{}'.format(self.serviceType, jobName))
			jobData = jobResults.get(jobName, {})
			self.jobDetails[jobName] = jobData

	def getFilteredJobs(self):
		objectId = 1
		self.jobView.clear()
		self.logger.debug('getFilteredJobs... service: {}, filter: {}'.format(self.serviceType, self.currentFilter))
		for jobName,jobData in self.jobDetails.items():
			## See if this job makes the cut
			isActive = jobData.get('active', False)
			if self.currentFilter == 'Active' and not isActive:
				continue
			elif self.currentFilter == 'Disabled' and isActive:
				continue
			## Only put specific keys in the view, and in a natural order
			attrList = []
			for col in self.orderedColumns:
				value = jobData.get(col)
				if value is None:
					value = ''
				attrList.append(value)
			self.jobView[objectId] = attrList
			objectId += 1

	def EvtRadioBox(self, event):
		filterId = event.GetInt()
		self.logger.debug('EvtRadioBox:     entry id : {}'.format(filterId))
		self.logger.debug('EvtRadioBox: selection: {}'.format(self.showFilters[filterId]))
		if self.filterId != filterId:
			try:
				self.currentFilter = self.showFilters[filterId]
				self.filterId = filterId
				self.getFilteredJobs()
				self.updateDataPanel()
			except:
				stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				self.logger.debug('Failure in EvtRadioBox: {}'.format(stacktrace))


	def EvtChooseServiceType(self, event):
		self.serviceType = event.GetString()
		self.getAllJobs()
		self.getFilteredJobs()
		self.updateDataPanel()
