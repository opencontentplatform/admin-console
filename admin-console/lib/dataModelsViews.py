"""Pane for Admin Console ribbon destination: Data->Models->Views.

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
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel='stylesheet' type='text/css' href="./static/ocp_model.css" />
</head>
<body>
	<script src="./static/d3.js"></script>
	<script src="./static/ocp_tree.js"></script>
	<div id="modelframe" name="modelframe">
		<script>
			var jsonData = """
	part2 = """;
			ocp_tree.exec(jsonData);
		</script>
	</div>
</body>
</html>"""
	fullPage = '{}{}{}'.format(part1, viewData, part2)

	## end mapViewData
	return fullPage


class AppTreeView(wx.Panel):
	def __init__(self, parent, log, api):
		try:
			log.debug('AppTreeView: 0')
			wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
			self.logger = log
			self.logger.debug('AppTreeView: 1')
			self.api = api
			self.webPageContent = []
			self.localDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webview')
			self.cachedPage = os.path.join(self.localDir, 'thisApp.html')
			self.browser = wx.html2.WebView.New(self)
			self.logger.debug('AppTreeView: 2')
			viewBox1 = wx.BoxSizer()
			viewBox1.Add(self.browser, 1, wx.EXPAND|wx.ALL, 5)
			self.SetSizer(viewBox1)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			log.debug('Failure in AppTreeView: {}'.format(stacktrace))


	def getPage(self, appId, appResult):
		query = '{"objects": [{"label": "APPLICATION","class_name": "BusinessApplication","attributes": [],"minimum": "1","maximum": "","filter": [{"condition": {"attribute": "object_id","operator": "equal","value": "' + appId + '"}}],"linchpin": true}, {"label": "ENVIRONMENT","class_name": "EnvironmentGroup","attributes": [],"minimum": "1","maximum": ""}, {"label": "SOFTWARE","class_name": "SoftwareGroup","attributes": [],"minimum": "1","maximum": ""}, {"label": "LOCATION","class_name": "LocationGroup","attributes": [],"minimum": "0","maximum": ""}, {"label": "MODELOBJECT","class_name": "ModelObject","attributes": [],"minimum": "0","maximum": "","filter": []}, {"label": "DISCOVERABLE","class_name": "SoftwareElement","attributes": [],"minimum": "0","maximum": "","filter": []}],    "links": [{"label": "APP_TO_ENV","class_name": "Contain","first_id": "APPLICATION","second_id": "ENVIRONMENT"}, {"label": "ENV_TO_SW","class_name": "Contain","first_id": "ENVIRONMENT","second_id": "SOFTWARE"}, {"label": "SW_TO_LOC","class_name": "Contain","first_id": "SOFTWARE","second_id": "LOCATION"}, {"label": "LOC_TO_OBJECT","class_name": "Contain","first_id": "LOCATION","second_id": "MODELOBJECT"}, {"label": "OBJECT_TO_DISCOVERABLE","class_name": "Usage","first_id": "MODELOBJECT","second_id": "DISCOVERABLE"}]}'
		apiResults = self.api.nestedQuery(query)
		self.webPageContent = ''
		if len(apiResults) > 0:
			self.webPageContent = mapViewData(apiResults[0])
		# else:
		# 	## Just drop the App CI in the pane
		# 	self.webPageContent = mapViewData(appResult)
		with open(self.cachedPage, 'w') as out:
			out.write(self.webPageContent)
		self.logger.debug('Web page to load:\n{}'.format(self.webPageContent))


	def loadPage(self, appId, appResult):
		self.getPage(appId, appResult)
		## Now serve the content out to our frame via html2 webview
		self.logger.debug('Local file to load: {}'.format(self.cachedPage))
		pageWithFileAppendage = r'file:///{}'.format(self.cachedPage)
		self.logger.debug('loading url:  {}'.format(pageWithFileAppendage))
		self.browser.LoadURL(pageWithFileAppendage)
		self.logger.debug('AppTreeView: 4')


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class SimpleQueryListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, dataPanelRef):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(250, -1), style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		self.api = api
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		sizer.Add(self.list, 1, wx.EXPAND)
		## Pull object count from API
		self.appIdToData = dict()
		self.apps = dict()
		self.getApps()
		self.logger.debug('Apps found: {}'.format(self.apps))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.apps
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
		# for wxMSW
		self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
		# for wxGTK
		self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)

	def getApps(self):
		apiResults = self.api.getResource('data/BusinessApplication')
		objectId = 0
		for appResult in apiResults.get('objects', {}):
			appId = appResult.get('identifier')
			appName = appResult.get('data', {}).get('name')
			appResult['children'] = []
			self.appIdToData[objectId] = (appId, appName, appResult)
			self.apps[objectId] = appName
			objectId += 1

	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.apps
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Application Name"
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
			self.list.SetItemData(index, key)
		self.list.SetColumnWidth(0, 250)

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def resetDataPanel(self, appId, appResult):
		self.logger.debug("SimpleQueryListCtrlPanel: resetDataPanel...")
		wx.BeginBusyCursor()
		self.owner.dataPanel.loadPage(appId, appResult)
		wx.EndBusyCursor()
		self.logger.debug("SimpleQueryListCtrlPanel: resetDataPanel... DONE")

	def OnItemSelected(self, event):
		self.currentItem = event.Index
		self.logger.debug("OnItemSelected: %s, %s, %s" % (self.currentItem, self.list.GetItemText(self.currentItem), self.getColumnText(self.currentItem, 1)))
		#self.resetDataPanel(self.getColumnText(self.currentItem, 0))
		## Need to probably track by app name instead of the ID or current item
		## because this is unnecessary overhead:
		#######################################################
		for thisId,thisData in self.appIdToData.items():
			(appId, appName, appResult) = thisData
			if appName == self.list.GetItemText(self.currentItem):
				self.logger.debug("OnItemSelected: appId: {}".format(appId))
				self.resetDataPanel(appId, appResult)
		#######################################################
		# (appId, appResult) = self.appIdToData[self.currentItem]
		# self.logger.debug("OnItemSelected: appId: {}".format(appId))
		# self.resetDataPanel(appId, appResult)
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
		self.rawPanel = RawPanel(thisPanel, wx.ID_ANY)
		self.dataPanel = None
		## Box for simple queries
		self.ModelViewsBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, "Model Views")
		self.ModelViewsList = SimpleQueryListCtrlPanel(self.ModelViewsBox, self.logger, self.api, self)
		self.filter = wx.SearchCtrl(self.ModelViewsBox, style=wx.TE_PROCESS_ENTER)
		self.filter.ShowCancelButton(True)
		self.filter.Bind(wx.EVT_TEXT, self.OnSearch)
		self.filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: self.filter.SetValue(''))
		self.filter.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
		self.icons8 = HyperlinkCtrl(self.ModelViewsBox, wx.ID_ANY, label="Icons provided by Icons8", url="https://icons8.com")

		self.dataPanel = AppTreeView(self.rawPanel, self.logger, self.api)
		viewBox1 = wx.BoxSizer()
		viewBox1.Add(self.dataPanel, 1, wx.EXPAND|wx.ALL, 5)
		self.rawPanel.SetSizer(viewBox1)
		self.rawPanel.Show()
		self.rawPanel.SendSizeEvent()

		self.resetMainPanel()
		wx.EndBusyCursor()


	def resetMainPanel(self):
		## Create boxes to arrange the panels
		mainBox = wx.BoxSizer(wx.HORIZONTAL)
		mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		self.thisPanel.Freeze()

		topBorder, otherBorder = self.ModelViewsBox.GetBordersForSizer()
		staticSizer1 = wx.BoxSizer(wx.VERTICAL)
		staticSizer1.AddSpacer(topBorder)
		caption2 = wx.StaticText(self.ModelViewsBox, label="Filter Models:")
		staticSizer1.Add(caption2, 0, wx.TOP|wx.LEFT, 5)
		staticSizer1.Add(self.filter, 0, wx.EXPAND|wx.ALL, 5)
		if 'wxMac' in wx.PlatformInfo:
			staticSizer1.Add((5,5))  # Make sure there is room for the focus ring
		staticSizer1.AddSpacer(5)
		staticSizer1.Add(self.ModelViewsList, 1, wx.EXPAND|wx.ALL, 5)
		staticSizer1.Add(self.icons8, 0, wx.EXPAND|wx.ALL, 5)
		self.ModelViewsBox.SetSizer(staticSizer1)
		mainQueryBox.Add(self.ModelViewsBox, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)

		mainBox.Add(mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		mainBox.Add(self.rawPanel, 1, wx.EXPAND|wx.TOP, 7)

		self.thisPanel.SetSizer(mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()


	def OnSearch(self, event=None):
		value = self.filter.GetValue()
		if not value:
			self.ModelViewsList.PopulateList()
			return
		wx.BeginBusyCursor()
		newData = dict()
		newId = 1
		for prevId,queryName in self.ModelViewsList.apps.items():
			if re.search(str(value), str(queryName), re.I):
				newData[newId] = queryName
				newId += 1
		self.ModelViewsList.PopulateList(newData)
		wx.EndBusyCursor()
