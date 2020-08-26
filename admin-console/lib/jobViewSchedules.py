"""Pane for Admin Console ribbon destination: Data->Content->Simple Queries.

This pane presents graphical layouts of models, through the D3 visualizer, using
icons provided by icons8 (https://icons8.com).
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix
import wx.html2
from wx.adv import HyperlinkCtrl


def mapViewData(viewData):
	part1 = """<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8" />
	<link rel="stylesheet" type="text/css" href="./static/ocp_calendar.css" />
</head>
<body>
	<script src="./static/d3.js"></script>
	<script src="./static/ocp_calendar.js"></script>
	<div>
		<script>
			var jsonData = """
	part2 = """;
			ocp_calendar.exec(jsonData);
		</script>
	</div>
</body>
</html>"""
	fullPage = '{}{}{}'.format(part1, viewData, part2)

	## end mapViewData
	return fullPage


class SchedulerChart(wx.Panel):
	def __init__(self, parent, log, api, dataPanelRef):
		try:
			wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
			self.logger = log
			self.logger.debug('SchedulerChart: 1')
			self.api = api
			self.owner = dataPanelRef
			self.webPageContent = ''
			self.localDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webview')
			self.cachedPage = os.path.join(self.localDir, 'thisCalendar.html')
			# self.localD3 = os.path.join(self.localDir, 'static', 'd3.js')
			# self.localWrapper = os.path.join(self.localDir, 'static', 'ocp_calendar.js')
			# self.localCSS = os.path.join(self.localDir, 'static', 'ocp_calendar.css')
			self.browser = wx.html2.WebView.New(self)
			self.viewBox1 = wx.BoxSizer()
			self.viewBox1.Add(self.browser, 1, wx.EXPAND|wx.ALL, 5)
			self.SetSizer(self.viewBox1)
			self.viewBox1.Layout()
			self.logger.debug('SchedulerChart: 2')

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			log.debug('Failure in SchedulerChart: {}'.format(stacktrace))


	def getPage(self, queryName):
		#results = [{"start":"2019-08-18 18:00:00","stop":"2019-08-18 20:00:00"},{"start":"2019-08-21 06:00:00","stop":"2019-08-21 10:00:00"},{"start":"2019-08-23 18:00:00","stop":"2019-08-23 23:00:00"},{"start":"2019-08-23 20:21:00","stop":"2019-08-23 21:21:00"},{"start":"2019-08-25 17:01:00","stop":"2019-08-25 22:01:00"},{"start":"2019-08-26 17:23:00","stop":"2019-08-26 23:23:00"},{"start":"2019-08-26 17:52:00","stop":"2019-08-26 23:52:00"},{"start":"2019-08-26 21:01:00","stop":"2019-08-26 23:01:00"},{"start":"2019-08-27 11:23:00","stop":"2019-08-27 23:23:00"},{"start":"2019-08-29 20:21:00","stop":"2019-08-29 21:21:00"},{"start":"2019-08-31 20:21:00","stop":"2019-08-31 21:21:00"}]
		#results = [{"time_started":"2019-08-18 18:00:00","time_finished":"2019-08-18 20:00:00"},{"time_started":"2019-08-21 06:00:00","time_finished":"2019-08-21 10:00:00"}]
		results = []
		if self.owner.showAllJobs == True:
			for job,valueList in self.owner.allData.items():
				for entry in valueList:
					results.append(entry)
		else:
			activeList = self.owner.jobListPanel.currentItems
			for job in activeList:
				for entry in self.owner.allData[job]:
					results.append(entry)
			self.owner.jobListPanel.currentItems
		if len(results) > 0:
			self.webPageContent = mapViewData(json.dumps(results))
		with open(self.cachedPage, 'w') as out:
			out.write(self.webPageContent)
		self.logger.debug('Web page to load:\n{}'.format(self.webPageContent))


	def loadPage(self, queryName):
		self.getPage(queryName)
		## Now serve the content out to our frame via html2 webview
		self.logger.debug('Local file to load: {}'.format(self.cachedPage))
		pageWithFileAppendage = r'file:///{}'.format(self.cachedPage)
		self.logger.debug('loading url:  {}'.format(pageWithFileAppendage))
		self.browser.LoadURL(pageWithFileAppendage)
		# self.browser.SetPage(self.webPageContent, pageWithFileAppendage)
		# self.browser.Reload()
		self.logger.debug('SchedulerChart: 4')


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class JobListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, dataPanelRef):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(240, -1), style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.CLIP_CHILDREN)
		sizer.Add(self.list, 1, wx.EXPAND)
		## Pull object count from API
		self.jobs = dict()
		self.currentItems = []
		self.formatJobs()
		self.logger.debug('Jobs found: {}'.format(self.jobs))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.jobs
		listmix.ColumnSorterMixin.__init__(self, 2)
		self.defaultColor = None
		if len(self.jobs) > 0:
			self.defaultColor = self.list.GetItemBackgroundColour(0)
			self.logger.debug('JobListCtrlPanel defaultColor: {}'.format(self.defaultColor))
		self.SetSizer(sizer)
		sizer.Fit(self)
		self.Layout()
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
		# self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
		# self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
		# self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
		# self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
		# self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self.list)
		# self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self.list)
		# self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self.list)
		# self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
		# for wxMSW
		# self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
		# # for wxGTK
		# self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)

	def formatJobs(self):
		objectId = 1
		for name in self.owner.jobDetails:
			self.jobs[objectId] = name
			objectId += 1

	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.jobs
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Select Specific Jobs"
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
			self.list.SetItemData(index, key)
		#self.list.SetColumnWidth(0, 240)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	# def getCurrentItem(self):
	# 	return self.currentItem

	# def setCurrentItem(self, value=0):
	# 	self.currentItem = value
	# 	self.list.Select(value)

	def clearSelection(self):
		self.logger.debug("JobListCtrlPanel: clearSelection...")
		for currentItem in list(self.currentItems):
			self.logger.debug("JobListCtrlPanel: clearing the current item: {}".format(currentItem))
			self.list.Select(currentItem, on=0)
			#self.list.SetItemBackgroundColour(currentItem, "WHITE")
			self.currentItems.remove(currentItem)

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def resetDataPanel(self, selection):
		self.logger.debug("JobListCtrlPanel: resetDataPanel...")
		wx.BeginBusyCursor()
		self.owner.schedulePanel.loadPage(selection)
		wx.EndBusyCursor()
		self.logger.debug("JobListCtrlPanel: resetDataPanel... DONE")

	def OnItemSelected(self, event):
		## Using simple click/select to both add and remove
		currentItem = event.Index
		name = self.list.GetItemText(currentItem)
		self.logger.debug("OnItemSelected: %s, %s" % (currentItem, name))
		if currentItem not in self.currentItems:
			self.currentItems.append(currentItem)
			#self.list.SetItemBackgroundColour(currentItem, "LIGHT GREY")
		# else:
		# 	self.logger.debug("Need to remove item: {}. set to {}".format(currentItem, self.defaultColor))
		# 	self.list.SetItemBackgroundColour(currentItem, wx.NullColour)
		# 	#self.list.SetItemBackgroundColour(currentItem, self.defaultColor)
		# 	self.currentItems.remove(currentItem)
		# 	#self.list.Select(currentItem, on=0)
		self.logger.debug("Current items: {}".format(self.currentItems))
		## Highlight all the currently selected items; default seems to be just
		## the last selected item
		# if len(self.currentItems) > 1:
		# 	for currentItem in self.currentItems:
		# 		self.list.SetItemBackgroundColour(currentItem, "LIGHT GREY")
		self.owner.resetMainPanel()
		event.Skip()

	# def OnItemDeselected(self, evt):
	# 	item = evt.GetItem()
	# 	self.logger.debug("OnItemDeselected: %d" % evt.Index)
	#
	# def OnItemActivated(self, event):
	# 	self.currentItem = event.Index
	# 	self.logger.debug("OnItemActivated: %s\nTopItem: %s" %
	# 					   (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))
	#
	# def OnColClick(self, event):
	# 	self.logger.debug("OnColClick: %d\n" % event.GetColumn())
	# 	event.Skip()
	#
	# def OnColRightClick(self, event):
	# 	item = self.list.GetColumn(event.GetColumn())
	# 	self.logger.debug("OnColRightClick: %d %s\n" %
	# 					   (event.GetColumn(), (item.GetText(), item.GetAlign(),
	# 											item.GetWidth(), item.GetImage())))
	# 	if self.list.HasColumnOrderSupport():
	# 		self.logger.debug("OnColRightClick: column order: %d\n" %
	# 						   self.list.GetColumnOrder(event.GetColumn()))
	#
	# def OnColBeginDrag(self, event):
	# 	self.logger.debug("OnColBeginDrag")
	#
	# def OnColDragging(self, event):
	# 	self.logger.debug("OnColDragging")
	#
	# def OnColEndDrag(self, event):
	# 	self.logger.debug("OnColEndDrag")
	#
	# def OnDoubleClick(self, event):
	# 	self.logger.debug("OnDoubleClick item %s\n" % self.list.GetItemText(self.currentItem))
	# 	event.Skip()
	#
	# def OnRightClick(self, event):
	# 	self.logger.debug("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))


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

		self.jobFilterBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Job Schedules')
		self.rb = wx.RadioBox(self.jobFilterBox, wx.ID_ANY, 'Data set', wx.DefaultPosition, wx.DefaultSize, ['Historical', 'Projected'], 1, wx.RA_SPECIFY_COLS)
		self.thisPanel.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
		self.rb.SetToolTip(wx.ToolTip('Historical shows past data. Projected shows actively scheduled jobs with projected runtimes based off past executions.'))
		self.getServices()
		self.serviceText = wx.StaticText(self.jobFilterBox, wx.ID_ANY, 'Select Service:')
		self.serviceChoice = wx.Choice(self.jobFilterBox, wx.ID_ANY, (120, 50), choices=self.services)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChooseServiceType, self.serviceChoice)
		self.serviceChoice.SetSelection(0)

		self.allJobsButton = wx.Button(self.jobFilterBox, wx.ID_ANY, 'All Jobs')
		self.allJobsButton.SetToolTip(wx.ToolTip('Show all jobs - the default selection'))
		self.jobFilterBox.Bind(wx.EVT_BUTTON, self.OnAllJobsButton, self.allJobsButton)
		self.clearButton = wx.Button(self.jobFilterBox, wx.ID_ANY, 'Clear')
		self.clearButton.SetToolTip(wx.ToolTip('Clear data panel'))
		self.jobFilterBox.Bind(wx.EVT_BUTTON, self.OnClearButton, self.clearButton)

		## Job List for selected package
		self.allData = {}
		self.activeData = []
		self.jobDetails = {}
		self.getHistoricalDataSet()
		self.showAllJobs = True

		self.jobListPanel = JobListCtrlPanel(self.jobFilterBox, self.logger, self)
		self.jobListPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.jobListPanelSizer.Add(self.jobListPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

		## Create boxes to arrange the panels
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		topBorder, otherBorder = self.jobFilterBox.GetBordersForSizer()
		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.AddSpacer(topBorder + 5)
		self.leftSizer.Add(self.rb, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.serviceText, 0, wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(5)
		self.leftSizer.Add(self.serviceChoice, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(20)
		self.leftSizer.Add(self.allJobsButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.clearButton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		self.leftSizer.AddSpacer(10)
		self.leftSizer.Add(self.jobListPanelSizer, 1, wx.EXPAND)
		self.jobFilterBox.SetSizer(self.leftSizer)
		self.mainQueryBox.Add(self.jobFilterBox, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)

		## Panel on right for the graphical chart
		self.schedulePanel = SchedulerChart(self.thisPanel, self.logger, self.api, self)
		# #self.schedulePanel = RawPanel(self.thisPanel, wx.ID_ANY)
		self.scheduleSizer = wx.BoxSizer(wx.VERTICAL)
		self.scheduleSizer.AddSpacer(6)
		self.scheduleSizer.Add(self.schedulePanel, 1, wx.EXPAND|wx.ALL, 6)
		# #self.schedulePanel.loadPage('test')
		self.scheduleSizer.Layout()

		self.mainBox.Add(self.mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.scheduleSizer, 1, wx.EXPAND)
		#self.mainBox.Add(self.schedulePanel, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 5)


		self.logger.debug('Main.init')
		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)

		wx.EndBusyCursor()
		self.resetMainPanel()


	def resetMainPanel(self, preserve=True):
		self.thisPanel.Freeze()

		## Cleanup previous data sets
		# self.scheduleSizer.Detach(self.schedulePanel)
		# self.mainBox.Detach(self.scheduleSizer)
		# self.schedulePanel.Destroy()
		# self.schedulePanel = None
		# self.scheduleSizer = None

		## Replace the pane on the right
		# self.schedulePanel = SchedulerChart(self.thisPanel, self.logger, self.api)
		#
		# ## Recreate the sizer and refresh
		# self.scheduleSizer = wx.BoxSizer(wx.VERTICAL)
		# self.scheduleSizer.Add(self.schedulePanel, 1, wx.EXPAND|wx.ALL, 10)
		#
		# self.mainBox.Add(self.scheduleSizer, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 5)
		# self.scheduleSizer.Layout()
		self.schedulePanel.loadPage('test')


		if not preserve:
			## Conditionally replace the job list on the left
			newListPanel = JobListCtrlPanel(self.jobFilterBox, self.logger, self)
			self.leftSizer.Detach(self.jobListPanelSizer)
			self.jobListPanel.Destroy()
			self.jobListPanel = newListPanel
			self.jobListPanelSizer = None
			self.jobListPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
			self.jobListPanelSizer.Add(self.jobListPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
			self.leftSizer.Insert(7, self.jobListPanelSizer, wx.EXPAND)
			self.leftSizer.Layout()
			self.jobFilterBox.Layout()
			## setCurrentItem will call resetMainPanel again, for force resizing
			#self.jobListPanel.setCurrentItem()

		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()
		self.logger.debug('Stop resetMainPanel')

	def getServices(self):
		self.services = ['contentGathering', 'universalJob']
		self.serviceType = self.services[0]


	def getProjectedDataSet(self):
		self.logger.debug('getProjectedDataSet')
		self.jobDetails.clear()
		apiResults = self.api.getResource('job/config/{}'.format(self.serviceType))
		jobList = apiResults.get('Jobs', [])
		for jobName in jobList:
			jobResults = self.api.getResource('job/config/{}/{}'.format(self.serviceType, jobName))
			if jobResults.get(jobName, {}).get('active', False):
				jobData = jobResults.get(jobName, {}).get('content', {})
				self.jobDetails[jobName] = {}
				self.jobDetails[jobName]['triggerType'] = jobData['triggerType']
				self.jobDetails[jobName]['schedulerArgs'] = jobData['schedulerArgs']


	def getHistoricalDataSet(self):
		self.logger.debug('getHistoricalDataSet')
		self.jobDetails.clear()
		self.allData.clear()
		## Set a filter condition to only get the last 2 weeks of data
		queryFilter = { "content": {
			"filter": [{
				"condition": {
					"attribute": "time_started",
					"operator": "lastnumhours",
					"value": 336
					}
			}]}
		}
		apiResults = self.api.getResource('job/review/{}/filter'.format(self.serviceType), customPayload=queryFilter)
		for key,result in apiResults.items():
			jobName = result.get('job')
			if jobName not in self.allData:
				self.allData[jobName] = []
				self.jobDetails[jobName] = {}
			self.allData[jobName].append(result)
		self.logger.debug('getHistoricalDataSet: allData count: {}'.format(len(self.jobDetails)))


	def getFilters(self):
		self.showFilters = ['True', 'False']
		self.filterId = 0
		self.currentFilter = self.showFilters[0]

	def EvtRadioBox(self, event):
		filterId = event.GetInt()
		if filterId == 0:
			self.getHistoricalDataSet()
		else:
			self.getProjectedDataSet()
		self.resetMainPanel()

	def EvtChooseServiceType(self, event):
		self.serviceType = event.GetString()
		self.getProjectedDataSet()
		self.resetMainPanel(False)

	def OnAllJobsButton(self, event=None):
		self.jobListPanel.clearSelection()
		self.showAllJobs = True

	def OnClearButton(self, event=None):
		self.jobListPanel.clearSelection()
		self.showAllJobs = False
