import MySQLdb as mdb
import numpy as np
import pandas as pd
import itertools
from DataReader import DataReader
from sklearn.metrics.pairwise import cosine_similarity 
from scipy import sparse
from datetime import datetime

class EnsembleRecommender(object):
    '''An ensemble recommender integrated from two content-based models and one item-based collaborative flitering.'''
    
    def __init__(self):
        self.dr = DataReader()
        
        self.score = self.dr.get_score_data()
        self.cb_matrix = None
        self.interacted_cb_matrix = None
        self.cl_matrix = None
        self.ensemble_matrix = None
        self.tech_keyword_matrix = self.get_tech_keyword_matrix()
        
    def build_content_based(self):
        '''Build a content-based model which calculates similarity between user keyword vector and tech keyword vector.'''
        if self.cb_matrix is not None:
            return self.cb_matrix
        
        print 'Start training content_based model...'
        start = datetime.now()
        
        all_user_ids = self.dr.get_user_ids()
        user_keyword_matrix = []     # Dimension: num_users * num_keywords
        for uid in all_user_ids:
            user_keyword_matrix.append(self.dr.get_user_keyword_vector(uid))
        
        # Convert matrix to sparse matrix to speed up similarity calculation
        user_keyword_matrix = sparse.csr_matrix(user_keyword_matrix)
        self.tech_keyword_matrix = sparse.csr_matrix(self.tech_keyword_matrix)
        self.cb_matrix = cosine_similarity(user_keyword_matrix, self.tech_keyword_matrix)  # Dim: num_users * num_techs
        print 'Done'
        print 'Time elapsed:', datetime.now() - start, '\n'
        
    def build_interacted_content_based(self):
        '''Build a intereacted cb model which calculates similarity between user preference vector and tech keyword vector.
        
        The user preference vector is a weighted average of tech keyword vectors with which users have interacted.
        '''
        if self.interacted_cb_matrix is not None:
            return self.interacted_cb_matrix
        
        self.tech_keyword_matrix = self.tech_keyword_matrix.toarray()
        
        print 'Start training interacted content_based model...'
        start = datetime.now()
        all_user_ids = self.dr.get_user_ids()
        tech_mapping_dict = self.dr.get_tech_mapping_dict()
        user_keyword_matrix = []
        for uid in all_user_ids:
            interacted_tech_ids = self.dr.get_interacted_tech_ids(uid)
            num = np.zeros(len(self.dr.get_all_keywords()), dtype=np.float32)
            deno = 0
            for tech_id in interacted_tech_ids:
                d= self.score[(self.score['user_id'] == uid) & (self.score['technology_id'] == tech_id)]['total_score']
    
                weight = d.values[0]
                num += weight * self.tech_keyword_matrix[tech_mapping_dict[tech_id], :]
                deno += weight
            if deno == 0:    # This user hasn't interacted with any technology
                user_keyword_matrix.append(self.dr.get_user_keyword_vector(uid))
            else:
                user_keyword_matrix.append(num / deno)

        # Convert matrix to sparse matrix to speed up similarity calculation
        user_keyword_matrix = sparse.csr_matrix(user_keyword_matrix)
        self.tech_keyword_matrix = sparse.csr_matrix(self.tech_keyword_matrix)
        self.interacted_cb_matrix = cosine_similarity(user_keyword_matrix, self.tech_keyword_matrix)  # Dim: num_users * num_techs
        print 'Done'
        print 'Time elapsed:', datetime.now() - start, '\n'
            
    def build_collaborative_filtering(self):
        '''Built a collaborative filtering model using score table.'''
        if self.cl_matrix is not None:
            return self.cl_matrix
        
        scoreData = self.score
        score_df = scoreData.pivot(index = 'user_id', columns = 'technology_id', values = 'total_score') # Reshape score table 
        score_df = score_df.fillna(0) # fill NaN data with 0

        # Calculate Technology based similarity
        score_df_t = score_df.T
        score_spare_t = sparse.csr_matrix(score_df_t) 

        similarities_tech = cosine_similarity(score_spare_t)
        similarities_tech_df = pd.DataFrame(similarities_tech, columns = score_df_t.index, index = score_df_t.index)

        # Create a list of user_ids and tech_ids which are available in score table
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
        
        
        print 'Start training collaborative filtering model...'
        start = datetime.now()
        count = 0
        base_line = {}
        prediction = {} # A dictionary storing predictions whose key is a tuple (user_id, tech_id)
        
        print 'Total num of calculation:', len(user_ids) * len(tech_ids)
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
                    count += 1
                    if count % 100000 == 0:
                        print 'Num of calcuation finished:', count,
                        print '\tTime elapsed:', datetime.now() - start

        idx = pd.MultiIndex.from_tuples(prediction.keys())
        item_based_cf = pd.DataFrame(list(prediction.values()),index = idx,columns = ['Technology_id']).unstack(fill_value = 0)['Technology_id']
        item_based_cf = item_based_cf.loc[self.dr.get_user_ids(), self.dr.get_tech_ids()].fillna(0)
        self.cl_matrix = item_based_cf.values
        print 'Done'
        print 'Time elapsed:', datetime.now() - start, '\n'
        
    
    def build_ensemble_model(self, weights):
        '''Build an ensemble model.
        
        Params
        ------
        weights: list
            Ensemble weights of item_based cf, content_based, interacted_content_based.
        '''
        if self.ensemble_matrix is not None:
            return self.ensemble_matrix
        index = self.dr.get_user_ids()
        cols = self.dr.get_tech_ids()
        norm_item_based_cf = self.normalize_df(pd.DataFrame(self.cl_matrix, index=index, columns=cols))
        norm_cb = self.normalize_df(pd.DataFrame(self.cb_matrix, index=index, columns=cols))
        norm_interacted_cb = self.normalize_df(pd.DataFrame(self.interacted_cb_matrix, index=index, columns=cols))
        
        weighted_ensemble = norm_item_based_cf * weights[0] + norm_cb * weights[1] + norm_interacted_cb * weights[2]
        self.ensemble_matrix = weighted_ensemble
    
    def ensemble_recommend(self, uid, k):
        '''Return top k recommendations for a user id.
        
        Returns
        -------
        tuple
            A tuple (a list of top k recommendations, a list of tech ids clicked in emails)
        '''
        user_preds = zip(self.ensemble_matrix.loc[uid], self.dr.get_tech_ids())
        user_preds = sorted(user_preds, key=lambda x: x[0], reverse=True)
        
        contacted_ids = self.dr.get_contacted_tech_ids(uid)
        top_k = [item_id for score, item_id in user_preds if item_id not in contacted_ids][:k]
        
        clicked_tech_ids = self.dr.get_clicked_tech_ids(uid)
        email_clicked = [tech_id for tech_id in top_k if long(tech_id) in clicked_tech_ids]
        return top_k, email_clicked

    def save_recommendations_to_database(self, k):
        '''Create a table and Write top k recommendations for each user to the database.
        
        Params
        ------
        k: int
            The number of recommendations for each user.
        '''
        uids = self.dr.get_user_ids()
        result = [self.ensemble_recommend(uid, k) for uid in uids]
        recommendations = [item[0] for item in result]
        email_clicked = [item[1] for item in result]
        output = pd.concat([pd.DataFrame({'user_id': uids}), pd.DataFrame(recommendations), pd.DataFrame({'email_clicked': email_clicked})], axis=1)
        output.to_csv('ensemble_recommendations_for_users.txt', sep='\t', index=False, header=False)
        
        top_k_str = ""
        for i in range(1, k + 1):
            top_k_str += "top_" + str(i) + " int, "
        self.dr.cur.execute("DROP TABLE IF EXISTS RecommendationResultForUsers;")
        self.dr.cur.execute('''CREATE TABLE RecommendationResultForUsers (
                                   user_id VARCHAR(60),
                                   %s 
                                   email_clicked VARCHAR(220));''' % top_k_str)
        self.dr.cur.execute('''LOAD DATA LOCAL INFILE 'ensemble_recommendations_for_users.txt' 
                                   INTO TABLE RecommendationResultForUsers 
                                   FIELDS TERMINATED BY '\t' 
                                   LINES TERMINATED BY '\n';''')
        self.dr.con.commit()

    
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
    
    def normalize_df(self, score_matrix):
        '''Normalize the range of each user's score to [0,1].
        
        Params
        ------
        score_matrix: DataFrame
            Row is user, Column is technology, Value is the score. Recommendations are made by ranking scores for a user.
        
        Returns
        -------
        DataFrame
        '''
        norm_df = score_matrix.copy()
        for idx, row in norm_df.iterrows():
            min_val = min(row)
            max_val = max(row)
            interval = max_val - min_val
            if interval == 0:
                continue
            norm_df.ix[idx] = [(r - min_val) / interval for r in row]
        return norm_df
    
if __name__ == "__main__":
    ensemble_weights = [0.65, 0.67, 0.52]
    recommender = EnsembleRecommender()
    recommender.build_content_based()
    recommender.build_interacted_content_based()
    recommender.build_collaborative_filtering()
    recommender.build_ensemble_model(ensemble_weights)
    recommender.save_recommendations_to_database(10)
   