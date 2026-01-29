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

#### first query attempt independant
attribute_names = "country region population gdp area coastline"
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
    # check the user input for commands first
    if user_query == helpQuery:
        print("| Available attributes: country, region, population, gdp, area, coastline |")
        print("| Available operators: =, <, >, <=, >=, of |")
        print("| Use double quotes for string values. Example: region of \"East Timor\" detail |")
        print("| Integer values DO require quotes. Example: population > \"1000000\" |")
        continue
    elif user_query == exitQuery:
        break
    # parse the user input 
    try:
        parsed_query = defaultQuery.parse_string(user_query)
        # currently not working in practice, leaving out for now
        #parsed_query = compoundQuery.parse_string(user_query)
        break
    except pp.exceptions.ParseException:
        print("Invalid Query - please try again or type -help for help.")

#print a list of each element type that makes up a compound query
attribute_list = []
operator_list = []
value_list = []


for item in parsed_query:
    if item in attribute_names:
        attribute_list.append(item)
    elif item in ["=", "<", ">", "<=", ">="]:   
        operator_list.append(item)
    elif item not in ["and", "or", "detail"]:
        value_list.append(item)
# doQuery
if operator not in ["of"]:
    if "and" in parsed_query:
        queryType = "and"
    elif "or" in parsed_query:
        queryType = "or"
    else:
        queryType = "compare"
    doQuery(queryType, attribute_list, operator_list, value_list, detail)

elif operator in ["of"]:
    queryType = "country_attribute"
    doQuery(queryType, attribute_list, operator_list, value_list, detail)

