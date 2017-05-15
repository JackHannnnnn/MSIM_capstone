import MySQLdb as mdb
import numpy as np
import pandas as pd
import re


class DataReader(object):
    '''A unified data reader interface to interact with the In-Part database.'''
    
    def __init__(self):
        """Connect to db and create a cursor for subsequent queries. """
        self.con = mdb.connect(host='localhost', user='root', passwd="123", db="capstone", local_infile=1) 
        self.cur = self.con.cursor() 
        
        # Other auxiliary instance variables
        self.user_num = None
        self.user_ids = None
        self.user_keywords = None
        
        self.tech_num = None
        self.tech_ids = None
        self.tech_keywords = None
        
        self.all_keywords = None
        self.keyword_mapping_dict = None
        
        self.tech_mapping_dict = None

    def get_user_num(self):
        """Return the number of unique users.
        
        Returns
        -------
        long
        """
        if self.user_num is not None:
            return self.user_num
        query = "SELECT DISTINCT id FROM users"
        self.cur.execute(query)
        self.user_num =  self.cur.rowcount
        return long(self.user_num)

    def get_user_ids(self):
        """Return a list of all user ids in the database. 
        
        Returns
        -------
        list
            A list of long like [1L, 2L, 3L].
        """
        if self.user_ids is not None:
            return self.user_ids
        query = "SELECT DISTINCT id FROM users"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.user_ids = [row[0] for row in rows]
        return self.user_ids


    def get_tech_num(self):
        """Return the number of unique technologies in the database.
        
        Returns
        -------
        long        
        """
        if self.tech_num is not None:
            return self.tech_num
        query = "SELECT DISTINCT id FROM technologies"
        self.cur.execute(query)
        self.technology_num = self.cur.rowcount
        return self.technology_num

    def get_tech_ids(self):
        """Return a list of all technologies id in the database.
        
        Returns
        -------
        list
            A list of long.
        """
        if self.tech_ids is not None:
            return self.tech_ids
        query = "SELECT DISTINCT id FROM technologies"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.tech_ids = [row[0] for row in rows]
        return self.tech_ids

    def get_tech_mapping_dict(self):
        '''Return a mapping dict which maps technology id to its index in the lis of all tech ids.
        
        Returns
        -------
        dict
        '''
        if self.tech_mapping_dict is not None:
            return self.tech_mapping_dict
        all_tech_ids = self.get_tech_ids()
        self.tech_mapping_dict = {value: index for index, value in enumerate(all_tech_ids)}
        return self.tech_mapping_dict
    
    
    def get_all_keywords(self):
        """Return a list of all keywords.
        
        Returns
        -------
        list 
            A list of long.
        """
        if self.all_keywords is not None:
            return self.all_keywords
        query = "SELECT DISTINCT id FROM keywords"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.all_keywords = [row[0] for row in rows]
        return self.all_keywords
        
    def get_tech_keywords(self):
        """Return a dictionary whose key is technology id and whose value is a list of associated keywords.
        
        Returns
        -------
        dict 
        """
        if self.tech_keywords is not None:
            return self.tech_keywords
        query = "SELECT * FROM technology_keywords"
        self.cur.execute(query)
        self.tech_keywords = {}
        rows = self.cur.fetchall()
        for row in rows:
            if row[1] not in self.tech_keywords:
                self.tech_keywords[row[1]] = []
                self.tech_keywords[row[1]].append(row[0])
            else:
                self.tech_keywords[row[1]].append(row[0])
        return self.tech_keywords
    
    def get_user_keywords(self):
        """Return a dictionary whose key is user id and whose value is a list of associated keywords.
        
        Returns
        -------
        dict 
        """
        if self.user_keywords is not None:
            return self.user_keywords
        query = "SELECT * FROM user_keywords"
        self.cur.execute(query)
        self.user_keywords = {}
        rows = self.cur.fetchall()
        for row in rows:
            if row[1] not in self.user_keywords:
                self.user_keywords[row[1]] = []
                self.user_keywords[row[1]].append(row[0])
            else:
                self.user_keywords[row[1]].append(row[0])
        return self.user_keywords
        
        
    def get_keyword_mapping_dict(self):
        '''Return a mapping dict which maps keyword id to its index in the technology/user keyword vector.
        
        Note
        ----
        A technology id has many associated keywords. 
        A technology keyword vector of a technology id is a vector where the value of at that location of a keyword is 1 
        if this technology id has that keyword.
        
        A user keyword vector has the same principle.
        '''
        if self.keyword_mapping_dict is not None:
            return self.keyword_mapping_dict
        all_keywords = self.get_all_keywords()
        self.keyword_mapping_dict = {value: index for index, value in enumerate(all_keywords)}
        return self.keyword_mapping_dict
    
    
    def get_tech_keyword_vector(self, tech_id):
        '''Return the technology keyword vector given a technology id.
        
        Params
        ------
        tech_id: long
        
        Returns
        -------
        list
            A list of int.
        '''
        tech_keyword_vector = np.zeros(len(self.get_all_keywords()), dtype=np.int8)
        tech_keywords = self.get_tech_keywords().get(tech_id, None)
        if tech_keywords is None:       # No keywords associated with this technology
            return tech_keyword_vector
        keyword_mapping_dict = self.get_keyword_mapping_dict()
        indices = [keyword_mapping_dict[keyword] for keyword in tech_keywords]
        tech_keyword_vector[indices] = 1
        return tech_keyword_vector
    
    def get_user_keyword_vector(self, user_id):
        '''Return the user keyword vector given a user id.
        
        Params
        ------
        user_id: str
        
        Returns
        -------
        list
            A list of int.
        '''
        user_keyword_vector = np.zeros(len(self.get_all_keywords()), dtype=np.int8)
        user_keywords = self.get_user_keywords().get(user_id, None)
        if user_keywords is None:       # No keywords associated with this user
            return user_keyword_vector
        keyword_mapping_dict = self.get_keyword_mapping_dict()
        indices = [keyword_mapping_dict[keyword] for keyword in user_keywords]
        user_keyword_vector[indices] = 1
        return user_keyword_vector    
    
    def get_score_data(self):
        """Returns the score table.
        
        Returns
        -------
        DataFrame
            A table which contains columns user_id, technology_id, total_score.
        """
        self.scoreData = pd.read_sql("SELECT user_id, technology_id, total_score FROM score", con = self.con)        
        return self.scoreData
    
    def get_interacted_tech_ids(self, user_id):
        """Return a list of technology ids with which this user has interacted.
        
        Params
        ------
        user_id: str
        
        Returns
        -------
        list
        """         
        query = "SELECT technology_id FROM score WHERE user_id = '%s'" % user_id
        self.cur.execute(query)              
        rows = self.cur.fetchall()
        return [row[0] for row in rows]
     
    def get_contacted_tech_ids (self, user_id):
        """Return a list of contacted technology ids given a user id.
        
        Returns
        -------
        list
            A list of long.
        """
        query ="SELECT technology_id FROM contacts WHERE user_id = '%s'" % user_id
        self.cur.execute(query) 
        rows = self.cur.fetchall() 
        return [row[0] for row in rows]
    
    
    def get_clicked_tech_ids (self, user_id):
        """Return a list of clicked technology ids in all emails containing recommended tech ids given a user id.
        
        Returns
        -------
        list
            A list of long.
        """
        query ="SELECT clicked_technology_id FROM email_clicks WHERE user_id = '%s'" % user_id
        self.cur.execute(query) 
        rows = self.cur.fetchall() 
        return [row[0] for row in rows]
    
    def get_university_tech_ids(self, university_id):
        """Return a list of technology ids associated with this given university id.
        
        Returns
        -------
        list
            A list of long.
        """
        query = "SELECT id FROM technologies WHERE university_profile_id = '%s'" % university_id   
        self.cur.execute(query)
        rows = self.cur.fetchall()
        return [row[0] for row in rows]   
    
    def get_orphan_tech_ids(self):
        """Find orphan tech ids in user_activtivies table.
        
        Returns
        -------
        list
            tech_ids which appear in the user_activities table, but not in the technologies table
        """   
        activities = self.get_activities_table()
        viewed_tech_ids = []
        for index, row in activities.iterrows():
            start = row[1].find("Article_id") # Finding start from "Article_id"
            end = row[1].find("content")
            tech_id = int(re.search(r'\d+', row[1][start:end]).group(0))
            viewed_tech_ids.append(tech_id)     
        tech_ids = self.get_tech_ids() 
        orphan_tech_ids = list(set(tech_ids) - set(viewed_tech_ids))
        return orphan_tech_ids

    def get_contacts_table(self):
        """Return the contact table.
        
        Returns
        -------
        DataFrame 
            A table which contains columns user_id, technology_id, number of contacts.
        """
        self.contacts = pd.read_sql( "SELECT user_id, technology_id , count(*) as c_count FROM contacts group by user_id, technology_id", con = self.con)    
        return self.contacts
    
    def get_clicks_table(self):
        """Return the click table.
        
        Returns
        -------
        DataFrame   
            A table which contains columns user_id, technology_id, number of clicks.
        """
        self.clicks =  pd.read_sql( "SELECT user_id, clicked_technology_id as technology_id, count(*) as e_count FROM email_clicks group by user_id, technology_id", con = self.con)
        return self.clicks

    def get_activities_table(self):
        """Return the activities table.
        
        Returns
        -------
        DataFrame   
            A table which contains columns user_id, details.
        """
        self.activities = pd.read_sql( "SELECT user_id, details FROM user_activities", con = self.con) 
        return self.activities   

