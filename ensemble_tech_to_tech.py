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
 
def normalize_sim(sims):
    max_val = max(sims)
    min_val = min(sims)
    interval = max_val - min_val
    return [(sim - min_val) / interval if interval != 0 else sim for sim in sims]

def ensemble_tech_sim(tech_id, k):
    norm_keyword = normalize_sim([sim for tid, sim in tech_keyword_sim[long(tech_id)]])
    norm_keyword = zip([tid for tid, sim in tech_keyword_sim[long(tech_id)]], norm_keyword)
    keyword = {tid: sim for tid, sim in norm_keyword}
    
    if int(tech_id) in tech_item_based_sim:
        norm_item = normalize_sim([sim for tid, sim in tech_item_based_sim[int(tech_id)]])
        norm_item = zip([tid for tid, sim in tech_item_based_sim[long(tech_id)]], norm_item)
        item_based = {tid: sim for tid, sim in norm_item} 
    else:
        item_based = {}
    output = []
    for tid in keyword.keys():
        if tid not in item_based:
            output.append((tid, keyword[tid]))
        else:
            output.append((tid, (keyword[tid] + item_based[tid]) / 2.0))
    return [tid for tid, sim in sorted(output, key=lambda x: x[1], reverse=True)][:k]

    
    
ensemble_output = []
for tech_id in all_tech_ids:
    ensemble_output.append(ensemble_tech_sim(tech_id, 5))
ensemble_output = pd.DataFrame(ensemble_output, index=all_tech_ids)
ensemble_output.index.name = 'tech_id'
ensemble_output.to_csv('ensemble_tech_to_tech_output.csv')

