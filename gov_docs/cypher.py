import re

import typeid

class Cypher:

    __CHILDREN_PROPERTY_NAME = "children"
    __PROPERTY_JOIN_STRING = ", "
    __PROPERTY_TYPE_KEY = "type"
    __PROPERTY_TYPE_ID_KEY = "typeId"

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
            self.__session.run(inStatement)
        else:
            print(inStatement)

    ## populate using JSON data
    def populateJSON(self, inId, inJSONObject):
        ## use the type as a part of the Node "type" AND as part of the unique identifier for this node
        theType = inJSONObject[self.__PROPERTY_TYPE_KEY]
        theType = re.sub(self.__TYPE_ID_REGEX, "", theType)

        ## create the unique ID using typeId
        ## https://github.com/akhundMurad/typeid-python
        theId = typeid.TypeID(prefix=theType)

        # add the type ID to the current structure
        inJSONObject[self.__PROPERTY_TYPE_ID_KEY] = str(theId)

        theStatement = "CREATE ({}:Division:{}{})".format("d", theType.capitalize(), self.__make_division(inJSONObject))
        self.__output_statement(theStatement)

        # All but the first one should have a parent id
        ## create the relationship between the parent and child
        if (inId != None):
            theStatement = 'MATCH (a:Division), (b:Division) WHERE a.typeId = "{}" AND b.typeId = "{}" CREATE (a)-[r:HAS_CHILD]->(b)'.format(inId, theId)
            self.__output_statement(theStatement)

        ## since this is a nested structure, iterate over the children calling this method recursivly
        try:
            for child in inJSONObject[self.__CHILDREN_PROPERTY_NAME]:
                self.populateJSON(theId, child)
        except KeyError as e:
            pass ## should only get this if there are no "children" objects
