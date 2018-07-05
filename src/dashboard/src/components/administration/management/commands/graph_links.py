# -*- coding: utf-8 -*-

r"""Management command to generate a graph of the workflow data.

Before you use this command you need to install some dependencies manually:

    $ docker-compose exec --user=root archivematica-dashboard \
        bash -c "apt-get update && apt-get install --yes graphviz libgraphviz-dev"

    $ docker-compose exec --user=root archivematica-dashboard \
        pip install pygraphviz
"""

# This file is part of the Archivematica development tools.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import datetime
import logging
import os
import sys

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand
from django.db import connection

from lxml import etree
import pygraphviz as pgv


linkUUIDtoNodeName = {}

excludedNodes = {
    '61c316a6-0a50-4f65-8767-1f44b1eeb6dd': 'default fail procedure for transfers. Too many lines',
    '7d728c39-395f-4892-8193-92f086c0546f': 'default fail procedure for SIPs. Too many lines',
    '333532b9-b7c2-4478-9415-28a3056d58df': 'reject transfer option.',
    '19c94543-14cb-4158-986b-1d2b55723cd8': 'reject sip option',
}

# See http://www.graphviz.org/doc/info/colors.html
COLORS = {
    'node_chain_link': 'black',
    'node_chain_link_start': 'darkgoldenrod',
    'edge_exit_codes_ok': 'black',
    'edge_exit_codes_err': 'red',
    'edge_user_selections': 'green',
    'edge_watched_directories': 'cyan3',
    'edge_load_variable': 'orangered',
}


# See: https://wiki.archivematica.org/MCP/TaskTypes
TASK_TYPES = {

    #
    # General
    #

    # description="one instance"
    'one_instance': '36b2e239-4a57-4aa5-8ebc-7a29139baca6',

    # description="for each file"
    # 'for_each_file': 'a6b1c323-7d36-428e-846a-e7e819423577',

    #
    # User choice
    #

    # description="get user choice to proceed with"
    # '?': '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',

    # description="get replacement dic from user choice"
    # '?': '9c84b047-9a6d-463f-9836-eafa49743b84',

    # description="Get microservice generated list in stdOut"
    # '?': 'a19bfd9f-9989-4648-9351-013a10b382ed',

    # description="Get user choice from microservice generated list"
    # '?': '01b748fe-2e9d-44e4-ae5d-113f74c9a0ba',

    #
    # Unit variables
    #

    # description="linkTaskManagerSetUnitVariable"
    'unit_var': '6f0b612c-867f-4dfd-8e43-5b35b7f882d7',
    # description="linkTaskManagerUnitVariableLinkPull"
    'unit_var_pull': 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11',

}


def query_all_sql(sql, arguments=None):
    """Ported and simplified from the now-deleted databaseInterface."""
    with connection.cursor() as c:
        c.execute(sql, arguments)
        return c.fetchall()


SVGPAN_SCRIPT = etree.CDATA("""
// https://www.cyberz.org/projects/SVGPan/SVGPan.js

/**
 *  SVGPan library 1.2.1
 * ======================
 *
 * Given an unique existing element with id "viewport" (or when missing, the first g
 * element), including the the library into any SVG adds the following capabilities:
 *
 *  - Mouse panning
 *  - Mouse zooming (using the wheel)
 *  - Object dragging
 *
 * You can configure the behaviour of the pan/zoom/drag with the variables
 * listed in the CONFIGURATION section of this file.
 *
 * Known issues:
 *
 *  - Zooming (while panning) on Safari has still some issues
 *
 * Releases:
 *
 * 1.2.1, Mon Jul  4 00:33:18 CEST 2011, Andrea Leofreddi
 *  - Fixed a regression with mouse wheel (now working on Firefox 5)
 *  - Working with viewBox attribute (#4)
 *  - Added "use strict;" and fixed resulting warnings (#5)
 *  - Added configuration variables, dragging is disabled by default (#3)
 *
 * 1.2, Sat Mar 20 08:42:50 GMT 2010, Zeng Xiaohui
 *  Fixed a bug with browser mouse handler interaction
 *
 * 1.1, Wed Feb  3 17:39:33 GMT 2010, Zeng Xiaohui
 *  Updated the zoom code to support the mouse wheel on Safari/Chrome
 *
 * 1.0, Andrea Leofreddi
 *  First release
 *
 * This code is licensed under the following BSD license:
 *
 * Copyright 2009-2010 Andrea Leofreddi <a.leofreddi@itcharm.com>. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification, are
 * permitted provided that the following conditions are met:
 *
 *    1. Redistributions of source code must retain the above copyright notice, this list of
 *       conditions and the following disclaimer.
 *
 *    2. Redistributions in binary form must reproduce the above copyright notice, this list
 *       of conditions and the following disclaimer in the documentation and/or other materials
 *       provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY Andrea Leofreddi ` + "``AS IS''" + ` AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
 * FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL Andrea Leofreddi OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * The views and conclusions contained in the software and documentation are those of the
 * authors and should not be interpreted as representing official policies, either expressed
 * or implied, of Andrea Leofreddi.
 */

"use strict";

/// CONFIGURATION
/// ====>

var enablePan = 1; // 1 or 0: enable or disable panning (default enabled)
var enableZoom = 1; // 1 or 0: enable or disable zooming (default enabled)
var enableDrag = 0; // 1 or 0: enable or disable dragging (default disabled)

/// <====
/// END OF CONFIGURATION

var root = document.documentElement;

var state = 'none', svgRoot, stateTarget, stateOrigin, stateTf;

setupHandlers(root);

/**
 * Register handlers
 */
function setupHandlers(root){
    setAttributes(root, {
        "onmouseup" : "handleMouseUp(evt)",
        "onmousedown" : "handleMouseDown(evt)",
        "onmousemove" : "handleMouseMove(evt)",
        //"onmouseout" : "handleMouseUp(evt)", // Decomment this to stop the pan functionality when dragging out of the SVG element
     });

     if(navigator.userAgent.toLowerCase().indexOf('webkit') >= 0)
         window.addEventListener('mousewheel', handleMouseWheel, false); // Chrome/Safari
     else
         window.addEventListener('DOMMouseScroll', handleMouseWheel, false); // Others
 }

 /**
  * Retrieves the root element for SVG manipulation. The element is then cached into the svgRoot global variable.
  */
 function getRoot(root) {
     if(typeof(svgRoot) == "undefined") {
         var g = null;

         g = root.getElementById("viewport");

         if(g == null)
             g = root.getElementsByTagName('g')[0];

         if(g == null)
             alert('Unable to obtain SVG root element');

         setCTM(g, g.getCTM());

         g.removeAttribute("viewBox");

         svgRoot = g;
     }

     return svgRoot;
 }

 /**
  * Instance an SVGPoint object with given event coordinates.
  */
 function getEventPoint(evt) {
     var p = root.createSVGPoint();

     p.x = evt.clientX;
     p.y = evt.clientY;

     return p;
 }

 /**
  * Sets the current transform matrix of an element.
  */
 function setCTM(element, matrix) {
     var s = "matrix(" + matrix.a + "," + matrix.b + "," + matrix.c + "," + matrix.d + "," + matrix.e + "," + matrix.f + ")";

     element.setAttribute("transform", s);
 }

 /**
  * Dumps a matrix to a string (useful for debug).
  */
 function dumpMatrix(matrix) {
     var s = "[ " + matrix.a + ", " + matrix.c + ", " + matrix.e + "  " + matrix.b + ", " + matrix.d + ", " + matrix.f + "  0, 0, 1 ]";

     return s;
 }

 /**
  * Sets attributes of an element.
  */
 function setAttributes(element, attributes){
     for (var i in attributes)
         element.setAttributeNS(null, i, attributes[i]);
 }

 /**
  * Handle mouse wheel event.
  */
 function handleMouseWheel(evt) {
     if(!enableZoom)
         return;

     if(evt.preventDefault)
         evt.preventDefault();

     evt.returnValue = false;

     var svgDoc = evt.target.ownerDocument;

     var delta;

     if(evt.wheelDelta)
         delta = evt.wheelDelta / 3600; // Chrome/Safari
     else
         delta = evt.detail / -90; // Mozilla

     var z = 1 + delta; // Zoom factor: 0.9/1.1

     var g = getRoot(svgDoc);

     var p = getEventPoint(evt);

     p = p.matrixTransform(g.getCTM().inverse());

     // Compute new scale matrix in current mouse position
     var k = root.createSVGMatrix().translate(p.x, p.y).scale(z).translate(-p.x, -p.y);

         setCTM(g, g.getCTM().multiply(k));

     if(typeof(stateTf) == "undefined")
         stateTf = g.getCTM().inverse();

     stateTf = stateTf.multiply(k.inverse());
 }

 /**
  * Handle mouse move event.
  */
 function handleMouseMove(evt) {
     if(evt.preventDefault)
         evt.preventDefault();

     evt.returnValue = false;

     var svgDoc = evt.target.ownerDocument;

     var g = getRoot(svgDoc);

     if(state == 'pan' && enablePan) {
         // Pan mode
         var p = getEventPoint(evt).matrixTransform(stateTf);

         setCTM(g, stateTf.inverse().translate(p.x - stateOrigin.x, p.y - stateOrigin.y));
     } else if(state == 'drag' && enableDrag) {
         // Drag mode
         var p = getEventPoint(evt).matrixTransform(g.getCTM().inverse());

         setCTM(
            stateTarget,
            root.createSVGMatrix().translate(p.x - stateOrigin.x, p.y - stateOrigin.y).multiply(g.getCTM().inverse()).multiply(stateTarget.getCTM())
         );

         stateOrigin = p;
     }
 }

 /**
  * Handle click event.
  */
 function handleMouseDown(evt) {
     if(evt.preventDefault)
         evt.preventDefault();

     evt.returnValue = false;

     var svgDoc = evt.target.ownerDocument;

     var g = getRoot(svgDoc);

     if(
         evt.target.tagName == "svg"
         || !enableDrag // Pan anyway when drag is disabled and the user clicked on an element
     ) {
         // Pan mode
         state = 'pan';

         stateTf = g.getCTM().inverse();

         stateOrigin = getEventPoint(evt).matrixTransform(stateTf);
     } else {
         // Drag mode
         state = 'drag';

         stateTarget = evt.target;

         stateTf = g.getCTM().inverse();

         stateOrigin = getEventPoint(evt).matrixTransform(stateTf);
     }
 }

 /**
  * Handle mouse button release event.
  */
 function handleMouseUp(evt) {
     if(evt.preventDefault)
         evt.preventDefault();

     evt.returnValue = false;

     var svgDoc = evt.target.ownerDocument;

     if(state == 'pan' || state == 'drag') {
         // Quit pan mode
         state = '';
     }
 }
""")

logging.basicConfig(format='%(message)s', stream=sys.stdout)
logger = logging.getLogger()

# TODO: the dashboard doens't have access to this file.
config = ConfigParser.ConfigParser()
config.read('/etc/archivematica/MCPClient/archivematicaClientModules')


def get_script_name(name):
    """Extract client script name."""
    if not isinstance(name, basestring):
        return
    if config.has_option('supportedBatchCommands', name.lower()):
        return config.get('supportedBatchCommands', name.lower())


def add_edge(g, source_uuid, dest_uuid, color='black', label=None):
    """Add edges to graph."""
    if source_uuid in excludedNodes or dest_uuid in excludedNodes:
        return
    if source_uuid is None or dest_uuid is None:
        return
    if label:
        g.add_edge(
            linkUUIDtoNodeName[source_uuid],
            linkUUIDtoNodeName[dest_uuid],
            color=color, label=label)
    else:
        g.add_edge(
            linkUUIDtoNodeName[source_uuid],
            linkUUIDtoNodeName[dest_uuid],
            color=color)


def load_chain_links(g):
    """Map chain links to nodes in the graph.

    Default links are represented with black arrows.
    """
    sql = """
        SELECT
            MicroServiceChainLinks.pk,
            MicroServiceChainLinks.defaultNextChainLink,
            TasksConfigs.description,
            TaskTypes.description,
            TasksConfigs.taskTypePKReference,
            MicroServiceChainLinks.microserviceGroup
        FROM MicroServiceChainLinks
        JOIN TasksConfigs ON currentTask = TasksConfigs.pk
        JOIN TaskTypes ON taskType = TaskTypes.pk;
    """
    links = query_all_sql(sql)
    for link in links:
        pk, defaultNextChainLink, description, taskType, pkRef, group = link
        if pk in excludedNodes:
            continue
        sql = """
            SELECT
                execute,
                arguments
            FROM StandardTasksConfigs
            WHERE pk=%s;
        """
        script_name = query_all_sql(sql, (pkRef,))
        arguments = None
        if script_name:
            script_name, arguments = script_name[0]
        elif not script_name:
            sql = """
                SELECT
                    variable,
                    variableValue,
                    microServiceChainLink
                FROM TasksConfigsSetUnitVariable
                WHERE pk=%s;
            """
            returned = query_all_sql(sql, (pkRef,))
            if returned:
                script_name = '%s, %s' % (returned[0][0], returned[0][1] or returned[0][2])
        # Node info:
        # {MSCL UUID} Name of node
        # (task type description) taskTypePKReference
        # [Name of script] Microservice Group
        node_name = r"{%s} %s\n(%s) %s\n[%s] %s" % (pk, description, taskType, pkRef, script_name or '', group)
        # Color if start of chain
        border_color = COLORS['node_chain_link']
        sql = """
            SELECT *
            FROM MicroServiceChains
            WHERE startingLink=%s;
        """
        if query_all_sql(sql, (pk,)):
            border_color = COLORS['node_chain_link_start']
        full_script_name = get_script_name(script_name)
        tooltip = 'Script name: {}. \n'.format(full_script_name) if full_script_name else 'Full script name not found. '
        tooltip += 'Arguments: {}'.format(arguments) if arguments is not None else 'No arguments'
        g.add_node(node_name, label=node_name, id=node_name, color=border_color, tooltip=tooltip)
        linkUUIDtoNodeName[pk] = node_name
    for link in links:
        pk = link[0]
        default_link_id = link[1]
        if default_link_id is not None:
            add_edge(g, pk, default_link_id, label='defaultNextChainLink')
    return


def bridge_exit_codes(g):
    """
    Connect tasks based on the exit code.

    The edges are red if the exit code is greater than zero and green otherwise.
    The exit code is included in the label of the edge.
    """
    sql = """
        SELECT
            microServiceChainLink,
            nextMicroServiceChainLink,
            exitCode
        FROM MicroServiceChainLinksExitCodes;
    """
    logger.info('Processing exit codes...')
    rows = query_all_sql(sql)
    for row in rows:
        microServiceChainLink, nextMicroServiceChainLink, exit_code = row
        if nextMicroServiceChainLink:
            color = COLORS['edge_exit_codes_ok'] \
                if not exit_code else COLORS['edge_exit_codes_err']
            add_edge(g, microServiceChainLink, nextMicroServiceChainLink,
                     label='EXITCODE={}'.format(exit_code), color=color)


def bridge_user_selections(g):
    """Connect tasks that prompt the user with its corresponding choices.

    The arrows are green and labeled with the choice description.
    """
    logger.info('Processing user choices...')
    sql = """
        SELECT
            MicroServiceChainChoice.choiceAvailableAtLink,
            MicroServiceChains.startingLink,
            MicroServiceChains.description
        FROM MicroServiceChainChoice
        JOIN MicroServiceChains ON (MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk);
    """
    rows = query_all_sql(sql)
    for row in rows:
        choiceAvailableAtLink, startingLink, description = row
        if choiceAvailableAtLink and startingLink:
            add_edge(g, choiceAvailableAtLink, startingLink,
                     color=COLORS['edge_user_selections'], label=description)


def bridge_watched_directories(g):
    u"""Connect tasks that represent the end of a chain.

    These are the links that move the package to a new watched directory.
    The arrows are yellow.

    For example:

        > {61a8de9c-7b25-4f0f-b218-ad4dde261eed} Generate DIP
        > (one instance) ed8c70b7-1456-461c-981b-6b9c84896263
        > [move_v0.0] Prepare DIP

            [↓] (yellow)

        > {92879a29-45bf-4f0b-ac43-e64474f0f2f9} Upload DIP
        > (get user choice to proceed with) None
        > [] Upload DIP

    Not all the chains are triggered by other tasks, e.g. the following task
    has no successor.

        > {9520386f-bb6d-4fb9-a6b6-5845ef39375f} Approve AIP reingest
        > (get user choice to proceed with) None
        > [] Reingest AIP

    """
    logger.info('Processing watched directories...')
    sql = """
        SELECT
            watchedDirectoryPath,
            startingLink
        FROM WatchedDirectories
        JOIN MicroServiceChains ON (WatchedDirectories.chain = MicroServiceChains.pk);
    """
    rows = query_all_sql(sql)
    for row in rows:
        watchedDirectoryPath, startingLink = row
        logger.debug("\nWatched directory [%s] [startingLink=%s]",
                     watchedDirectoryPath.replace('%watchDirectoryPath%', ''),
                     startingLink)
        count = 0

        sql = """
            SELECT
                MicroServiceChainLinks.pk,
                execute,
                arguments
            FROM StandardTasksConfigs
            JOIN TasksConfigs ON (TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk)
            JOIN MicroServiceChainLinks ON (MicroServiceChainLinks.currentTask = TasksConfigs.pk)
            WHERE
                execute LIKE 'move%%'
                AND taskType = %s
                AND (arguments LIKE %s OR arguments LIKE %s);
        """
        rows2 = query_all_sql(sql, (
            TASK_TYPES['one_instance'],
            '%{}%'.format(watchedDirectoryPath.replace('%', '\%')),
            '%{}%'.format(watchedDirectoryPath.replace('%watchDirectoryPath%', '%sharedPath%watchedDirectories/', 1).replace('%', '\%')),
        ))
        for row2 in rows2:
            microServiceChainLink, execute, arguments = row2
            add_edge(g, microServiceChainLink, startingLink,
                     color=COLORS['edge_watched_directories'],
                     label=watchedDirectoryPath)
            logger.debug('  MATCHED SOURCE:\n   -> %s \n   -> %s\n   -> %s', microServiceChainLink, execute, arguments)
            count += 1

        if count == 0:
            logger.info("No sources for watched directory: %s", watchedDirectoryPath)


def bridge_load_variable(g):
    """Bridge load variable links."""
    sql = """
        SELECT
            MicroServiceChainLinks.pk,
            TasksConfigsUnitVariableLinkPull.variable,
            TasksConfigsUnitVariableLinkPull.defaultMicroServiceChainLink
        FROM MicroServiceChainLinks
        JOIN TasksConfigs ON (MicroServiceChainLinks.currentTask = TasksConfigs.pk)
        JOIN TasksConfigsUnitVariableLinkPull ON (TasksConfigsUnitVariableLinkPull.pk = TasksConfigs.taskTypePKReference)
        WHERE TasksConfigs.taskType = %s;
    """
    rows = query_all_sql(sql, (TASK_TYPES['unit_var_pull'],))
    for row in rows:
        count = 0
        microServiceChainLink, variable, defaultMicroServiceChainLink = row
        sql = """
            SELECT
                MicroServiceChainLinks.pk,
                TasksConfigsSetUnitVariable.variable,
                TasksConfigsSetUnitVariable.microServiceChainLink
            FROM MicroServiceChainLinks
            JOIN TasksConfigs ON MicroServiceChainLinks.currentTask = TasksConfigs.pk
            JOIN TasksConfigsSetUnitVariable ON TasksConfigsSetUnitVariable.pk = TasksConfigs.taskTypePKReference
            WHERE
                TasksConfigs.taskType = %s
                AND TasksConfigsSetUnitVariable.variable = %s;
        """
        rows2 = query_all_sql(sql, (
            TASK_TYPES['unit_var'],
            variable,
        ))
        for row2 in rows2:
            microServiceChainLink2, variable, microServiceChainLinkDest = row2
            add_edge(g, microServiceChainLink, microServiceChainLinkDest,
                     color=COLORS['edge_load_variable'], label=variable)
            count += 1
        if defaultMicroServiceChainLink:
            add_edge(g, microServiceChainLink, defaultMicroServiceChainLink,
                     color=COLORS['edge_load_variable'], label='default MSCL')
        if count == 0:
            logger.info("No bridge variable set for %s",
                        linkUUIDtoNodeName[microServiceChainLink])


def add_svgpan(filename):
    """
    Change the SVG document to allow zooming and panning.

    This is useful when viewing the graph from a browser.
    Embed the JavaScript snippet stored in SVGPAN_SCRIPT.
    """
    xml = etree.parse(filename)
    svg = xml.getroot()
    svg.set('width', '100%')
    svg.set('height', '100%')
    del svg.attrib['viewBox']
    g = svg.find('{http://www.w3.org/2000/svg}g')
    g.set('id', 'viewport')
    g.set('transform', 'matrix(0.13429683446884155,0,0,0.13429683446884155,-878.8951971178758,2349.1367317996337)')
    script = etree.Element('script')
    script.set('type', 'text/ecmascript')
    script.text = SVGPAN_SCRIPT
    g.addprevious(script)
    g.find('{http://www.w3.org/2000/svg}title').text = 'Archivematica MCP Workflows'
    xml.write(filename)


def main(format_, verbosity):
    """Entry point."""
    if verbosity > 1:
        logger.setLevel(logging.DEBUG)
    g = pgv.AGraph(strict=True, directed=True)

    # Nodes
    load_chain_links(g)

    # Edges
    bridge_exit_codes(g)
    bridge_user_selections(g)
    bridge_watched_directories(g)
    bridge_load_variable(g)

    # HACK? Represent the connection of the transfer and the ingest chains.
    #
    #     > {3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5} Move to SIP creation directory for completed transfers
    #     > (one instance) ac562701-7672-4e1d-a318-b986b7c9007c
    #     > [moveTransfer_v0.0] Create SIP from Transfer
    #
    #         [↓] (black)
    #
    #     > {70669a5b-01e4-4ea0-ac70-10292f87da05} Set file permissions
    #     > (one instance) 6157fe87-26ff-49da-9899-d9036b21c4b0
    #     > [setDirectoryPermissionsForAppraisal_v0.0] Verify SIP compliance
    #
    add_edge(g, '3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5', '70669a5b-01e4-4ea0-ac70-10292f87da05', label='Transfer -> Ingest (manual)')

    g.layout(prog='dot')

    date = datetime.date.today()
    filename = os.path.join(django_settings.SHARED_DIRECTORY, 'tmp/chainlinks-{}.{}'.format(date, format_))
    draw_args = "-Goverlap=prism "
    if verbosity > 1:
        draw_args += "-v "

    ret = 1
    try:
        print(filename)
        g.draw(filename, args=draw_args)
        ret = 0
    except:
        logger.exception('g.draw() failed! See exception details below...\n\n')

    if ret == 0 and format_ == 'svg':
        add_svgpan(filename)

    return ret


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-f', '--format', choices=['png', 'svg'], default='svg')

    def handle(self, *args, **options):
        main(options['format'], options['verbosity'])
