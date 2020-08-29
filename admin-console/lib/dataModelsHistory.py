"""Pane for Admin Console ribbon destination: Data->Models->Model History.

This pane presents details of models in the archive schema.
"""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress

import wx
import wx.lib.mixins.listctrl as listmix


class DataPanel(wx.Panel):
	def __init__(self, parent, log, modelSnapshots):
		try:
			wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.EXPAND|wx.CLIP_CHILDREN)
			log.debug('DataPanel: 0')
			self.logger = log
			self.modelSnapshots = modelSnapshots
			self.modelInstance = None
			self.modelChanges = None
			self.modelPane = None
			self.changePane = None

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			self.logger.debug('Failure in DataPanel: {}'.format(stacktrace))

	def loadData(self, selection):
		thisSnapshot = self.modelSnapshots.get(selection)
		self.logger.debug('DataPanel: loadData: {}'.format(thisSnapshot))
		self.modelInstance = thisSnapshot.get('data')
		self.modelChanges = thisSnapshot.get('change_list')

		self.Freeze()
		self.createModelPane()
		self.createChangePane()

		## Expand the list to the full size
		paneBox = wx.BoxSizer()
		paneBox.AddSpacer(10)
		vBox1 = wx.BoxSizer(wx.VERTICAL)
		modelHeader = wx.StaticText(self, wx.ID_ANY, 'Model Instance:')
		vBox1.Add(modelHeader, 0, wx.TOP, 3)
		vBox1.Add(self.modelPane, 1, wx.EXPAND)
		paneBox.Add(vBox1, 1, wx.EXPAND|wx.BOTTOM, 6)
		paneBox.AddSpacer(10)
		vBox2 = wx.BoxSizer(wx.VERTICAL)
		modelHeader = wx.StaticText(self, wx.ID_ANY, 'Changes:')
		vBox2.Add(modelHeader, 0, wx.TOP, 3)
		vBox2.Add(self.changePane, 1, wx.EXPAND|wx.RIGHT, 10)
		paneBox.Add(vBox2, 1, wx.EXPAND|wx.BOTTOM, 6)

		self.SetSizer(paneBox)
		self.Show()
		self.SendSizeEvent()
		self.Thaw()


	def createModelPane(self):
		if self.modelPane is not None:
			self.modelPane.Destroy()
		self.logger.debug('DataPanel: createModelPane')
		if self.modelInstance is not None:
			self.logger.debug('DataPanel: createModelPane: drawing Instance')
			textString = json.dumps(self.modelInstance, indent=8)
			self.modelPane = wx.TextCtrl(self, wx.ID_ANY, textString, style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY|wx.EXPAND)
		else:
			self.modelPane = RawPanel(self, wx.ID_ANY)

	def createChangePane(self):
		if self.changePane is not None:
			self.changePane.Destroy()
		self.logger.debug('DataPanel: createModelPane')
		if self.modelChanges is not None:
			self.logger.debug('DataPanel: createChangePane: drawing Changes')
			textString = json.dumps(self.modelChanges, indent=8)
			self.changePane = wx.TextCtrl(self, wx.ID_ANY, textString, style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY|wx.EXPAND)
		else:
			self.changePane = RawPanel(self, wx.ID_ANY)


class ObjectListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class SnapshotListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
	def __init__(self, parent, log, dataPanelRef, modelSnapshots):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, style=wx.EXPAND|wx.CLIP_CHILDREN)
		self.logger = log
		self.owner = dataPanelRef
		self.modelSnapshots = modelSnapshots
		self.snapshots = dict()
		self.getFormattedSnapshots()
		sizer = wx.BoxSizer()
		self.list = ObjectListCtrl(self, wx.ID_ANY, style=wx.EXPAND|wx.LC_REPORT|wx.BORDER_NONE|wx.LC_HRULES|wx.LC_SINGLE_SEL|wx.CLIP_CHILDREN)
		sizer.Add(self.list, 1, wx.EXPAND)
		self.logger.debug('Snapshots found: {}'.format(self.snapshots))
		self.PopulateList()
		# Now that the list exists we can init the other base class,
		# see wx/lib/mixins/listctrl.py
		self.itemDataMap = self.snapshots
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

	def getFormattedSnapshots(self):
		objectId = 0
		for timeStamp in self.modelSnapshots:
			self.snapshots[objectId] = timeStamp
			objectId += 1


	def PopulateList(self, data=None):
		self.currentItem = 0
		self.list.ClearAll()
		if data is None:
			data = self.snapshots
		info = wx.ListItem()
		info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info.Align = wx.LIST_FORMAT_LEFT
		info.Text = 'Timestamp'
		self.list.InsertColumn(0, info)
		for key,name in data.items():
			index = self.list.InsertItem(self.list.GetItemCount(), name)
			self.list.SetItemData(index, key)
		#self.list.SetColumnWidth(0, 250)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		return self.list

	def getColumnText(self, index, col):
		item = self.list.GetItem(index, col)
		return item.GetText()

	def resetDataPanel(self, selection):
		self.logger.debug("SnapshotListCtrlPanel: resetDataPanel...")
		wx.BeginBusyCursor()
		self.owner.dataPanel.loadData(selection)
		wx.EndBusyCursor()
		self.logger.debug("SnapshotListCtrlPanel: resetDataPanel... DONE")

	def OnItemSelected(self, event):
		self.currentItem = event.Index
		self.logger.debug("OnItemSelected: %s, %s, %s" % (self.currentItem, self.list.GetItemText(self.currentItem), self.getColumnText(self.currentItem, 1)))
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

		self.ModelHistoryBox = wx.StaticBox(self.thisPanel, wx.ID_ANY, 'Model History')
		self.modelType = None
		self.modelTypes = []
		self.model = {}
		self.modelListTracker = {}
		self.modelList = []
		self.modelSnapshots = {}
		self.getModels()
		self.modelTypeText = wx.StaticText(self.ModelHistoryBox, wx.ID_ANY, 'Model Type:')
		self.modelTypeChoice = wx.Choice(self.ModelHistoryBox, wx.ID_ANY, (120, 50), choices=self.modelTypes)
		self.modelTypeChoice.SetSelection(0)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChooseModelType, self.modelTypeChoice)
		self.modelText = wx.StaticText(self.ModelHistoryBox, wx.ID_ANY, 'Select Model:')
		self.modelChoice = wx.Choice(self.ModelHistoryBox, wx.ID_ANY, (120, 50), choices=self.modelList)
		self.thisPanel.Bind(wx.EVT_CHOICE, self.EvtChooseModel, self.modelChoice)


		## Placeholder for the SnapshotList
		self.rawSnapshotPanel = RawPanel(self.ModelHistoryBox, wx.ID_ANY)
		self.snapshotList = None
		## Placeholder for the DataPanel
		self.rawDataPanel = RawPanel(thisPanel, wx.ID_ANY)
		self.dataPanel = DataPanel(self.rawDataPanel, self.logger, self.modelSnapshots)
		viewBox1 = wx.BoxSizer()
		viewBox1.Add(self.dataPanel, 1, wx.EXPAND|wx.ALL, 5)
		self.rawDataPanel.SetSizer(viewBox1)
		self.rawDataPanel.Show()
		self.rawDataPanel.SendSizeEvent()

		## Draw the panels
		self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
		self.mainQueryBox = wx.BoxSizer(wx.VERTICAL)
		self.thisPanel.Freeze()
		topBorder, otherBorder = self.ModelHistoryBox.GetBordersForSizer()
		self.staticSizer = wx.BoxSizer(wx.VERTICAL)
		self.staticSizer.AddSpacer(topBorder)
		self.staticSizer.Add(self.modelTypeText, 0, wx.TOP|wx.LEFT, 5)
		self.staticSizer.Add(self.modelTypeChoice, 0, wx.EXPAND|wx.ALL, 5)
		self.staticSizer.AddSpacer(10)
		self.staticSizer.Add(self.modelText, 0, wx.TOP|wx.LEFT, 5)
		self.staticSizer.Add(self.modelChoice, 0, wx.EXPAND|wx.ALL, 5)
		self.staticSizer.AddSpacer(10)
		self.staticSizer.Add(self.rawSnapshotPanel, 1, wx.EXPAND|wx.ALL, 5)
		self.ModelHistoryBox.SetSizer(self.staticSizer)
		self.mainQueryBox.Add(self.ModelHistoryBox, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.mainQueryBox, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 5)
		self.mainBox.Add(self.rawDataPanel, 1, wx.EXPAND|wx.TOP, 7)
		self.thisPanel.SetSizer(self.mainBox)
		self.thisPanel.Thaw()
		self.thisPanel.SendSizeEvent()
		wx.EndBusyCursor()


	def getModels(self):
		apiResults = self.api.getResource('archive/model')
		objectId = 0
		for model in apiResults.get('Models', []):
			modelId = model.get('object_id')
			modelType = model.get('object_type')
			modelName = model.get('caption')
			## Add to model types drop down list
			if modelType not in self.modelTypes:
				self.modelTypes.append(modelType)
				self.modelListTracker[modelType] = {}
			self.modelListTracker[modelType][objectId] = model
			self.modelList.append(modelName)
			objectId += 1
		if len(self.modelTypes) > 0:
			self.modelType = self.modelTypes[0]


	def getModelSnapshots(self, identifier):
		apiResults = self.api.getResource('archive/modelSnapshot/{}'.format(identifier))
		self.modelSnapshots.clear()
		for snapshotId, snapshotData in apiResults.items():
			simpleDateString = snapshotData.get('time_stamp')
			self.modelSnapshots[simpleDateString] = snapshotData


	def EvtChooseModelType(self, event):
		self.modelType = event.GetString()

	def EvtChooseModel(self, event):
		lookupDict = self.modelListTracker[self.modelType]
		self.model = lookupDict[event.GetInt()]
		modelId = self.model.get('object_id')
		self.logger.debug('EvtChooseModel: selected model: {}'.format(self.model))
		wx.BeginBusyCursor()
		self.getModelSnapshots(modelId)
		if self.snapshotList is not None:
			self.snapshotList.Destroy()
		self.snapshotList = SnapshotListCtrlPanel(self.rawSnapshotPanel, self.logger, self, self.modelSnapshots)

		## Expand the list to the full size
		viewBox1 = wx.BoxSizer()
		viewBox1.Add(self.snapshotList, 1, wx.EXPAND)
		self.rawSnapshotPanel.SetSizer(viewBox1)
		self.rawSnapshotPanel.Show()
		self.rawSnapshotPanel.SendSizeEvent()
		wx.EndBusyCursor()
