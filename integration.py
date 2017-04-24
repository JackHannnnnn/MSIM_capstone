# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 16:52:07 2017

@author: Wen Qin
"""

import pandas as pd
import numpy as np
import math
import itertools
import ScoreCalculate as sc
import DataReaderplus as dr
from sklearn.metrics.pairwise import cosine_similarity 
from scipy import sparse
import time


scoreData = dr.DataReader().get_score_data()

#get interacted user in score table
interacted_users = scoreData.user_id.unique()

#get all users in data base
all_users = dr.DataReader().get_user_id()

#get list of all keywords
all_keywords= dr.DataReader().get_all_keywords()

#get list of all tech ids
all_tech_ids = dr.DataReader().get_technology_id()

########### Content based Algorithm ##################

#create empty dictionary to store tech_profiles. Key is the technology id and value is technology and its keywords mapping list 
tech_profiles = {}
for tech in all_tech_ids:
    #tech profiling by mapping with all_keywords
    tech_profile = np.array(dr.DataReader().cal_technology_keywords(all_keywords, tech))
    tech_profiles[tech] = tech_profile 
    
# Calculate keyword_based technology similarity
tech_keyword_sim = {}
num_tech_ids = len(all_tech_ids)
for i in range(num_tech_ids):
    for j in range(i + 1, num_tech_ids):
        id1 = all_tech_ids[i]
        id2 = all_tech_ids[j]
        sim = cosine_similarity(tech_profiles[id1].reshape(1, -1), tech_profiles[id2].reshape(1, -1))[0, 0]
        if id1 not in tech_keyword_sim.keys():
            tech_keyword_sim[id1] = []
        tech_keyword_sim[id1].append((id2, sim))
        if id2 not in tech_keyword_sim.keys():
            tech_keyword_sim[id2] = []
        tech_keyword_sim[id2].append((id1, sim))  

for i in range(num_tech_ids):
    tech_keyword_sim[all_tech_ids[i]] = sorted(tech_keyword_sim[all_tech_ids[i]], key=lambda x : x[1], reverse=True)


#############user profiling mapping with all_keywords############# 
#dictionary to store user profile with user_id as key

def user_profile_interacted(user_id):
    """
    given user_id, function returns the user profile weighted by interacted scores
    """
    weight_sum = 0
    #initial user_keywords_sums
    
    user_keywords_sum = np.zeros(len(all_keywords))
    user_tech_ids = dr.DataReader().extract_interacted_technology(user_id)
    if user_tech_ids: # it is possible that this user never interacts with any technology
        #iterate through all tech ids which this user has interaction with
        for tech_id in user_tech_ids:
            #user viewed tech mapping with all keywords and weight by score
            weight = scoreData.loc[(scoreData.user_id == user_id) & (scoreData.technology_id == tech_id), "total_score"].iloc[0]  

            # user_keywords = np.array(dr.DataReader().cal_technology_keywords(all_keywords, tech_id)) * weight
            user_keywords = tech_profiles[tech_id]*weight
            
            #sum all vectors of this user
            user_keywords_sum = user_keywords_sum + user_keywords 
            
            #sum weigth for one user
            weight_sum = weight_sum + weight
    
        # mean of vector as user profile
        this_interacted_prof = user_keywords_sum/weight_sum
    else:
        this_interacted_prof = np.zeros(len(all_keywords))
    return this_interacted_prof
    

def user_selfidentified_prof(user_id): 
    """
    given one user_id, function returns a keywords mapping list for this user
    """  
    # user profiles built on self-identified keywords by users
    
    this_selfidentified_prof = dr.DataReader().cal_user_keywords(all_keywords, user_id)
    return this_selfidentified_prof

# Given user id make recommendation
def recommend_top_similarity(method, user_id):
    """
    return the recommend technology for one user, based on user profile calculate method and the number of technologies to recommend
    parameters
    ----------
    method: function    
        one of the three above profile calculate method 
    user_id:
        parameters to method function
    
    return: tech similarity
    """
    tech_similarity = {}
    #####assign which version of user profile will be used in the function#####
    #versions include: user_profiles_interacted, user_profiles_keyword
    user_preference = method(user_id)
    contacted_tech_ids = dr.DataReader().get_contacted_tech_ids(user_id)
    uncontacted_tech_ids = np.delete(np.array(all_tech_ids), contacted_tech_ids)
    # only recommend technologies which are not contacted
    for tech in uncontacted_tech_ids:
        tech_similarity[tech] = cosine_similarity(user_preference.reshape(1,-1), tech_profiles[tech].reshape(1,-1))[0,0]        
    for tech in contacted_tech_ids:
        tech_similarity[tech] = 0.0
    
    return tech_similarity


#start = time.time()
cb_interaction_dict = {}
# count = 0
for uid in all_users:
    cb_interaction_dict[uid] = recommend_top_similarity(user_profile_interacted,uid)
#    count += 1
#    if count % 10 == 0:
#        print "Time taken " + str((time.time() - start)/60)
cb_interaction = pd.DataFrame(cb_interaction_dict).T

cb_self_identified_dict = {}
for uid in all_users:
    cb_self_identified_dict[uid] = recommend_top_similarity(user_selfidentified_prof, uid)
    
cb_self_identified = pd.DataFrame(cb_self_identified_dict).T

#%%
######## Item based Collaborative filtering ##########
score_df = scoreData.pivot(index = 'user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
score_df = score_df.fillna(0) # fill NaN data with 0

# Calculate Technology based similarity
score_df_t = score_df.T
score_spare_t = sparse.csr_matrix(score_df_t) 

similarities_tech = cosine_similarity(score_spare_t)
similarities_tech_df = pd.DataFrame(similarities_tech, columns = score_df_t.index, index = score_df_t.index)

tech_item_based_sim = {}
for i in range(similarities_tech_df.shape[0]):
    tech_id = similarities_tech_df.index[i]
    sim_list = zip(similarities_tech_df.columns.tolist(), similarities_tech_df.iloc[i])
    tech_item_based_sim[tech_id] = sorted(sim_list, key=lambda x: x[1], reverse=True)[1:]

    
def get_similari_tech_ids(tech_id, k, method='keyword'):
    if method == 'keyword':
        return [id for id, sim in tech_keyword_sim[long(tech_id)][:k]]
    if method == 'item_based':
        if int(tech_id) in tech_item_based_sim.keys():
            return [id for id, sim in tech_item_based_sim[int(tech_id)][:k]]
        else:
            return [id for id, sim in tech_keyword_sim[long(tech_id)][:k]]
     
# Output technology similarity result
keyword_sim_output = []
item_based_sim_output = []
for tech_id in all_tech_ids:
    keyword_sim_output.append(get_similari_tech_ids(tech_id, 5, method='keyword'))
    item_based_sim_output.append(get_similari_tech_ids(tech_id, 5, method='item_based'))

keyword_sim_output = pd.DataFrame(keyword_sim_output, index=all_tech_ids)
keyword_sim_output.index.name = 'tech_id'
item_based_sim_output = pd.DataFrame(item_based_sim_output, index=all_tech_ids)
item_based_sim_output.index.name = 'tech_id'
keyword_sim_output.to_csv('keyword_sim_output.csv')
item_based_sim_output.to_csv('item_based_sim_output.csv')


# Create a list of user_ids and tech_ids which are available in scoreData
user_ids = scoreData['user_id'].unique()
tech_ids = scoreData['technology_id'].unique()

# Calculate mean of all ratings, mean rating given by each user and mean rating given to each technology
all_mean = np.mean(scoreData['total_score'])
avg_user = {}
for user in user_ids:
    avg_user[user] = np.mean(scoreData[scoreData['user_id'] == user]['total_score']) - all_mean
    
avg_tech = {}
for tech in tech_ids:
    avg_tech[tech] = np.mean(scoreData[scoreData['technology_id'] == tech]['total_score'])-all_mean


# Create a dictionary storing baseline
# Create a dictionary storing prediction, the key is tuple(user_id, tech_id)

#start = time.time()
#count = 0
base_line = {}
prediction = {}

for i in itertools.product(user_ids,tech_ids):
    prediction[i] = score_df.ix[i[0],i[1]]
    base_line[i] = avg_user[i[0]] + avg_tech[i[1]] + all_mean
    if prediction[i] == 0:
        numerator = sum((score_df.ix[i[0]] - base_line[i])*similarities_tech_df.ix[i[1]])
        denominator = sum(similarities_tech_df.ix[i[1]])-1
        if denominator == 0:
            prediction[i] = 0
        else:
            prediction[i] = base_line[i] + numerator/float(denominator)
#            count += 1
#            if count%1000 == 0:
#                print count
#                print "Time taken " + str((time.time() - start)/60)

idx = pd.MultiIndex.from_tuples(prediction.keys())
item_based_cf = pd.DataFrame(list(prediction.values()),index = idx,columns = ['Technology_id']).unstack(fill_value = 0)['Technology_id']


#%%
################### Ensemble ####################

# Normalize the range of each user's score to [0,1]
def normalize_df(dataframe):
    norm_df = dataframe.copy()
    for idx, row in norm_df.iterrows():
        min_val = min(row)
        max_val = max(row)
        interval = max_val - min_val
        if interval == 0:
            continue
        norm_df.ix[idx] = [(r - min_val) / interval for r in row]
    return norm_df
        
norm_item_based_cf = normalize_df(item_based_cf)
norm_cb_interaction = normalize_df(cb_interaction)
norm_cb_self_identified = normalize_df(cb_self_identified)


# Preprocess collaborative filatering result to make dimensions equal for three data frames
for item in all_tech_ids:
    if item not in norm_item_based_cf.columns:
        norm_item_based_cf[item] = np.zeros(norm_item_based_cf.shape[0])

        
uids = [uid for uid in all_users if uid not in norm_item_based_cf.index]
padded_df = pd.DataFrame(np.zeros((len(uids), norm_item_based_cf.shape[1])), index=uids, columns=norm_item_based_cf.columns)
norm_item_based_cf = pd.concat([norm_item_based_cf, padded_df], axis=0)


# Ensemble: optimized weighted average
norm_item_based_cf.sort_index(0, inplace=True)
norm_item_based_cf.sort_index(1, inplace=True)

norm_cb_interaction.sort_index(0, inplace=True)
norm_cb_interaction.sort_index(1, inplace=True)
norm_cb_self_identified.sort_index(0, inplace=True)
norm_cb_self_identified.sort_index(1, inplace=True)

weights = [0.65, 0.67, 0.52]
weighted_ensemble = norm_item_based_cf * weights[0] + norm_cb_interaction * weights[1] + norm_cb_self_identified * weights[2]
cols = weighted_ensemble.columns


def ensemble_recommend(uid, k):
    ''' Returns top k recommendations for a user id '''
    user_preds = zip(weighted_ensemble.loc[uid], cols)
    user_preds = sorted(user_preds, key=lambda x: x[0], reverse=True)
    contact_ids = dr.DataReader().get_contacted_tech_ids(uid)
    top_k = [item_id for score, item_id in user_preds if item_id not in contact_ids][:k]
    email_clicked = [tech_id for tech_id in top_k if long(tech_id) in dr.DataReader().get_clicked_tech_ids(uid)]
    return top_k, email_clicked



