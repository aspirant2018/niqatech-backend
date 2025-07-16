from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///niqatech.db')
inspector = inspect(engine)

# List all tables
print(inspector.get_table_names())

# Get column info for a specific table
for column in inspector.get_columns('users'):
    print(column)