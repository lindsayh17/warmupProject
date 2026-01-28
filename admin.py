# Admin program
'''
The admin program will read data from a JSON file saved locally and will initialize and upload the data
to a Google Firebase Cloud Datastore (not a Firebase Realtime Database). You’ll run this program one
time. If you run it a second time, it should delete and recreate the datastore
'''
import sys

'''
Your admin program should take a single command-line argument: the name of the JSON file containing
the data to load. So for example, I would run my program this way:

$ python admin.py restaurant-data.json

The admin program will then read and parse the JSON file and upload the data to your Firebase
datastore. If the datastore already contains data, then the existing data will first be deleted.
'''
import json
from connectionAuthentication import db

class Country:
    def __init__(self, country, region, population, gdp, coastline):
        self.country = country
        self.region = region
        self.population = population
        self.gdp = gdp
        self.coastline = coastline

    @staticmethod
    def from_dict(source):
        return json.loads(source)

    def to_dict(self):
        return {'Country': self.country, 'Region': self.region, 'Population': self.population, 'GDP': self.gdp, 'Coastline': self.coastline}

    def __repr__(self):
        return f"Country(\
                country={self.country}, \
                region={self.region}, \
                population={self.population}, \
                gdp={self.gdp}, \
                coastline={self.coastline}\
            )"

# TODO: should this be a function in the connectionAuthentication/Firebase file
# TODO: should I have used the to_dict and from_dict
def populate_firebase(source):
    try:
        with open(source, 'r') as f:
            country_data = json.load(f)

        collection_reference = db.collection("countries")
        for country in country_data:
            country_name = country['Country']
            clean_country = country_name.strip()
            country.pop('Country')
            if country['Coastline'] == 0:
                country.pop('Coastline')
            collection_reference.document(clean_country).set(country)
    except FileNotFoundError:
        print("Error: File not found")

# for country_object in country_data:
#     doc_ref = db.collection(country_data[1]).document(country_object[1])
#     doc_ref.set(country_object)

if len(sys.argv) == 2:
    populate_firebase(sys.argv[1])
else:
    print("Please provide the file path")
