# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import ScoreCalculate as sc
import DataReaderplus as dr
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
import time

t0 = time.time()
score = sc.calculate_score()
sc.create_table(score)
dataReader = dr.DataReader()
scoreData = dataReader.get_score_data()# read data from the Score table
score_df = scoreData.pivot(index='user_id', columns = 'technology_id', values = 'total_score') # reshape score table 

# calculate the baseline table 
mu = score_df.stack().mean() # average of total scores
usr_dev = score_df.mean(axis=1) - mu 
tech_dev = score_df.mean(axis=0) - mu
                        
score_df = score_df.fillna(0) # fill missing values with 0
score_spare = sparse.csr_matrix(score_df) # get the similarity table
similarities = cosine_similarity(score_spare)

"""
Given a user and an item to rate, predict the ratings of the user on the item
"""
def rating_predict(user, item):
    # users who have rated the item, return a user list
    userls = score_df[score_df[item]!=0].index.values                      
    # similarity betwen the user and each user in the user list
    sim_usr = similarities[score_df.index.isin(userls), score_df.index.isin([user])]
    # rating of similar users 
    sim_scores = score_df.loc[userls, item]
    # baseline of similar users
    baseline_usr = usr_dev[userls] + tech_dev[item] + mu
    # predict rating of the user on the item
    if np.sum(sim_usr)!=0:
        score_pred = usr_dev[user] + tech_dev[item] + mu + np.sum(sim_usr*(sim_scores-baseline_usr))/np.sum(sim_usr)
    else:                                         
        score_pred =  0
    return score_pred

score_pred_df = score_df.copy()
for user in score_df.index:
    for item in score_df.columns:
        if score_df.loc[user, item]==0.0:            
            score_pred_df.loc[user, item] = rating_predict(user, item)


predResult_df = pd.DataFrame(index=score_pred_df.index, columns=range(5))
for user in score_pred_df.index:
    contactedItem = dataReader.get_contacted_tech_ids(user)
    pred_item = score_pred_df.loc[user] 
    mask = (pred_item.index).isin(contactedItem) # exclude the items user has contacted
    predResult_df.loc[user] = pred_item[~mask].nlargest(5).index.values # find the largest 5 scores for each user

predResult_df["emailed"] = np.array([np.intersect1d(dataReader.get_emailed_tech_ids(user), predResult_df.loc[user], assume_unique=True) for user in predResult_df.index]) # add a column to show emailed items
predResult_df.to_csv("User_Based_CF.csv")
t1 = time.time()
print "time:", t1-t0


