import MySQLdb as mdb
import sys
import numpy as np
import re
import pandas as pd

class DataReader(object):
    def __init__(self):
        self.con = mdb.connect(host = 'localhost', user = 'root', passwd = "123", db = "capstone") 
        self.cur = self.con.cursor() # the cursor object will let you execute all the queries you need
        # self.user_num = 0

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
        parameters: 
        -----------
        keywords: dictionary
            given technology_keywords (dictionary of all technology ids and its corresponding keywords) 
        technology_id: int
            some specific technology_id (int)
        return
        -----------
        this_matchinglist: np.array
             a technology keywords 0-1 mapping list used for content-based algorithm
        """
        query5 = "SELECT keyword_id FROM technology_keywords WHERE technology_id =" + str(technology_id)
        self.cur.execute(query5)
        rows = self.cur.fetchall()
        this_keywords_list = [] # list of keywords for this technology
        for row in rows:
            this_keywords_list.append(row[0])
        index_dict = dict((value, idx) for idx, value in enumerate(keywords))
        index_list = [index_dict[x] for x in this_keywords_list] # return the index of each keyword id for this technology in the full list of keywords
        this_matchinglist = np.zeros(len(keywords))  # initialize the matching list of this technology 
        this_matchinglist[index_list] = 1 # set value equals 1 if this technology has some certain keyword
        # np.set_printoptions(threshold='nan') # print all values in array when it is too long
        return np.array(this_matchinglist)
    
    def get_user_keywords (self, user_id):
        
        """
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
    

    def get_techID_by_university(self, university_id):
    	"""
    	return
    	------
    	technology_ids: list
    		All technology IDs published by the given universeity_id 
    	"""
    	technology_ids = []
    	query14 = "SELECT DISTINCT id FROM capstone.technologies where university_profile_id = '%s'"%(university_id)
    	self.cur.execute(query14)
    	rows = self.cur.fetchall()
    	for row in rows:
    		technology_ids.append(row[0])
    	return technology_ids

    def get_user_views(self, technology_ids):
    	"""
    	return 
    	------
    	tech_views: list of dictionary
			A list of dictionary with the key being the technology ID and the value being the count of views on the technology
    	"""
    	tech_views = []
    	query12 = "SELECT technology_id, sum(viewed_score) as views FROM score WHERE technology_id IN (" +", ".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ") GROUP BY technology_id"
    	self.cur.execute(query12)
    	rows = self.cur.fetchall()
    	for row in rows:
    		tech_views.append({"TechID": row[0], "Views": row[1]})
    	return tech_views

    def get_user_views_all(self):
        """
        return 
        ------
        tech_views: list of dictionary
            A list of dictionary with the key being the technology ID and the value being the count of views on the technology
        """
        tech_views_all = []
        query15 = "SELECT technology_id, sum(viewed_score) as views FROM " \
                  "score GROUP BY technology_id"
        self.cur.execute(query15)
        rows = self.cur.fetchall()
        for row in rows:
            tech_views_all.append({"TechID": row[0], "Views": row[1]})
        return tech_views_all

    def get_user_keywords_of_viewed_tech (self, technology_ids):
    	"""
    	return 
    	------
    	ukey_obj: dictionary
    		a dictionary showing the hierarchy of user keywords under each technology
    	"""
    	ukey_tech = {}
        ukey_obj = {"name": "technologies", "children": []}
    	# ukey_list = []
    	query13 = "SELECT S.technology_id, U.keyword_id, COUNT(*) AS CNT FROM " \
                  "score as S RIGHT JOIN user_keywords AS U " \
                  "ON S.user_id = U.user_id " \
                  "WHERE S.technology_id " \
                  "IN (" +", ".join(['%s']*len(technology_ids)) \
                          % tuple(technology_ids) + ") " \
                  "AND S.viewed_score IS NOT NULL " \
                  "GROUP BY S.technology_id, U.keyword_id " \
                  "ORDER BY S.technology_id, CNT DESC"
    	self.cur.execute(query13)
    	rows = self.cur.fetchall()
    	i = 0
        for row in rows:
            if row[0] not in ukey_tech:
                ukey_tech[row[0]] = [{"name": row[1], "size": row[2]}]
                i = 1
            elif i<10:
                ukey_tech[row[0]].append({"name": row[1], "size": row[2]})
                i += 1 
            else:
                pass
    	for key, value in ukey_tech.iteritems():
            ukey_obj["children"].append({"name": key, "children": value})
    	
    	return ukey_obj

    def get_tech_keywords(self, technology_ids):
    	"""
    	return
    	------
    	keywords: list of dictionary
    		a list of dictionary with the keys being the keyword and the value being the count of occurence
    	"""
    	keywords = []
    	query14 = "SELECT K.keyword_id, COUNT(*) AS CNT FROM technologies AS T LEFT JOIN technology_keywords AS K ON T.id = K.technology_id WHERE T.id IN (" +", ".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ") GROUP BY K.keyword_id ORDER BY CNT DESC"
    	self.cur.execute(query14)
    	rows = self.cur.fetchall()
    	for row in rows:
    		keywords.append({"keyword": row[0], "Count": row[1]})
    	return keywords


    def get_tech_viewed_user(self, technology_ids):
        """
        return
        ------
        viewed_users: list of dictionary
            a list of dictionary showing the technology id and associated user id
        """
        viewed_users = {}
        viewed_users_list = []
        query15 = "SELECT S.technology_id, U.user_id FROM score as S RIGHT JOIN user_keywords AS U on S.user_id = U.user_id WHERE S.technology_id IN (" + ", ".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ") AND S.viewed_score IS NOT NULL GROUP BY S.technology_id, U.user_id"
        self.cur.execute(query15)
        rows = self.cur.fetchall()
        # for row in rows:
        #     if row[0] in viewed_users:
        #         viewed_users[row[0]].append(row[1])
        #     else:
        #         viewed_users[row[0]] = [row[1]]
        for row in rows:
            viewed_users_list.append({"Technology": row[0], "Company": row[1]})
        # for key, value in viewed_users.iteritems():
        #     viewed_users_list.append({"Technology": key, "Company": value})
        return viewed_users_list


    def email_sent_vs_click(self, technology_ids):
        """
        return 
        ------
        emails: list of dictionary
            a list of dictionary showing number of email sent and number of email clicks associated with each technology
        -----
        """
        emails = []
        query16 = "SELECT SENT.*, CLICK.CLICK " \
                  "FROM " \
                  "(SELECT T.technology_id, count(E.user_id) AS SENT " \
                  "FROM emails AS E " \
                  "LEFT JOIN email_technologies AS t " \
                  "ON E.id = T.email_id " \
                  "GROUP BY T.technology_id) AS SENT " \
                  "LEFT JOIN " \
                  "(SELECT clicked_technology_id, count(event) as CLICK " \
                  "FROM email_clicks GROUP BY clicked_technology_id) AS CLICK " \
                  "ON SENT.technology_id = CLICK.clicked_technology_id " \
                  "WHERE SENT.technology_id in (" + ",".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ")"
        self.cur.execute(query16)
        rows = self.cur.fetchall()
        for row in rows:
            emails.append({"Technology": row[0], "Emails Sent": row[1], "Emails Clicked": row[2]})
   
        return emails


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





