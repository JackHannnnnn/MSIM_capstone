import pandas as pd
import numpy as np
import ScoreCalculate as sc
import DataReaderplus as dr
from sklearn.metrics.pairwise import cosine_similarity 

#get score table
scoreData = dr.DataReader().get_score_data()

#get interacted user in score table
interacted_users = scoreData.user_id.unique()

#get all users in data base
all_users = dr.DataReader().get_user_id()

#get list of all keywords
all_keywords= dr.DataReader().get_all_keywords()

#get list of all tech ids
all_tech_ids = dr.DataReader().get_technology_id()

#creat empty dictionary to store tech_profiles 
tech_profiles = {}
 
for tech in all_tech_ids:
    #tech profiling by mapping with all_keywords
    tech_profile = np.array(dr.DataReader().cal_technology_keywords(all_keywords, tech))
    tech_profiles[tech] = tech_profile 
    
    

#############user profiling mapping with all_keywords############# 
#dictionary to store user profile with user_id as key

user_profiles_interacted = {}



#iterate through all users in score table
for user in interacted_users:  
    #initial weight_sum 
    weight_sum = 0
    #initial user_keywords_sums
    user_keywords_sum = np.zeros(len(all_keywords))
    user_tech_ids = dr.DataReader().extract_interacted_technology(user)
    #iterate through all tech ids which this user has interaction with
    for tech_id in user_tech_ids:
        #user viewed tech mapping with all keywords and weight by score
        weight = scoreData.loc[ (scoreData.user_id == user) & (scoreData.technology_id == tech_id), "total_score"].iloc[0]  
        #print weight
        user_keywords = np.array(dr.DataReader().cal_technology_keywords(all_keywords, tech_id)) * weight
        #sum all vectors of this user
        user_keywords_sum = user_keywords_sum + user_keywords       
        #sum weigth for one user
        weight_sum = weight_sum + weight
    #print weight_sum
    #print user_keywords_sum
    # mean of vector as user profile
    user_profiles[user] = user_keywords_sum/weight_sum
    
    
# user profiles built on self-identified keywords by users
#empty dictionary to store user_profiles
user_profiles_keyword = {}

#extract user_keywords mapped with all_keywords
for user in all_users:     
    user_profiles_keyword[user] = dr.DataReader().cal_user_keywords(all_keywords, user)

#user profiles combines user self-identified keywords and interacted keywords
#empty dictionary to store user_profiles
user_profiles_comb = {}
#if user not in interacted user list using user profiles based on user_profiles_keywords 
for user in all_users:
    if user not in interacted_users:
        user_profiles_comb[user] = dr.DataReader().cal_user_keywords(all_keywords, user)
    else:  
     #if user in interacted user list using user profiles based on user_profiles_keywords plus user_profiles_interacted
        user_profiles_comb[user] = (user_profiles_interacted[user]+user_profiles_keyword[user])/2    
    
    
    
# Given user id make recommendation
def recomend_top_similarity(user_id, reco_count):
    """Given user id to make recommendation for top 5 most similar technologies """
    tech_similarity = {}
    #####assign which version of user profile will be used in the function#####
    #versions include: user_profiles_interacted, user_profiles_keyword, user_profiles_comb
    user_preference =user_profiles_interacted[user_id]
    contacted_tech_ids = dr.DataReader().get_contacted_tech_ids(user_id)
    uncontacted_tech_ids = np.delete(np.array(all_tech_ids), contacted_tech_ids)
    for tech in uncontacted_tech_ids:
        tech_similarity[tech] = cosine_similarity(user_preference.reshape(1,-1), tech_profiles[tech].reshape(1,-1))        
    sorted_similarity = sorted(tech_similarity, key = tech_similarity.get, reverse = True)
    #print sorted_similarity
    top_similarity = sorted_similarity[:reco_count]
    recommends = {}
    emailed = []
    unemailed = []
    for tech in top_similarity:
        if tech in dr.DataReader().get_emailed_tech_ids(user_id):
            emailed.append(tech)
        else: 
            unemailed.append(tech)
    recommends['emailed'] = emailed
    recommends['unemailed'] = unemailed
    return recommends
    #print 'emailed = {}， unemailed = {}\n'.format(emailed, unemailed)  
    


#test
recomend_top_similarity('57d97d4a-23b8-4148-a0a5-004a0a2ae3a6',5)

