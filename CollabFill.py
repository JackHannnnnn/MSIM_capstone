# -*- coding: utf-8 -*-
"""
Author: Yao Zhou
"""
import pandas as pd
import numpy as np
import ScoreCalculate as sc
import DataReaderplus as dr
import math
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse


scoreData = dr.DataReader().get_score_data() # read data from the Score table
score_df = scoreData.pivot(index='user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
score_df = score_df.fillna(0) # fill NaN data with 0
score_spare = sparse.csr_matrix(score_df) 
similarities = cosine_similarity(score_spare) # pairwise cosine similarity
similarities_df = pd.DataFrame(similarities, columns=score_df.index, index = score_df.index)

"""
Given a user and an item to rate, predict the ratings of the user on the item
"""
def rating_predict(user, item):
    # find all users who have rated the item, return a user list
    userls = rated_users(item)
    # find the similarity betwen the user and each user in the user list
    sim_urs = similarities_df.loc[user, userls]
    # find the score of similar users on the given item
    sim_scores = score_df.loc[userls, item]
    # predict rating of the user based on the weighted rating of similar users
    score_pred = np.sum(sim_urs*sim_scores)/np.sum(sim_scores)
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
print score_pred_df.head


#pred_df = pd.DataFrame({index:score_df.loc[index].nlargest(5).index.tolist() for index in score_df.index}).T
for index in score_pred_df.index:
    pred_item = score_pred_df.loc[index] 
    print pred_item[pred_item!=0.0].nlargest(5) # find the largest 5 scores for each user