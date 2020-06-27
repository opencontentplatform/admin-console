OCP Admin Console
=================
Thick client GUI for administrative tasks on the Open Content Platform.

Details
-------
OCP (https://github.com/opencontentplatform/ocp/) was indended to be driven by automation, but it's nice to have a way to visualize or point-and-click on something.

The admin console leverages wxPython (https://wxpython.org/) to expose a graphical user interface wrapping interaction to the OCP REST API.  This enables a native Python thick client.  As of posting this, the first two tabs (Platform and Data) are functional.  In the second tab, we leveraged D3 (https://d3js.org/) for graphical renderings with Simple Queries, Input Driven Queries, and Model Views.

Installation
------------
  * pip install wx
  * Download this repo
  * Edit the ./admin-console/ocpSettings.json file to set the OCP endpoint the API user/key
  * Start it up: python ./admin-console/adminConsole.py

Community Forum
---------------
  * https://www.opencontentplatform.org/forums/forum/public/

License
-------
  * GNU Lesser General Public License: https://github.com/opencontentplatform/admin-console/blob/master/LICENSE
