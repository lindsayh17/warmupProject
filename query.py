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

#actual database reference
countries_ref = db.collection("countries")

# Variables
attribute_names = "country region population gdp area coastline"
detail_bool = False
# Query pattern parts
attribute = pp.one_of(attribute_names, caseless = True)
operator = pp.one_of("== < > <= >= of")
value = pp.QuotedString('"') | pp.Word(pp.alphanums + "-_")
detail = pp.Optional(pp.CaselessKeyword("detail"))
compoundOperator = pp.one_of("and or", caseless = True)
# Commands
helpCommand = pp.CaselessKeyword("help")
exitCommand = pp.CaselessKeyword("exit")
# Parser Patterns
defaultQuery = attribute + operator + value + detail
compoundQuery = defaultQuery + compoundOperator + defaultQuery
helpQuery = helpCommand
exitQuery = exitCommand

'''
Takes in an attribute string and a country string as variables. 
Accesses firebase to find the info of the attribute according to the country. 
Returns the information requested.

Example query: getInfo(“population”,  “Western Sahara”)
              return: 273008

'''
def getInfo(attribute, country):
    doc_ref = db.collection("countries").document(country)

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
# TODO Note from Nick, been trying this out and not ever receiving any data in list
# TODO tried {region == "western europe"} and got back: []
# TODO also need to test if this is case sensitive?
def getCompare(attribute, operator, input):
    docs = (
        db.collection("countries")
        .where(filter=FieldFilter(attribute, operator, input))
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
    doc_ref = db.collection("countries").document(country)

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print("No such document.")

'''
Exact same functionality as "getCompare", but returns a dictionary containing all attributes
'''
def getDetailedCompare(attribute, operator, input):
    docs = (
        db.collection("countries")
        .where(filter=FieldFilter(attribute, operator, input))
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
    # 
    if detail:
        # debugging
        print("*dQ*detail = TRUE")
        #
        match user_query_type:
            case QueryType.COMPARE:
                return getDetailedCompare(attribute[0], operator[0], value[0])
            case QueryType.COUNTRY_ATTRIBUTE:
                return getDetailedInfo(attribute[0], value[0])
            case QueryType.AND:
                query1 = getDetailedCompare(attribute[0], operator[0], value[0])
                query2 = getDetailedCompare(attribute[1], operator[1], value[1])
                result = {}
                for countryInfo in query1.values():
                    if countryInfo in query2.values():
                        result[countryInfo.value] = countryInfo.items()
                return result
            case QueryType.OR:
                query1 = getDetailedCompare(attribute[0], operator[0], value[0])
                query2 = getDetailedCompare(attribute[1], operator[1], value[1])
                for countryInfo in query2.values():
                    if countryInfo not in query1.values():
                        query1[countryInfo.value] = countryInfo.items()
                return query1
    else:
        # debugging
        print("*dQ*detail = FALSE")
        #
        match user_query_type:
            case QueryType.COMPARE:
                return getCompare(attribute[0], operator[0], value[0])
            case QueryType.COUNTRY_ATTRIBUTE:
                return getInfo(attribute[0], value[0])
            case QueryType.AND:
                query1 = getCompare(attribute[0], operator[0], value[0])
                query2 = getCompare(attribute[1], operator[1], value[1])
                result = []
                for country in query1:
                    if country in query2:
                        result.append(country)
                return result
            case QueryType.OR:
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
            parsed_query = defaultQuery.parse_string(user_query)
            # TODO currently not working in practice, leaving out for now
            #parsed_query = compoundQuery.parse_string(user_query)
        except pp.exceptions.ParseException:
            print("Invalid Query - please try again or type -help for help.")
            continue

    #print a list of each element type that makes up a compound query
    attribute_list = []
    operator_list = []
    value_list = []

    # process parsed input
    # compound queries there should alwasy be 2 attributes and operators
    for item in parsed_query:
        # add to list attribute names, e.g. "region", "population", etc.
        if item in attribute_names:
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
    
    # debugging
    print(f"*P*Parsed List: \t\t {parsed_query}")
    print(f"*P*attribute list proccessed: \t {attribute_list}")
    print(f"*P*operator list processed: \t {operator_list}")
    print(f"*P*value list processed: \t {value_list}")
    #

    # doQuery
    if "of" not in operator_list:
        if "and" in parsed_query:
            qType = "and"
        elif "or" in parsed_query:
            qType = "or"
        else:
            qType = "comparison"
        # will return list of 
        output = doQuery(qType, attribute_list, operator_list, value_list, detailBool)
        # maybe do a 'if detailBool', then we know its gonna return a dict
        print(output)

    # 'attribute' of 'country' always returns one value,
    # e.g. 'region of "china"' would output 'Asia'
    elif "of" in operator_list:
        qType = "country_attribute"
        output = doQuery(qType, attribute_list, operator_list, value_list, detailBool)
        # would also need to do a 'if detailBool' for the details of one country
        print(output)

