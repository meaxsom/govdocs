import argparse
import json
import os

import dotenv
import neo4j

import cypher
import aws


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
    theParser.add_argument("path", help="file or S3 bucket path for JSON/XML input", type=str, default="", nargs='?')
    theParser.add_argument("-d", "--dry", help="dry run; output to STDOUT", action="store_true")

    bucket = None
    dry_run = False
    file_path = None

    theArgs=theParser.parse_args()

    if (theArgs.dry):
        dry_run=True

    if (theArgs.bucket):
        bucket = theArgs.bucket

    if (theArgs.path):
        file_path = theArgs.path


    json_data=None
    if (bucket):
        json_data=json.loads(aws.read_file_from_s3(bucket, file_path))
    else:
        json_data=json.loads(read_file_from_local(file_path))

    driver = None
    session = None
    if (dry_run):
        pass
    else:
        uri = "neo4j://localhost:7687"
        driver = neo4j.GraphDatabase.driver(uri, auth=("neo4j", "neo4j_test"))
        session = driver.session(database="neo4j")

    parser = cypher.Cypher(session)
    parser.populateJSON(None, json_data)

    if (driver):
        driver.close()

if __name__ == "__main__":
    main()
