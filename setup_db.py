from application import db
db.create_all() # create all the tables
from csv_loader import CSVLoader
CSVLoader.readListingCSV("listings.csv") # load all the data
