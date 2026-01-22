# Admin program
'''
The admin program will read data from a JSON file saved locally and will initialize and upload the data
to a Google Firebase Cloud Datastore (not a Firebase Realtime Database). You’ll run this program one
time. If you run it a second time, it should delete and recreate the datastore
'''
'''
Your admin program should take a single command-line argument: the name of the JSON file containing
the data to load. So for example, I would run my program this way:

$ python admin.py restaurant-data.json

The admin program will then read and parse the JSON file and upload the data to your Firebase
datastore. If the datastore already contains data, then the existing data will first be deleted.
'''
