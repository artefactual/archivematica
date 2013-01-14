# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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

import sys
from components.preservation_planning import forms
from django.db import connection, transaction
from django.shortcuts import render
from django.http import HttpResponse
from main import models
from components import helpers
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes

results_per_page = 6

# TODO: remove this after FPR work finalized
def preservation_planning(request):
    query="""SELECT
        Groups.description,
        FIBE.id AS Extension,
        CC.classification,
        CT.TYPE,
        CR.countAttempts,
        CR.countOK,
        CR.countNotOK,
        CR.countAttempts - (CR.countOK + CR.countNotOK) AS countIncomplete,
        Commands.PK AS CommandPK,
        Commands.description,
        Commands.command
      FROM FileIDsBySingleID AS FIBE
      RIGHT OUTER JOIN FileIDs ON FIBE.FileID = FileIDs.pk
      LEFT OUTER JOIN FileIDGroupMembers AS FIGM ON FIGM.fileID = FileIDs.pk
      LEFT OUTER JOIN Groups on Groups.pk = FIGM.groupID
      JOIN CommandRelationships AS CR ON FileIDs.pk = CR.FileID
      JOIN Commands ON CR.command = Commands.pk
      JOIN CommandClassifications AS CC on CR.commandClassification = CC.pk
      JOIN CommandTypes AS CT ON Commands.commandType = CT.pk
      WHERE
        CC.classification IN ('access', 'preservation')
      ORDER BY Groups.description, FIBE.id, CC.classification"""

    cursor = connection.cursor()
    cursor.execute(query)
    planning = cursor.fetchall()

    url = {
      'Audio': 'http://archivematica.org/wiki/index.php?title=Audio',
      'Email': 'http://archivematica.org/wiki/index.php?title=Email',
      'Office Open XML': 'http://archivematica.org/wiki/index.php?title=Microsoft_Office_Open_XML',
      'Plain text': 'http://archivematica.org/wiki/index.php?title=Plain_text',
      'Portable Document Format': 'http://archivematica.org/wiki/index.php?title=Portable_Document_Format',
      'Presentation': 'http://archivematica.org/wiki/index.php?title=Presentation_files',
      'Raster Image': 'http://archivematica.org/wiki/index.php?title=Raster_images',
      'Raw Camera Image': 'http://archivematica.org/wiki/index.php?title=Raw_camera_files',
      'Spreadsheet': 'http://archivematica.org/wiki/index.php?title=Spreadsheets',
      'Vector Image': 'http://archivematica.org/wiki/index.php?title=Vector_images',
      'Video': 'http://archivematica.org/wiki/index.php?title=Video',
      'Word Processing': 'http://archivematica.org/wiki/index.php?title=Word_processing_files'
    }

    file_types = []
    last_type = ''
    for item in planning:
        if last_type == item[0]:
            row = file_types.pop()
        else:
            row = {}
            row['type'] = last_type = item[0] # File type
            if row['type'] in url:
                row['url'] = url[row['type']]
            row['extensions'] = []
        row['extensions'].append(item) # Extensions
        file_types.append(row)

    cursor.close()

    return render(request, 'main/preservation_planning.html', locals())

def get_fpr_table():
#    query = """SELECT FileIDs.pk, FileIDsBySingleID.id, tool, toolVersion, FileIDs.description, classification, Commands.command, outputLocation, Commands.description FROM 
#            FileIDsBySingleID 
#            LEFT OUTER JOIN FileIDs ON FileIDs.pk = FileIDsBySingleID.fileID
#            LEFT OUTER JOIN FileIDTypes ON FileIDTypes.pk = FileIDs.fileIDType
#            LEFT OUTER JOIN CommandRelationships ON CommandRelationships.fileID = FileIDs.pk
#            LEFT OUTER JOIN CommandClassifications on CommandClassifications.pk = CommandRelationships.commandClassification
#            LEFT OUTER JOIN Commands ON CommandRelationships.command = Commands.pk
#            ORDER BY FileIDTypes.description, FileIDs.description, CommandClassifications.classification"""
   
    query = """SELECT FileIDs.pk, FileIDsBySingleID.id, tool, toolVersion, FileIDs.description, classification, Commands.command, 
                    outputLocation, Commands.description, FileIDs.validPreservationFormat, FileIDs.validAccessFormat
                FROM FileIDsBySingleID              
                LEFT OUTER JOIN FileIDs ON FileIDs.pk = FileIDsBySingleID.fileID             
                LEFT OUTER JOIN FileIDTypes ON FileIDTypes.pk = FileIDs.fileIDType             
                LEFT OUTER JOIN CommandRelationships ON CommandRelationships.fileID = FileIDs.pk             
                LEFT OUTER JOIN CommandClassifications on CommandClassifications.pk = CommandRelationships.commandClassification             
                LEFT OUTER JOIN Commands ON CommandRelationships.command = Commands.pk
                ORDER BY FileIDTypes.description, FileIDs.description, CommandClassifications.classification"""

    # Get FPR data

    cursor = connection.cursor()
    cursor.execute(query)
    planning = cursor.fetchall()

    results = []
    for item in planning:
       row = { 'pk': item[0],
               'id': item[1],
               'tool': item[2],
               'toolVersion': item[3],
               'FileIDs_description': item[4],
               'classification': item[5],
               'Commands_command': item[6],
               'outputLocation': item[7],
               'Commands_description': item[8],
               'FileIDs_validPreservationFormat': 'True' if item[9] == 1 else "False",
               'FileIDs_validAccessFormat': 'True' if item[10] == 1 else "False"
             }

       results.append(row)
 
    return results

def preservation_planning_fpr_search(request, current_page_number = None):
    if current_page_number == None:                
        current_page_number = 1

    query = request.GET.get('query', '')

    if query == '':
        # No query in the URL parameters list, try to see if we've got an existing query going from a previous page...
        query = request.session['fpr_query']
  
        # No query from a previous page either
        if query == '':
            query = '*'
            return HttpResponse('No query.')


    request.session['fpr_query'] = query # Save this for pagination...
    conn = pyes.ES('127.0.0.1:9200')

    indexes = conn.get_indices()

    if 'fpr_file' not in indexes:
        # Grab relevant FPR data from the DB
        results = get_fpr_table()
        request.session['fpr_results'] = results

        # Setup indexing for some Elastic Search action.
        for row in results:
            conn.index(row, 'fpr_file', 'fpr_files')
    else:
        results = request.session['fpr_results']
    
    # do fulltext search
    q = pyes.StringQuery(query)
    s = pyes.Search(q)

    try:
        results = conn.search_raw(s, size=len(results), indices='fpr_file')
    except:
        return HttpResponse('Error accessing index.')
    
    form = forms.FPRSearchForm()

    search_hits = []

    for row in results.hits.hits:
        search_hits.append(row['_source'].copy())

    page = helpers.pager(search_hits, results_per_page, current_page_number)
    hit_count = len(search_hits) 
  
    return render(request, 'main/preservation_planning_fpr.html', locals())


def preservation_planning_fpr_data(request, current_page_number = None):

    results = get_fpr_table()
    request.session['fpr_results'] = results

    if current_page_number == None:
        current_page_number = 1

    form = forms.FPRSearchForm()

    page = helpers.pager(results, results_per_page, current_page_number)
    request.session['fpr_query'] = ''

    item_count = len(results)

    return render(request, 'main/preservation_planning_fpr.html', locals())
