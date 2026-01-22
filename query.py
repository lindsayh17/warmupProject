# Query Program
'''
he second program is the user query program. The example below shows my query program. A user
can run this program as often as they want, but the query program will only return results if the admin
program has been run (i.e., if the data has been uploaded).
Each time the program starts, a new session starts. All requests for information take the form of a query
in the “query language” of the system.
Use the PyParsing module for your parser.
The flow for the user is:

1. start the query program
2. make a query and receive a response
3. make additional queries, if desired, and receive responses
4. exit the program

To summarize: the data is uploaded once, using the admin program; after it’s been uploaded, it can be
queried repeatedly.
'''
# Parsing system should be independent of the datastore system


## Help Command Function

# The datastore operations: create wrapper functions for the various operations 
# you’ll need to perform (load data, query)