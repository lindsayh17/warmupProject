# Query Program
'''
the second program is the user query program. The example below shows my query program. A user
can run this program as often as they want, but the query program will only return results if the admin program has been run (i.e., if the data has been uploaded).
Each time the program starts, a new session starts. All requests for information take the form of a query in the “query language” of the system.
Use the PyParsing module for your parser.
The flow for the user is:

1. start the query program
2. make a query and receive a response
3. make additional queries, if desired, and receive responses
4. exit the program

To summarize: the data is uploaded once, using the admin program; after it’s been uploaded, it can be
queried repeatedly.
'''
from connectionAuthentication import db
from enum import Enum
from google.cloud.firestore_v1.base_query import FieldFilter
import pyparsing as pp

class QueryType(Enum):
    COMPARE = "comparison"
    COUNTRY_ATTRIBUTE = "country_attribute"
    AND = "and"
    OR = "or"

#list of regions for error handling
region_ref = ["ASIA (EX. NEAR EAST)", "BALTICS", "C.W. OF IND. STATES", "EASTERN EUROPE", "LATIN AMER. & CARIB", "NEAR EAST", "NORTHERN AFRICA", "OCEANIA", "SUB-SAHARAN AFRICA", "WESTERN EUROPE"]
#database reference
countries_ref = db.collection("countries")

# Variables
attribute_names = "Country Region Population GDP Area Coastline"
detail_bool = False
# Query pattern parts
attribute = pp.one_of(attribute_names, caseless = True)
operator = pp.one_of("== < > <= >= of")
value = (
    pp.QuotedString('"') | 
    pp.pyparsing_common.real |
    pp.pyparsing_common.integer |
    pp.Word(pp.alphanums + "-_") | pp.pyparsing_common.real
)
detail = pp.Optional(pp.CaselessKeyword("detail"))
compoundOperator = pp.one_of("and or", caseless = True)
# Commands
helpCommand = pp.CaselessKeyword("help")
exitCommand = pp.CaselessKeyword("exit")
# Parser Patterns
defaultQuery = attribute + operator + value + detail
compoundQuery = defaultQuery + compoundOperator + defaultQuery
parseQuery = defaultQuery ^ compoundQuery

helpQuery = helpCommand
exitQuery = exitCommand

def regionChecker(attribute, input):
    if attribute.lower() == "region":
        return input.upper()
    else:
        return input

'''
Takes in an attribute string and a country string as variables. 
Accesses firebase to find the info of the attribute according to the country. 
Returns the information requested.

Example query: getInfo(“population”,  “Western Sahara”)
              return: 273008

'''
def getInfo(attribute, country):
    """
    Gets the value of an attribute for a specific country.
    :param attribute: region, population, area, gdp, coastline
    :param country
    :return: string containing that countries attribute
    """

    capsCountry = country.lower().capitalize()

    doc_ref = db.collection("countries").document(capsCountry)

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()[attribute]
    else:
        print("No such document.")


'''
Takes in an attribute string, a comparison operator string, and a number or string.
Access firebase does a comparison operator to find what the user requests. 
Returns what is found in firebase.

Example query: getCompare(“gdp”, “==”, 500)
              return: East Timor, Sierra Leone, Somalia

'''
def getCompare(attribute, operator, input):
    """
    Uses the comparison operator to query firebase based on the input

    :param attribute:
    :param operator: <, >, ==, etc... used to compare all of the values in firebase to a specific input
    :param input: limiting factor for values returned
    :return: list of countries
    """

    # convert any region to all caps
    checkedInput = regionChecker(attribute, input)

    # get all entries that satisfy condition
    docs = (
        db.collection("countries")
        .where(filter=FieldFilter(attribute, operator, checkedInput))
        .stream()
    )

    # make list of countries
    countries = []
    for doc in docs:
        countries.append(doc.id)

    return countries


'''
Exact same functionality as "getInfo", but returns a dictionary containing all attriubutes
'''
def getDetailedInfo(attribute, country):
    """
    Gets all of the information for a specific country. An attribute may be supplied, but will not change results.
    :param attribute:
    :param country:
    :return: dictionary with country information with format {attribute: value} (ex. {'GDP': 2200, 'Area': 239460})
    """

    capsCountry = country.lower().capitalize()

    # get country data
    doc_ref = db.collection("countries").document(capsCountry)

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print("No such document.")

'''
Exact same functionality as "getCompare", but returns a dictionary containing all attributes
'''
def getDetailedCompare(attribute, operator, input):
    """
    Gets all information for all countries with attributes of a certain value
    :param attribute:
    :param operator:
    :param input:
    :return: nested dictionary, where outer keys are the countries and values for those keys are the list of
        attributes and their values, as in the dict for getDetailedInfo
    """

    # convert any region to all caps
    checkedInput = regionChecker(attribute, input)

    # get collection of countries that meet the criteria
    docs = (
        db.collection("countries")
        .where(filter=FieldFilter(attribute, operator, checkedInput))
        .stream()
    )

    # make list of countries
    countryInfo = {}
    for doc in docs:
        countryInfo[doc.id] = doc.to_dict()

    return countryInfo

'''
Parser passes enum query type and all other necessary data like attribute, operator, values, and optionally detail in a list to the doQuery function. The doQuery function has a boolean detail argument that is true if the keyword detail is present. The do query evaluates the data given and then calls the appropriate written wrapper functions which call the actual firebase gets. It will return the data and then the parser will format it as output to the user.
'''
def doQuery(qType, attribute, operator, value, detail: bool):
    # debugging
    print("*dQ*qType: \t\t\t" + qType)
    #
    # convert string qType to enum, will fail if string is not one of enum vals
    user_query_type = QueryType(qType)
    # debugging
    print("*dQ*user_query_type: \t\t" + str(user_query_type))

    # if detail keyword is used, get all details for every query
    if detail:
        # debugging
        print("*dQ*detail = TRUE")
        # check user query type according to enum
        match user_query_type:
            case QueryType.COMPARE:
                return getDetailedCompare(attribute[0], operator[0], value[0])
            case QueryType.COUNTRY_ATTRIBUTE:
                return getDetailedInfo(attribute[0], value[0])
            case QueryType.AND:
                # select query results that appear on both sides of and
                query1 = getDetailedCompare(attribute[0], operator[0], value[0])
                query2 = getDetailedCompare(attribute[1], operator[1], value[1])
                result = {}
                for countryName in query1.keys():
                    if countryName in query2.keys():
                        result[countryName] = query1.get(countryName)
                return result
            case QueryType.OR:
                # select all query results from both sides of or without duplicates
                query1 = getDetailedCompare(attribute[0], operator[0], value[0])
                query2 = getDetailedCompare(attribute[1], operator[1], value[1])
                for countryName in query2.keys():
                    if countryName not in query1.keys():
                        query1[countryName] = query2.get(countryName)
                return query1
    # no detail if keyword detail not included
    else:
        # debugging
        print("*dQ*detail = FALSE")
        # check user query type according to enum
        match user_query_type:
            case QueryType.COMPARE:
                return getCompare(attribute[0], operator[0], value[0])
            case QueryType.COUNTRY_ATTRIBUTE:
                return getInfo(attribute[0], value[0])
            case QueryType.AND:
                # select query results that appear on both sides of and
                query1 = getCompare(attribute[0], operator[0], value[0])
                query2 = getCompare(attribute[1], operator[1], value[1])
                result = []
                for country in query1:
                    if country in query2:
                        result.append(country)
                return result
            case QueryType.OR:
                # select all query results from both sides of or without duplicates
                query1 = getCompare(attribute[0], operator[0], value[0])
                query2 = getCompare(attribute[1], operator[1], value[1])
                for country in query2:
                    if country not in query1:
                        query1.append(country)
                return query1

    return "did not match to any in doQuery"

# PARSER COMPONENT
while (True):
    user_query = input("!? ")
    # Check for Help Command
    if user_query == helpQuery:
        print("| Available attributes: country, region, population, gdp, area, coastline |")
        print("| Available operators: ==, <, >, <=, >=, of |")
        print("| Use double quotes for string values. Example: region of \"East Timor\" detail |")
        print("| Integer values DO require quotes. Example: population > \"1000000\" |")
        continue
    # Check for Exit Command
    elif user_query == exitQuery:
        print("exiting program!!!")
        break
    # parse the user input 
    else: 
        try:
            parsed_query = parseQuery.parse_string(user_query)
        except pp.exceptions.ParseException:
            print("Invalid Query - please try again or type help for a list of commands.")
            continue

    # create lists of each element type
    # to make parsing compound queries easier for do_query function
    attribute_list = []
    operator_list = []
    value_list = []
    flat_results = parsed_query.asList()

    # process parsed input
    # compound queries there should alwasy be 2 attributes and operators
    for item in flat_results:
        # add to list attribute names, e.g. "region", "population", etc.
        if str(item) in attribute_names:
            attribute_list.append(item)
        # add to list any operators
        elif item in ["==", "<", ">", "<=", ">=", "of"]:   
            operator_list.append(item)
        # includes values of operators, names of countries
        elif item not in ["and", "or", "detail"]:
            value_list.append(item)
    # add detail bool val to pass to doQuery
    if parsed_query[-1] == "detail":
        detailBool = True
    else:
        detailBool = False
    
    # TODO handle logical error handling, for example currently coastline > stop
    # TODO currently just gives nothing from firebase call, should give feedback
    # TODO error instead

    # debugging
    print(f"*P*Parsed List: \t\t {parsed_query}")
    print(f"*P*attribute list proccessed: \t {attribute_list}")
    print(f"*P*operator list processed: \t {operator_list}")
    print(f"*P*value list processed: \t {value_list}")
    #

    # handle type of query for doQuery function
    if "of" not in operator_list:
        if "and" in flat_results:
            qType = "and"
        elif "or" in flat_results:
            qType = "or"
        else:
            qType = "comparison"
        # will return list of 
        output = doQuery(qType, attribute_list, operator_list, value_list, detailBool)

    # 'attribute' of 'country' always returns one value,
    # e.g. 'region of "china"' would output 'Asia'
    # set query type and call doQuery function from firebase module
    elif "of" in operator_list:
        qType = "country_attribute"
        output = doQuery(qType, attribute_list, operator_list, value_list, detailBool)
    else:
        output = "doQuery not called"

    # TODO handle output style
    if detail:
        # TODO handle detailed output
        print(output)
    else:
        # TODO handle non detailed output
        print(output)