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
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse

# Create Score table and write score table back to MySQL database
score=calculate_score()
create_table()

scoreData = dr.DataReader().get_score_data() # read data from the Score table
score_df = scoreData.pivot(index='user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
score_df = score_df.fillna(0) # fill NaN data with 0
score_spare = sparse.csr_matrix(score_df) 
similarities = cosine_similarity(score_spare) # pairwise cosine similarity
similarities_df = pd.DataFrame(similarities, columns=score_df.index, index = score_df.index)

# Calculate Technology based similarity
score_df_t=score_df.T
score_spare_t = sparse.csr_matrix(score_df_t) 
similarities_tech = cosine_similarity(score_spare_t)
similarities_tech_df = pd.DataFrame(similarities_tech, columns=score_df_t.index, index = score_df_t.index)


# Fill in utility matrix where score is missing
new_scoredf=score_df.copy()

for i in new_scoredf.index:
    for j in new_scoredf.columns:
        if new_scoredf.ix[i,j]==0:
            numerator=sum(new_scoredf.ix[i]*similarities_tech_df.ix[j])
            denominator=sum(similarities_tech_df.ix[j])-1
            if denominator==0:
                new_scoredf.ix[i,j]=0
            else:
                new_scoredf.ix[i,j]=numerator/float(denominator)
                
# Generate predictions for company users

# user_id is the company user id
# pre_count is the number of predictions you want to generate
def user_prediction(user_id,pre_count):
    pre_df=pd.DataFrame({n: new_scoredf.T[col].nlargest(pre_count).index.tolist() 
                  for n, col in enumerate(new_scoredf.T)}).T
    pre_df.index=new_scoredf.index
    return pre_df.ix[user_id]
   
#==============================================================================
# user_prediction('58788ee8-bd40-4c20-992f-008a0a2a6136',5) 
# 
# pre_count=5
# pre_df=pd.DataFrame({n: new_scoredf.T[col].nlargest(pre_count).index.tolist() 
#                   for n, col in enumerate(new_scoredf.T)}).T
# pre_df.index=new_scoredf.index
#
# pre_df.to_csv('5 Predictions for Each User Using Technology Based Collaborative Filtering.csv', sep=',', index = True, header =True)
#==============================================================================
