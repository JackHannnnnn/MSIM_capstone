import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import DataReaderViz as dr
import sys

def find_match(tech_ids):
	match = []
	dataReader = dr.DataReader()
	all_users = dataReader.get_user_id() # get all users from the database
	all_keywords= dataReader.get_all_keywords() # get all keywords from the database

	all_user_profile =np.array([dataReader.cal_user_keywords(all_keywords, user) for user in all_users]) # keywords profile for all users

	tech_profile = np.array([dataReader.cal_technology_keywords(all_keywords, tech) for tech in tech_ids])


	similarity = cosine_similarity(tech_profile, all_user_profile)
	similarity_df = pd.DataFrame(similarity, columns=all_users, index=tech_ids)

	for tech in similarity_df.index.values.tolist():
		matched_users = similarity_df.loc[tech].nlargest(5).index.values.tolist()
		match.append({"Technology": tech, "Matches": matched_users})

	return match



