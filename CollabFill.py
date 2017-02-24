# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import DataReaderplus as dr

dataReader = dr.DataReader()
con = dataReader.con

score = pd.read_sql("SELECT user_id, technology_id, total_score FROM score", con = con)  
reshape = score.pivot(index='user_id', columns = 'technology_id', values = 'total_score')
print reshape

#def get_score_data():
#    """return the score table with user_id, technology_id, total_score  """
#    scoreData = pd.read_sql("SELECT user_id, technology_id, total_score FROM score", con = con)        
#    return scoreData
