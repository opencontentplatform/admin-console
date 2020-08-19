"""Module for the communicating with the Open Content Platform (OCP)."""

import sys
import traceback
import requests
import json
import logging
logger = logging.getLogger("ocpRestAPI")


class RestAPI():
	"""Protocol type wrapper for the OCP REST API."""

	def __init__(self, restEndpoint, protocol, port, context, apiUser, apiKey):
		"""Constructor."""
		self.token = None
		self.baseURL = '{}://{}:{}/{}'.format(protocol, restEndpoint, port, context)
		self.apiUser = apiUser
		self.apiKey = apiKey
		self.header = {}
		self.header['Content-Type'] = 'application/json'
		self.header['ApiUser'] = self.apiUser
		self.header['ApiKey'] = self.apiKey
		self.establishConnection()


	def establishConnection(self):
		"""Attempt a REST connection and validate output."""
		testUrl = '{}/tool/count/IpAddress'.format(self.baseURL)
		## Convert payload dictionary into json string format (not json)
		payloadAsString = json.dumps({})
		## Set the headers
		self.header['ResultsFormat'] = 'Nested-Simple'
		## Issue a POST call to URL for token generation
		apiResponse = requests.get(testUrl, data=payloadAsString, headers=self.header, verify=False)
		responseAsJson =  json.loads(apiResponse.text)
		if int(apiResponse.status_code) != 200:
			logger.debug('Response code: {}'.format(apiResponse.status_code))
			logger.debug('Response: {}'.format(apiResponse.text))
			raise EnvironmentError('Failure in ocpRestAPI.establishConnection. Code: {}. Response: {}'.format(apiResponse.status_code, str(apiResponse.text)))
		if responseAsJson.get("IpAddress") is None:
			raise EnvironmentError('Failure in ocpRestAPI.establishConnection. Unexpected Return: {}'.format(str(apiResponse.text)))
		logger.info('OCP connection established')

		## end establishConnection
		return


	def count(self):
		"""Request a dataset from OCP."""
		responseAsJson = None
		try:
			urlForCiQuery = '{}/tool/count'.format(self.baseURL)
			logger.info("Calling url in ocpRestAPI.count: {}".format(urlForCiQuery))
			payloadAsString = json.dumps({})
			customHeaders = self.header.copy()
			customHeaders['ResultsFormat'] = 'Flat'
			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson = json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.count: {}".format(stacktrace))

		## end count
		return responseAsJson


	def objectEntries(self, objectType):
		"""Request a dataset from OCP."""
		responseAsJson = None
		try:
			urlForCiQuery = '{}/data/{}'.format(self.baseURL, objectType)
			logger.info("Calling url in ocpRestAPI.objectEntries: {}".format(urlForCiQuery))
			payloadAsString = json.dumps({})
			customHeaders = self.header.copy()
			customHeaders['removePrivateAttributes'] = 'False'
			customHeaders['removeEmptyAttributes'] = 'False'
			customHeaders['resultsFormat'] = 'Flat'
			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			logger.debug('Response code: {}'.format(apiResponse.status_code))
			logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson = json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.objectEntries: {}".format(stacktrace))

		## end objectEntries
		return responseAsJson


	def getResource(self, resource, customPayload=None):
		responseAsJson = None
		try:
			urlForCiQuery = '{}/{}'.format(self.baseURL, resource)
			logger.info("Calling url in ocpRestAPI.getResource: {}".format(urlForCiQuery))
			payloadAsString = json.dumps({})
			if customPayload is not None and isinstance(customPayload, dict):
				payloadAsString = json.dumps(customPayload)
			customHeaders = self.header.copy()
			customHeaders['resultsFormat'] = 'Flat'
			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson = json.loads(apiResponse.text)
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.getResource: {}".format(stacktrace))

		## end getResource
		return responseAsJson

	def postResourceWithoutPayload(self, resource):
		responseCode = 500
		responseAsJson = None
		try:
			urlForCiQuery = '{}/{}'.format(self.baseURL, resource)
			logger.info("Calling url in ocpRestAPI.postResourceWithoutPayload: {}".format(urlForCiQuery))
			payloadAsString = json.dumps({})
			customHeaders = self.header.copy()
			customHeaders['resultsFormat'] = 'Flat'
			## Issue a POST call to URL
			apiResponse = requests.post(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseCode = apiResponse.status_code
			responseAsJson = json.loads(apiResponse.text)
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.postResourceWithoutPayload: {}".format(stacktrace))

		## end postResourceWithoutPayload
		return (responseCode, responseAsJson)

	def postResource(self, resource, customPayload):
		responseCode = 500
		responseAsJson = None
		try:
			urlForCiQuery = '{}/{}'.format(self.baseURL, resource)
			logger.info("Calling url in ocpRestAPI.postResource: {}".format(urlForCiQuery))
			## The custom payload is sometimes appearing empty unless acted on
			## here (e.g. print or inspection); somehow getting lost when passed
			## through multiple functions... potential python memory bug?
			logger.info("  --> postResource has custom payload: {}".format(customPayload))
			payloadAsString = json.dumps(customPayload)
			logger.info("  --> postResource payloadAsString: {}".format(payloadAsString))
			customHeaders = self.header.copy()
			customHeaders['resultsFormat'] = 'Flat'
			## Issue a POST call to URL
			apiResponse = requests.post(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseCode = apiResponse.status_code
			responseAsJson = json.loads(apiResponse.text)
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.postResource: {}".format(stacktrace))

		## end postResource
		return (responseCode, responseAsJson)

	def putResource(self, resource, customPayload):
		responseCode = 500
		responseAsJson = None
		try:
			urlForCiQuery = '{}/{}'.format(self.baseURL, resource)
			logger.info("Calling url in ocpRestAPI.putResource: {}".format(urlForCiQuery))
			## The custom payload is sometimes appearing empty unless acted on
			## here (e.g. print or inspection); somehow getting lost when passed
			## through multiple functions... potential python memory bug?
			logger.info("  --> putResource has custom payload: {}".format(customPayload))
			payloadAsString = json.dumps(customPayload)
			logger.info("  --> putResource payloadAsString: {}".format(payloadAsString))
			customHeaders = self.header.copy()
			customHeaders['resultsFormat'] = 'Flat'
			## Issue a PUT call to URL
			apiResponse = requests.put(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseCode = apiResponse.status_code
			responseAsJson = json.loads(apiResponse.text)
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.putResource: {}".format(stacktrace))

		## end putResource
		return (responseCode, responseAsJson)

	def deleteResource(self, resource):
		responseCode = 500
		responseAsJson = None
		try:
			urlForCiQuery = '{}/{}'.format(self.baseURL, resource)
			logger.info("Calling url in ocpRestAPI.deleteResource: {}".format(urlForCiQuery))
			payloadAsString = json.dumps({})
			## Issue a POST call to URL
			apiResponse = requests.delete(urlForCiQuery, data=payloadAsString, headers=self.header, verify=False)
			if int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseCode = apiResponse.status_code
			responseAsJson = json.loads(apiResponse.text)
		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.postResource: {}".format(stacktrace))

		## end postResource
		return (responseCode, responseAsJson)


	def dynamicQuery(self, content, retryFlag=False):
		"""Request a dataset from OCP."""
		try:
			urlForCiQuery = '{}/query/this'.format(self.baseURL)
			## Payload is passed in as a string type
			payloadAsString = json.dumps({'content': content})
			customHeaders = self.header.copy()
			customHeaders['removePrivateAttributes'] = 'True'
			customHeaders['removeEmptyAttributes'] = 'False'
			customHeaders['resultsFormat'] = 'Flat'
			logger.debug('payloadAsString: {}'.format(payloadAsString))

			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) == 401 and retryFlag is False:
				## Token expired; need to re-authenticate
				self.establishConnection()
				self.dynamicQuery(payloadAsString, retryFlag=True)
			elif int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson = json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.dynamicQuery: {}".format(stacktrace))

		## end dynamicQuery
		return responseAsJson

	def nestedQuery(self, content, retryFlag=False):
		"""Request a dataset from OCP."""
		try:
			urlForCiQuery = '{}/query/this'.format(self.baseURL)
			## Payload is passed in as a string type
			payloadAsString = json.dumps({'content': content})
			customHeaders = self.header.copy()
			customHeaders['removePrivateAttributes'] = 'True'
			customHeaders['removeEmptyAttributes'] = 'True'
			customHeaders['resultsFormat'] = 'Nested-Simple'
			logger.debug('payloadAsString: {}'.format(payloadAsString))

			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) == 401 and retryFlag is False:
				## Token expired; need to re-authenticate
				self.establishConnection()
				self.dynamicQuery(payloadAsString, retryFlag=True)
			elif int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson =  json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.dynamicQuery: {}".format(stacktrace))

		## end dynamicQuery
		return responseAsJson

	def taskQuery(self, content, retryFlag=False):
		"""Request a dataset from OCP."""
		responseCode = 500
		responseAsJson = None
		try:
			urlForCiQuery = '{}/query/this'.format(self.baseURL)
			customHeaders = self.header.copy()
			customHeaders['ResultsFormat'] = 'Flat'
			## Payload is passed in as a string type
			payloadAsString = json.dumps({'content': content})
			logger.debug('payloadAsString: {}'.format(payloadAsString))

			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			responseCode = apiResponse.status_code
			if int(responseCode) == 401 and retryFlag is False:
				## Token expired; need to re-authenticate
				self.establishConnection()
				self.dynamicQuery(payloadAsString, retryFlag=True)
			elif int(responseCode) != 200:
				logger.debug('Response code: {}'.format(responseCode))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson =  json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.dynamicQuery: {}".format(stacktrace))

		## end taskQuery
		return (responseCode, responseAsJson)


	def flatQuery(self, content, retryFlag=False):
		"""Request a dataset from OCP."""
		try:
			urlForCiQuery = '{}/query/this'.format(self.baseURL)
			customHeaders = self.header.copy()
			customHeaders['ResultsFormat'] = 'Flat'
			## Payload is passed in as a string type
			payloadAsString = json.dumps({'content': content})
			logger.debug('payloadAsString: {}'.format(payloadAsString))

			## Issue a GET call to URL
			apiResponse = requests.get(urlForCiQuery, data=payloadAsString, headers=customHeaders, verify=False)
			if int(apiResponse.status_code) == 401 and retryFlag is False:
				## Token expired; need to re-authenticate
				self.establishConnection()
				self.dynamicQuery(payloadAsString, retryFlag=True)
			elif int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson =  json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.dynamicQuery: {}".format(stacktrace))

		## end flatQuery
		return responseAsJson


	##  Update a CI
	def updateCI(self, identifier, payloadAsString, retryFlag=False):
		try:
			urlForCiQuery = '{}/dataModel/ci/{}'.format(self.baseURL, identifier)
			## Issue a PUT call to URL
			apiResponse = requests.put(urlForCiQuery, data=payloadAsString, headers=self.header, verify=False)
			if int(apiResponse.status_code) == 401 and retryFlag is False:
				## Token expired; need to re-authenticate
				self.establishConnection()
				self.updateCI(identifier, payloadAsString, retryFlag=True)
			elif int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.updateCI: {}".format(stacktrace))

		## end updateCI
		return


	##  Delete a CI
	def deleteCI(self, identifier, retryFlag=False):
		try:
			urlForCiQuery = '{}/dataModel/ci/{}'.format(self.baseURL, identifier)
			logger.debug('urlForCiQuery: {}'.format(urlForCiQuery))
			## Issue a DELETE call to URL; no payload required
			apiResponse = requests.delete(urlForCiQuery, headers=self.header, verify=False)
			if int(apiResponse.status_code) == 401 and retryFlag is False:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))
				## Token expired; need to re-authenticate
				self.establishConnection()
				self.deleteCI(identifier, retryFlag=True)
			elif int(apiResponse.status_code) != 200:
				logger.debug('Response code: {}'.format(apiResponse.status_code))
				logger.debug('Response: {}'.format(apiResponse.text))

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.deleteCI: {}".format(stacktrace))

		## end deleteCI
		return


	def insertTopology(self, payloadAsString, retryFlag=False):
		"""Insert a new topology."""
		try:
			urlForCiQuery = '{}/dataModel'.format(self.baseURL)
			## Payload is passed in as a string type
			logger.debug('header: {}'.format(self.header))
			logger.debug('payloadAsString: {}'.format(payloadAsString))

			## Issue a GET call to URL
			apiResponse = requests.post(urlForCiQuery, data=payloadAsString, headers=self.header, verify=False)
			if int(apiResponse.status_code) == 401 and retryFlag is False:
				## Token expired; need to re-authenticate
				logger.debug('Response code: {}  Message:'.format(apiResponse.status_code, apiResponse.text))
				logger.debug('Attempting re-authentication and a retry...')
				self.establishConnection()
				self.insertTopology(payloadAsString, retryFlag=True)
			logger.debug('Response code: {}'.format(apiResponse.status_code))
			logger.debug('Response: {}'.format(apiResponse.text))
			responseAsJson =  json.loads(apiResponse.text)

		except:
			stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			logger.error("Failure in ocpRestAPI.insertTopology: {}".format(stacktrace))

		## end insertTopology
		return
