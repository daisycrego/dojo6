import os
from application import User, db 
db.create_all() # create all the tables
from csv_loader import CSVLoader
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv # for working locally, to access the .env file
load_dotenv() # load the env vars from local .env

CSVLoader.readListingCSV("listings.csv") # load all the data

# create an admin user 
new_user = User(email=os.environ.get("ADMIN_EMAIL"), name="Root User", password=generate_password_hash(os.environ.get("ADMIN_PASS"), method='sha256'), is_admin=True)
# add the new user to the database
db.session.add(new_user)
db.session.commit()
print("Created an admin user based on ADMIN_EMAIL and ADMIN_PASS.")