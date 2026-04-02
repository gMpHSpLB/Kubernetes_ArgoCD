import os
import pytest
import time

#1. Note: any pytest ->  pytest = functions + assertions + controlled execution
#2. naming convention -> test_ function pytest detects it
#3. if you are not using pytest db fixture then start docker db image manually before running this test if you want to test db connection
#4. add Mark DB tests, sothat you can run pytest selectively ->  
#      poetry run pytest -m "not db"
#          or
#      poetry run pytest -m db
#  

@pytest.mark.db
def test_db_connection(db_connection):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

    assert result[0] == 1
