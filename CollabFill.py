
# coding: utf-8

import pandas as pd
import numpy as np
import ScoreCalculate as sc
import DataReaderplus as dr
import math
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse


score = sc.calculate_score()
sc.create_table(score)
dataReader = dr.DataReader()
scoreData = dataReader.get_score_data()# read data from the Score table
score_df = scoreData.pivot(index='user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
# calculate the baseline table 
mu = score_df.stack().mean() # average of total scores
baseline_df = score_df.copy()
for user in baseline_df.index:
    for item in baseline_df.columns:
        user_dev = score_df.loc[user].mean() - mu
        item_dev = score_df[item].mean()-mu
        baseline_df.loc[user,item] = mu + user_dev + item_dev
score_df = score_df.fillna(0) # fill missing values with 0

# get the similarity table
score_spare = sparse.csr_matrix(score_df)
similarities = cosine_similarity(score_spare)
similarities_df = pd.DataFrame(similarities, columns=score_df.index, index = score_df.index)


"""
Given a user and an item to rate, predict the ratings of the user on the item
"""
def rating_predict(user, item):
    # users who have rated the item, return a user list
    userls = rated_users(item)
    # similarity betwen the user and each user in the user list
    sim_usr = similarities_df.loc[user, userls]
    # rating of similar users 
    sim_scores = score_df.loc[userls, item]
    # baseline of similar users
    baseline_usr = baseline_df.loc[userls,item] 
    # predict rating of the user on the item
    if np.sum(sim_usr)!=0:
        score_pred =  baseline_df.loc[user,item] + np.sum(sim_usr*(sim_scores-baseline_usr))/np.sum(sim_usr) 
    else:                                         
        score_pred =  0
    return score_pred

"""
given an item, return all users in a list who have rated the item
"""
def rated_users(item):
    score = score_df[item] # score vector of the item 
    userls = score[score!=0].index.values # users that rated the item
    return userls


score_pred_df = score_df.copy()
for user in score_df.index:
    for item in score_df.columns:
        if score_df.loc[user, item]==0.0:            
            score_pred_df.loc[user, item] = rating_predict(user, item)
#print score_pred_df.head()


predResult_df = pd.DataFrame(index=score_pred_df.index, columns=range(5))
for user in score_pred_df.index:
    contactedItem = dataReader.get_contacted_tech_ids(user)
    pred_item = score_pred_df.loc[user] 
    mask = (pred_item.index).isin(contactedItem) # exclude the items user has contacted
    predResult_df.loc[user] = pred_item[~mask].nlargest(5).index.values # find the largest 5 scores for each user

predResult_df["emailed"] = np.array([dataReader.get_emailed_tech_ids(user) for user in predResult_df.index]) # add a column to show emailed items
predResult_df.to_csv("User_Based_CF.csv")


