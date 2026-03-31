import os
import psycopg2
import pytest

#1. Note: any pytest ->  pytest = functions + assertions + controlled execution
#2. naming convention -> test_ function pytest detects it
#3. if you are not using pytest db fixture then start docker db image manually before running this test if you want to test db connection
#4. add Mark DB tests, sothat you can run pytest selectively ->  
#      poetry run pytest -m "not db"
#          or
#      poetry run pytest -m db
#  

#Note:
#   Default values used by testcontainers:
#     user = test
#     password = test
#     db = test

@pytest.mark.db
def test_db_connection(postgres_container):
    #Recommended approach: Use the below built-in connection URL instead of manual fields.
    #conn = psycopg2.connect(postgres_container.get_connection_url())
    
    #Using manual fields 
    conn = psycopg2.connect(
        host=postgres_container.get_container_host_ip(),
        port=postgres_container.get_exposed_port(5432),
        dbname="test",
        user="test",
        password="test"
    )

    assert conn is not None
    conn.close()
