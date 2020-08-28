"""Pane for Admin Console ribbon destination: Data->Content->Simple Queries.

This pane presents graphical layouts of models, through the D3 visualizer, using
icons provided by icons8 (https://icons8.com).
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress
import datetime
import wx
import wx.lib.mixins.listctrl as listmix
import wx.html2
from wx.adv import HyperlinkCtrl
import locale
from cstriggers.core.trigger import QuartzCron


## Global helpers
def monthConversionFromApsToQuartz(value, newValue=None):
	## Conversion: 1-12 for APS, but 0-11 for Quartz
	if isinstance(value, int) or value.isdigit():
		if newValue is None:
			newValue = int(value)-1
		else:
			newValue = '{}{}'.format(newValue, int(value)-1)

	elif isinstance(value, str):
		## If value has commas, split and work through each entry
		if re.search(',', value):
			for entry in value.split(','):
				if newValue is None:
					newValue = monthConversionFromApsToQuartz(entry, '')
				else:
					newValue = '{},{}'.format(newValue, monthConversionFromApsToQuartz(entry, ''))

		## If value has hyphens, split and work the start/stop
		elif re.search('-', value):
			entries = value.split('-')
			rawStart = entries[0]
			rawStop = entries[1]

			## Abreviated month names will be the same for both schedulers
			start = monthConversionFromApsToQuartz(rawStart, '')
			stop = monthConversionFromApsToQuartz(rawStop, '')
			if newValue is None:
				newValue = '{}-{}'.format(start, stop)
			else:
				newValue = '{}{}-{}'.format(newValue, start, stop)

		else:
			## Probably could do more parsing to verify it's a proper month, but
			## let's just assume that's enough for now
			if newValue is None:
				newValue = value
			else:
				newValue = '{}{}'.format(newValue, value)

	else:
		raise EnvironmentError('month value not recognized: {}'.format(value))
	if newValue is None:
		raise EnvironmentError('month value not recognized: {}'.format(value))

	## end monthConversionFromApsToQuartz
	return newValue


def dayOfWeekConversionFromApsToQuartz(value, newValue=None):
	## Conversion: str|int 0-6 mon-sun for APS, str|int 1-7 sun-sat for Quartz
	## This doesn't take into account xth y, last, and other special cases;
	## just trying to convert between common library value differences...

	## accept both JSON string or int forms: e.g. '2' or 2
	if isinstance(value, int) or value.isdigit():
		conversionTool = { 0 : 2,
						   1 : 3,
						   2 : 4,
						   3 : 5,
						   4 : 6,
						   5 : 7,
						   6 : 1 }
		if newValue is None:
			newValue = conversionTool.get(value)
		else:
			newValue = '{}{}'.format(newValue, conversionTool.get(value))

	elif isinstance(value, str):
		## If value has commas, split and work through each entry
		if re.search(',', value):
			for entry in value.split(','):
				if newValue is None:
					newValue = dayOfWeekConversionFromApsToQuartz(entry, '')
				else:
					newValue = '{},{}'.format(newValue, dayOfWeekConversionFromApsToQuartz(entry, ''))

		## If value has hyphens, split and work the start/stop
		elif re.search('-', value):
			entries = value.split('-')
			rawStart = entries[0]
			rawStop = entries[1]

			## Account for different end days of sequence (sun for APS, but sat for Quartz)
			alreadyProcessed = False

			## Need to do something different if the stop sequence is SUNDAY
			## Deal with this on digit ranges first...
			if rawStop.isdigit():
				rawStop = int(rawStop)
				if rawStop == 6:
					## If start is SAT and stop is SUN
					## Assuming since we started with a digit, we have digits
					rawStart = int(rawStart)
					if rawStart == 5:
						## Replace the 5-6 range with 1,7
						if newValue is None:
							newValue = '1,7'
						else:
							newValue = '{}1,7'.format(newValue)
							alreadyProcessed = True
					## Otherwise move stop back to SAT and add SUN with a comma
					else:
						## Comma add SUN at the start
						if newValue is None:
							newValue = '1,'
						else:
							newValue = '{}1,'.format(newValue)
						## Convert the remaining range
						start = dayOfWeekConversionFromApsToQuartz(rawStart, '')
						stop = dayOfWeekConversionFromApsToQuartz(5, '')
						newValue = '{}{}-{}'.format(newValue, start, stop)
						alreadyProcessed = True

			## Now address the abreviated word ranges...
			else:
				if rawStop.lower() == 'sun':
					## If start is SAT and stop is SUN
					if rawStart.lower() == 'sat':
						## Replace the sat-sun range with sun,sat
						if newValue is None:
							newValue = 'sun,sat'
						else:
							newValue = '{}sun,sat'.format(newValue)
							alreadyProcessed = True
					## Otherwise move stop back to SAT and add SUN with a comma
					else:
						## Comma add SUN at the start
						if newValue is None:
							newValue = 'sun,'
						else:
							newValue = '{}sun,'.format(newValue)
						## Convert the remaining range
						start = dayOfWeekConversionFromApsToQuartz(rawStart, '')
						stop = dayOfWeekConversionFromApsToQuartz('sat', '')
						newValue = '{}{}-{}'.format(newValue, start, stop)
						alreadyProcessed = True

			if not alreadyProcessed:
				## This means SUNDAY wasn't in the range, so do normal processing
				start = dayOfWeekConversionFromApsToQuartz(rawStart, '')
				stop = dayOfWeekConversionFromApsToQuartz(rawStop, '')
				if newValue is None:
					newValue = '{}-{}'.format(start, stop)
				else:
					newValue = '{}{}-{}'.format(newValue, start, stop)

		else:
			## Probably could do more parsing to verify it's a proper day, but
			## let's just assume that's enough for now
			if newValue is None:
				newValue = value
			else:
				newValue = '{}{}'.format(newValue, value)

	else:
		raise EnvironmentError('day_of_week value not recognized: {}'.format(value))
	if newValue is None:
		raise EnvironmentError('day_of_week value not recognized: {}'.format(value))

	## end dayOfWeekConversionFromApsToQuartz
	return newValue


class SchedulerChart(wx.Panel):
	def __init__(self, parent, log, dataSet):
		try:
			wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
			self.logger = log
			self.logger.debug('SchedulerChart initialized')
			self.jsonData = []
			if isinstance(dataSet, list) and len(dataSet) > 0:
				self.jsonData = dataSet
			self.localDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webview')
			self.cachedPage = os.path.join(self.localDir, 'thisCalendar.html')
			self.browser = wx.html2.WebView.New(self)
			self.viewBox1 = wx.BoxSizer()
			self.viewBox1.Add(self.browser, 1, wx.EXPAND|wx.ALL, 5)
			self.SetSizer(self.viewBox1)
			self.viewBox1.Layout()
			## Create the webpage content
			self.createWebPageContent(json.dumps(self.jsonData))
			## Load content into the pane
			self.loadWebPageContent()

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			log.debug('Failure in SchedulerChart: {}'.format(stacktrace))


	def createWebPageContent(self, jsonString):
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
		self.webPageContent = '{}{}{}'.format(part1, jsonString, part2)


	def loadWebPageContent(self):
		## Serve the content out to our frame via html2 webview...

		## Note, this *should* work, but doesn't on Windows:
		# self.browser.SetPage(self.webPageContent, pageWithFileAppendage)
		# self.browser.Reload()

		## This appears to be OS agnostic; dumping into a file and using LoadURL
		pageWithFileAppendage = r'file:///{}'.format(self.cachedPage)
		self.logger.debug('loading url:  {}'.format(pageWithFileAppendage))
		with open(self.cachedPage, 'w') as out:
			out.write(self.webPageContent)
		self.browser.LoadURL(pageWithFileAppendage)
		self.logger.debug('SchedulerChart loaded page')


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
		self.jobs = dict()
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


	def formatJobs(self):
		referenceSet = self.owner.historicalData
		if self.owner.dataType == 'Projected':
			referenceSet = self.owner.projectedData
		objectId = 1
		for name in self.owner.jobDetails:
			## Just filter it out here so we don't have to keep another list
			if name in referenceSet:
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

	def clearSelection(self):
		self.logger.debug("JobListCtrlPanel: clearSelection...")
		for currentItem in list(self.owner.currentItems):
			self.logger.debug("JobListCtrlPanel: clearing the current item: {}".format(currentItem))
			self.list.Select(currentItem, on=0)
			#self.list.SetItemBackgroundColour(currentItem, "WHITE")
			self.owner.currentItems.remove(currentItem)

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def OnItemSelected(self, event):
		## Using simple click/select to both add and remove
		currentItem = event.Index
		name = self.list.GetItemText(currentItem)
		self.logger.debug("OnItemSelected: %s, %s" % (currentItem, name))
		if currentItem not in self.owner.currentItems:
			self.owner.currentItems.append(currentItem)
			#self.owner.currentItems.append(name)
			#self.list.SetItemBackgroundColour(currentItem, "LIGHT GREY")
		# else:
		# 	self.logger.debug("Need to remove item: {}. set to {}".format(currentItem, self.defaultColor))
		# 	self.list.SetItemBackgroundColour(currentItem, wx.NullColour)
		# 	#self.list.SetItemBackgroundColour(currentItem, self.defaultColor)
		# 	self.owner.currentItems.remove(currentItem)
		# 	#self.list.Select(currentItem, on=0)
		self.logger.debug("Current items: {}".format(self.owner.currentItems))
		## Highlight all the currently selected items; default seems to be just
		## the last selected item
		# if len(self.owner.currentItems) > 1:
		# 	for currentItem in self.owner.currentItems:
		# 		self.list.SetItemBackgroundColour(currentItem, "LIGHT GREY")
		self.owner.resetMainPanel()
		event.Skip()


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

		## Need to set local in order for the QuartzCron to parse date strings,
		## which uses datetime.strptime and several date formats
		locale.setlocale(locale.LC_ALL, 'en_US.utf8')

		self.dataType = 'Historical'
		self.getTimeFormats()
		self.getServices()

		self.jobFilterBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Job Schedules')
		self.rb = wx.RadioBox(self.jobFilterBox, wx.ID_ANY, 'Data set', wx.DefaultPosition, wx.DefaultSize, ['Historical', 'Projected'], 1, wx.RA_SPECIFY_COLS)
		self.thisPanel.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
		self.rb.SetToolTip(wx.ToolTip('Historical shows past data. Projected shows actively scheduled jobs with projected runtimes based off past executions.'))
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

		self.dataSet = []
		self.historicalData = {}
		self.projectedData = {}
		self.activeData = []
		self.currentItems = []
		self.jobDetails = {}
		self.getJobSchedules()
		self.getHistoricalDataSet()
		self.getProjectedDataSet()
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
		self.schedulePanel = SchedulerChart(self.thisPanel, self.logger, [])
		self.scheduleSizer = wx.BoxSizer(wx.VERTICAL)
		self.scheduleSizer.AddSpacer(6)
		self.scheduleSizer.Add(self.schedulePanel, 1, wx.EXPAND|wx.ALL, 6)
		self.scheduleSizer.Layout()

		self.mainBox.Add(self.mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.scheduleSizer, 1, wx.EXPAND)
		self.logger.debug('Main.init')
		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)

		wx.EndBusyCursor()
		self.resetMainPanel()


	def resetMainPanel(self, preserve=True):
		self.thisPanel.Freeze()

		## Cleanup previous data sets
		self.scheduleSizer.Detach(self.schedulePanel)
		self.mainBox.Detach(self.scheduleSizer)
		self.schedulePanel.Destroy()
		self.schedulePanel = None
		self.scheduleSizer = None

		## Replace the pane on the right
		self.getDataSet()
		self.schedulePanel = SchedulerChart(self.thisPanel, self.logger, self.dataSet)
		# ## Recreate the sizer and refresh
		self.scheduleSizer = wx.BoxSizer(wx.VERTICAL)
		self.scheduleSizer.Add(self.schedulePanel, 1, wx.EXPAND|wx.ALL, 10)
		self.mainBox.Add(self.scheduleSizer, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 5)
		self.scheduleSizer.Layout()

		if not preserve:
			## Conditionally replace the job list on the left
			newListPanel = JobListCtrlPanel(self.jobFilterBox, self.logger, self)
			self.leftSizer.Detach(self.jobListPanelSizer)
			self.jobListPanel.Destroy()
			self.jobListPanel = newListPanel
			self.jobListPanelSizer = None
			self.jobListPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
			self.jobListPanelSizer.Add(self.jobListPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
			self.leftSizer.Insert(11, self.jobListPanelSizer, wx.EXPAND)
			self.leftSizer.Layout()
			self.jobFilterBox.Layout()

		self.mainBox.Layout()
		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()
		self.logger.debug('Stop resetMainPanel')


	def getTimeFormats(self):
		## Time formats for the D3 to parse OCP output: '2019-08-27 00:00:00'
		#startDay = '{} 00:00:00'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
		startDay = datetime.date.today()
		self.startDayD3 = '{} 00:00:00'.format(startDay.isoformat())
		## TODO: consider parameterizing the time range, for user interaction
		timeRange = datetime.timedelta(days=14)
		stopDay = startDay + timeRange
		self.stopDayD3 = '{} 00:00:00'.format(stopDay.isoformat())
		self.logger.debug('getProjectedDataSet: date range: {} to {}'.format(startDay.isoformat(), stopDay.isoformat()))

		## Time formats for QuartzCron input: '2019-08-27T00:00:00'
		self.startDayQuartz = self.startDayD3.replace(' ', 'T')
		self.stopDayQuartz = self.stopDayD3.replace(' ', 'T')


	def getServices(self):
		self.services = ['contentGathering', 'universalJob']
		self.serviceType = self.services[0]


	def getJobSchedules(self):
		self.logger.debug('getProjectedDataSet')
		self.jobDetails.clear()
		apiResults = self.api.getResource('job/config/{}'.format(self.serviceType))
		jobList = apiResults.get('Jobs', [])
		for jobName in jobList:
			jobResults = self.api.getResource('job/config/{}/{}'.format(self.serviceType, jobName))
			jobData = jobResults.get(jobName, {}).get('content', {})
			self.jobDetails[jobName] = {}
			self.jobDetails[jobName]['triggerType'] = jobData['triggerType']
			self.jobDetails[jobName]['triggerArgs'] = jobData['triggerArgs']
			self.jobDetails[jobName]['active'] = jobResults.get(jobName, {}).get('active', False)


	def getHistoricalDataSet(self):
		self.logger.debug('getHistoricalDataSet')
		self.historicalData.clear()
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
			if jobName not in self.historicalData:
				self.historicalData[jobName] = []
			## JSON rendering in web looks like [object Object], so remove these:
			result.pop('count_per_client')
			result.pop('count_per_status')
			self.historicalData[jobName].append(result)
		## Get an average runtime from successful runs in this timeframe; to be
		## used in the projected functions
		for jobName,resultList in self.historicalData.items():
			total = 0
			count = 0
			average = 0
			for entry in resultList:
				self.logger.debug('    entry: {}'.format(entry))
				if entry.get('job_completed', False):
					total += entry['time_elapsed']
					count += 1
			if count > 0:
				average = total / count
			## This shouldn't happen, but to catch extraneous scenarios...
			if jobName not in self.jobDetails:
				self.jobDetails[jobName] = {}
			self.jobDetails[jobName]['averageRuntime'] = average
			self.logger.debug('   getHistoricalDataSet: average for: {}: {}'.format(jobName, average))
		self.logger.debug('getHistoricalDataSet: total tracked jobs: {}'.format(len(self.jobDetails)))


	def cronSyntaxConversion(self, triggerArgs):
		## This doesn't account for all the special scheduling; there's more
		## parsing that would need to be done, which the default jobs do not
		## use. For example, defined start_date/end_date, or "xth y", range
		## with mins, etc. This is good enough to plot the default jobs...

		## Second defaults to 0
		value = triggerArgs.get('second')
		scheduleString = '0'
		if value is not None and value != '':
			scheduleString = value

		## Treat these the same with straight pass-through & default value=0
		for entry in ['minute', 'hour']:
			value = triggerArgs.get(entry)
			if value is not None and value != '':
				scheduleString = '{} {}'.format(scheduleString, value)
			else:
				scheduleString = '{} 0'.format(scheduleString)

		## Hold off assigning other values until after parsing day-of-week...
		## Since you can't have both day and day-of-week; only one can be set
		## with the other ?, or both must be *
		day = '?'
		month = '*'
		day_of_week = '?'

		## Day (day-of-month 1-31) defaults to *
		value = triggerArgs.get('day')
		if value is not None and value != '':
			day = value

		## Week
		value = triggerArgs.get('week')
		if value is not None and value != '':
			## Need to look at how APScheduler is converting this since Quartz
			## doesn't have a CronExpression entry for the ISO weeks (1-53)
			pass

		## Month defaults to *
		value = triggerArgs.get('month')
		if value is not None and value != '':
			## Conversion: 1-12 for APS, but 0-11 for Quartz
			month = monthConversionFromApsToQuartz(value)

		## Day-of-Week defaults to ?
		value = triggerArgs.get('day_of_week')
		if value is not None and value != '':
			## Conversion: str|int 0-6 mon-sun for APS, str|int 1-7 sun-sat for Quartz
			day_of_week = dayOfWeekConversionFromApsToQuartz(triggerArgs['day_of_week'])

		## Check/reset the day and day_of_week values
		if day_of_week == '?' and day == '?':
			day = '*'
		elif day_of_week == '*' and day == '*':
			day_of_week = '?'
		## Now bring the scheduleString up to speed
		scheduleString = '{} {} {} {}'.format(scheduleString, day, month, day_of_week)

		## Year is optional
		value = triggerArgs.get('year')
		if value is not None and value != '':
			scheduleString = '{} {}'.format(scheduleString, triggerArgs['year'])
		# else:
		# 	scheduleString = '{} *'.format(scheduleString)

		## end scheduleString
		return scheduleString


	def parseProjectedCronJob(self, jobName, triggerArgs):
		try:
			if jobName not in self.projectedData:
				self.projectedData[jobName] = []
			self.logger.debug('parseProjectedCronJob: Job {}  input schedule : {}'.format(jobName, triggerArgs))
			## Approx conversion between ApScheduler and QuartzCron syntax
			scheduleString = self.cronSyntaxConversion(triggerArgs)
			self.logger.debug('parseProjectedCronJob: output schedule: {}'.format(scheduleString))
			self.logger.debug('                     : [{}] to [{}]'.format(self.startDayD3, self.stopDayD3))
			runtimeSeconds = self.jobDetails[jobName]['averageRuntime']
			tmpSchedule = QuartzCron(schedule_string=scheduleString, start_date=self.startDayD3, end_date=self.stopDayD3)
			while True:
				try:
					nextScheduleString = tmpSchedule.next_trigger(isoformat=True)
					startSchedule = datetime.datetime.strptime(nextScheduleString, '%Y-%m-%dT%H:%M:%S')
					timeRange = datetime.timedelta(seconds=runtimeSeconds)
					stopSchedule = startSchedule + timeRange

					## Clean up ISO Format before handing off to javascript
					startDayD3 = startSchedule.isoformat()
					stopDayD3 = stopSchedule.isoformat()
					## Remove any decimal seconds
					startDayD3 = startDayD3.split('.')[0]
					stopDayD3 = stopDayD3.split('.')[0]
					## Replace 'T' separator between day and time with a space
					startDayD3 = startDayD3.replace('T', ' ')
					stopDayD3 = stopDayD3.replace('T', ' ')
					self.logger.debug('getProjectedDataSet: date range: {} to {}'.format(startDayD3, stopDayD3))

					## Add a new entry to show in the dataSet
					jobData = {}
					jobData['job'] = jobName
					jobData['time_started'] = startDayD3
					jobData['time_finished'] = stopDayD3
					jobData['time_elapsed'] = runtimeSeconds
					self.projectedData[jobName].append(jobData)

				except StopIteration:
					## Expecting QuartzCron to return this when end is hit
					break
				except:
					raise
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure parsing job {}: {}'.format(jobName, stacktrace))
		## end parseProjectedCronJob


	def getProjectedDataSet(self):
		self.logger.debug('getProjectedDataSet')
		self.projectedData.clear()
		for jobName,data in self.jobDetails.items():
			## Don't use disabled jobs to show projected run times
			self.logger.debug(' getProjectedDataSet: data {}'.format(data))
			self.logger.debug(' getProjectedDataSet: data.active: {}'.format(data.get('active', False)))
			if data.get('active', False):
				triggerType = data.get('triggerType')
				triggerArgs = data.get('triggerArgs')
				## Intervals: Use last run time, if it doesn't exist, we won't
				## know when to anchor the first start time... service may not
				## be running, clients may not be running or overburdened...
				## showing anything visual, could be misleading.
				if triggerType.lower() == 'interval':
					self.logger.debug(' TODO: enable interval jobs.  Skipping interval job: {} with args {}'.format(jobName, triggerArgs))
				elif triggerType.lower() == 'date':
					self.logger.debug(' TODO: enable date jobs.  Skipping interval job: {} with args {}'.format(jobName, triggerArgs))
				elif triggerType.lower() == 'cron':
					self.logger.debug(' loading cron job: {} with args {}'.format(jobName, triggerArgs))
					self.parseProjectedCronJob(jobName, triggerArgs)


	def getDataSet(self):
		self.dataSet.clear()
		#self.dataSet = [{"time_started":"2019-08-18 18:00:00","time_finished":"2019-08-18 20:00:00"},{"time_started":"2019-08-21 06:00:00","time_finished":"2019-08-21 10:00:00"}]

		## Default to the 'Historical' set
		referenceSet = self.historicalData
		if self.dataType == 'Projected':
			## Set the 'Projected' set
			referenceSet = self.projectedData

		## If we are showing all jobs, add everything from the reference set
		if self.showAllJobs == True:
			for job,valueList in referenceSet.items():
				for entry in valueList:
					self.dataSet.append(entry)
		else:
			## Otherwise, just add those in the active list
			activeList = self.currentItems
			for jobId in activeList:
				## The +1 is because activeList starts with 0, but the .jobs
				## list starts with 1 in jobListPanel.formatJobs
				jobName = self.jobListPanel.jobs[jobId+1]
				for entry in referenceSet[jobName]:
					self.dataSet.append(entry)


	def EvtRadioBox(self, event):
		self.dataType = event.GetString()
		self.resetMainPanel(False)

	def EvtChooseServiceType(self, event):
		self.serviceType = event.GetString()
		self.getHistoricalDataSet()
		self.getProjectedDataSet()
		self.resetMainPanel(False)

	def OnAllJobsButton(self, event=None):
		self.jobListPanel.clearSelection()
		self.showAllJobs = True
		self.resetMainPanel()

	def OnClearButton(self, event=None):
		self.jobListPanel.clearSelection()
		self.showAllJobs = False
		self.resetMainPanel()
