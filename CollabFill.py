# -*- coding: utf-8 -*-
"""
Spyder Editor

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



# create a score dataframe as test data
# score_array = np.array([[1,0,2,0], [1,1,2,1], [0,0,1,1], [0,1,1,0]])
# print score_array 
# score_df = pd.DataFrame(score_array, columns=["M1", "M2", "M3", "M4"], index=["U1", "U2", "U3", "U4"]) 
# score.iloc[0,[1,3]] = np.nan
# score.iloc[2,[0,1]] = np.nan
# score.iloc[3,[0,3]] = np.nan
# print score_df  
# score_spare = sparse.csr_matrix(score_df)
# similarities = cosine_similarity(score_spare)
# print('pairwise dense output:\n {}\n'.format(similarities))
# similarities_df = pd.DataFrame(similarities, columns=score_df.index, index = score_df.index)
# print similarities_df



"""
Given a user and an item to rate, predict the ratings of the user on the item
"""
def rating_predict(user, item):
    # find all users who have rated the item, return a user list
    userls = rated_users(item)
    # find the similarity bettwen the user and each user in the user list
    sim_urs = similarities_df.loc[user, userls].index
    # find the score of similar users on the given item
    sim_scores = score_df.loc[sim_urs, item]
    print sim_scores

"""
given an item, return all users in a list who have rated the item
"""
def rated_users(item):
    score = score_df[item] # score vector of the item 
    userls = score[score!=0].index.values # users that rated the item
    return userls

# """
# given a score vector for an item, centralize the score by substracting average score
# from each score value
# """
# def score_centralization(score):
#     cnt_score = len(score[score!=0]) # the count of items with score
#     avg_score = score.sum()/cnt_score # average score
#     print "average", avg_score
#     score[score!=0] = score[score!=0] - avg_score
#     print "centralized score:", score


user = "5260234c-9878-4d49-9d26-46b2d4718e13"
item = 17
rating_predict(user,item)



