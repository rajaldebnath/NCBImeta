#!/usr/bin env python -u
"""
Created on Thurs Mar 08 2018

@author: Katherine Eaton

"NCBImeta Main Program"
"""

# This program should only be called from the command-line
if __name__ != "__main__": quit()

import argparse
import sqlite3
import os
import sys
import importlib
import datetime
from Bio import Entrez
from xml.dom import minidom
#import xml.etree.cElementTree as ET

src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '') + "src"
sys.path.append(src_dir)

import NCBImeta_Utilities
import NCBImeta_Errors


def flushprint(message):
    print(message)
    sys.stdout.flush()

#-----------------------------------------------------------------------#
#                            Argument Parsing                           #
#-----------------------------------------------------------------------#

# To Be Done: Full Description
parser = argparse.ArgumentParser(description='Description of NCBImeta.',
                                 add_help=True)


# Argument groups for the program
mandatory_parser = parser.add_argument_group('mandatory')

mandatory_parser.add_argument('--outputdir',
                    help = 'Output directory.',
                    action = 'store',
                    dest = 'outputDir',
                    required = True)

parser.add_argument('--config',
                    help = 'Path to configuration file "NCBImeta_config.py".',
                    action = 'store',
                    dest = 'configPath',
                    required = True)

parser.add_argument('--flat',
                    help = 'Do not create organization directories, output all files to output directory.',
                    action = 'store_true',
                    dest = 'flatMode')



# Retrieve user parameters
args = vars(parser.parse_args())

config_path = args['configPath']
output_dir = args['outputDir']
flat_mode = args['flatMode']




#------------------------------------------------------------------------------#
#                              Argument Parsing                                #
#------------------------------------------------------------------------------#

# Check if config.py file exists
if not os.path.exists(config_path):
    raise ErrorConfigFileNotExists(config_path)

# Add the directory containing config.py to the system path for import
sys.path.append(os.path.dirname(config_path))

# Get the module name for import
config_module_name = os.path.basename(config_path).split(".")[0]

# Dynamic module loading
CONFIG = importlib.import_module(config_module_name)


flushprint(
"\n" + "NCBImeta run with the following options: " + "\n" +
"\t" + "Output Directory: " + CONFIG.OUTPUT_DIR + "\n" +
"\t" + "Email: " + CONFIG.EMAIL + "\n" +
"\t" + "User Database: " + str(CONFIG.DATABASE) + "\n" +
"\t" + "Tables: " + str(CONFIG.TABLES) + "\n" +
"\t" + "Search Terms: " + str(CONFIG.SEARCH_TERMS) + "\n\n")

# Flat mode checking
if flat_mode:
    flushprint("Flat mode was requested, organizational directories will not be used.")
    DB_DIR = os.path.join(output_dir, "")
    LOG_PATH = output_dir


elif not flat_mode:
    # Create accessory directory (ex. log, data, database, etc.)
    flushprint("Flat mode was not requested, organization directories will be used.")
    NCBImeta_Utilities.check_accessory_dir(output_dir)
    DB_DIR = os.path.join(output_dir, "", "database", "")
    LOG_PATH = os.path.join(output_dir, "", "log")

DB_PATH = os.path.join(DB_DIR, "", CONFIG.DATABASE)

#------------------------- Database Connection---------------------------------#
if not os.path.exists(DB_PATH):
    flushprint("\n" + "Creating database: " + DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.commit()
    flushprint("\n" + "Connected to database: " + DB_PATH)

elif os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.commit()
    flushprint("\n" + "Connected to database: " + DB_PATH)

#------------------------------------------------------------------------------#
#                       Database Processing Function                           #
#------------------------------------------------------------------------------#

def UpdateDB(table, output_dir, database, email, search_term, table_columns, log_path, db_dir):
    flushprint("\nCreating/Updating the " + table + " table using the following parameters: " + "\n" +
    "\t" + "Database: " + "\t\t" + database + "\n" +
    "\t" + "Search Term:" + "\t" + "\t" + search_term + "\n" +
    "\t" + "Email: " + "\t\t\t" + email + "\n" +
    "\t" + "Output Directory: "     + "\t" + output_dir + "\n\n")


    Entrez.email = email

    #---------------------------------------------------------------------------#
    #                                File Setup                                 #
    #---------------------------------------------------------------------------#
    # Name of Log File
    log_file_path = os.path.join(LOG_PATH, "",
                                os.path.splitext(database)[0] + "_" + table + ".log")

    # Check if the file already exists, either write or append to it.
    if os.path.exists(log_file_path):
        log_file = open(log_file_path, "a")
    else:
        log_file = open(log_file_path, "w")

    #--------------------------------------------------------------------------#
    #                                SQL Setup                                 #
    #--------------------------------------------------------------------------#

    # Connect to database and establish cursor for commands.
    conn = sqlite3.connect(os.path.join(db_dir, "", database))
    cur = conn.cursor()

    ## Create the database, with dynamic variables from config file
    sql_query = ("Create TABLE IF NOT EXISTS " + table +
    " (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, " +
    table + "_id TEXT")

    for column_name_dict in table_columns:
        column_name = column_name_dict.keys()[0]
        # By default, every user-specified column is type TEXT
        sql_query += ", " + column_name + " TEXT"
    sql_query += ")"

    cur.execute(sql_query)

    #-----------------------------------------------------------------------#
    #                          Entrex Search                                #
    #-----------------------------------------------------------------------#

    handle = Entrez.esearch(db=table.lower(),
                            term=search_term,
                            retmax = 10)

    # Read the record, count total number entries, create counter
    record = Entrez.read(handle)
    num_records = int(record['Count'])
    num_processed = 0

    #-----------------------------------------------------------------------#
    #                          Iterate Through ID List                      #
    #-----------------------------------------------------------------------#

    for ID in record['IdList']:
        #-------------------Progress Log and Entry Counter-------------------#
        # Increment entry counter and record progress to screen
        num_processed += 1
        flushprint("ID: " + ID)
        flushprint("Processing record: " +
               str(num_processed) + \
               "/" + str(num_records))

        #------------Check if Record Already Exists in Database------------#

        sql_query = ("SELECT EXISTS(SELECT " + table + "_id FROM " +
                    table + " WHERE " + table + "_id=?)")
        cur.execute(sql_query, (ID,))

        # 0 if not found, 1 if found
        record_exists = cur.fetchone()[0]

        if record_exists:
            continue
        '''
        IMPORTANT:
        The ID should not exists in the table UNLESS the record was fully parsed.
        ie. The database does not get updated until the end of each record.
        '''

        #---------------If Assembly Isn't in Database, Add it------------#
        # Retrieve Assembly record using ID, read, store as dictionary
        ID_handle = Entrez.esummary(db=table.lower(),id=ID)
        ID_record = Entrez.read(ID_handle, validate=False)
        try:
            record_dict = ID_record['DocumentSummarySet']['DocumentSummary'][0]
        except TypeError:
            record_dict = ID_record[0]
        flatten_record_dict = list(NCBImeta_Utilities.flatten_dict(record_dict))
        column_dict = {}

        # Add ID to the dictionary
        column_dict[table + "_id"] = ID

        # Iterate through each column to search for values
        for column in table_columns:
            column_name = column.keys()[0]
            column_payload = column.values()[0]
            column_value = ""
            column_index = 0


            #-------------------------------------------------------#
            # Attempt 1: Simple Dictionary Parse, taking first match

            for row in flatten_record_dict:
                #print(row)
                # For simple column types, as strings
                if type(column_payload) == str and column_payload in row:
                    column_value = row[-1]
                    break

                # For complex column types, as list
                elif type(column_payload) == list:
                    while column_payload[column_index] in row:
                        if column_index + 1 == len(column_payload):
                            column_value = row[-1]
                            break
                        column_index += 1

            # If the value was found, skip the next section of XML parsing
            if column_value:
                column_value = "'" + column_value.replace("'","") + "'"
                column_dict[column_name] = column_value

            #-------------------------------------------------------#
            # Attempt 2: XML Parse for node or attribute
            for row in flatten_record_dict:
                if type(column_payload) == str:
                    result = [s for s in row if column_payload in s]

                elif type(column_payload) == list:
                    result = [s for s in row if column_payload[0] in s and column_payload[1] in s ]
                if not result: continue
                result = result[0].strip()
                if result[0] != "<" or result[-1] != ">": continue
                #print(result)
                # Just in case, wrap sampledata in a root node for XML formatting
                xml = "<Root>" + result + "</Root>"
                # minidom doc object for xml manipulation and parsing
                root = minidom.parseString(xml).documentElement
                #print(root.toprettyxml())
                # Names of nodes and attributes we are searching for
                if type(column_payload) == str:
                    node_name = column_payload
                    attr_name = column_payload

                elif type(column_payload) == list:
                    node_name = column_payload[0]
                    if len(column_payload) > 2:
                        attr_name = column_payload[1:]
                    else:
                        attr_name = column_payload[1]
                # Dictionaries store recovered nodes and attributes
                node_dict = {}
                attr_dict = {}

                NCBImeta_Utilities.xml_find_node(root,node_name,node_dict)
                NCBImeta_Utilities.xml_find_attr(root,node_name,attr_name,attr_dict)
                #print(node_dict)
                #print(attr_dict)

                if type(column_payload) == list:
                    attr_name = column_payload[1]

                try:
                    column_value = attr_dict[attr_name]
                    column_value = "'" + column_value.replace("'","") + "'"
                    column_dict[column_name] = column_value
                    break
                except KeyError:
                    None

                try:
                    column_value = node_dict[node_name]
                    column_value = "'" + column_value.replace("'","") + "'"
                    column_dict[column_name] = column_value
                except KeyError:
                    None
                break

        # Write the column values to the db with dynamic variables
        sql_dynamic_table = "INSERT INTO " + table + " ("
        sql_dynamic_vars = ",".join([column for column in column_dict.keys()]) + ") "
        #sql_dynamic_qmarks = "VALUES (" + ",".join(["?" for column in column_dict.keys()]) + ") "
        sql_dynamic_values = " VALUES (" + ",".join([column_dict[column] for column in column_dict.keys()]) + ")"
        sql_query = sql_dynamic_table + sql_dynamic_vars + sql_dynamic_values
        #print(sql_query)
        cur.execute(sql_query)

        # Write to logfile
        now = datetime.datetime.now()
        log_file.write("[" + str(now) + "]" +
                     "\t" + "New entry added with ID:" +
                     "\t" + ID + "." + "\n")


    # CLEANUP
    conn.commit()
    cur.close()
    log_file.close()


#------------------------Iterate Through Tables--------------------------------#

for table in CONFIG.TABLES:
    OUTPUT_DIR = CONFIG.OUTPUT_DIR
    DATABASE = CONFIG.DATABASE
    EMAIL = CONFIG.EMAIL
    SEARCH_TERM = CONFIG.SEARCH_TERMS[table]
    TABLE_COLUMNS = CONFIG.TABLE_COLUMNS[table]
    UpdateDB(table, OUTPUT_DIR, DATABASE, EMAIL, SEARCH_TERM, TABLE_COLUMNS, LOG_PATH, DB_DIR)
