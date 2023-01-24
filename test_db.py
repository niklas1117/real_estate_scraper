from sqlalchemy import create_engine
import pandas as pd


engine = create_engine("mysql:///root:root@localhost/first_db")

df = pd.DataFrame(
    {
        'a': [1,2,3], 
        'b': [4,5,6]
    }


)

with engine.begin as con:
    df.to_sql('test_table', con)