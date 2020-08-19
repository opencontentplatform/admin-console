"""Pane for Admin Console ribbon destination: Jobs->Modify->Config.

This pane presents details of jobs by service.
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix


class MyEvent(wx.PyCommandEvent):
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)
		self.myVal = None

class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

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

		self.jobFilterBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Toggle Job')
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
		self.enableButton = None
		self.disableButton = None

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
		self.enableButton = None
		self.disableButton = None
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

		## Buttons
		self.enableButton = wx.Button(self.jobConfigBox, wx.ID_ANY, 'Enable job')
		self.jobConfigBox.Bind(wx.EVT_BUTTON, self.OnEnableButton, self.enableButton)
		self.disableButton = wx.Button(self.jobConfigBox, wx.ID_ANY, 'Disable job')
		self.jobConfigBox.Bind(wx.EVT_BUTTON, self.OnDisableButton, self.disableButton)

		## Get current dataSet to display in the textCtl pane on the right
		self.getEndpoints()
		if len(self.endpoints) > 0:
			textString = json.dumps(self.endpoints, indent=8)
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
		self.dataSizer6 = wx.BoxSizer(wx.HORIZONTAL)
		self.dataSizer6.Add(self.enableButton, 0, wx.LEFT|wx.RIGHT, 10)
		self.dataSizer6.Add(self.disableButton, 0, wx.LEFT|wx.RIGHT, 10)
		self.jobConfigSizerV.Add(self.dataSizer6, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		self.jobConfigSizerV.AddSpacer(10)

		if self.text6 is not None:
			self.dataSizer6 = wx.BoxSizer(wx.HORIZONTAL)
			self.dataSizer6.Add(self.text6, 0, wx.LEFT, 5)
			self.dataSizer6.Add(self.value6, 0, wx.EXPAND)
			self.jobConfigSizerV.Add(self.dataSizer6, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		if self.text7 is not None:
			self.dataSizer7 = wx.BoxSizer(wx.HORIZONTAL)
			self.dataSizer7.Add(self.text7, 0, wx.LEFT, 5)
			self.dataSizer7.Add(self.value7, 0, wx.EXPAND)
			self.jobConfigSizerV.Add(self.dataSizer7, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

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

	def getEndpoints(self):
		dataSet = self.jobDetails.get(self.currentJob)
		jobContent = dataSet.get('content')
		## Get target endpoints (via either JSON query or Python script)
		self.endpoints = []
		self.text6 = None
		self.value6 = None
		self.text7 = None
		self.value7 = None
		if 'clientOnlyTrigger' in jobContent:
			## Runs on clients
			clientEndpoint = jobContent.get('clientEndpoint', '')
			self.text6 = wx.StaticText(self.jobConfigBox, label="clientEndpoint: ")
			self.value6 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(clientEndpoint), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)

			healthType = 'Unknown'
			if self.serviceType == 'contentGathering':
				healthType = 'ServiceContentGatheringHealth'
			elif self.serviceType == 'universalJob':
				healthType = 'ServiceUniversalJobHealth'
			clientData = self.api.getResource('config/search/{}'.format(healthType), {'content': {"filter": []}})
			for key,value in clientData.items():
				self.endpoints.append(value.get('name', ''))

			## if clientEndpoint is 'any' or a specific name:
			numberOfEndpoints = 1
			if clientEndpoint.lower() == 'all':
				## if clientEndpoint is 'all', count currently active clients
				numberOfEndpoints = len(self.endpoints)
			self.text7 = wx.StaticText(self.jobConfigBox, label="number of endpoints: ")
			self.value7 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(numberOfEndpoints), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)

		elif 'endpointQuery' in jobContent:
			## Get the results of the endpointQuery
			endpointQuery = jobContent.get('endpointQuery', '')
			endpointIdColumn = jobContent.get('endpointIdColumn')
			endpoints = self.api.getResource('query/endpoint/{}'.format(endpointQuery))
			for endpoint in endpoints:
				## Only use the endpointIdColumn attribute, to keep the data neat
				entry = endpoint.get('data', {}).get(endpointIdColumn)
				if entry is not None:
					self.endpoints.append(entry)

			self.text6 = wx.StaticText(self.jobConfigBox, label="endpointQuery: ")
			self.value6 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=endpointQuery, size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)
			self.text7 = wx.StaticText(self.jobConfigBox, label="number of endpoints: ")
			self.value7 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=str(len(self.endpoints)), size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)

		elif 'endpointScript' in jobContent:
			endpointScript = jobContent.get('endpointScript', '')
			self.text6 = wx.StaticText(self.jobConfigBox, label="endpointScript: ")
			self.value6 = wx.TextCtrl(self.jobConfigBox, wx.ID_ANY, value=endpointScript, size=(500,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)


	def OnDisableButton(self, event=None):
		self.logger.debug('OnDisableButton... current job: {}'.format(self.currentJob))
		jobData = self.jobDetails[self.currentJob]
		jobContent = jobData.get('content', {})
		jobIsDisabled = jobContent.get('isDisabled', True)
		## First check if it's disabled and needs modified
		if jobIsDisabled:
			dlgResult = wx.MessageDialog(self.thisPanel, 'Job is already disabled: {}'.format(self.currentJob), 'WARNING', wx.OK|wx.ICON_WARNING)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()
			self.logger.error('OnDisableButton: job already enabled.')

		else:
			## Job needs an update
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.putResource('job/config/{}/{}'.format(self.serviceType, self.currentJob), {'content' : {'isDisabled': True}})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'Disabled job: {}'.format(self.currentJob), 'SUCCESS', wx.OK|wx.ICON_INFORMATION)
				dlgResult.CenterOnScreen()
				dlgResult.ShowModal()
				dlgResult.Destroy()
				self.logger.debug('OnDisableButton: job disabled: {}'.format(self.currentJob))
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


	def OnEnableButton(self, event=None):
		self.logger.debug('OnEnableButton... current job: {}'.format(self.currentJob))
		jobData = self.jobDetails[self.currentJob]
		jobContent = jobData.get('content', {})
		jobIsDisabled = jobContent.get('isDisabled', True)
		## First check if it's disabled and needs modified
		if not jobIsDisabled:
			#dlgResult = wx.MessageDialog(self.thisPanel, 'WARNING', 'Job is already active: {}'.format(self.currentJob), wx.OK|wx.ICON_ERROR)
			dlgResult = wx.MessageDialog(self.thisPanel, 'Job is already active: {}'.format(self.currentJob), 'WARNING', wx.OK|wx.ICON_WARNING)
			dlgResult.CenterOnScreen()
			dlgResult.ShowModal()
			dlgResult.Destroy()
			self.logger.error('OnEnableButton: job already enabled.')

		else:
			## Job needs an update
			wx.BeginBusyCursor()
			(responseCode, responseAsJson) = self.api.putResource('job/config/{}/{}'.format(self.serviceType, self.currentJob), {'content' : {'isDisabled': False}})
			wx.EndBusyCursor()
			if responseCode == 200:
				dlgResult = wx.MessageDialog(self.thisPanel, 'Enabled job: {}'.format(self.currentJob), 'SUCCESS', wx.OK|wx.ICON_INFORMATION)
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
