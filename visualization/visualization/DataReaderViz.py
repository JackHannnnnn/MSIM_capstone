import MySQLdb as mdb
import sys
import numpy as np
import re
import pandas as pd

class DataReader(object):
    def __init__(self):
        self.con = mdb.connect(host = 'localhost', user = 'root', passwd = "123", db = "capstone") 
        self.cur = self.con.cursor() # the cursor object will let you execute all the queries you need

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

    def get_user_id(self):
        """ return the list of all user ids in the database"""
        if self.user_ids is not None:
            return self.user_ids
        query = "SELECT DISTINCT id FROM users"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.user_ids = [row[0] for row in rows]
        return self.user_ids
    
    def get_all_keywords(self):
        """return a list of all keywords"""
        if self.all_keywords is not None:
            return self.all_keywords

        query = "SELECT DISTINCT id FROM keywords"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.all_keywords = [row[0] for row in rows]
        return self.all_keywords
        

    def cal_technology_keywords(self, keywords, technology_id):
        """
        return
        -----------
        this_matchinglist: np.array
             a technology keywords 0-1 mapping list 
        """
        query = "SELECT keyword_id FROM technology_keywords WHERE technology_id =" + str(technology_id)
        self.cur.execute(query)
        rows = self.cur.fetchall()
        this_keywords_list = [row[0] for row in rows] # list of keywords for this technology
        # for row in rows:
        #     this_keywords_list.append(row[0])
        index_dict = dict((value, idx) for idx, value in enumerate(keywords))
        index_list = [index_dict[x] for x in this_keywords_list] # return the index of each keyword id for this technology in the full list of keywords
        this_matchinglist = np.zeros(len(keywords))  # initialize the matching list of this technology 
        this_matchinglist[index_list] = 1 # set value equals 1 if this technology has some certain keyword
        return np.array(this_matchinglist)
    
    def get_user_keywords (self, user_id):
        
        """
        return 
        --------
        user_keywords: list
            all keywords for the input user_id
        """
        query ="SELECT keyword_id FROM user_keywords WHERE user_id = '%s'" %(user_id)
        self.cur.execute (query) 
        rows = self.cur.fetchall() 
        user_keywords= [row[0] for row in rows]        
        # for row in rows:
        #     user_keywords.append(row[0])                             
        return user_keywords

    def cal_user_keywords(self, keywords, user_id):
        """
        this_matchinglist: np.array
            a user keywords 0-1 mapping list 
        """     
        user_keywords = self.get_user_keywords(user_id)
        index_dict = dict((value, idx) for idx, value in enumerate(keywords))
        index_list = [index_dict[x] for x in user_keywords] # return the index of each keyword id for this technology in the full list of keywords
        this_matchinglist = np.zeros(len(keywords))  # initialize the matching list of this technology 
        this_matchinglist[index_list] = 1 # set value equals 1 if this technology has some certain keyword
        return np.array(this_matchinglist)
   

    def get_techID_by_university(self, university_id):
    	"""
    	return
    	------
    	technology_ids: list
    		All technology IDs published by the given universeity_id 
    	"""
    	technology_ids = []
    	if university_id=="all":
    		query = "SELECT DISTINCT id FROM capstone.technologies"
    	else:
	    	query = "SELECT DISTINCT id FROM capstone.technologies where university_profile_id = '%s'"%(university_id)
    	self.cur.execute(query)
    	rows = self.cur.fetchall()
        technology_ids = [row[0] for row in rows]
    	# for row in rows:
    	# 	technology_ids.append(row[0])
    	return technology_ids

    def get_user_views(self, technology_ids):
    	"""
    	return 
    	------
    	tech_views: list of dictionary
			A list of dictionary with the key being the technology ID and the value being the count of views on the technology
    	"""
    	tech_views = []
    	query12 = "SELECT technology_id, sum(viewed_score) as views FROM score " \
                  "WHERE technology_id " \
                  "IN (" +", ".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ") " \
                  "GROUP BY technology_id ORDER BY views DESC LIMIT 50" 
    	self.cur.execute(query12)
    	rows = self.cur.fetchall()
    	for row in rows:
    		tech_views.append({"TechID": row[0], "Count": row[1]})
    	return tech_views

    def get_user_keywords_of_viewed_tech (self, technology_ids, university_id):
    	"""
    	return 
    	------
    	ukey_obj: dictionary
    		a dictionary showing the hierarchy of user keywords under each technology
    	"""
    	ukey_tech = {}
        ukey_obj = {"name": university_id, "children": []}
    	# ukey_list = []
    	query = "SELECT S.technology_id, U.keyword_id, COUNT(*) AS CNT FROM " \
                  "score as S RIGHT JOIN user_keywords AS U " \
                  "ON S.user_id = U.user_id " \
                  "WHERE S.technology_id " \
                  "IN (" +", ".join(['%s']*len(technology_ids)) \
                          % tuple(technology_ids) + ") " \
                  "AND S.viewed_score IS NOT NULL " \
                  "GROUP BY S.technology_id, U.keyword_id " \
                  "ORDER BY S.technology_id, CNT DESC"
    	self.cur.execute(query)
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
    	query = "SELECT K.keyword_id, COUNT(*) AS CNT FROM technologies AS T "\
                    "LEFT JOIN technology_keywords AS K "\
                    "ON T.id = K.technology_id WHERE T.id IN (" +", ".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ") "\
                    "GROUP BY K.keyword_id ORDER BY CNT DESC"
    	self.cur.execute(query)
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
        query = "SELECT S.technology_id, U.user_id "\
                    "FROM score as S RIGHT JOIN user_keywords AS U "\
                    "on S.user_id = U.user_id "\
                    "WHERE S.technology_id IN (" + ", ".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ") AND S.viewed_score IS NOT NULL "\
                    "GROUP BY S.technology_id, U.user_id"
        self.cur.execute(query)
        rows = self.cur.fetchall()

        for row in rows:
            viewed_users_list.append({"Technology": row[0], "Company": row[1]})
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
        query = "SELECT SENT.*, CLICK.CLICK " \
                  "FROM " \
                  "(SELECT T.technology_id, count(E.user_id) AS SENT " \
                  "FROM emails AS E " \
                  "LEFT JOIN email_technologies AS T " \
                  "ON E.id = T.email_id " \
                  "GROUP BY T.technology_id) AS SENT " \
                  "LEFT JOIN " \
                  "(SELECT clicked_technology_id, count(event) as CLICK " \
                  "FROM email_clicks GROUP BY clicked_technology_id) AS CLICK " \
                  "ON SENT.technology_id = CLICK.clicked_technology_id " \
                  "WHERE SENT.technology_id in (" + ",".join(['%s']*len(technology_ids)) % tuple(technology_ids) + ")"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        for row in rows:
            emails.append({"Technology": row[0], "Sent": row[1], "Clicked": row[2]})
        return emails


    def  email_sent_per_tech(self):
    	"""
    	return 
    	------
    	email_sent: list of dictionary
			A list of dictionary with the key being the technology ID and the value being the count of email sent for the technology
    	"""
    	email_sent = []
    	query17 = "SELECT T.technology_id, count(E.user_id) as SENT FROM emails AS E LEFT JOIN email_technologies AS T ON E.id = T.email_id GROUP BY T.technology_id Having T.technology_id is not null ORDER BY SENT DESC LIMIT 50"
    	self.cur.execute(query17)
    	query = "SELECT T.technology_id, count(E.user_id) as SENT FROM emails AS E " \
                  "LEFT JOIN email_technologies AS T " \
                  "ON E.id = T.email_id " \
                  "GROUP BY T.technology_id ORDER BY SENT DESC LIMIT 50"
    	self.cur.execute(query)
    	rows = self.cur.fetchall()
    	for row in rows:
    		email_sent.append({"TechID": row[0], "Count": row[1]})
    	return email_sent
    	
    
    def  all_contacted_keywords(self):
        """
        return
        -------
        keywords: a list of dictionary
            A list of dictionary showing all keywords appearing in the contacted technologies and the frequency of appearance
        """
    	keywords = []
    	query = "SELECT K.keyword_id, count(K.keyword_id) as Count FROM contacts as C " \
			    	"LEFT JOIN technology_keywords as K " \
			    	"ON C.technology_id = K.keyword_id " \
			    	"GROUP BY K.keyword_id ORDER BY Count DESC"
    	self.cur.execute(query)
    	rows = self.cur.fetchall()
    	for row in rows:
			keywords.append({"text": row[0], "size": row[1]})

    	return keywords
    	

