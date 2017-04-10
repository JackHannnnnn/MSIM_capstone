# -*- coding: utf-8 -*-
"""
Created on Sun Mar 12 18:27:34 2017

@author: Wen Qin
"""

import pandas as pd
import numpy as np
import ScoreCalculate as sc
import DataReaderplus as dr
import math
import itertools
import time
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse

# Create Score table and write score table back to MySQL database
# score=calculate_score()
# create_table(score)

scoreData = dr.DataReader().get_score_data() # read data from the Score table
score_df = scoreData.pivot(index='user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
score_df = score_df.fillna(0) # fill NaN data with 0

# Calculate Technology based similarity
score_df_t=score_df.T
score_spare_t = sparse.csr_matrix(score_df_t) 

similarities_tech = cosine_similarity(score_spare_t)
similarities_tech_df = pd.DataFrame(similarities_tech, columns=score_df_t.index, index = score_df_t.index)

# Create a list of user_ids and tech_ids which are available in scoreData
user_ids = scoreData['user_id'].unique()
tech_ids = scoreData['technology_id'].unique()

# Calculate mean of all ratings, mean rating given by each user and mean rating given to each technology
all_mean=np.mean(scoreData['total_score'])
avg_user={}
for user in user_ids:
    avg_user[user]=np.mean(scoreData[scoreData['user_id']==user]['total_score'])-all_mean
    
avg_tech={}
for tech in tech_ids:
    avg_tech[tech]=np.mean(scoreData[scoreData['technology_id']==tech]['total_score'])-all_mean


# Create a dictionary storing baseline
# Create a dictionary storing prediction, the key is tuple(user_id, tech_id)

# start=time.time()
# count=0
base_line={}
prediction={}
for i in itertools.product(user_ids,tech_ids):
    prediction[i]=score_df.ix[i[0],i[1]]
    base_line[i]=avg_user[i[0]]+avg_tech[i[1]]+all_mean
    if prediction[i]==0:
        numerator=sum((score_df.ix[i[0]]-base_line[i])*similarities_tech_df.ix[i[1]])
        denominator=sum(similarities_tech_df.ix[i[1]])-1
        if denominator==0:
            prediction[i]=0
        else:
            prediction[i]=base_line[i]+numerator/float(denominator)
#            count+=1
#            if count%1000==0:
#                print count
#                print "Time taken " +str((time.time()-start)/60)


# Create a dict storing the technology ids each user has contacted before
user_contact={}
for user in user_ids:
    user_contact[user]=np.array(dr.DataReader().get_contacted_tech_ids(user))

# Decompose the dict into a list of tuples. Each tuple is a pair of user_id and contacted technology_id
tuple_list = [(uid, tech_id) for uid, tech_list in user_contact.items() if tech_list.shape[0] != 0 for tech_id in tech_list]

# Set the prediction of contacted technologies into infinitely small
# So that when sorting, they will not be recommended
for tl in tuple_list:
    prediction[tl]=-float("inf")

# Unstack the prediction dict into prediction data frame
idx=pd.MultiIndex.from_tuples(prediction.keys())
prediction_df=pd.DataFrame(list(prediction.values()),index=idx,columns=['Technology_id']).unstack(fill_value=0)['Technology_id']
print prediction_df
# Generate predictions for company users
# Email_clicked column indicates the technology ids the user has clicked before

# user_ID is the company user id
# pre_count is the number of predictions you want to generate
def user_prediction(user_ID,pre_count):
    pre_df=pd.DataFrame({n: prediction_df.T[col].nlargest(pre_count).index.tolist() 
                  for n, col in enumerate(prediction_df.T)}).T
    pre_df.index=score_df.index
    pre_df['email_clicked']=pre_df.index.map(lambda user_id:np.intersect1d(np.array(pre_df.ix[user_id]), np.array(dr.DataReader().get_clicked_tech_ids(user_id))))
    return pre_df.ix[user_ID]


#==============================================================================
user_prediction('57e5254e-80c8-479b-979f-00530a2a1238',10)
# 
# pre_count=5
# pre_df=pd.DataFrame({n: prediction_df.T[col].nlargest(pre_count).index.tolist() 
#                   for n, col in enumerate(prediction_df.T)}).T
# pre_df.index=score_df.index
# pre_df['email_clicked']=pre_df.index.map(lambda user_id:np.intersect1d(np.array(pre_df.ix[user_id]), np.array(dr.DataReader().get_clicked_tech_ids(user_id))))
# pre_df.to_csv('Item based Collaborative Filtering_final.csv', sep=',', index = True, header =True)
#==============================================================================

if __name__ == '__main__':
    # Output a csv file
    prediction_df.index.name = 'user_id'
    prediction_df.to_csv("item_based_cf.csv")
