#Auto-start DB in pytest
#No manual docker command
#Tests are self-contained

#To achieve above
#    use testcontainers library : poetry add --group dev testcontainers psycopg2-binary2

import pytest
from testcontainers.postgres import PostgresContainer

#Adding pytest fixture to auto start DB in pytest
#    Before tests → starts PostgreSQL container
#    After tests → stops automatically
@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres