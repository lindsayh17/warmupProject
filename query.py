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
from firebase import doQuery
import pyparsing as pp
'''
# creates tokens and patterns. patterns must be matched if you use it to parse string
greet = pp.Word(pp.alphas) + "," + pp.Word(pp.alphas) + "!"
# get user input
user_greeting = input("!? ")
# parse the user input
parsed_greeting = greet.parse_string(user_greeting)
# print out our parsed list
print(parsed_greeting)
'''
# PARSER COMPONENT

# Variables
attribute_names = "country region population gdp area coastline"
detail_bool = False
# Query pattern parts
attribute = pp.one_of(attribute_names, caseless = True)
operator = pp.one_of("= < > <= >= of")
value = pp.QuotedString('"')
detail = pp.Optional(pp.CaselessKeyword("detail"))
compoundOperator = pp.one_of("and or", caseless = True)
helpCommand = pp.CaselessKeyword("-help")
exitCommand = pp.CaselessKeyword("-exit")

# example of default query is "region of "east timor" detail
defaultQuery = attribute + operator + value + detail
compoundQuery = defaultQuery + compoundOperator + defaultQuery
helpQuery = helpCommand
exitQuery = exitCommand

# get user input
while (True):
    user_query = input("!? ")
    # Check for Help Command
    if user_query == helpQuery:
        print("| Available attributes: country, region, population, gdp, area, coastline |")
        print("| Available operators: =, <, >, <=, >=, of |")
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
        elif item in ["=", "<", ">", "<=", ">="]:   
            operator_list.append(item)
        # includes of, values of operators, names of countries
        elif item not in ["and", "or", "detail"]:
            value_list.append(item)
    
    if parsed_query[-1] == "detail":
        detailBool = True
    else:
        detailBool = False
    
    # debugging
    print(parsed_query)
    print(attribute_list)
    print(operator_list)
    print(value_list)

    # doQuery
    if operator not in ["of"]:
        if "and" in parsed_query:
            queryType = "and"
        elif "or" in parsed_query:
            queryType = "or"
        else:
            queryType = "comparison"
        doQuery(queryType, attribute_list, operator_list, value_list, detailBool)

    # 'attribute' of 'country' always returns one value,
    # e.g. 'region of "china"' would output 'Asia'
    elif operator in ["of"]:
        queryType = "country_attribute"
        output = doQuery(queryType, attribute_list, operator_list, value_list, detailBool)
        print(output)

