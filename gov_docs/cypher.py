import re
import xml.etree.ElementTree as ET

import typeid

class Cypher:

    __CHILDREN_PROPERTY_NAME = "children"
    __PROPERTY_JOIN_STRING = ", "
    __PROPERTY_TYPE_KEY = "type"
    __PROPERTY_TYPE_ID_KEY = "typeId"
    __PROPERTY_XML_KEY = "xml"
    __PROPERTY_ELEMENT_ID_KEY = "elementId"

    __TYPE_ID_REGEX = "[_\-.0-9]"

    ## the session is the Neo4J session or None
    def __init__(self, inSession=None):
        self.__session = inSession

    ## These methods are for handling the different property types
    ## basicially return a string value of the data unless it's a string, in which case quote the value
    def __handle_int(self, value):
        return str(value)

    def __handle_str(self, value):
        return '"' + value + '"'

    def __handle_float(self, value):
        return str(value)

    def __handle_bool(self, value):
        return str(value)

    ## lists are just what they are.. could iterate over list and call switch_on_type...
    def __handle_list(self, value):
        return value
    
    ## convert any unknown type into a string
    def __handle_default(self, value):
        return '"' + str(value) + '"'

    ## handling types in the dictionary so the match up w/Cypher supported tyeps
    def __switch_on_type(self, value):
        type_to_function = {
            int: self.__handle_int,
            str: self.__handle_str,
            float: self.__handle_float,
            bool: self.__handle_bool,
            list: self.__handle_list,
        }
        value_type = type(value)

        return type_to_function.get(value_type, self.__handle_default)(value)

    ## collect all the propertyies defined in this dictionay - except "children" - and create the Cypher statement
    ## represeting the date for the node
    def __make_division(self, inObject):
        result = None

        ## Iterate over all elements in this object that are not labled "children"
        ## put the output in a list and then join the list with ", "
        theProperties = []
        for theKey in inObject.keys():
            if (theKey != self.__CHILDREN_PROPERTY_NAME):
                theProperties.append( "{0}: {1}".format(theKey, self.__switch_on_type(inObject[theKey])))

        return "{"  + self.__PROPERTY_JOIN_STRING.join(theProperties) + "}"


    ## output to the session or stdout
    def __output_statement(self, inStatement):
        if (self.__session):
            result=self.__session.run(inStatement)
            if (result):
                return list(result)
        else:
            print(inStatement)

    ## create the unique ID using typeId
    ## https://github.com/akhundMurad/typeid-python
    def __make_id(self, inTagName):
        theType = re.sub(self.__TYPE_ID_REGEX, "", inTagName)
        theId = typeid.TypeID(prefix=theType)
        return theId
    

    ## craft the node that will contain the XML data
    def __make_xml_node(self, inTypeId, inId, inXML):
        theProperties = []
        theProperties.append("{0}: \"{1}\"".format(self.__PROPERTY_TYPE_ID_KEY, inTypeId))
        theProperties.append("{0}: \"{1}\"".format(self.__PROPERTY_ELEMENT_ID_KEY, inId))
        theProperties.append("{0}: \"{1}\"".format(self.__PROPERTY_XML_KEY, inXML))
        return "{"  + self.__PROPERTY_JOIN_STRING.join(theProperties) + "}"


    ## find the nodes that have a direct HAS_CHILD relationship
    def __find_nodes(self, inParentN, inChildN):
        result = None

        theStatement = 'MATCH (a:Division)-[r:HAS_CHILD]->(b:Division) WHERE a.identifier = "{}" AND b.identifier = "{}" return a.typeId, b.typeId'.format(inParentN, inChildN)
        nodes=self.__output_statement(theStatement)
        if (nodes and len(nodes) > 0):
            result = nodes[0].data();
        return result


    ## populate using JSON data recursively
    def populateJSON(self, inId, inJSONObject):
        ## use the type as a part of the Node "type" AND as part of the unique identifier for this node
        theType = inJSONObject[self.__PROPERTY_TYPE_KEY]
        theId = self.__make_id(theType)

        # add the type ID to the current structure
        inJSONObject[self.__PROPERTY_TYPE_ID_KEY] = str(theId)

        theStatement = "MERGE ({}:Division:{}{})".format("d", theId.prefix.capitalize(), self.__make_division(inJSONObject))
        self.__output_statement(theStatement)

        # All but the first one should have a parent id
        ## create the relationship between the parent and child
        if (inId != None):
            theStatement = 'MATCH (a:Division), (b:Division) WHERE a.typeId = "{}" AND b.typeId = "{}" MERGE (a)-[r:HAS_CHILD]->(b)'.format(inId, theId)
            self.__output_statement(theStatement)

        ## since this is a nested structure, iterate over the children calling this method recursivly
        try:
            for child in inJSONObject[self.__CHILDREN_PROPERTY_NAME]:
                self.populateJSON(theId, child)
        except KeyError as e:
            pass ## should only get this if there are no "children" objects

    
    ## create constraints
    def createUniqueConstraint(self, inLabel, inProperty):
        theStatement = 'CREATE CONSTRAINT {0}_{1}_unique IF NOT EXISTS FOR (x:{0}) REQUIRE x.{1} is UNIQUE'.format(inLabel, inProperty)
        self.__output_statement(theStatement)

    ## populate using XML data recursively
    def populateXML(self, inParent, inXMLObject):
        ## create a new element and put any elements except DIVn elements in it
        node_root = ET.Element(inXMLObject.tag)
        node_root.attrib = inXMLObject.attrib.copy()
        node_root.text=inXMLObject.text
        node_id = inXMLObject.get("N")
        
        div_elements = []
        for child in inXMLObject:
            element_name = child.tag
            ## it has to start w/DIV but not actually be an actual HTML DIV
            if (not element_name.startswith("DIV") or element_name == "DIV"):
                new_child = ET.SubElement(node_root, child.tag)
                new_child.attrib = child.attrib.copy()
                new_child.text = child.text
            else:
                div_elements.append(child)
        
        ## create our linking ID
        theId = self.__make_id(inXMLObject.tag.lower())

        ## insert the XML into neo4J
        theStatement = "MERGE ({}:XMLData:{}{})".format("d", inXMLObject.tag.capitalize(), self.__make_xml_node(str(theId), node_id, ET.tostring(node_root).decode("utf-8").replace('"', r'\"')))
        self.__output_statement(theStatement)

        ## find the relationship between the "N" of this record and the "N" of the child record
        if (inParent):
            matching_nodes=self.__find_nodes(inParent, node_id)
            if (matching_nodes):
                ## B is typically the target of the relationship so we'll need it's typeId and the typeId of the node we
                ## just inserted
                theStatement = 'MATCH (a:Division), (b:XMLData) WHERE a.typeId = "{}" AND b.typeId = "{}" MERGE (a)-[r:HAS_XML]->(b)'.format(matching_nodes["b.typeId"], str(theId))
                self.__output_statement(theStatement)

        elif len(div_elements) > 0:
            ## in this case, we want to match one of the child nodes but we want "a" not "b"
            matching_nodes=self.__find_nodes(node_id, div_elements[0].get("N"))
            if (matching_nodes):
                theStatement = 'MATCH (a:Division), (b:XMLData) WHERE a.typeId = "{}" AND b.typeId = "{}" MERGE (a)-[r:HAS_XML]->(b)'.format(matching_nodes["a.typeId"], str(theId))
                self.__output_statement(theStatement)

        ## walk the child elements and insert them
        for element in div_elements:
            self.populateXML(node_id, element)


    