import sqlite3
import numpy as np
import io
# Declare numpy types

def adapt_array(array):
    out = io.BytesIO()
    np.save(out, array)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(string):
    out = io.BytesIO(string)
    out.seek(0)
    return np.load(out)

sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("array", convert_array)


class DB(object):

    def __init__(self):

        self._conn = sqlite3.connect("PhotoClusters.db",detect_types=sqlite3.PARSE_DECLTYPES)
        self.c = self._conn.cursor()

    def __del__(self):
        print("[DB Message] Closing database connection.")
        self._conn.close()


    def new_query(self,query, payload=None):
        if payload:
            print("[DB Message] Running query '" + str(query) + "' with payload")
            return self.c.execute(query, payload)
        else:
            print("[DB Message] Running query '" + str(query) + "' without payload")
            return self.c.execute(query)


    def print_query(self,query, payload=None):
        print("[DB Message] Running and Printing query " + str(query))
        for x in self.c.execute(query):
            print(x)


    def clean_tables(self):
        prompt = "This will clear all data from submissions. If you want to do this, type 'Delete'"
        if input(prompt) == "Delete":
            print("[DB Message] Deleting Table")
            self.c.execute('''DROP TABLE submissions''')
            self.c.execute('''CREATE TABLE submissions (ID text PRIMARY KEY, Title text,URL text,URLDomain text,Subreddit text,SubredditID text,PostURL text,PostTime BIGINT, PostAuthor text, PostScore INTEGER)''')
            print("[DB Message] Table deleted")
db = DB()

# db.new_query('''CREATE TABLE submission (ID text PRIMARY KEY, Title text,URL text,URLDomain text,Subreddit text,SubredditID text,PostURL text,PostTime BIGINT, PostAuthor text, Score INTEGER)''')
