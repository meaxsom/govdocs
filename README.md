# Python Data Munging into Neo4J

## Background

Found on [UpWork](https://www.upwork.com/jobs/~010f399c86288cbe73):

Need someone to download the [following file](https://www.ecfr.gov/current/title-12) into a Neo4J database, then download and parse the [following file]( https://www.ecfr.gov/api/versioner/v1/full/2024-02-21/title-12.xml?part=1002), and attach/match it to the hierarchy file (the first file).

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
- [Build applications with Neo4j and Python](https://neo4j.com/docs/python-manual/current/)

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
- used [dotenv](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1) to control enviornment variable (AWS keys injection into container)


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


- adjust Cypher queries to use "best practices"
  - use `MERGE` instead of `CREATE`
  - create `CONSTRAINTS` on `typeId` for uniquness and value
  - standardize on property creation so each node has the same "primary" key(??)


## Schema

There are 2 general purpose "nodes" in the graph:
- `Division` nodes represent an individual "record" from the JSON file
  - each `Division` has an additional label that is derived from the `type` property, e.g. "Section", "Chapter", etc
  - each `Division` node contains a `typeId` property that represents a unique ID for the node since one doesn't seem to exist within the existing data structure. The `typeId` property us gerated using the "typeid-python" module
  - each `Division` node also contains all the properties from the original JSON record with the exception of `children`
  - Each "child" of a `Division` become its own `Division` node, i.e. all `children` records of a `Division` are themselves `Divisions` and related to their parent `Division` by a `HAS_CHILD` relationship. 

- `XMLData` nodes represent the collection of elements within a XML `DIVn` element, e.g. `DIV5`. HTML/XML tags with the element name of `DIV` are ignored.
  - each `XMLData` node contains a `typeId` property that represents a unique ID for the node since one doesn't seem to exist within the existing data structure. The `typeId` property us gerated using the "typeid-python" module
  - each `XMLData` node also contains all the properties from the original XML `DIVn` element - including text - with the exception of embedded `DIVn` elements
  - each "child" `DIVn` element of a `DIVn` element becomes its own `XMLData` node.
  - Each `XMLData` node is assoicated with a `Division` node by the following:
    - discover the related parent/child `Division` nodes via the `HAS_CHILD` relationship that contain matching `identifier` propertie from the parent/child `DIVn/N` element values
      - i.e `MATCH (a:Division)-[:HAS_CHILD]->(b:Division) return a.typeId, b.typeId`
    - use the approperiate `typeId` to create a `[:HAS_XML]` relationship between the `Division` and `XMLData` nodes
  
- The population of the JSON `Division` nodes and `XMLData` nodes is recursive

```
(a:Division)-[:HAS_CHILD]->(b:Divsion)
(a:Division)-[:HAS_XML]->(x:XMLData)
```
Each `Division` may have multiple `[:HAS_CHILD]` relationships
Each `Division` may have only 1 [:HAS_XML] relationship


