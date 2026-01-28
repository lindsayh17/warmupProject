from connectionAuthentication import db

#actual database reference
countries_ref = db.collection("countries")

'''
Takes in an attribute string and a country string as variables. 
Accesses firebase to find the info of the attribute according to the country. 
Returns the information requested.

Example query: getInfo(“population”,  “Western Sahara”)
              return: 273008

'''
def getInfo(attribute, country):
    doc_ref = db.collection("countries").document("Afghanistan ")

    doc = doc_ref.get()
    if doc.exists:
        print(f"Document data: {doc.to_dict()}")
    else:
        print("No such document.")

    # docs = (
    #     db.collection("countries")
    #     .stream()
    # )
    #
    # for doc in docs:
    #     print(f"{doc.id} => {doc.to_dict()}")


'''
Takes in an attribute string, a comparison operator string, and a number or string.
Access firebase does a comparison operator to find what the user requests. 
Returns what is found in firebase.

Example query: getCompare(“gdp”, “==”, 500)
              return: East Timor, Sierra Leone, Somalia

'''
def getCompare(attribute, comparison, input):
    return countries_ref.where(filter=FieldFilter(attribute, comparison, input))

'''
Exact same functionality as "getInfo", but returns a dictionary containing all attriubutes
'''
def getDetailedInfo(attribute, country):
    query = countries_ref.where("country", "==", country)
    return "got detailed info!"

'''
Exact same functionality as "getCompare", but returns a dictionary containing all attributes
'''
def getDetailedCompare(attribute, comparison, input):
    return countries_ref.where(attribute, comparison, input)

'''
Parser passes enum query type and all other necessary data like attribute, operator, values, and optionally detail in a list to the doQuery function. The doQuery function has a boolean detail argument that is true if the keyword detail is present. The do query evaluates the data given and then calls the appropriate written wrapper functions which call the actual firebase gets. It will return the data and then the parser will format it as output to the user.
'''
def doQuery(queryType, dataValues: list,detail: bool):
    return "list of values from firebase function"

getInfo("Region", "Algeria")