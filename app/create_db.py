from app.database.database import Base, engine
from app.database import models  # make sure all models are imported here

# This will create all tables defined in models.py

_ = models.User()
_ = models.UploadedFile()


print("Deleting database and tables...")
Base.metadata.drop_all(bind=engine)   # <-- supprime toutes les tables
print("Creating database and tables...")
Base.metadata.create_all(bind=engine)
print("Done.")