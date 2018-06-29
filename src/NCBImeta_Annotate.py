"""
NCBI Metadata Database Annotator

@author: Katherine Eaton
"""

import argparse
import sqlite3
import datetime
import os
import sys

from NCBImeta_Errors import *
from NCBImeta_Utilities import os_check,table_exists

def flushprint(message):
    print(message)
    sys.stdout.flush()

#-----------------------------------------------------------------------#
#                            Argument Parsing                           #
#-----------------------------------------------------------------------#

parser = argparse.ArgumentParser(description=("NCBInfect Annotation Tool"),
                                 add_help=True)

mandatory = parser.add_argument_group('mandatory')
bonus = parser.add_argument_group('bonus')

mandatory.add_argument('--database',
                    help='Path to the sqlite database generated by NCBImeta.',
                    type = str,
                    action = 'store',
                    dest = 'dbName',
                    required=True)

mandatory.add_argument('--table',
                    help='Table in NCBImeta database to modify',
                    type = str,
                    action = 'store',
                    dest = 'dbTable',
                    required=True)

mandatory.add_argument('--annotfile',
                    help='Path to annotation file. The first column must contain a field that is unique to the record (ex. Accession)',
                    type = str,
                    action = 'store',
                    dest = 'annotFile',
                    required=True)

args = vars(parser.parse_args())

db_name = args['dbName']
db_table = args['dbTable']
annot_file_name = args['annotFile']


#-----------------------------------------------------------------------#
#                           Argument Checking                           #
#-----------------------------------------------------------------------#


#---------------------------Check Database------------------------------#

if os.path.exists(db_name):
    conn = sqlite3.connect(db_name)
    flushprint('\nOpening database: ' + db_name)
else:
    raise ErrorDBNotExists(db_name)

if not os.path.exists(annot_file_name):
    raise ErrorAnnotFileNotExists(annot_file_name)

# no errors were raised, safe to connect to db
cur = conn.cursor()

#---------------------------Check Table---------------------------------#

if not table_exists(cur, db_table):
    raise ErrorTableNotInDB(db_table)




#-----------------------------------------------------------------------#
#                                File Setup                             #
#-----------------------------------------------------------------------#


# get list of column names in Table
cur.execute('''SELECT * FROM {}'''.format(db_table))
db_col_names = [description[0] for description in cur.description]

#-----------------------------------------------------------------------#
#                             Annotation Setup                          #
#-----------------------------------------------------------------------#
annot_file = open(annot_file_name, "r")
annot_dict = {}

# Read header columns into list
header_columns_list = annot_file.readline().split("\t")
header_dict = {}

for i,header in enumerate(header_columns_list):
    header_dict[i] = header

annot_line = annot_file.readline()


#-----------------------------------------------------------------------#
#                         Process Annotations                           #
#-----------------------------------------------------------------------#

while annot_line:
    # Create a dictionary for storing all attributes for this one line
    line_dict = {}
    # Split line since this is a tsv file
    split_line = annot_line.split("\t")
    # Walk through each column value
    for i,element in enumerate(split_line):
        # Save the name of the column/header being processed
        header = header_dict[i].strip()
        # Cleanup extra white space, remove extra quotation marks
        element = element.strip().replace('\"','')

        # If it's the first column (index 0) this is the unique column for matching
        if i == 0:
            unique_header = header
            unique_element = element

        # IF annotation file header is a db column name, retain for annotation
        elif header in db_col_names:
            line_dict[header] = element

    # Check if unique_element is in table
    query = "SELECT * FROM {0} WHERE {1}={2}".format(db_table,
                                                    unique_header,
                                                    "'" + unique_element + "'")

    cur.execute(query)
    fetch_records = cur.fetchall()

    if not fetch_records:
        flushprint("Entry not in DB: " + line_strain)
        raise ErrorEntryNotInDB(line_strain)

    elif len(fetch_records) > 1:
        flushprint("Multiple Matches in DB: " + line_strain)
        raise ErrorEntryMultipleMatches(line_strain)


    # This section allows for dynamic variable creation and column modification
    sql_dynamic_vars = ",".join([header + "=" + "'" + line_dict[header] + "'" for header in line_dict.keys()])
    sql_dynamic_query = "UPDATE {0} SET {1} WHERE {2}={3}".format(db_table,
                                                    sql_dynamic_vars,
                                                    unique_header,
                                                    "'" + unique_element + "'")
    cur.execute(sql_dynamic_query)

    # Read in the next line
    annot_line = annot_file.readline()







#-----------------------------------------------------------------------#
#                                    Cleanup                            #
#-----------------------------------------------------------------------#
# Commit changes
conn.commit()
flushprint("Closing database: " + db_name)
cur.close()
annot_file.close()
