from app.database.database import Base, engine
from app.database import models  # make sure all models are imported here

# This will create all tables defined in models.py

_ = models.User()
_ = models.UploadedFile()


print("Creating database and tables...")
Base.metadata.create_all(bind=engine)
print("Done.")