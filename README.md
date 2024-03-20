# Python Data Munging into Neo4J

## Background

Found on UpWork:

Need someone to download the [following file](https://www.ecfr.gov/current/title-12) into a Neo4J deatabase, then download and parse the [following file]( https://www.ecfr.gov/api/versioner/v1/full/2024-02-21/title-12.xml?part=1002), and attach/match it to the hierarchy file (the first file).

If successful, we will keep doing this with other files.

Must have Neo4J experience, must have data parsing and matching experience.


## Goals
- develop in 100% Python
- Files should reside in S3 or be read from local file
  - could be http(s) as well??

- Neo4j and python development should run in a container
  - DockerFile or devcontainer??
    - Ended up using a single Dockerfile.
      - Devcontainer had problems mounting/working with attached database directory from Neo4J
  
- should be updatable with new XML data


### Step 0
- set up s3 bucket with access restricted with no public access. Access will be by AWS "keys" attached to a new IAM user/group

- set up Python dev environment in a dev container with python, s3, and neo4j support
	- [boto3](https://github.com/boto/boto3)
	
- set up neo4j into same environment
	-[Build applications with Neo4j and Python](https://neo4j.com/docs/python-manual/current/)

### Step 0.5

- develop data structures for Neo4J access
	- JSON Structure 
    - related by `[HAS_CHILD]` between Parent/Child in JSON

```
    typeId: "{our-generated-type-id},
    identifier: "1.130",
    label: "\u00a7 1.130 Type II securities; guidelines for obligations issued for university and housing purposes.",
    label_level: "\u00a7 1.130",
    label_description: "Type II securities; guidelines for obligations issued for university and housing purposes.",
    reserved: false,
    type: "section",
    volumes: [
      "1"
    ],
    received_on: "2017-01-07T00:00:00-0500"
```
  
- XML Structure
  - related by `[HAS_XML]` between related JSON node

```
      typeId: "{our-generated-type-id},
      elementId: "B",
      xml: "{quote-encoded-xml-as-in-the-original}"
```

### Step 2
- read file from s3 into local environment 
- used [dotenv](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1) to control enviornment variable (AWS keysinjection into container


### Step 3
- parse JSON file recurslively and populate Neo4J
  - inserted full node from JSON file less children
    - used existing JSON format
  - children related using `(a:Division)-[r:HAS_CHILD]->(b:Division)`
- used [TypeId](https://github.com/akhundMurad/typeid-python) to generate unique node IDs

### Step 4
- parse XML recurslively and attach it to Neo4J nodes from JSON data
  - similar approach to JSON/Step 3
    - used TypeID to generate unique node IDs
    - carried "N" identifier into structure
    - xml inserted directly as quote escaped XML string
      - xml nodes related using `(a:Division)-[r:HAS_XML]->(b:XMLData)`


## To Do
- would be interesting to see if we can do this using AWS cloud resourcs
  - Use EC2 w/mounted EBS for Neo4J DB
  - Use lambda function tied to S3 bucket(s) for updating JSON/XML files and serverless Neptune
  - Some combo of the above