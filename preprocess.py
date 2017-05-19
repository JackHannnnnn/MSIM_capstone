# -*- coding: utf-8 -*-

import MySQLdb as mdb
import numpy as np
import pandas as pd
import re
import csv

def calculate_score(weights):
    '''Integrate implicit feedback from different sources into one explicit feedback/score used for training recommenders.
    
    Params
    ------
    weights: list
        The weights of contact data, clicked data, view data.
        
    Returns
    DataFrame
    '''
    
    # Connect to db and create a cursor for subsequent queries.
    con = mdb.connect(host='localhost', user='root', passwd="123", db="capstone")
    cur = con.cursor() 
    
    # Read implicit feedback from mysql
    contacts = pd.read_sql("SELECT user_id, technology_id , count(*) AS c_count FROM contacts GROUP BY user_id, technology_id", con=con)
    clicks =  pd.read_sql("SELECT user_id, clicked_technology_id AS technology_id, count(*) AS e_count FROM email_clicks GROUP BY user_id, technology_id", con=con)
    activities = pd.read_sql( "SELECT user_id, details FROM user_activities", con=con) 

    # Get orphan tech ids which appear in the user_activities table, but not in the technologies table
    viewed_tech_ids = []
    for index, row in activities.iterrows():
        start = row[1].find("Article_id") # Finding start from "Article_id"
        end = row[1].find("content")
        tech_id = int(re.search(r'\d+', row[1][start:end]).group(0))
        viewed_tech_ids.append(tech_id)  
    query = "SELECT DISTINCT id FROM technologies"
    cur.execute(query)
    rows = cur.fetchall()
    tech_ids = [row[0] for row in rows]
    orphan_tech_ids = list(set(viewed_tech_ids) - set(tech_ids))
    
    technology_id = viewed_tech_ids
    
    # Add one more column tech id viewed by a user (Mapping)
    activities['technology_id'] = technology_id 
    
    # Drop column detials 
    activities = activities.drop('details', 1)
    activities = activities.groupby(["user_id", "technology_id"]).size().reset_index(name = "v_count")

    # Merge implicit feedbacks into one table
    score_orig = pd.merge(contacts, clicks, how = 'outer').merge(activities, how = 'outer')
    score = score_orig[-score_orig['technology_id'].isin(orphan_tech_ids)].reset_index(drop=True)

    # Create training and test data set
    np.random.seed(seed=13579)
    n = len(score)
    rand_order = np.arange(n)
    np.random.shuffle(rand_order)
    score['whether_train'] = np.zeros(len(score))
    train_index = list(rand_order[:int(n*.66)])
    score.loc[train_index, 'whether_train'] == 1

    # Calculate the score used for training recommenders like Collaborative filtering, Latent factor model etc.
    weights = np.array([weights]).T
    score["total_score"] = score[['c_count', "e_count", "v_count"]].fillna(0).dot(weights).sum(axis=1) 
    # Use -1 to indicate null value 
    score = score.replace(np.nan, -1)
    # Add primary key column: score_id
    score.index +=1
    score.index.name = 'score_id'
    score.reset_index(inplace=True) 
    return score
   
    
def create_table(score):
    """Create a Score table and Import the score data.
    
    Params
    ------
    score: DataFrame
    """
    # Drop score table if exists
    con = mdb.connect(host='localhost', user='root', passwd="123", db="capstone")
    cur = con.cursor()
    query = 'DROP TABLE IF EXISTS Score'
    cur.execute(query)

    print 'Start...'
    cur.execute('''create table Score(
                        score_id int, 
                        user_id varchar(220), 
                        technology_id int,
                        contact_score float,
                        clicked_score float,
                        viewed_score float,                    
                        whether_train int,
                        total_score float)''')
    # Write dataframe to a local csv and then write back to sql
    score.to_csv('score.csv', sep=',', index = False, header =False  )
    csv_data = csv.reader(file('score.csv'))

    # Iterate rows in csv file
    for row in csv_data:    
        cur.execute('INSERT INTO score VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', row)
    # Use null to replace -1
    cur.execute('UPDATE score SET contact_score = null WHERE contact_score= -1')
    cur.execute('UPDATE score SET clicked_score = null WHERE clicked_score= -1')    
    cur.execute ('UPDATE score SET viewed_score = null WHERE viewed_score= -1')
    # Close the connection to the database.
    con.commit()

    print "Done."

if __name__ == '__main__':
    score = calculate_score([5, 1, 2])
    create_table(score)

