# Query Program
# TODO: Better documentation for functions and inline comments
# TODO: go through and fix cases
# TODO: review Jason's project doc
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
from tabulate import tabulate #detail formatting, pip install tabulate to use!

class QueryType(Enum):
    COMPARE = "comparison"
    COUNTRY_ATTRIBUTE = "country_attribute"
    AND = "and"
    OR = "or"

#list of regions for error handling
region_ref = ["ASIA (EX. NEAR EAST)", "BALTICS", "C.W. OF IND. STATES", "EASTERN EUROPE", "LATIN AMER. & CARIB", "NEAR EAST", "NORTHERN AFRICA", "NORTHERN AMERICA", "OCEANIA", "SUB-SAHARAN AFRICA", "WESTERN EUROPE"]
#database reference
countries_ref = db.collection("countries")

# Variables
attribute_names = "Country Region Population GDP Area Coastline"
detail_bool = False
# Query pattern pieces
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
regionCommand = pp.CaselessKeyword("regions")
# Parser Patterns
countryDetailQuery = value + detail
defaultQuery = attribute + operator + value + detail
compoundQuery = defaultQuery + compoundOperator + defaultQuery
# Parses the pattern with longest match
parseQuery = countryDetailQuery ^ defaultQuery ^ compoundQuery

def country_exists(country_name):
    try:
        caps_country = country_name.lower().capitalize()
    except AttributeError:
        # return false if not a string - can't be a country
        return False

    doc_ref = db.collection("countries").document(caps_country)

    doc = doc_ref.get()
    if doc.exists:
        return True
    else:
        return False

def region_checker(region_attribute, region_input):
    if region_attribute.lower() == "region":
        return region_input.upper()
    else:
        return region_input

# for help command, rules of the query language
def help_func():
    print("! 'exit' to leave program")
    print("! 'regions' to see list of regions")
    print("!  Query Syntax")
    print("!    Available query starters: country, region, population, gdp, area, coastline")
    print("!    Available operators: ==, <, >, <=, >=, of")
    print("!    Use quotations for regions or countries with more than one word")
    print("!    Add 'detail' to end of query to get all values of countries")
    print("!    Example: region of \"East Timor\" detail")

# print out regions formatted
def regions():
    for region in region_ref:
        print(region)

'''
Takes in an attribute string and a country string as variables. 
Accesses firebase to find the info of the attribute according to the country. 
Returns the information requested.

Example query: getInfo(“population”,  “Western Sahara”)
              return: 273008

'''

def get_info(attribute_input, country):
    """
    Gets the value of an attribute for a specific country.
    :param attribute_input: region, population, area, gdp, coastline
    :param country
    :return: string containing that countries attribute
    """

    caps_country = country.lower().capitalize()

    doc_ref = db.collection("countries").document(caps_country)

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()[attribute_input]
    else:
        print("No such document.")


'''
Takes in an attribute string, a comparison operator string, and a number or string.
Access firebase does a comparison operator to find what the user requests. 
Returns what is found in firebase.

Example query: getCompare(“gdp”, “==”, 500)
              return: East Timor, Sierra Leone, Somalia

'''
def get_compare(attribute_input, operator_input, value_input):
    """
    Uses the comparison operator to query firebase based on the input

    :param attribute_input:
    :param operator_input: <, >, ==, etc... used to compare all of the values in firebase to a specific input
    :param value_input: limiting factor for values returned
    :return: list of countries
    """

    # convert any region to all caps
    checked_input = region_checker(attribute_input, value_input)

    # get all entries that satisfy condition
    docs = (
        db.collection("countries")
        .where(filter=FieldFilter(attribute_input, operator_input, checked_input))
        .stream()
    )

    # make list of countries
    countries = []
    for doc in docs:
        countries.append(doc.id)

    return countries


'''
Exact same functionality as "getInfo", but returns a dictionary containing all attributes
'''
def get_detailed_info(country):
    """
    Gets all the information for a specific country. An attribute may be supplied, but will not change results.
    :param country:
    :return: dictionary with country information with format {attribute: value} (ex. {'GDP': 2200, 'Area': 239460})
    """

    caps_country = country.lower().capitalize()

    # get country data
    doc_ref = db.collection("countries").document(caps_country)

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print("No such document.")

'''
Exact same functionality as "getCompare", but returns a dictionary containing all attributes
'''
def get_detailed_compare(attribute_input, operator_input, value_input):
    """
    Gets all information for all countries with attributes of a certain value
    :param attribute_input:
    :param operator_input:
    :param value_input:
    :return: nested dictionary, where outer keys are the countries and values for those keys are the list of
        attributes and their values, as in the dict for getDetailedInfo
    """

    # convert any region to all caps
    checked_input = region_checker(attribute_input, value_input)

    # get collection of countries that meet the criteria
    docs = (
        db.collection("countries")
        .where(filter=FieldFilter(attribute_input, operator_input, checked_input))
        .stream()
    )

    # make list of countries
    country_info = {}
    for doc in docs:
        country_info[doc.id] = doc.to_dict()

    return country_info

'''
Parser passes enum query type and all other necessary data like attribute, operator, values, and optionally detail in a list to the doQuery function. The doQuery function has a boolean detail argument that is true if the keyword detail is present. The do query evaluates the data given and then calls the appropriate written wrapper functions which call the actual firebase gets. It will return the data and then the parser will format it as output to the user.
'''
def do_query(q_type, attribute_input, operator_input, value_input, detail_input: bool):
    # debugging
    print("*dQ*qType: \t\t\t" + q_type)
    #
    # convert string qType to enum, will fail if string is not one of enum vals
    user_query_type = QueryType(q_type)
    # debugging
    print("*dQ*user_query_type: \t\t" + str(user_query_type))
    # if given just a country as value then return details of it
    if not attribute_input and not operator_input and country_exists(value_input[0]):
        return get_detailed_info(value_input[0])

    # if "Country of countryName" return details
    if "Country" in attribute_input and "of" in operator_input and country_exists(value_input[0]):
        return get_detailed_info(value_input[0])

    # if detail keyword is used, get all details for every query
    elif detail_input:
        # debugging
        print("*dQ*detail = TRUE")
        # check user query type according to enum
        match user_query_type:
            case QueryType.COMPARE:
                return get_detailed_compare(attribute_input[0], operator_input[0], value_input[0])
            case QueryType.COUNTRY_ATTRIBUTE:
                return get_detailed_info(value_input[0])
            case QueryType.AND:
                # select query results that appear on both sides of and
                query1 = get_detailed_compare(attribute_input[0], operator_input[0], value_input[0])
                query2 = get_detailed_compare(attribute_input[1], operator_input[1], value_input[1])
                result = {}
                for countryName in query1.keys():
                    if countryName in query2.keys():
                        result[countryName] = query1.get(countryName)
                return result
            case QueryType.OR:
                # select all query results from both sides of or without duplicates
                query1 = get_detailed_compare(attribute_input[0], operator_input[0], value_input[0])
                query2 = get_detailed_compare(attribute_input[1], operator_input[1], value_input[1])
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
                return get_compare(attribute_input[0], operator_input[0], value_input[0])
            case QueryType.COUNTRY_ATTRIBUTE:
                return get_info(attribute_input[0], value_input[0])
            case QueryType.AND:
                # select query results that appear on both sides of and
                query1 = get_compare(attribute_input[0], operator_input[0], value_input[0])
                query2 = get_compare(attribute_input[1], operator_input[1], value_input[1])
                result = []
                for country in query1:
                    if country in query2:
                        result.append(country)
                return result
            case QueryType.OR:
                # select all query results from both sides of or without duplicates
                query1 = get_compare(attribute_input[0], operator_input[0], value_input[0])
                query2 = get_compare(attribute_input[1], operator_input[1], value_input[1])
                for country in query2:
                    if country not in query1:
                        query1.append(country)
                return query1

    return "did not match to any in doQuery"

# PARSER COMPONENT
while True:
    user_query = input("!? ")
    # Check for Help Command
    if user_query == helpCommand:
        help_func()
        continue
    # Check for Exit Command
    elif user_query == exitCommand:
        print("exiting program!!!")
        break
    elif user_query == regionCommand:
        regions()
        continue
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
    # compound queries there should always be 2 attributes and operators
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

    # keep track of whether query is invalid to fully break out of loop
    invalidQuery = False
    index = 0

    # check 'of' queries first
    if "of" in operator_list:
        if len(flat_results) == 6:
            print("Invalid Query - Compound queries may not use 'of' operator")
            invalidQuery = True
        else:
            if not country_exists(value_list[0]):
                print(f"Invalid Query - {value_list[0]} is not a valid country")
                invalidQuery = True
    else:
        while index < len(flat_results):
            if flat_results[index] in attribute_list:
                if flat_results[index] == "Region":
                    # make sure region is in list of regions
                    if flat_results[index + 2] not in region_ref and not country_exists(flat_results[index + 2]):
                        invalidQuery = True
                        print(f"Invalid Query - {flat_results[index + 2]} is not a region.")
                        regions()
                        print("Please try again or type help for help.")
                        break
                elif flat_results[index] == "Country":
                    if not country_exists(flat_results[index + 2]):
                        invalidQuery = True
                        print(f"Invalid Query - {flat_results[index + 2]} is not a valid country.")
                        print(f"Please try again or type help for help. ")
                        break
                else:
                    if not isinstance(flat_results[index + 2], (int, float)):
                        invalidQuery = True
                        print(f"Invalid Query - {flat_results[index + 2]} cannot be read as a number.")
                        print("Ensure that numbers are not in quotes")
                        print("Please try again or type help for help.")
                        break
            index += 1

    if invalidQuery:
        continue

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
        output = do_query(qType, attribute_list, operator_list, value_list, detailBool)

    # 'attribute' of 'country' always returns one value,
    # e.g. 'region of "china"' would output 'Asia'
    # set query type and call doQuery function from firebase module
    elif "of" in operator_list:
        qType = "country_attribute"
        output = do_query(qType, attribute_list, operator_list, value_list, detailBool)
    else:
        output = "doQuery not called"

    #print output in a table when detail is true.
    if detail:
        if isinstance(output, dict):
            output = [output]
            print(tabulate(output, headers="keys", tablefmt="fancy_grid"))
    else:
        # TODO handle non detailed output
        output = [output]
        print(tabulate(output, headers="keys", tablefmt="fancy_grid"))
        #print(output)
