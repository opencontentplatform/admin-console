"""Pane for Admin Console ribbon destination: Data->Content->Input Driven.

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
	<script src="./static/ocp_many.js"></script>
	<div id="modelframe" name="modelframe">
		<script>
			var jsonData = """
	part2 = """;
			ocp_many.exec(jsonData);
		</script>
	</div>
</body>
</html>"""
	fullPage = '{}{}{}'.format(part1, viewData, part2)

	## end mapViewData
	return fullPage


class InputDrivenQueryListView(wx.Panel):
	def __init__(self, parent, log, api):
		try:
			log.debug('InputDrivenQueryListView: 0')
			wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
			self.logger = log
			self.logger.debug('InputDrivenQueryListView: 1')
			self.api = api
			self.webPageContent = []
			self.rawQuery = None
			self.updatedQuery = None
			self.localDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webview')
			self.cachedPage = os.path.join(self.localDir, 'thisView.html')
			self.localD3 = os.path.join(self.localDir, 'static', 'thisView.html')
			self.localWrapper = os.path.join(self.localDir, 'static', 'ocp_many.js')
			self.localCSS = os.path.join(self.localDir, 'static', 'ocp_model.css')
			self.browser = wx.html2.WebView.New(self)
			self.logger.debug('InputDrivenQueryListView: 2')
			viewBox1 = wx.BoxSizer()
			viewBox1.Add(self.browser, 1, wx.EXPAND|wx.ALL, 5)
			self.SetSizer(viewBox1)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			log.debug('Failure in InputDrivenQueryListView: {}'.format(stacktrace))


	def setInputDrivenAttribute(self, expression, value):
		self.logger.debug("setInputDrivenAttribute: called with expression {} and value {}".format(expression, value))
		self.logger.debug("========> BEFORE: expression {}".format(expression))
		subExpression = expression.get('expression')
		subCondition = expression.get('condition')
		if subExpression is not None:
			subExpression = expression['expression']
			self.logger.debug("setInputDrivenAttribute: subExpression: {}".format(subExpression))
			## setup and recurse
			for entry in subExpression:
				classAttribute = self.setInputDrivenAttribute(entry, value)
		elif subCondition is not None:
			subCondition = expression['condition']
			self.logger.debug("setInputDrivenAttribute: subCondition: {}".format(subCondition))
			classAttribute = subCondition.get('attribute')
			if classAttribute == self.classAttr and subCondition.get('value') == 'INPUT':
				self.logger.debug("setInputDrivenAttribute: found attribute {} with value {}".format(classAttribute, subCondition['value']))
				subCondition['value'] = value
				self.logger.debug("setInputDrivenAttribute: updated attribute to 1: {}".format(value))
				self.logger.debug("setInputDrivenAttribute: updated attribute to 2: {}".format(subCondition['value']))
				self.logger.debug("========> AFTER : expression {}".format(expression))
				return

		## end setInputDrivenAttribute
		self.logger.debug("========> AFTER : expression {}".format(expression))
		return


	def recurseExpressionsForInputDrivenAttribute(self, expression):
		classAttribute = None
		subExpression = expression.get('expression')
		subCondition = expression.get('condition')
		if subExpression is not None:
			self.logger.debug("recurseExpressionsForInputDrivenAttribute: subExpression: {}".format(subExpression))
			for entry in subExpression:
				classAttribute = self.recurseExpressionsForInputDrivenAttribute(entry)
		elif subCondition is not None:
			classAttribute = subCondition.get('attribute')
			self.logger.debug("recurseExpressionsForInputDrivenAttribute: subCondition: {}".format(subCondition))
			value = subCondition.get('value')
			if value == 'INPUT':
				return classAttribute

		## end recurseExpressionsForInputDrivenAttribute
		return classAttribute


	def setQuery(self, queryName):
		self.className = None
		self.classAttr = None
		try:
			apiResult = self.api.getResource('query/config/inputdriven/{}'.format(queryName))
			self.rawQuery = apiResult.get('json_query', {})
			self.logger.debug("InputDrivenQueryListView: setQuery:  rawQuery:\n{}".format(self.rawQuery))
			if len(self.rawQuery) > 0:
				for objectDefinition in self.rawQuery.get('objects', []):
					self.className = objectDefinition.get('class_name')
					if 'filter' in objectDefinition:
						filterList = objectDefinition.get('filter', [])
						self.logger.debug("InputDrivenQueryListView: setQuery:  looking at class {} with filter {}".format(self.className, filterList))
						for expression in filterList:
							self.classAttr = self.recurseExpressionsForInputDrivenAttribute(expression)
							if self.classAttr is not None:
								self.logger.debug("InputDrivenQueryListView: setQuery: found filter attribute: {}".format(self.classAttr))
								break
						if self.classAttr is not None:
							break

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in getQuery: {}'.format(stacktrace))

		## end setQuery
		return (self.className, self.classAttr)


	def updateQuery(self, value):
		try:
			## Convert through json to get a copy of the rawQuery
			self.updatedQuery = json.loads(json.dumps(self.rawQuery))
			for objectDefinition in self.updatedQuery['objects']:
				thisClass = objectDefinition.get('class_name')
				if thisClass == self.className and 'filter' in objectDefinition:
					filterList = objectDefinition['filter']
					self.logger.debug("InputDrivenQueryListView: updateQuery:  looking at class {} with filter {}".format(self.className, filterList))
					for expression in filterList:
						self.logger.debug("===> BEFORE setInputDrivenAttribute: expression {}".format(expression))
						self.setInputDrivenAttribute(expression, value)
						self.logger.debug("===> AFTER  setInputDrivenAttribute: expression {}".format(expression))
			apiResults = self.api.dynamicQuery(self.updatedQuery)
			## Convert so Python values are understood ('None' -> 'null', True -> true, etc)
			self.webPageContent = mapViewData(json.dumps(apiResults))
			with open(self.cachedPage, 'w') as out:
				out.write(self.webPageContent)
			self.logger.debug('Updated web page:\n{}'.format(self.webPageContent))

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in getQuery: {}'.format(stacktrace))

		## end updateQuery
		return


	def loadPage(self):
		self.logger.debug('Local file to load: {}'.format(self.cachedPage))
		pageWithFileAppendage = r'file:///{}'.format(self.cachedPage)
		self.logger.debug('loading url:  {}'.format(pageWithFileAppendage))
		self.browser.LoadURL(pageWithFileAppendage)
		self.logger.debug('InputDrivenQueryListView: 4')


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	#def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
	def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class InputListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, className, attrName, dataPanelRef):
		#wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(240, -1), style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		self.api = api
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY, size=(-1,-1))
		sizer.Add(self.list, 1, wx.EXPAND)
		## Pull object count from API
		self.inputData = dict()
		self.getInput(className, attrName)
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.inputData
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

	def getInput(self, className, attrName):
		self.logger.debug("InputListCtrlPanel: getInput: class name: {}".format(className))
		apiResults = self.api.getResource('data/{}'.format(className))
		## First go through to sort and unique the entries
		self.logger.debug("InputListCtrlPanel: results: {}".format(apiResults))
		attrValues = []
		for entry in apiResults.get('objects', []):
			val = entry.get('data', {}).get(attrName)
			if val is not None:
				attrValues.append(val)
		self.logger.debug("InputListCtrlPanel: attrValues: {}".format(attrValues))
		orderedUniqueAttrValues = sorted(list(set(attrValues)))
		## Now go through and create a dictionary in the expected format
		objectId = 1
		for name in orderedUniqueAttrValues:
			self.inputData[objectId] = name
			objectId += 1

	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.inputData
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Attribute Value"
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
			self.list.SetItemData(index, key)
		#self.list.SetColumnWidth(0, 200)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)


	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def resetDataPanel(self, selection):
		self.logger.debug("InputListCtrlPanel: resetDataPanel to selection: {}".format(selection))
		wx.BeginBusyCursor()
		self.owner.dataPanel.updateQuery(selection)
		self.owner.dataPanel.loadPage()
		wx.EndBusyCursor()
		self.logger.debug("InputListCtrlPanel: resetDataPanel... DONE")

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


class InputDrivenQueryListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, api, dataPanelRef):
		#wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, size=(240, -1), style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		self.api = api
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY)
		sizer.Add(self.list, 1, wx.EXPAND)
		## Pull object count from API
		self.queries = dict()
		self.getQueries()
		self.logger.debug('Queries found: {}'.format(self.queries))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.queries
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

	def getQueries(self):
		apiResults = self.api.getResource('query/config/inputdriven')
		objectId = 1
		for name in apiResults.get('Queries', {}):
			self.queries[objectId] = name
			objectId += 1

	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.queries
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = "Query Name"
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
			self.list.SetItemData(index, key)
		#self.list.SetColumnWidth(0, 200)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def resetDataPanel(self, selection):
		self.logger.debug("InputDrivenQueryListCtrlPanel: resetDataPanel...")
		wx.BeginBusyCursor()
		#self.owner.dataPanel.loadPage(selection)
		(className, classAttr) = self.owner.dataPanel.setQuery(selection)
		self.owner.className.SetValue(className)
		self.owner.attrName.SetValue(classAttr)
		if self.owner.inputQueryList is not None:
			self.owner.inputQueryList.Destroy()
		self.owner.inputQueryList = InputListCtrlPanel(self.owner.inputListRawPanel, self.logger, self.api, className, classAttr, self.owner)
		## Expand the list to the full size
		viewBox1 = wx.BoxSizer()
		viewBox1.Add(self.owner.inputQueryList, 1, wx.EXPAND)
		self.owner.inputListRawPanel.SetSizer(viewBox1)
		self.owner.inputListRawPanel.Show()
		self.owner.inputListRawPanel.SendSizeEvent()

		wx.EndBusyCursor()

		self.logger.debug("InputDrivenQueryListCtrlPanel: resetDataPanel... DONE")

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
		## Placeholder for when we known how to create an InputListCtrlPanel
		self.inputQueryList = None

		self.inputDrivenQueryBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, "Input Driven Queries")
		self.inputDrivenQueryList = InputDrivenQueryListCtrlPanel(self.inputDrivenQueryBox, self.logger, self.api, self)
		self.inputListRawPanel = RawPanel(self.inputDrivenQueryBox, wx.ID_ANY)

		self.filter = wx.SearchCtrl(self.inputDrivenQueryBox, style=wx.TE_PROCESS_ENTER)
		self.filter.ShowCancelButton(True)
		self.filter.Bind(wx.EVT_TEXT, self.OnSearch)
		self.filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: self.filter.SetValue(''))
		self.filter.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)

		self.filterInputList = wx.SearchCtrl(self.inputDrivenQueryBox, style=wx.TE_PROCESS_ENTER)
		self.filterInputList.ShowCancelButton(True)
		self.filterInputList.Bind(wx.EVT_TEXT, self.OnInputListSearch)
		self.filterInputList.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: self.filterInputList.SetValue(''))
		self.filterInputList.Bind(wx.EVT_TEXT_ENTER, self.OnInputListSearch)
		self.icons8 = HyperlinkCtrl(self.inputDrivenQueryBox, wx.ID_ANY, label="Icons provided by Icons8", url="https://icons8.com")

		self.className = wx.TextCtrl(self.inputDrivenQueryBox, wx.ID_ANY, '', size=(110,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)
		self.attrName = wx.TextCtrl(self.inputDrivenQueryBox, wx.ID_ANY, '', size=(110,-1), style=wx.TE_READONLY|wx.EXPAND|wx.BORDER_NONE)

		self.dataPanel = InputDrivenQueryListView(self.rawPanel, self.logger, self.api)
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

		topBorder, otherBorder = self.inputDrivenQueryBox.GetBordersForSizer()
		staticSizer1 = wx.BoxSizer(wx.VERTICAL)
		staticSizer1.AddSpacer(topBorder)
		caption1 = wx.StaticText(self.inputDrivenQueryBox, label="Filter Queries:")
		staticSizer1.Add(caption1, 0, wx.TOP|wx.LEFT, 5)
		staticSizer1.Add(self.filter, 0, wx.EXPAND|wx.ALL, 5)
		if 'wxMac' in wx.PlatformInfo:
			staticSizer1.Add((5,5))  # Make sure there is room for the focus ring
		staticSizer1.AddSpacer(5)
		staticSizer1.Add(self.inputDrivenQueryList, 0, wx.EXPAND|wx.ALL, 5)

		staticSizer1.AddSpacer(15)
		inputCaptionText = wx.StaticText(self.inputDrivenQueryBox, label="Input Driven Context:")
		staticSizer1.Add(inputCaptionText, 0, wx.TOP|wx.LEFT, 5)
		inputCaptionSizer1 = wx.BoxSizer(wx.HORIZONTAL)
		inputCaptionText1 = wx.StaticText(self.inputDrivenQueryBox, label="Class: ")
		inputCaptionSizer1.Add(inputCaptionText1, 0, wx.LEFT, 5)
		inputCaptionSizer1.Add(self.className, 0, wx.EXPAND)
		staticSizer1.Add(inputCaptionSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		inputCaptionSizer2 = wx.BoxSizer(wx.HORIZONTAL)
		inputCaptionText2 = wx.StaticText(self.inputDrivenQueryBox, label="Attribute: ")
		inputCaptionSizer2.Add(inputCaptionText2, 0, wx.LEFT, 5)
		inputCaptionSizer2.Add(self.attrName, 0, wx.EXPAND)
		staticSizer1.Add(inputCaptionSizer2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

		staticSizer1.AddSpacer(10)
		caption2 = wx.StaticText(self.inputDrivenQueryBox, label="Filter Input:")
		staticSizer1.Add(caption2, 0, wx.TOP|wx.LEFT, 5)
		staticSizer1.Add(self.filterInputList, 0, wx.EXPAND|wx.ALL, 5)
		if 'wxMac' in wx.PlatformInfo:
			staticSizer1.Add((5,5))  # Make sure there is room for the focus ring
		staticSizer1.AddSpacer(5)
		staticSizer1.Add(self.inputListRawPanel, 1, wx.EXPAND|wx.ALL, 5)
		staticSizer1.Add(self.icons8, 0, wx.EXPAND|wx.ALL, 5)

		self.inputDrivenQueryBox.SetSizer(staticSizer1)
		mainQueryBox.Add(self.inputDrivenQueryBox, 2, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)

		mainBox.Add(mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		mainBox.Add(self.rawPanel, 1, wx.EXPAND|wx.TOP, 7)

		self.thisPanel.SetSizer(mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()


	def OnSearch(self, event=None):
		value = self.filter.GetValue()
		if not value:
			self.inputDrivenQueryList.PopulateList()
			return
		wx.BeginBusyCursor()
		newData = dict()
		newId = 1
		for prevId,queryName in self.inputDrivenQueryList.queries.items():
			if re.search(str(value), str(queryName), re.I):
				newData[newId] = queryName
				newId += 1
		self.inputDrivenQueryList.PopulateList(newData)
		wx.EndBusyCursor()


	def OnInputListSearch(self, event=None):
		value = self.filterInputList.GetValue()
		if self.inputQueryList is None:
			return
		if not value:
			self.inputQueryList.PopulateList()
			return
		wx.BeginBusyCursor()
		newData = dict()
		newId = 1
		for prevId,context in self.inputQueryList.inputData.items():
			if re.search(str(value), str(context), re.I):
				newData[newId] = context
				newId += 1
		self.inputQueryList.PopulateList(newData)
		wx.EndBusyCursor()
