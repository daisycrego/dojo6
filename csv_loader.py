from csv import DictReader
from application import db, Agent, Listing

class CSVLoader:
    def readListingCSV(filename=None):
        if not filename:
            print("readListingCSV(): filename required")
            return

        # open file in read mode
        with open(filename, 'r') as reader_object2:
            # pass the file object to reader() to get the reader object
            csv_reader = DictReader(reader_object2)

            # detect agents
            agents = set()
            for row in csv_reader:
                agent_name = row["Agent"].strip()
                agent = None
                if not agent_name in agents:
                    agents.add(agent_name)
                    agent = Agent(name=agent_name)
                    db.session.add(agent)
                    db.session.commit()
                else:
                    agent = Agent.query.filter_by(name=agent_name).first()

                price = int(row["Listing Price"].replace("$", "").replace("","").replace(",",""))
                new_listing = Listing(address=row["Address"], url_zillow=row["Zillow URL"], url_redfin=row["Redfin URL"], url_cb=row["Coldwell Banker URL"], agent=agent, agent_id=agent.id, price=price)
                
                db.session.add(new_listing)
                db.session.commit()
        
            print("Created the listings")