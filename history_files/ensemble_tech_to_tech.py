# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 16:52:07 2017

@author: Wen Qin
"""

import pandas as pd
import numpy as np
import DataReaderplus as dr
from sklearn.metrics.pairwise import cosine_similarity 
from scipy import sparse
import time

scoreData = dr.DataReader().get_score_data()

#get all users in data base
all_users = dr.DataReader().get_user_id()

#get list of all keywords
all_keywords= dr.DataReader().get_all_keywords()

#get list of all tech ids
all_tech_ids = dr.DataReader().get_technology_id()


# Calculate keyword vector similarity 
tech_profiles = {}
for tech in all_tech_ids:
    #tech profiling by mapping with all_keywords
    tech_profile = np.array(dr.DataReader().cal_technology_keywords(all_keywords, tech))
    tech_profiles[tech] = tech_profile 


tech_profile_df = pd.DataFrame(tech_profiles).T
tech_profile = sparse.csr_matrix(tech_profile_df)
tech_kw_sim = cosine_similarity(tech_profile)
tech_kw_sim_df = pd.DataFrame(tech_kw_sim, columns = tech_profile_df.index, index = tech_profile_df.index)

# Calculate Technology based similarity
score_df = scoreData.pivot(index = 'user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
score_df = score_df.fillna(0) # fill NaN data with 0

score_df_t = score_df.T
score_spare_t = sparse.csr_matrix(score_df_t) 

similarities_tech = cosine_similarity(score_spare_t)
similarities_tech_df = pd.DataFrame(similarities_tech, columns = score_df_t.index, index = score_df_t.index)

ensemble_df = (similarities_tech_df + tech_kw_sim_df)/2

start = time.time()
count = 0
for i in all_tech_ids:
    for j in all_tech_ids:
        if np.isnan(ensemble_df.ix[int(i),int(j)]) == True:
            ensemble_df.ix[int(i),int(j)] = tech_kw_sim_df.ix[int(i),int(j)]
        else:
            pass
        count += 1
        if count % 10000 ==0:
            print "Time taken " + str((time.time() - start)/60)
            
cols = ensemble_df.columns          
def ensemble_recommend(tid, k):
    ''' Returns top k recommendations for a user id '''
    tech_sim = zip(ensemble_df.loc[tid], cols)
    tech_sim = sorted(tech_sim, key=lambda x: x[0], reverse=True)[1:k+1]
    sim_tid = [tech_id for score, tech_id in tech_sim]
    return sim_tid

sim_tech = {}
for i in all_tech_ids:
    sim_tech[i] = ensemble_recommend(i, 10)
sim_tid_preds = pd.DataFrame(sim_tech).T
    
sim_tid_preds.index.name = 'tech_id'
sim_tid_preds.to_csv('ensemble_tech_to_tech_output.csv')







