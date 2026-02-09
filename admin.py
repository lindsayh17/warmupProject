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
    def __init__(self, country, region, area, population, gdp, coastline=None):
        self.country = country.strip()
        self.region = region
        self.area = area
        self.population = population
        self.gdp = gdp
        self.coastline = coastline

    @classmethod
    def from_dict(cls, source):
        return cls(source['Country'], source['Region'], source['Area'], source['Population'], source['GDP'], source.get('Coastline'))

    def to_dict(self):
        dictionary = {
            'Region': self.region,
            'Area': self.area,
            'Population': self.population,
            'GDP': self.gdp,
        }

        if self.coastline != 0:
            dictionary['Coastline'] = self.coastline

        return dictionary

    def __repr__(self):
        return f"Country(\
                country={self.country}, \
                region={self.region}, \
                area={self.area}, \
                population={self.population}, \
                gdp={self.gdp}, \
                coastline={self.coastline}\
            )"

# TODO: delete current docs first?
def populate_firebase(source):
    try:
        with open(source, 'r') as f:
            country_data = json.load(f)


        collection_reference = db.collection("countries")
        for country_dict in country_data:
            country = Country.from_dict(country_dict)
            collection_reference.document(country.country).set(country.to_dict())

    except FileNotFoundError:
        print("Error: File not found")

if len(sys.argv) == 2:
    populate_firebase(sys.argv[1])
else:
    print("Please provide the file path")
