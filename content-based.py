import pandas as pd
import numpy as np
import ScoreCalculate as sc
import DataReaderplus as dr
from sklearn.metrics.pairwise import cosine_similarity 

#get score table
scoreData = dr.DataReader().get_score_data()

#get all user in score table
unique_users = scoreData.user_id.unique()

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

user_profiles = {}



#iterate through all users in score table
for user in unique_users:  
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
    

    
    
# Given user id to make recommendation for the top 5 most similar technologies 
def recomend_top_similarity(user_id):
    """ Given user_id make recommendation from the tech_ids which excludes previously interacted tech_ids"""
    tech_similarity = {}
    user_preference =user_profiles[user_id]
    #extract interacted tech_ids
    known_tech_ids = dr.DataReader().extract_interacted_technology(user_id)
    #exclude interacted tech_ids
    unknown_tech_ids = np.delete(np.array(all_tech_ids),known_tech_ids)
    #iterate through all non interacted tech_ids
    for tech in unknown_tech_ids:
        tech_similarity[tech] = cosine_similarity(user_preference.reshape(1,-1), tech_profiles[tech].reshape(1,-1))
    sorted_similarity = sorted(tech_similarity, key = tech_similarity.get)
    #print sorted_similarity
    top_similarity = sorted_similarity[:5]
    return top_similarity

#test
recomend_top_similarity('528f575a-c6a8-4fdb-9bd7-4662d4718e13')

