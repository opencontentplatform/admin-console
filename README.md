OCP Admin Console
=================
Python-based graphical user interface for administrative tasks on the Open Content Platform.

Details
-------
OCP (https://github.com/opencontentplatform/ocp/) was intended to be driven by automation, but it's nice to have a way to visualize or point-and-click on something.

The admin console leverages wxPython (https://wxpython.org/) to expose a graphical user interface, wrapping interaction to the OCP REST API.  This enables a native Python thick client on your OS of choice.  We leveraged D3 (https://d3js.org/) for sections providing graphical rendering.

Installation
------------
  * Add wxPython to your Python environment: pip install wxpython
  * Download this repo
  * Edit the ./admin-console/conf/ocpSettings.json file to set the OCP endpoint and API user/key
  * Start it up: python ./admin-console/adminConsole.py

Community Forum
---------------
  * https://www.opencontentplatform.org/forums/forum/public/

License
-------
  * GNU Lesser General Public License: https://github.com/opencontentplatform/admin-console/blob/master/LICENSE
