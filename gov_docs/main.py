import argparse
import json
import os
import xml.etree.ElementTree as ET

import dotenv
import neo4j

import cypher
import aws

__NEO4J_URI_KEY = 'NEO4J_URI'
__NEO4J_USER_KEY = 'NEO4J_USER'
__NEO4J_PASS_KEY = 'NEO4J_PASS'
__NEO4J_DB_KEY= 'NEO4J_DB'

def read_file_from_local(inPath):
    result = None

    with open(inPath, "r") as f:
        result = f.read()
        f.close();

    return result

def main():
    dotenv.load_dotenv()

    theParser = argparse.ArgumentParser()
    theParser.add_argument("-b", "--bucket", help="name of S3 bucket", type=str)
    theParser.add_argument("-x", "--xml", help="input is XML description file", action="store_true")
    theParser.add_argument("-d", "--dry", help="dry run; output to STDOUT", action="store_true")
    theParser.add_argument("path", help="file or S3 bucket path for JSON/XML input", type=str)

    bucket = None
    is_dry_run = False
    file_path = None
    is_xml = False

    theArgs=theParser.parse_args()

    if (theArgs.dry):
        is_dry_run=True

    if (theArgs.bucket):
        bucket = theArgs.bucket

    if (theArgs.xml):
        is_xml = True

    if (theArgs.path):
        file_path = theArgs.path


    raw_data=None
    if (bucket):
        raw_data=aws.read_file_from_s3(bucket, file_path)
    else:
        raw_data=read_file_from_local(file_path)

    driver = None
    session = None
    if (is_dry_run):
        pass
    else:
        uri = os.getenv(__NEO4J_URI_KEY)
        driver = neo4j.GraphDatabase.driver(uri, auth=(os.getenv(__NEO4J_USER_KEY), os.getenv(__NEO4J_PASS_KEY)))
        session = driver.session(database=os.getenv(__NEO4J_DB_KEY))

    parser = cypher.Cypher(session)

    ## apply uniqueness constraints to Division.typeId and XMLData.typeId
    parser.createUniqueConstraint('Division', 'typeId')
    parser.createUniqueConstraint('XMLData', 'typeId')

    if (not is_xml):
        parser.populateJSON(None, json.loads(raw_data))
    else:
        parser.populateXML(None, ET.fromstring(raw_data))

    if (driver):
        driver.close()

if __name__ == "__main__":
    main()
