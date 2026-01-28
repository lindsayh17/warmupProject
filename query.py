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
'''
while (True):
    userString = input("!? ")
    if userString.lower() == "exit":
        break

print("Program Closed")
'''

####first query attempt independant
attribute_names = "country region population gdp area coastline"
attribute = pp.one_of(attribute_names, caseless = True)
operator = pp.one_of("= < > <= >= of")
value = pp.QuotedString('"')
detail = pp.Optional(pp.CaselessKeyword("detail"))

# example of default query is "region of "east timor" detail
defaultQuery = attribute + operator + value + detail

# get user input
while (True):
    user_greeting = input("!? ")
    # parse the user input
    try:
        parsed_greeting = defaultQuery.parse_string(user_greeting)
        break
    except pp.exceptions.ParseException:
        print("invalid query")

# print out our parsed list
print(parsed_greeting)