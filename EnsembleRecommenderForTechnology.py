import MySQLdb as mdb
import numpy as np
import pandas as pd
from DataReader import DataReader
from sklearn.metrics.pairwise import cosine_similarity 
from scipy import sparse
from datetime import datetime


class EnsembleRecommenderForTechnology(object):
    '''An ensemble recommender to recommend technologies for a tehchnology.
    
    First, calculate technology similarities between technology keyword vector.
    Second, calculate technology similarities between columns of utility matrix. Each technology vector is represented by scores given by users.
    Finally, do a weighted average of two technology matrix. The weights are [0.5, 0.5].
    '''
    def __init__(self):
        self.dr = DataReader()
        
        self.score = self.dr.get_score_data()
        self.tech_keyword_matrix = self.get_tech_keyword_matrix() 
        
        self.tech_keyword_sim_matrix = None
        self.item_based_sim_matrix = None
        self.ensemble_sim_matrix = None
        
        # Auxiliary variable
        self.tech_id_set_for_item_based = None
    
    def build_tech_keyword_sim_matrix(self):
        if self.tech_keyword_sim_matrix is not None:
            return self.tech_keyword_sim_matrix
        
        print "Start building tech keyword sim matrix..."
        self.tech_keyword_matrix = sparse.csr_matrix(self.tech_keyword_matrix)
        self.tech_keyword_sim_matrix = pd.DataFrame(cosine_similarity(self.tech_keyword_matrix),
                                                    index=self.dr.get_tech_ids(),
                                                    columns=self.dr.get_tech_ids())
        print "Done."
        print '\n'
        
    def build_item_based_cl_sim_matrix(self):
        if self.item_based_sim_matrix is not None:
            return self.item_based_sim_matrix
        
        print "Start building item_based Collaborative Filtering sim matrix..."
        scoreData = self.score
        score_df = scoreData.pivot(index = 'user_id', columns = 'technology_id', values = 'total_score') # Reshape score table 
        score_df = score_df.fillna(0) # fill NaN data with 0

        # Calculate Technology based similarity
        score_df_t = score_df.T
        score_spare_t = sparse.csr_matrix(score_df_t) 

        similarities_tech = cosine_similarity(score_spare_t)
        similarities_tech_df = pd.DataFrame(similarities_tech, columns=score_df_t.index, index=score_df_t.index)
        self.item_based_sim_matrix = similarities_tech_df
        self.tech_id_set_for_item_based = set(self.item_based_sim_matrix.index)

        print "Done."
        print '\n'    

    def build_ensemble_model(self):
        if self.ensemble_sim_matrix is not None:
            return self.ensemble_sim_matrix
        
        print "Start building Ensemble sim matrix..."
        ensemble_sim_matrix = (self.tech_keyword_sim_matrix + self.item_based_sim_matrix) / 2
        ensemble_sim_matrix = ensemble_sim_matrix.loc[self.dr.get_tech_ids(), self.dr.get_tech_ids()]        

        # Replace null values of Item based sim matrix with similarity values in Technology keyword sim matrix
        all_tech_ids = set(self.dr.get_tech_ids())
        tech_ids_null_set = all_tech_ids - self.tech_id_set_for_item_based        
        for tech_id in tech_ids_null_set:
            ensemble_sim_matrix.loc[tech_id] = self.tech_keyword_sim_matrix.loc[tech_id]
            ensemble_sim_matrix.loc[:, tech_id] = self.tech_keyword_sim_matrix.loc[:, tech_id]
        
        self.ensemble_sim_matrix = ensemble_sim_matrix
        print "Done."
        print '\n'  
        
    def ensemble_recommend(self, tid, k):
        '''Return top k recommendations for a user id.
        
        Params
        ------
        tid: int
            technology id
        k: int
        
        Returns
        -------
        list
        '''
        tech_sim = zip(self.ensemble_sim_matrix.loc[tid], self.dr.get_tech_ids())
        tech_sim = sorted(tech_sim, key=lambda x: x[0], reverse=True)[1:k+1]
        return [tech_id for sim, tech_id in tech_sim]
    
    def save_recommendations_to_database(self, k):
        '''Create a table and Write top k recommendations for technology to the database.
        
        Params
        ------
        k: int
            The number of recommendations for each technology.
        '''
        print "Start writing recommendations to the database..."
        tech_ids = self.dr.get_tech_ids()
        recommendations = pd.DataFrame([self.ensemble_recommend(tid, k) for tid in tech_ids], 
                                       index=tech_ids)
        
        recommendations.to_csv('ensemble_recommendations_for_techs.txt', sep='\t', header=False)
        
        top_k_str = ""
        for i in range(1, k + 1):
            top_k_str += "top_" + str(i) + " int, "
        self.dr.cur.execute("DROP TABLE IF EXISTS RecommendationResultForTechs;")
        self.dr.cur.execute('''CREATE TABLE RecommendationResultForTechs (
                                   technology_id int,
                                   %s);''' % top_k_str[:-2])
        self.dr.cur.execute('''LOAD DATA LOCAL INFILE 'ensemble_recommendations_for_techs.txt' 
                                   INTO TABLE RecommendationResultForTechs 
                                   FIELDS TERMINATED BY '\t' 
                                   LINES TERMINATED BY '\n';''')
        self.dr.con.commit()
        print "Done"
    
    def get_tech_keyword_matrix(self):
        '''Return a technology keyword matrix whose row is a technology keyword vector.
        
        Returns
        -------
        A list of list
        '''
        all_tech_ids = self.dr.get_tech_ids()
        tech_keyword_matrix = []     # Dimension: num_techs * num_keywords
        for tech_id in all_tech_ids:
            tech_keyword_matrix.append(self.dr.get_tech_keyword_vector(tech_id))
        return tech_keyword_matrix

if __name__ == "__main__":
    recommender = EnsembleRecommenderForTechnology()
    recommender.build_tech_keyword_sim_matrix()
    recommender.build_item_based_cl_sim_matrix()
    recommender.build_ensemble_model()
    recommender.save_recommendations_to_database(10)
