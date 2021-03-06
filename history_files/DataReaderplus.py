import MySQLdb as mdb
import sys
import numpy as np
import re
import pandas as pd

class DataReader(object):
    def __init__(self):
        """construction function. Initiate and connect to db"""
        self.con = mdb.connect(host = 'localhost', user = 'root', passwd = "123", db = "capstone") 
        self.cur = self.con.cursor() # the cursor object will let you execute all the queries you need

    def get_user_num(self):
        """return the number of unique users """
        query1 = "SELECT * FROM users"
        self.cur.execute(query1)
        # store number of users from users id count
        self.user_num =  self.cur.rowcount
        return self.user_num

    def get_user_id(self):
        """ return the list of all user ids in the database"""
        query1 = "SELECT * FROM users"
        self.cur.execute(query1)
        self.user_id = [] # array of all user id
        rows = self.cur.fetchall()
        for row in rows:
            self.user_id.append(row[0])
        return self.user_id

    def get_technology_num(self):
        """ return number of unique technologies in the database """
        query2 = "SELECT * FROM technologies"
        self.cur.execute(query2)
        self.technology_num = self.cur.rowcount # store number of technologies from technology id count
        return self.technology_num

    def get_technology_id(self):
        """ return the list of all technologies id in the database """
        query2 = "SELECT * FROM technologies"
        self.cur.execute(query2)
        self.technology_id = [] # array of all technology id
        rows = self.cur.fetchall()
        for row in rows:
            self.technology_id.append(row[0])
        return self.technology_id
    
    def get_all_keywords(self):
        """return a list of all keywords"""
        query3 = "SELECT * FROM keywords"
        self.cur.execute(query3)
        self.keywords = [] # store all the keywords
        rows = self.cur.fetchall()
        for row in rows:
            self.keywords.append(row[0])
        return self.keywords
        
    def technology_keywords(self):
            """ return the dictionary, which key is technology id and value is a list of keywords """
            query4 = "SELECT * FROM technology_keywords"
            self.cur.execute(query4)
            self.technology_keywords = {}
            rows = self.cur.fetchall()
            for row in rows:
                if row[1] not in self.technology_keywords:
                    self.technology_keywords[row[1]] = []
                    self.technology_keywords[row[1]].append(row[0])
                else:
                    self.technology_keywords[row[1]].append(row[0])
            return self.technology_keywords

    def cal_technology_keywords(self, keywords, technology_id):
        """
        Map each technology keywords to the keywords library. Return binary list

        parameters: 
        -----------
        keywords: dictionary
            given technology_keywords (dictionary of all technology ids and its corresponding keywords) 
        technology_id: int
            some specific technology_id (int)
        return
        -----------
        this_matching_list: np.array
             a technology keywords 0-1 mapping list used for content-based algorithm
        """
        query5 = "SELECT keyword_id FROM technology_keywords WHERE technology_id =" + str(technology_id)
        self.cur.execute(query5)
        rows = self.cur.fetchall()
        this_keywords_list = [] # list of keywords for this technology
        for row in rows:
            this_keywords_list.append(row[0])
        index_dict = dict((value, idx) for idx, value in enumerate(keywords))
        # return the index of each keyword id for this technology in the full list of keywords
        index_list = [index_dict[x] for x in this_keywords_list] 
        this_matching_list = np.zeros(len(keywords))  # initialize the matching list of this technology 
        this_matching_list[index_list] = 1 # set value equals 1 if this technology has some certain keyword
        # np.set_printoptions(threshold='nan') # print all values in array when it is too long
        return np.array(this_matchinglist)
    
    def get_user_keywords (self, user_id):
        
        """
        given user id, return user keywords

        parameters
        -----------
        user_id: str
            id of user
        return 
        --------
        user_keywords: list
            all keywords for the input user_id
        """
        query11 ="SELECT keyword_id FROM user_keywords WHERE user_id = '%s'" %(user_id)
        self.cur.execute (query11) 
        rows = self.cur.fetchall() 
        user_keywords= []        
        for row in rows:
            user_keywords.append(row[0])                             
        return user_keywords

    def cal_user_keywords(self, keywords, user_id):
        """
        mapping user keywords with all keywords return, binary vector
        
        parameters:
        -----------
        keywords: dictionary
            given technology_keywords (dictionary of all technology ids and its corresponding keywords)
        user_id: string
        return
        -----------
        this_matchinglist: np.array
            a user keywords 0-1 mapping list used for content-based algorithm
        """     
        user_keywords = self.get_user_keywords(user_id)
        index_dict = dict((value, idx) for idx, value in enumerate(keywords))
        index_list = [index_dict[x] for x in user_keywords] # return the index of each keyword id for this technology in the full list of keywords
        this_matchinglist = np.zeros(len(keywords))  # initialize the matching list of this technology 
        this_matchinglist[index_list] = 1 # set value equals 1 if this technology has some certain keyword
        # np.set_printoptions(threshold='nan') # print all values in array when it is too long
        return np.array(this_matchinglist)
    
    

    def get_score_data(self):
        """
        return 
        -------
        scoreData: table
            the score table with user_id, technology_id, total_score  """
        self.scoreData = pd.read_sql("SELECT user_id, technology_id, total_score FROM score", con = self.con)        
        return self.scoreData
    
    def get_contacts_table(self):
        """
        return
        --------
        contacts: table 
            table for contacts which contain columns user_id, technology_id, number of records
        """
        self.contacts = pd.read_sql( "SELECT user_id, technology_id , count(*) as c_count FROM contacts group by user_id, technology_id", con = self.con)    
        return self.contacts
    
    def get_clicks_table(self):
        """
        return
        --------
        clicks: table   
            table for clicks which contain columns user_id, technology_id, number of records
        """
        self.clicks =  pd.read_sql( "SELECT user_id, clicked_technology_id as technology_id, count(*) as e_count FROM email_clicks group by user_id, technology_id", con = self.con)
        return self.clicks

    def get_activities_table(self):
        """
        return
        --------
        activities: table   
            table for activities which contain columns user_id, details
        """
        self.activities = pd.read_sql( "SELECT user_id, details FROM user_activities", con = self.con) 
        return self.activities
    
    def extract_interacted_technology(self, user_id):
        """ 
        return
        -------
        tech_id_list: list
            the list of all technology ids which have interaction with the user
        """         
        query6 = "SELECT technology_id FROM score WHERE user_id = '%s'" %(user_id)
        self.cur.execute(query6)              
        rows = self.cur.fetchall()    
        tech_id_list = []
        for row in rows:
            tech_id_list.append(row[0])
        return tech_id_list
    
    def extract_interacted_keywords(self, user_id):
        """ 
        return 
        ------
        keywords_list: list
            the list of all keywords which have interaction with the user"""         
        tech_id_list = self.extract_interacted_technology(user_id)
        query7 ="SELECT * FROM technology_keywords"  
        self.cur.execute (query7) 
        rows = self.cur.fetchall() 
        keywords_list = []        
        for row in rows:
            if row[1] in tech_id_list:
                keywords_list.append(row[0])             
        return keywords_list
    
    
    def extract_keywords(self, technology_id):
        """ 
        return 
        ------
        keywords_list: list
            keywords of given technology id
        """         
        query8 ="SELECT keyword_id FROM technology_keywords WHERE technology_id = '%s'" %(technology_id)
        self.cur.execute (query8) 
        rows = self.cur.fetchall() 
        keywords_list = []        
        for row in rows:
            keywords_list.append(row[0])             
        return keywords_list
    
    
    def get_contacted_tech_ids (self, user_id):
        
        """
        return 
        -------
        contacted_tech_ids: list
            contacted technology_ids while input user_id
        """
        query9 ="SELECT technology_id FROM contacts WHERE user_id = '%s'" %(user_id)
        self.cur.execute (query9) 
        rows = self.cur.fetchall() 
        contacted_tech_ids = []        
        for row in rows:
            contacted_tech_ids.append(row[0])             
        return contacted_tech_ids
    
    
    def get_emailed_tech_ids (self, user_id):
        """
        return
        --------
        emailed_tech_ids: list
            contacted technology_ids while input user_id
        """
        query10 ="SELECT included_technology_ids FROM email_clicks WHERE user_id = '%s'" %(user_id)
        self.cur.execute (query10) 
        rows = self.cur.fetchall() 
        included_tech_ids = []        
        for row in rows:
            split_tech_ids = row[0].split(',') 
            included_tech_ids = list(map(int,split_tech_ids))
            included_tech_ids.extend(included_tech_ids)   
        emailed_tech_ids = list(set(included_tech_ids))                 
        return emailed_tech_ids
    
    
    def get_clicked_tech_ids (self, user_id):
        
        """
        return 
        ------
        clicked_tech_ids: list
            clicked technology_ids from email list while input user_id
        """
        query7 ="SELECT clicked_technology_id FROM email_clicks WHERE user_id = '%s'" %(user_id)
        self.cur.execute (query7) 
        rows = self.cur.fetchall() 
        clicked_tech_ids = []        
        for row in rows:
            clicked_tech_ids.append(row[0])                
        return clicked_tech_ids
    
    
    def get_university_tech_ids(self, university_id):

        query12 = "SELECT id FROM technologies WHERE university_profile_id = '%s'"%(university_id)    
        self.cur.execute(query12)
        rows = self.cur.fetchall()
        tech_ids = []
        for row in rows:
            tech_ids.append(row[0])
        return tech_ids     
    
    def get_orphan_tech_ids(self):
        """find orphan tech id in user_activtivies table
        parameters:
        ----------- 
        technologies table
        user_activities table
        return:
        ------
        orphan tech_id: list
         tech_ids which are in the user_activities table, but not in the technologies table
        """   
        
        activities = self.get_activities_table()
        viewed_tech_ids = []
        for index, row in activities.iterrows():
            start = row[1].find("Article_id") # finding start from "Article_id"
            end = row[1].find("content")
            tech_id = int(re.search(r'\d+', row[1][start:end]).group(0))
            viewed_tech_ids.append(tech_id)     
        tech_ids = self.get_technology_id()    
        orphan_tech_ids = np.setdiff1d(np.array(viewed_tech_ids), np.array(tech_ids))
        return orphan_tech_ids
    

    # def get_contentview(self, user_id):
    #     """given one user id, find all his/her content view (id of technology). Return a list of technology ids """
    #     query6 = "SELECT details FROM user_activities WHERE user_id =" + "'" +  user_id + "'" 
    #     self.cur.execute(query6)
    #     this_content = []
    #     rows = self.cur.fetchall()
    #     for row in rows: # calculate score for "content_view"
    #         # print row
    #         detail = row[0]
    #         # print detail
    #         start_index = detail.find("Article_id") # finding start from "Article_id"
    #         article_id = int(re.search('\d+', detail[start_index:]).group(0)) # return the first matched group -- technilogy id for this user
    #         this_content.append(article_id)
    #     return this_content
    
     
    
    
    #
# def find_techid_index(this_tech_id, technology_id):
#     """ given a list of technology id, list of all ids for technologies. Find the technology id index (natural number)"""
#     techid_index = []
#     for id in this_tech_id:
#         index =  technology_id.index(id)
#         techid_index.append(index)
#     return techid_index

# def find_userid_index(this_user_id, user_id):
#     """ given a user id (str), list of all ids for users. Find the user id index (natural number)"""
#     user_index =  user_id.index(this_user_id)
#     return user_index





