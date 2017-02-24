# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import MySQLdb as mdb
import sys
import numpy as np
import re
import pandas as pd

con = mdb.connect(host = 'localhost', 
                 user = 'root', 
                 passwd = '1234', 
                 db = 'capstone')
cur = con.cursor()


#read tables from mysql
contacts = pd.read_sql( "SELECT user_id, technology_id , count(*) as c_count FROM contacts group by user_id, technology_id", con = con)    
clicks =  pd.read_sql( "SELECT user_id, clicked_technology_id as technology_id, count(*) as e_count FROM email_clicks group by user_id, technology_id", con = con)
activities = pd.read_sql( "SELECT user_id, details FROM user_activities", con = con) 
# extract technology_id from details
technology_id = []
for index, row in activities.iterrows():
    start = row[1].find("Article_id") # finding start from "Article_id"
    end = row[1].find("content")
    tech_id = int(re.search(r'\d+', row[1][start:end]).group(0))
    technology_id.append(tech_id)
    
#mapping tech_id with user_id   
activities['technology_id'] = technology_id 
#drop column detials 
activities = activities.drop('details', 1)
activities = activities.groupby(["user_id", "technology_id"]).size().reset_index(name = "v_count")

#dfs outer joins

score = pd.merge(contacts, clicks, how = 'outer').merge(activities, how = 'outer')

#df split train/test
np.random.seed(seed = 13579)
n = len(score)
#print n
rand_order = np.arange(0,n)
np.random.shuffle(rand_order)
score['whether_train'] = np.zeros(len(score))
train_index = list(rand_order[:int(n*.66)])
score.loc[train_index, 'whether_train'] = 1

#############################weight##############
weight = np.array([[1, 1, 1]]).T
#################################################

#add total_score
score["total_score"] = score[['c_count', "e_count", "v_count"]].fillna(0).dot(weight).sum(1) 
 
#use -1 to mark null value 
score = score.replace(np.nan, -1)

#add score_id as index
score.index +=1
score.index.name = 'score_id'
score.reset_index(inplace =True) 


####################################################################################
#create mysql table score 


cur.execute('''create table Score(
                    score_id int, 
                    user_id varchar(220), 
                    technology_id int,
                    contact_score float,
                    clicked_score float,
                    viewed_score float,                    
                    whether_train int,
                    total_score float)''')


#write score back to sql

import csv
#write dataframe to local csv
score.to_csv('score.csv', sep=',', index = False, header =False  )
csv_data = csv.reader(file('score.csv'))

#iterate rows in csv file
for row in csv_data:    
    cur.execute('INSERT INTO score VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', row)
#use null to replace -1
cur.execute('UPDATE score SET contact_score = null WHERE contact_score= -1')
cur.execute('UPDATE score SET clicked_score = null WHERE clicked_score= -1')    
cur.execute ('UPDATE score SET viewed_score = null WHERE viewed_score= -1')
#close the connection to the database.
con.commit()
 
print "Done"
#csv_data.to_sql=(con = con, name='<score>', if_exists='replace')
#from pandas.io import sql
#sql.write_frame(score, con=con, name = 'score', if_exists = "replace")

