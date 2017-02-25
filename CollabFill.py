# -*- coding: utf-8 -*-
"""
Spyder Editor

"""
import pandas as pd
import ScoreCalculate as sc
import DataReaderplus as dr

scoreData = dr.DataReader().get_score_data() # read data from the Score table

score = scoreData.pivot(index='user_id', columns = 'technology_id', values = 'total_score') # reshape score table 
print score

