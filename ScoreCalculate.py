# -*- coding: utf-8 -*-

import DataReaderplus as dr
import MySQLdb as mdb
import numpy as np
import pandas as pd
import re
import csv

def calculate_score():
    #read tables from mysql
    contacts = dr.DataReader().get_contacts_table()
    clicks =  dr.DataReader().get_clicks_table()
    activities = dr.DataReader().get_activities_table()
    orphan_tech_ids = dr.DataReader().get_orphan_tech_ids()
    # extract technology_id from details
    technology_id= []
    for index, row in activities.iterrows():
        start = row[1].find("Article_id") # finding start from "Article_id"
        end = row[1].find("content")
        tech_id = int(re.search(r'\d+', row[1][start:end]).group(0))
        technology_id.append(tech_id)
    
        
    #mapping tech_id with user_id   
    activities['technology_id'] = technology_id 
    #drop column detials 
    activities = activities.drop('details', 1)
    #
    activities = activities.groupby(["user_id", "technology_id"]).size().reset_index(name = "v_count")

    #dfs outer joins

    score_orig = pd.merge(contacts, clicks, how = 'outer').merge(activities, how = 'outer')
    score = score_orig[-score_orig['technology_id'].isin(orphan_tech_ids)].reset_index(drop=True)

    #df split train/test
    np.random.seed(seed = 13579)
    n = len(score)
    #print n
    rand_order = np.arange(0,n)
    np.random.shuffle(rand_order)
    score['whether_train'] = np.zeros(len(score))
    train_index = list(rand_order[:int(n*.66)])
    score.loc[train_index, 'whether_train'] == 1

    #############################weight##############
    weight = np.array([[5, 1, 2]]).T
    #################################################

    #add total_score
    score["total_score"] = score[['c_count', "e_count", "v_count"]].fillna(0).dot(weight).sum(1) 
    #use -1 to mark null value 
    score = score.replace(np.nan, -1)
    #add score_id as index
    score.index +=1
    score.index.name = 'score_id'
    score.reset_index(inplace =True) 
    return score
   
def create_table(score):
    """ create mysql table score and insert into database"""
    #drop score table if exists
    con = mdb.connect(host = 'localhost', user = 'root', passwd = "1234", db = "capstone")
    cur = con.cursor()
    query = 'DROP TABLE IF EXISTS score'
    cur.execute(query)
    print "Score Table is dropped" 

    cur.execute('''create table Score(
                        score_id int, 
                        user_id varchar(220), 
                        technology_id int,
                        contact_score float,
                        clicked_score float,
                        viewed_score float,                    
                        whether_train int,
                        total_score float)''')
    #write dataframe to local csv and then write back to sql
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

    print "Done. Table Inserted"
    #csv_data.to_sql=(con = con, name='<score>', if_exists='replace')
    #from pandas.io import sql
    #sql.write_frame(score, con=con, name = 'score', if_exists = "replace")


score = calculate_score()
create_table(score)
