"""Sets up the main window frame, the ribbon, and module references."""
import sys, traceback, os
import re, json
import logging, logging.handlers
from contextlib import suppress
import wx
import wx.lib.agw.ribbon as RB

from images import ChartDot, Binocular, BoxWhiteClosed, TextList
from images import Blueprint, BlueprintEdit, BlueprintDelete
from images import UserBlue, User, Branch, Code, CodeColored, Components
from images import ControlPanel, Cloud, DateTime, EyeGlasses, Info, Objects
from images import FormBlue, FormGreen, History, HistoryPad, Package, Pencil
from images import Replace, System, Text, View, Wrench, DataFind, DataScroll

import env

## Modules for the ribbon buttons
import platformBoundaryRealm
import platformBoundaryNetworks
import platformConfigOsParams
import platformConfigConfigGroups
import platformConfigDefaultConfig
import platformAccountsApi
import platformAccountsCreds
import dataContentObjects
import dataContentManualInsert
import dataContentViewsSimple
import dataContentViewsInput
import dataModelsInsertMetaData
import dataModelsUpdateMetaData
import dataModelsDeleteMetaData
import dataModelsViews
import dataModelsHistory
import dataModelsMetaDataHistory
import jobViewListing
import jobViewStatistics
#import jobViewSchedules
import jobModifyToggle
import jobModifyConfig
import ocpRestAPI

## Constants for ribbon buttons
ID_START = wx.ID_HIGHEST
ID_BROWSE_OBJECTS = 		ID_START + 1
ID_BROWSE_QUERIES = 		ID_START + 2
ID_BROWSE_VIEWS_SIMPLE = 	ID_START + 3
ID_BROWSE_VIEWS_INPUT = 	ID_START + 4
ID_ACCOUNTS_USERS = 		ID_START + 5
ID_ACCOUNTS_CREDENTIALS = 	ID_START + 6
ID_CONFIG_REALM = 			ID_START + 7
ID_CONFIG_NETWORK_SCOPES = 	ID_START + 8
ID_CONFIG_OSPARAMETERS = 	ID_START + 9
ID_CONFIG_CONFIGGROUPS = 	ID_START + 10
ID_CONFIG_DEFAULTCONFIG = 	ID_START + 11
ID_CONFIG_INSERT_OBJECT = 	ID_START + 12
ID_JOBS_LIST = 				ID_START + 13
ID_JOBS_STATS = 			ID_START + 14
ID_JOBS_SCHEDULE = 			ID_START + 15
ID_JOBS_TOGGLE = 			ID_START + 16
ID_JOBS_EDIT = 				ID_START + 17
ID_MODELS_STATS = 			ID_START + 18
ID_MODELS_METADATA_INSERT = ID_START + 19
ID_MODELS_METADATA_UPDATE = ID_START + 20
ID_MODELS_METADATA_DELETE = ID_START + 21
ID_MODELS_VIEWS = 			ID_START + 22
ID_MODELS_HISTORY = 		ID_START + 23
ID_MODELS_META_HISTORY =    ID_START + 24
ID_MAIN_TOOLBAR = 			ID_START + 34


## Bitmaps for ribbon buttons
def CreateBitmap(xpm):
	bmp = eval(xpm).Bitmap
	return bmp


def loadSettings(fileName):
	"""Read defined configurations from JSON file.
	Arguments:
	  fileName (str) : file to read in
	Return:
	  settings (json) : dictionary to hold the the configuration parameter
	"""
	settings = None
	with open(fileName, 'r') as json_data:
		settings = json.load(json_data)
	## end loadSettings
	return settings


def setupLogger(env, loggerName, logSettingsFileName):
	"""Setup requested log handler."""
	if not os.path.exists(env.logPath):
		os.mkdir(env.logPath)
	## Open defined configurations
	logSettings = loadSettings(os.path.join(env.configPath, logSettingsFileName))
	## Create requested handler
	logEntry = logSettings.get(loggerName)
	logFile = os.path.join(env.logPath, logEntry.get('fileName'))
	logger = logging.getLogger(loggerName)
	logger.handlers = []
	logger.setLevel(logEntry.get('logLevel'))
	mainHandler = logging.handlers.RotatingFileHandler(logFile, maxBytes=int(logEntry.get('maxSizeInBytes')), backupCount=int(logEntry.get('maxRollovers')))
	fmt = logging.Formatter(logEntry.get('lineFormat'), datefmt = logEntry.get('dateFormat'))
	mainHandler.setFormatter(fmt)
	logger.addHandler(mainHandler)
	## end setupLogger
	return logger


class MainPanel(wx.Panel):
	"""
	Just a simple derived panel where we override Freeze and Thaw to work
	around an issue on wxGTK.
	"""
	def Freeze(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(MainPanel, self).Freeze()

	def Thaw(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(MainPanel, self).Thaw()


class RawPanel(wx.Panel):
	def __init__(self, parent, log):
		wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, style=wx.EXPAND|wx.CLIP_CHILDREN, name="rawPanel")
		self.Layout()
	def Freeze(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(RawPanel, self).Freeze()
	def Thaw(self):
		if 'wxMSW' in wx.PlatformInfo:
			return super(RawPanel, self).Thaw()


class MainFrame(wx.Frame):
	"""Main Windows Frame holding the ribbon and a generic/overriden panel."""
	def __init__(self, parent, id=wx.ID_ANY, title="My Ribbon Pane", pos=wx.DefaultPosition,
				 size=(1280, 960), style=wx.DEFAULT_FRAME_STYLE, log=None, api=None):
		wx.Frame.__init__(self, parent, id, title, pos, size, style)
		self.panel = panel = MainPanel(self)
		self.name = 'MainFrame'
		self.logger = log
		self.api = api
		## Ribbon tool bar
		self._ribbon = RB.RibbonBar(panel, wx.ID_ANY, agwStyle=RB.RIBBON_BAR_DEFAULT_STYLE)
		ribbonPanels = self.setupRibbonBar()
		## Raw panel; this is where the ribbon buttons will load data
		self.rawPanel = RawPanel(panel, wx.ID_ANY)
		## Box for the ribbon at the top and a data panel on the bottom
		self.mainBox = wx.BoxSizer(wx.VERTICAL)
		self.mainBox.Add(self._ribbon, 0, wx.EXPAND)
		self.mainBox.Add(self.rawPanel, 1, wx.EXPAND)
		self.Layout()
		## Apply the layout
		panel.SetSizer(self.mainBox)
		## Bind events
		self.BindEvents(ribbonPanels)
		self.CenterOnScreen()
		self.Show()
		panel.SendSizeEvent()


	def setupRibbonBar(self):
		self._bitmap_creation_dc = wx.MemoryDC()
		self._colour_data = wx.ColourData()
		label_font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT)

		######################################################################
		## Ribbon Tab: Config
		######################################################################
		config = RB.RibbonPage(self._ribbon, wx.ID_ANY, "Platform")
		## Panel: Config.Boundary
		config_boundary_panel = RB.RibbonPanel(config, wx.ID_ANY, "Boundary", wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize,
										agwStyle=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)
		config_boundary_selection = RB.RibbonButtonBar(config_boundary_panel, wx.ID_ANY)
		config_boundary_selection.AddSimpleButton(ID_CONFIG_REALM, "Realm", CreateBitmap("Cloud"), "Realm settings")
		config_boundary_selection.AddSimpleButton(ID_CONFIG_NETWORK_SCOPES, "Networks", CreateBitmap("Wrench"), "Network scopes")
		## Panel: Config.PlatformConfiguration
		config_base_panel = RB.RibbonPanel(config, wx.ID_ANY, "Configuration", wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize,
										agwStyle=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)
		config_base_selection = RB.RibbonButtonBar(config_base_panel, wx.ID_ANY)
		config_base_selection.AddSimpleButton(ID_CONFIG_OSPARAMETERS, "OS Parameters", CreateBitmap("System"), "Base OS Parameters")
		config_base_selection.AddSimpleButton(ID_CONFIG_CONFIGGROUPS, "Config Groups", CreateBitmap("Components"), "Config Group settings")
		config_base_selection.AddSimpleButton(ID_CONFIG_DEFAULTCONFIG, "Default Config", CreateBitmap("BoxWhiteClosed"), "Default Config settings")


		## Panel: Config.Accounts
		config_accounts_panel = RB.RibbonPanel(config, wx.ID_ANY, "Accounts", wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize,
										agwStyle=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)
		config_accounts_selection = RB.RibbonButtonBar(config_accounts_panel, wx.ID_ANY)
		config_accounts_selection.AddSimpleButton(ID_ACCOUNTS_CREDENTIALS, "Credentials", CreateBitmap("UserBlue"), "Protocol credentials")
		config_accounts_selection.AddSimpleButton(ID_ACCOUNTS_USERS, "API Users", CreateBitmap("User"), "API user accounts")

		######################################################################
		## Ribbon Tab: Data
		######################################################################
		content = RB.RibbonPage(self._ribbon, wx.ID_ANY, "Data")
		## Panel: Data.Content
		content_objects_panel = RB.RibbonPanel(content, wx.ID_ANY, "Content")
		content_objects_selection = RB.RibbonButtonBar(content_objects_panel)
		content_objects_selection.AddSimpleButton(ID_BROWSE_OBJECTS, "Objects", CreateBitmap("DataFind"), "Objects in the database")
		content_objects_selection.AddSimpleButton(ID_BROWSE_VIEWS_SIMPLE, "Simple Queries", CreateBitmap("EyeGlasses"), "Query results in visual graph form")
		content_objects_selection.AddSimpleButton(ID_BROWSE_VIEWS_INPUT, "Input Driven", CreateBitmap("ChartDot"), "Input Driven Query results in visual graph form")
		content_objects_selection.AddSimpleButton(ID_CONFIG_INSERT_OBJECT, "Insert Object ", CreateBitmap("FormBlue"), "Manually insert an object")

		## Panel: Data.Models
		content_models_panel = RB.RibbonPanel(content, wx.ID_ANY, "Models")
		content_models_selection = RB.RibbonButtonBar(content_models_panel)
		content_models_selection.AddSimpleButton(ID_MODELS_METADATA_INSERT, "Insert MetaData", CreateBitmap("Blueprint"), "Insert model blueprint")
		content_models_selection.AddSimpleButton(ID_MODELS_METADATA_UPDATE, "Update MetaData", CreateBitmap("BlueprintEdit"), "Update model blueprint")
		content_models_selection.AddSimpleButton(ID_MODELS_METADATA_DELETE, "Delete MetaData", CreateBitmap("BlueprintDelete"), "Delete model blueprint")
		content_models_selection.AddSimpleButton(ID_MODELS_VIEWS, "Views", CreateBitmap("Branch"), "Model presented in visual tree form")
		content_models_selection.AddSimpleButton(ID_MODELS_HISTORY, "Model History", CreateBitmap("History"), "Snapshots of models over time")
		content_models_selection.AddSimpleButton(ID_MODELS_META_HISTORY, "MetaData History", CreateBitmap("DataScroll"), "Snapshots of MetaData over time")

		######################################################################
		## Ribbon Tab: Jobs
		######################################################################
		jobs = RB.RibbonPage(self._ribbon, wx.ID_ANY, "Jobs")
		## Panel: Jobs.View
		jobs_view_panel = RB.RibbonPanel(jobs, wx.ID_ANY, "View", wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize,
										agwStyle=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)
		jobs_view_selection = RB.RibbonButtonBar(jobs_view_panel, wx.ID_ANY)
		jobs_view_selection.AddSimpleButton(ID_JOBS_LIST, "Listing", CreateBitmap("TextList"), "Job listing")
		jobs_view_selection.AddSimpleButton(ID_JOBS_STATS, "Statistics", CreateBitmap("Info"), "Job statistics")
		jobs_view_selection.AddSimpleButton(ID_JOBS_SCHEDULE, "Schedules", CreateBitmap("DateTime"), "View job schedules")
		## Panel: Jobs.Modify
		jobs_modify_panel = RB.RibbonPanel(jobs, wx.ID_ANY, "Modify", wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize,
										agwStyle=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)
		jobs_modify_selection = RB.RibbonButtonBar(jobs_modify_panel, wx.ID_ANY)
		jobs_modify_selection.AddSimpleButton(ID_JOBS_TOGGLE, "Toggle", CreateBitmap("Replace"), "Enable/Disable jobs")
		jobs_modify_selection.AddSimpleButton(ID_JOBS_EDIT, "Config", CreateBitmap("ControlPanel"), "Edit job configurations")

		self._bitmap_creation_dc.SetFont(label_font)
		self._ribbon.Realize()
		return [jobs_view_panel, jobs_modify_panel, config_accounts_panel, config_boundary_panel, config_base_panel, content_models_panel, content_objects_panel]


	def BindEvents(self, bars):

		[jobs_view_panel, jobs_modify_panel, config_accounts_panel, config_boundary_panel, config_base_panel, content_models_panel, content_objects_panel] = bars

		content_objects_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionBrowseObjects, id=ID_BROWSE_OBJECTS)
		content_objects_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionBrowseViewsSimple, id=ID_BROWSE_VIEWS_SIMPLE)
		content_objects_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionBrowseViewsInput, id=ID_BROWSE_VIEWS_INPUT)
		content_objects_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionInsertObject, id=ID_CONFIG_INSERT_OBJECT)

		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelJobStats, id=ID_MODELS_STATS)
		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelMetadataInsert, id=ID_MODELS_METADATA_INSERT)
		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelMetadataUpdate, id=ID_MODELS_METADATA_UPDATE)
		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelMetadataDelete, id=ID_MODELS_METADATA_DELETE)
		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelViews, id=ID_MODELS_VIEWS)
		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelHistory, id=ID_MODELS_HISTORY)
		content_models_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionModelMetaDataHistory, id=ID_MODELS_META_HISTORY)

		config_boundary_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionConfigRealm, id=ID_CONFIG_REALM)
		config_boundary_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionConfigNetworks, id=ID_CONFIG_NETWORK_SCOPES)

		config_base_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionOsParameters, id=ID_CONFIG_OSPARAMETERS)
		config_base_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionConfigGroups, id=ID_CONFIG_CONFIGGROUPS)
		config_base_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionDefaultConfig, id=ID_CONFIG_DEFAULTCONFIG)

		config_accounts_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionApiUsers, id=ID_ACCOUNTS_USERS)
		config_accounts_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionProtocolCreds, id=ID_ACCOUNTS_CREDENTIALS)

		jobs_view_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionJobList, id=ID_JOBS_LIST)
		jobs_view_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionJobStats, id=ID_JOBS_STATS)
		jobs_view_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionJobSchedules, id=ID_JOBS_SCHEDULE)
		jobs_modify_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionJobToggle, id=ID_JOBS_TOGGLE)
		jobs_modify_panel.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSelectionJobEdit, id=ID_JOBS_EDIT)


	def SetBarStyle(self, agwStyle):
		self._ribbon.Freeze()
		self._ribbon.SetAGWWindowStyleFlag(agwStyle)
		pTopSize = self.panel.GetSizer()
		pToolbar = wx.FindWindowById(ID_MAIN_TOOLBAR)
		if agwStyle & RB.RIBBON_BAR_FLOW_VERTICAL:
			self._ribbon.SetTabCtrlMargins(10, 10)
			pTopSize.SetOrientation(wx.HORIZONTAL)
			if pToolbar:
				pToolbar.SetRows(3, 5)
		else:
			self._ribbon.SetTabCtrlMargins(50, 20)
			pTopSize.SetOrientation(wx.VERTICAL)
			if pToolbar:
				pToolbar.SetRows(2, 3)
		self._ribbon.Realize()
		self._ribbon.Thaw()
		self.panel.Layout()


	def GetGalleryColour(self, gallery, item, name=None):
		data = gallery.GetItemClientData(item)
		if name != None:
			name = data.GetName()
		return data.GetColour(), name


	def OnHoveredColourChange(self, event):
		# Set the background of the gallery to the hovered colour, or back to the
		# default if there is no longer a hovered item.
		gallery = event.GetGallery()
		provider = gallery.GetArtProvider()
		if event.GetGalleryItem() != None:
			if provider == self._ribbon.GetArtProvider():
				provider = provider.Clone()
				gallery.SetArtProvider(provider)
			provider.SetColour(RB.RIBBON_ART_GALLERY_HOVER_BACKGROUND_COLOUR,
							   self.GetGalleryColour(event.GetGallery(), event.GetGalleryItem(), None)[0])
		else:
			if provider != self._ribbon.GetArtProvider():
				gallery.SetArtProvider(self._ribbon.GetArtProvider())
				del provider


	def OnPrimaryColourSelect(self, event):
		colour, name = self.GetGalleryColour(event.GetGallery(), event.GetGalleryItem(), "")
		self.logger.debug("Colour %s selected as primary."%name)
		dummy, secondary, tertiary = self._ribbon.GetArtProvider().GetColourScheme(None, 1, 1)
		self._ribbon.GetArtProvider().SetColourScheme(colour, secondary, tertiary)
		self.ResetGalleryArtProviders()
		self._ribbon.Refresh()


	def OnSecondaryColourSelect(self, event):
		colour, name = self.GetGalleryColour(event.GetGallery(), event.GetGalleryItem(), "")
		self.logger.debug("Colour %s selected as secondary."%name)
		primary, dummy, tertiary = self._ribbon.GetArtProvider().GetColourScheme(1, None, 1)
		self._ribbon.GetArtProvider().SetColourScheme(primary, colour, tertiary)
		self.ResetGalleryArtProviders()
		self._ribbon.Refresh()


	def ResetGalleryArtProviders(self):
		if self._primary_gallery.GetArtProvider() != self._ribbon.GetArtProvider():
			self._primary_gallery.SetArtProvider(self._ribbon.GetArtProvider())
		if self._secondary_gallery.GetArtProvider() != self._ribbon.GetArtProvider():
			self._secondary_gallery.SetArtProvider(self._ribbon.GetArtProvider())


	def resetRawPanel(self):
		self.panel.Freeze()
		## Detach and destry the rawPanel inside mainBox, instead of recreating
		## mainBox; this hit an exception in migrating to newer versions of wx.
		self.mainBox.Detach(self.rawPanel)
		self.rawPanel.Destroy()
		self.rawPanel = RawPanel(self.panel, wx.ID_ANY)
		## Box for the ribbon at the top and a data panel on the bottom
		self.mainBox.Add(self.rawPanel, 1, wx.EXPAND)
		self.Layout()
		## Apply the layout
		self.panel.SetSizer(self.mainBox)
		self.panel.Thaw()
		self.panel.SendSizeEvent()

	def OnSelectionBrowseObjects(self, event):
		self.logger.debug("Browse Objects button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataContentObjects.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionBrowseQueries(self, event):
		self.logger.debug("Browse Queries button clicked.")
		self.resetRawPanel()

	def OnSelectionBrowseViewsSimple(self, event):
		self.logger.debug("Browse Simple Views button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataContentViewsSimple.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionBrowseViewsInput(self, event):
		self.logger.debug("Browse Input driven Views button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataContentViewsInput.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionModelJobStats(self, event):
		self.logger.debug("Model Job Stats button clicked.")
		self.resetRawPanel()

	def OnSelectionModelMetadataInsert(self, event):
		self.logger.debug("Insert model metadata button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataModelsInsertMetaData.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionModelMetadataUpdate(self, event):
		self.logger.debug("Update model metadata button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataModelsUpdateMetaData.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionModelMetadataDelete(self, event):
		self.logger.debug("Delete model metadata button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataModelsDeleteMetaData.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionModelViews(self, event):
		self.logger.debug("Model Views button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataModelsViews.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionModelHistory(self, event):
		self.logger.debug("Model History button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataModelsHistory.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionModelMetaDataHistory(self, event):
		self.logger.debug("Model MetaData History button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataModelsMetaDataHistory.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionOsParameters(self, event):
		self.logger.debug("OsParameters button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformConfigOsParams.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionConfigGroups(self, event):
		self.logger.debug("ConfigGroups button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformConfigConfigGroups.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionDefaultConfig(self, event):
		self.logger.debug("ConfigGroups button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformConfigDefaultConfig.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionConfigRealm(self, event):
		self.logger.debug("ConfigRealm button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformBoundaryRealm.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionConfigNetworks(self, event):
		self.logger.debug("ConfigNetworks button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformBoundaryNetworks.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionApiUsers(self, event):
		self.logger.debug("Users button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformAccountsApi.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionProtocolCreds(self, event):
		self.logger.debug("Credentials button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		platformAccountsCreds.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionInsertObject(self, event):
		self.logger.debug("Insert Object1 button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		dataContentManualInsert.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionJobList(self, event):
		self.logger.debug("Job Lists button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		jobViewListing.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionJobStats(self, event):
		self.logger.debug("Job Stats button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		jobViewStatistics.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionJobSchedules(self, event):
		self.logger.debug("Job Schedules button clicked.")
		self.resetRawPanel()
		#wx.BeginBusyCursor()
		#jobViewSchedules.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionJobToggle(self, event):
		self.logger.debug("Job Toggle button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		jobModifyToggle.Main(self.rawPanel, self.logger, self.api)

	def OnSelectionJobEdit(self, event):
		self.logger.debug("Job Edit button clicked.")
		self.resetRawPanel()
		wx.BeginBusyCursor()
		jobModifyConfig.Main(self.rawPanel, self.logger, self.api)


	def OnTogglePanels(self, event):
		self._ribbon.ShowPanels(self._togglePanels.GetValue())


	def OnDefaultProvider(self, event):
		self._ribbon.DismissExpandedPanel()
		self.SetArtProvider(RB.RibbonDefaultArtProvider())


	def OnAUIProvider(self, event):
		self._ribbon.DismissExpandedPanel()
		self.SetArtProvider(RB.RibbonAUIArtProvider())


	def OnMSWProvider(self, event):
		self._ribbon.DismissExpandedPanel()
		self.SetArtProvider(RB.RibbonMSWArtProvider())


	def SetArtProvider(self, prov):
		self._ribbon.Freeze()
		self._ribbon.SetArtProvider(prov)
		self._default_primary, self._default_secondary, self._default_tertiary = \
							   prov.GetColourScheme(self._default_primary, self._default_secondary, self._default_tertiary)
		self._ribbon.Thaw()
		self.panel.GetSizer().Layout()
		self._ribbon.Realize()


def main():
	"""Main entry point."""
	try:
		setupLogger(env, 'ocpRestAPI', 'logSettings.json')
		logger = setupLogger(env, 'adminConsole', 'logSettings.json')

		## Establish a connection
		logger.info('Connecting to OCP')
		settings = loadSettings(os.path.join(env.configPath, 'ocpSettings.json'))
		logger.debug('settings: {}'.format(settings))
		restApi = ocpRestAPI.RestAPI(settings['restEndpoint'], settings['restProtocol'], settings['restPort'], settings['restPath'], settings['apiUser'], settings['apiKey'])
		#app = wx.App(redirect=True, filename="F:\\Work\\openContentPlatform\\adminConsole\\log\\logfile.log")
		#app = wx.App(redirect=True)
		app = wx.App()
		window = MainFrame(None, -1, "ITDM Admin console", log=logger, api=restApi)

		## Start the event loop
		app.MainLoop()

	except:
		exception = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		print('Exception in main: {}'.format(exception))
		with suppress(Exception):
			logger.error('Exception in main: {}'.format(exception))

	## end main
	return


if __name__ == '__main__':
	sys.exit(main())
