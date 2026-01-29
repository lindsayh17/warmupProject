from connectionAuthentication import db
from enum import Enum
from google.cloud.firestore_v1.base_query import FieldFilter

#actual database reference
countries_ref = db.collection("countries")

class queryType(Enum):
    COMPARE = "comparison"
    COUNTRY_ATTRIBUTE = "country_attribute"
    AND = "and"
    OR = "or"

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
def doQuery(queryType, attribute, operator, value, detail: bool):
    if detail:
        match queryType:
            case queryType.COMPARE:
                return getDetailedCompare(attribute[0], operator[0], value[0])
            case queryType.COUNTRY_ATTRIBUTE:
                return getDetailedInfo(attribute[0], value[0])
            case queryType.AND:
                query1 = getDetailedCompare(attribute[0], operator[0], value[0])
                query2 = getDetailedCompare(attribute[1], operator[1], value[1])
                result = {}
                for countryInfo in query1.values():
                    if countryInfo in query2.values():
                        result[countryInfo.value] = countryInfo.items()
                return result
            case queryType.OR:
                query1 = getDetailedCompare(attribute[0], operator[0], value[0])
                query2 = getDetailedCompare(attribute[1], operator[1], value[1])
                for countryInfo in query2.values():
                    if countryInfo not in query1.values():
                        query1[countryInfo.value] = countryInfo.items()
                return query1
    else:
        match queryType:
            case queryType.COMPARE:
                return getCompare(attribute[0], operator[0], value[0])
            case queryType.COUNTRY_ATTRIBUTE:
                return getInfo(attribute[0], value[0])
            case queryType.AND:
                query1 = getCompare(attribute[0], operator[0], value[0])
                query2 = getCompare(attribute[1], operator[1], value[1])
                result = []
                for country in query1:
                    if country in query2:
                        result.append(country)
                return result
            case queryType.OR:
                query1 = getCompare(attribute[0], operator[0], value[0])
                query2 = getCompare(attribute[1], operator[1], value[1])
                for country in query2:
                    if country not in query1:
                        query1.append(country)
                return query1

    return "list of values from firebase function"
