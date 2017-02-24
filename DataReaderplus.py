import MySQLdb as mdb
import sys
import numpy as np
import re
import pandas as pd

class DataReader(object):
    def __init__(self):
        self.con = mdb.connect(host = 'localhost', user = 'root', passwd = "1234", db = "capstone") 
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
        query3 = "SELECT * FROM keywords"
        self.cur.execute(query3)
        self.keywords = [] # store all the keywords
        rows = self.cur.fetchall()
        for row in rows:
            self.keywords.append(row[0])
        return self.keywords
        

    def technology_keywords(self, keywords, technology_id):
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
        """given technology_keywords (dictionary of all technology ids and its corresponding keywords) and some specific technology_id (int), return a technology keywords 0-1 mapping list"""
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
    
    def get_contentview(self, user_id):
        """given one user id, find all his/her content view (id of technology). Return a list of technology ids """
        query6 = "SELECT details FROM user_activities WHERE user_id =" + "'" +  user_id + "'" 
        self.cur.execute(query6)
        this_content = []
        rows = self.cur.fetchall()
        for row in rows: # calculate score for "content_view"
            # print row
            detail = row[0]
            # print detail
            start_index = detail.find("Article_id") # finding start from "Article_id"
            article_id = int(re.search('\d+', detail[start_index:]).group(0)) # return the first matched group -- technilogy id for this user
            this_content.append(article_id)
        return this_content
    
     
    def get_tech_clicked(self, user_id):
        """given one user id, find all his/her email_clicks (id of technology). Return a list of technology ids """
        query7 = "SELECT * FROM email_clicks" 
        self.cur.execute(query7)
        user_click = []
        rows = self.cur.fetchall()
        for row in rows: # each click record"
            #print row
            if row[3] == user_id:
                clicked = row[4]
                user_click.append (clicked)
            
        #print user_click     
        return user_click 
    
    def get_contacted(self,user_id):
        """given one user id, find all his/her contacted technology ids. Return a list of technology ids """
    
        query8 = "SELECT * FROM contacts"
        self.cur.execute(query8)
        user_contact = []
        rows = self.cur.fetchall()
        #print rows
        for row in rows: # each contact record
            if row[1] == user_id:
                contacted = row[2]
                #print contacted
                user_contact.append(contacted)
        return user_contact
    
    def get_score_data(self):
        """return the score table with user_id, technology_id, total_score  """
        scoreData = pd.read_sql("SELECT user_id, technology_id, total_score FROM score", con = con)        
        return scoreData
    
     
#print DataReader().get_user_num()
#print DataReader().get_user_id()
#print DataReader().get_technology_num()
#print DataReader().get_technology_id()
#technology_id = DataReader().get_technology_id()      # test function get_technology_id()
#print DataReader().find_techid_index(870, technology_id)
#user_id = DataReader().get_user_id()          # test function get_user_id
#print DataReader().find_userid_index('58518963-b814-4df9-a49d-03900a2a839b', user_id)
#keywords =  DataReader().get_all_keywords()
#print DataReader().technology_keywords(keywords, 870)
#print DataReader().get_contentview('5260234c-9878-4d49-9d26-46b2d4718e13')   #test get_contentview
#print DataReader().get_tech_clicked('57d97d4a-23b8-4148-a0a5-004a0a2ae3a6')  #test get_tech_clicked
#print DataReader().get_contacted('56c31212-73e0-43b9-9195-02080a2a6be7')     #test get_contacted
#print DataReader().get_score_data()                                          #test get_score_data

def find_techid_index(this_tech_id, technology_id):
    """ given a list of technology id, list of all ids for technologies. Find the technology id index (natural number)"""
    techid_index = []
    for id in this_tech_id:
        index =  technology_id.index(id)
        techid_index.append(index)
    return techid_index

def find_userid_index(this_user_id, user_id):
    """ given a user id (str), list of all ids for users. Find the user id index (natural number)"""
    user_index =  user_id.index(this_user_id)
    return user_index



def technology_user_score(user_num, technology_num, user_id, technology_id):
    """given the total number of users and technologies, return the score matrix. ongoing."""
    score = np.zeros((user_num, technology_num)) # initiate the 2d array
    for i in range(len(user_id)):
        # print range(len(user_id))
        content_list = DataReader().get_contentview(user_id[i]) # return a list of technologies this user viewed
        if content_list: # if the list if not null, then do the following operation
            print 'aaa'
            techid_index = find_techid_index(content_list, technology_id) # change technology id into natural number
            score[i, techid_index] += 1 # change 1 according to weight
    return score
# np.set_printoptions(threshold='nan') # show all values in array when it is too long

# test technology_user_score
technology_id = DataReader().get_technology_id()  
#print technology_id
user_id = DataReader().get_user_id()[:1]  # test with the first user id
technology_num = DataReader().get_technology_num()
user_num = DataReader().get_user_num()



#print user_id[:1] # this returns a list. user_id[0] returns a value.
#print technology_id 
#print technology_user_score(user_num, technology_num, user_id, technology_id)




