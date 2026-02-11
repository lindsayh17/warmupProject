from connection_authentication import db
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

# Query allowed inputs
attribute_names = ["Country", "Region", "Population", "GDP", "Area", "Coastline"]
operators = ["==", "<", ">", "<=", ">=", "of"]
detail_bool = False

# Query pattern pieces
attribute = pp.one_of(attribute_names, caseless = True)("attribute")
operator = pp.one_of("== < > <= >= of")("operator")
value = (
    pp.QuotedString('"') | 
    pp.pyparsing_common.real |
    pp.pyparsing_common.integer |
    pp.Word(pp.alphanums + "-_") | pp.pyparsing_common.real
)("value")
#sets detail as optional keyword
detail = pp.Optional(pp.CaselessKeyword("detail"))("detail")
compound_operator = pp.one_of("and or", caseless = True)("compound_operator")

# Commands
help_command = pp.CaselessKeyword("help")
exit_command = pp.CaselessKeyword("exit")
region_command = pp.CaselessKeyword("regions")

# Parser Patterns
country_detail_query = pp.Group(value + detail)("country_detail_query")
default_query = pp.Group(attribute + operator + value + detail)("default_query")
compound_query = pp.Group(default_query("left") + compound_operator + default_query("right"))("compound_query")

# Parses the pattern with longest match
parseQuery = (compound_query | default_query | country_detail_query) + pp.StringEnd()

def country_exists(country_name):
    # helper functions to check if country exists in firebase
    try:
        caps_country = country_name.title()
    except AttributeError:
        # return false if not a string - can't be a country
        return False

    # convert for firebase query
    doc_ref = db.collection("countries").document(caps_country)

    doc = doc_ref.get()
    if doc.exists:
        return True
    else:
        return False

def region_checker(region_attribute, region_input):
    # helper function to convert region input to caps for firebase query
    if region_attribute.lower() == "region":
        return region_input.upper()
    else:
        return region_input

def valid_value(attr, op, val):
    """
    helper function to check if value is valid for the attribute and operator given in user query

    :param attr: string attribute
    :param op: string operator
    :param val: string or number input
    :return: boolean true if valid, false if not valid
    """
    if op == "of":
        # of must be followed by a country
        if not country_exists(val):
            print(f"Invalid Query - {val} is not a valid country. The 'of' operator must be followed by a country.")
            print(f"Please try again or type help for help. ")
            return False
    else:
        if attr == "Region":
            # region needs to be followed by region input (since of operator already checked)
            try:
                if val.upper() not in region_ref:
                    print(f"Invalid Query - {val} is not a region.")
                    regions()
                    print("Please try again or type help for help.")
                    return False
                elif op != "==":
                    print(f"Invalid Query - {op} is not a valid operator for regions.")
                    print(f"Please try again or type help for help. ")
                    return False
            except AttributeError:
                # catch attribute error in case input is not a string
                print(f"Invalid Query - {val} is not a region.")
                regions()
                print("Please try again or type help for help.")
                return False
        elif attr == "Country":
            if not country_exists(val):
                print(f"Invalid Query - {val} is not a valid country.")
                print(f"Please try again or type help for help. ")
                return False
            elif op != "==":
                print(f"Invalid Query - {op} is not a valid operator for country.")
                print(f"Please try again or type help for help. ")
                return False
        else:
            if not isinstance(val, (int, float)):
                print(f"Invalid Query - {val} cannot be read as a number.")
                print("Ensure that numbers are not in quotes")
                print("Please try again or type help for help.")
                return False

    return True

def help_func():
    # for help command, rules of the query language
    print("! 'exit' to leave program")
    print("! 'regions' to see list of regions")
    print("!  Query Syntax")
    print("!    Available query starters: country, region, population, gdp, area, coastline")
    print("!    Available operators: ==, <, >, <=, >=, of")
    print("!    Use quotations for regions or countries with more than one word")
    print("!    Add 'detail' to end of query to get all values of countries")
    print("!    Example: region of \"East Timor\" detail")

def regions():
    # print out regions formatted
    for region in region_ref:
        print(region.title())

def get_info(attribute_input, country_name):
    """
    Gets the value of an attribute for a specific country.
    :param attribute_input: region, population, area, gdp, coastline
    :param country_name
    :return: string containing that countries attribute
    Example query: getInfo(“population”,  “Western Sahara”)
            return: 273008
    """
    caps_country = country_name.title()

    doc_ref = db.collection("countries").document(caps_country)

    doc = doc_ref.get()
    if doc.exists:
        # check to see if attribute exists
        try:
            return doc.to_dict()[attribute_input]
        except KeyError:
            return "None"
    else:
        print("No such document.")

def get_compare(attribute_input, operator_input, value_input):
    """
    Takes in an attribute string, a comparison operator string, and a number or string.
    Access firebase does a comparison operator to find what the user requests. 
    Returns what is found in firebase.

    :param attribute_input:
    :param operator_input: <, >, ==, etc... used to compare all of the values in firebase to a specific input
    :param value_input: limiting factor for values returned
    :return: list of countries
    Example query: getCompare(“gdp”, “==”, 500)
              return: East Timor, Sierra Leone, Somalia
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

def get_detailed_info(country_name):
    """
    Gets all the information for a specific country. An attribute may be supplied, but will not change results.
    :param country_name:
    :return: dictionary with country information with format {attribute: value} (ex. {'GDP': 2200, 'Area': 239460})
    """
    caps_country = country_name.title()

    # get country data
    doc_ref = db.collection("countries").document(caps_country)

    # check to see if country exists
    doc = doc_ref.get()
    country_info = {}
    if doc.exists:
        country_info[doc.id] = doc.to_dict()
        return country_info
    else:
        print("No such document.")

def get_detailed_compare(attribute_input, operator_input, value_input):
    """
    Gets all information for all countries with attributes of a certain value
    :param attribute_input: list of attributes
    :param operator_input: list of operators
    :param value_input: list of values
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


def do_query(q_type, attribute_input, operator_input, value_input, detail_input: bool):
    """
    Parser passes enum query type and all other necessary data like attribute, operator, values, and optionally detail in a list to the do_query function. The do_query function has a boolean detail argument that is true if the keyword detail is present. The do query evaluates the data given and then calls the appropriate written wrapper functions which call the actual firebase gets. It will return the data and then the parser will format it as output to the user.
    """
    # convert string qType to enum, will fail if string is not one of enum vals
    user_query_type = QueryType(q_type)
    # debugging
    #print("*dQ*user_query_type: \t\t" + str(user_query_type))
    # if given just a country as value then return details of it
    if not attribute_input and not operator_input and country_exists(value_input[0]):
        return get_detailed_info(value_input[0])

    # if "Country of countryName" return details
    if "Country" in attribute_input and "of" in operator_input and country_exists(value_input[0]):
        return get_detailed_info(value_input[0])

    # if detail keyword is used, get all details for every query
    elif detail_input:
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
                for country_name in query1:
                    if country_name in query2:
                        result.append(country_name)
                return result
            case QueryType.OR:
                # select all query results from both sides of or without duplicates
                query1 = get_compare(attribute_input[0], operator_input[0], value_input[0])
                query2 = get_compare(attribute_input[1], operator_input[1], value_input[1])
                for country_name in query2:
                    if country_name not in query1:
                        query1.append(country_name)
                return query1

    return "did not match to any in do_query"

########## PARSER COMPONENT ##########
print(" ______________________________________________________")
print("| Welcome to the Countries of the World Query Program! |")
print("|   Please enter a query, or type 'help' for help.     |")
print("| _____________________________________________________|")
print("                       ___,")
print("                  _.-'` __|__")
print("                .'  ,-:` \\;',`'-,")
print("               /  .'-;_,;  ':-;_,' .")
print("              /  /;   '/    ,  _`.-\\")
print("             |  | '`. (`     /` ` \\`|")
print("             |  |:.  `\\`-.   \\_   / |")
print("             |  |     (   `,  .`\\ ;'|")
print("              \\  \\     | .'     `-'/")
print("               \\  `.   ;/        .'")
print("                '._ `'-._____.-'`")
print("                   `-.____|")
print("                     _____|_____")
print("                    /___________\\")
#credit to https://asciiart.website/cat.php?category_id=339 for ascii art ;)

while True:
    detail_bool = False
    user_query = input("!? ")
    # Check for Help Command
    if user_query == help_command:
        help_func()
        continue
    # Check for Exit Command
    elif user_query == exit_command:
        print("exiting program!!!")
        break
    elif user_query == region_command:
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

    # new processing to help with error handling
    invalidQuery = False

    # check country only query
    if "country_detail_query" in parsed_query:
        country = parsed_query.country_detail_query[0]

        if not country_exists(country):
            print("Invalid Query - only countries can be used in a single parameter query")
            print("Please try again or type help for a list of commands.")
            invalidQuery = True
        else:
            value_list.append(country)
            detail_bool = True
    elif "default_query" in parsed_query:
        q = parsed_query.default_query

        attr = q.attribute
        op = q.operator
        val = q.value
        detail = q.detail

        if attr not in attribute_names:
            print("Invalid Query - queries must start with an attribute.")
            print("Please try again or type help for a list of commands.")
            invalidQuery = True
        elif op not in operators:
            print("Invalid Query - invalid operator")
            print("Please try again or type help for a list of commands.")
            invalidQuery = True
        elif not valid_value(attr, op, val):
            print("Please try again or type help for a list of commands.")
            invalidQuery = True
        else:
            attribute_list.append(attr)
            operator_list.append(op)
            value_list.append(val)
            if detail:
                detail_bool = True
    elif "compound_query" in parsed_query:
        q = parsed_query.compound_query

        left_side = q.left
        right_side = q.right
        compound_op = q.compound_operator

        # check detail
        right_detail = q.right.detail
        left_detail = q.left.detail
        detail_bool = right_detail or left_detail

        for default_query in (left_side, right_side):
            attr = default_query.attribute
            op = default_query.operator
            val = default_query.value

            if attr not in attribute_names:
                print("Invalid Query - queries must start with an attribute.")
                print("Please try again or type help for a list of commands.")
                invalidQuery = True
            elif op == "of":
                print("Invalid Query - 'of' cannot be used in compound queries.")
                print("Please try again or type help for a list of commands.")
            elif not valid_value(attr, op, val):
                invalidQuery = True
            else:
                attribute_list.append(attr)
                operator_list.append(op)
                value_list.append(val)


    if invalidQuery:
        continue

    # debugging
    '''
    print(f"*P*Parsed List: \t\t {parsed_query}")
    print(f"*P*attribute list proccessed: \t {attribute_list}")
    print(f"*P*operator list processed: \t {operator_list}")
    print(f"*P*value list processed: \t {value_list}")
    #'''

    # handle type of query for do_query function
    if "compound_query" in parsed_query:
        qType = parsed_query.compound_query.compound_operator
        output = do_query(qType, attribute_list, operator_list, value_list, detail_bool)
    elif "of" not in operator_list:
        qType = "comparison"
        # will return list of 
        output = do_query(qType, attribute_list, operator_list, value_list, detail_bool)
    # 'attribute' of 'country' always returns one value,
    # e.g. 'region of "china"' would output 'Asia'
    # set query type and call do_query function from firebase module
    elif "of" in operator_list:
        qType = "country_attribute"
        output = do_query(qType, attribute_list, operator_list, value_list, detail_bool)
    else:
        output = "do_query not called"

    #print output in a table when detail is true.
    if not output:
        print("No results found.")
    elif detail_bool or isinstance(output, dict):
        rows = []
        for country, data in output.items():
            row = {"Country": country}
            row.update(data)
            rows.append(row)
        print(tabulate(rows, headers="keys", tablefmt="fancy_grid"))
    else:
        # non-detailed output
        if isinstance(output, (int, float)):
            if "Population" in attribute_list:
                print(f"{output:,} people")
            elif "Area" in attribute_list:
                print(f"{output:,} km\u00b2")
            elif "Coastline" in attribute_list:
                print(f"{output:,} coast/area ratio")
            elif "GDP" in attribute_list:
                print(f"${output:,}")
            else:
                print(output)
        elif isinstance(output, list):
            print(", ".join(output))
        elif isinstance(output, str):
            print(output.title())
        else:
            print(output)
