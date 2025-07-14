'''
script to create tables
'''
from database import Base, engine
from database import User

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
