import numpy as np
import tensorflow as tf
from datetime import datetime
from DataReaderplus import *

def batch_generator(X, batch_size, shuffle):
    number_of_batches = np.ceil(X.shape[0]/batch_size)
    counter = 0
    sample_index = np.arange(X.shape[0])
    if shuffle:
        np.random.shuffle(sample_index)
    while True:
        batch_index = sample_index[batch_size*counter:batch_size*(counter+1)]
        X_batch = X[batch_index,:]
        counter += 1
        yield X_batch
        if (counter == number_of_batches):
            if shuffle:
                np.random.shuffle(sample_index)
            counter = 0
            

class BiasLatentFactorModel(object):
    def __init__(self, batch_size=128, num_factors=1, lr=0.001, n_epochs=20, penalty=[0.001, 0.001, 0.001, 0.001]):
        self.batch_size = batch_size
        self.num_factors = num_factors
        self.lr = lr
        self.n_epochs = n_epochs
        self.penalty = penalty
        self.user_dict = {}
        self.prod_dict = {}
        self.data_reader = DataReader()
        self.split_percentile = 0.8
        self.pred_matrix = None
        
    def build(self):
        ''' Build the recommender system '''
        t1 = datetime.now()
        print "Start building the model..."
        
        train_split = self.data_reader.get_score_data().shape[0] * self.split_percentile
        train_data = self.data_reader.get_score_data().values[:train_split, :]
        bg = batch_generator(train_data, self.batch_size, shuffle=True)
        
        num_prods = self.data_reader.get_technology_num()
        num_users = self.data_reader.get_user_num()
        num_batches = int(np.floor(train_data.shape[0] / self.batch_size))
        
        # Define model variables
        self.Wp = tf.Variable(tf.random_normal([num_prods, self.num_factors]), name='ProductWeightMatrix')
        self.Wu = tf.Variable(tf.random_normal([num_users, self.num_factors]), name='UserWeightMatrix')
        self.Bp = tf.Variable(tf.ones([num_prods]), name='ProductBiasVector')
        self.Bu = tf.Variable(tf.ones([num_users]), name='UserBiasVector')
        self.mu = tf.Variable(0.0, name='OverallAverageRating')
        
        # Define placeholders / input data
        self.user_index_list = tf.placeholder(tf.int32, shape=[self.batch_size])
        self.prod_index_list = tf.placeholder(tf.int32, shape=[self.batch_size])
        self.rating_list = tf.placeholder(tf.float32, shape=[self.batch_size])
        
        for i in xrange(self.batch_size):
            user_index = tf.gather(self.user_index_list, i)
            curWu = tf.gather(self.Wu, user_index)
            curBu = tf.reshape(tf.gather(self.Bu, user_index), [1, 1])    # reshape to [1, 1] before tf.concat
            
            prod_index = tf.gather(self.prod_index_list, i)
            curWp = tf.gather(self.Wp, prod_index)
            curBp = tf.reshape(tf.gather(self.Bp, prod_index), [1, 1])
            
            if i == 0:
                batchWu = curWu
                batchBu = curBu
                batchWp = curWp
                batchBp = curBp
            else:
                batchWu = tf.concat([batchWu, curWu], 0)
                batchBu = tf.concat([batchBu, curBu], 0)
                batchWp = tf.concat([batchWp, curWp], 0)
                batchBp = tf.concat([batchBp, curBp], 0)
        batchWu = tf.reshape(batchWu, shape=[self.batch_size, self.num_factors])
        batchBu = tf.reshape(batchBu, shape=[self.batch_size])
        batchWp = tf.reshape(batchWp, shape=[self.batch_size, self.num_factors])
        batchBp = tf.reshape(batchBp, shape=[self.batch_size])
        
        
        # Define loss
        self.pred = tf.reduce_sum(batchWu * batchWp, 1) + batchBu + batchBp + self.mu
        self.loss = tf.reduce_sum(tf.squared_difference(self.pred, self.rating_list)) / self.batch_size
        self.l2_loss = self.penalty[0]*tf.nn.l2_loss(self.Wp) + self.penalty[1]*tf.nn.l2_loss(self.Wu) + \
                      self.penalty[2]*tf.nn.l2_loss(self.Bu) + self.penalty[3]*tf.nn.l2_loss(self.mu)
        self.loss += self.l2_loss   

        optimizer = tf.train.AdamOptimizer(self.lr).minimize(self.loss)
        
        # Define the RMSE
        self.sse = tf.reduce_mean(tf.squared_difference(self.pred, self.rating_list))
        self.accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.round(self.pred), self.rating_list), tf.float32))
        
        init = tf.global_variables_initializer()
        print "Time: ", datetime.now() - t1
        
        # Start training
        print "Training starts..."
        start = datetime.now()
        self.sess = tf.Session()
        self.sess.run(init)
        print "Initialization is done: ", datetime.now() - start
        res = 0.0
        for i in range(self.n_epochs):
                total_loss = 0
                for batch in range(num_batches):
                    #print "Batch ", batch
                    batch_start = datetime.now()
                    _, loss_batch = self.sess.run([optimizer, self.loss], feed_dict=self.get_feed_dict(bg.next().tolist()))
                    
                    #print "Time elapsed: ", datetime.now() - batch_start
                    total_loss += loss_batch
                res += total_loss / num_batches
                print "Epoch ", i, " - total loss: ", total_loss / num_batches
        print "Time elapsed: ", datetime.now() - start
        
        self.pred_matrix = self.sess.run(tf.matmul(self.Wu, tf.transpose(self.Wp))).tolist()

        return res / self.n_epochs
            

    def test(self):
        train_split = self.data_reader.get_score_data().shape[0] * self.split_percentile
        test_data = self.data_reader.get_score_data().values[train_split:, :]
        num_batches = int(np.floor(test_data.shape[0] / self.batch_size))
        bg = batch_generator(test_data, self.batch_size, False)
        total_sse = 0
        total_accuracy = 0
        for _ in range(num_batches):
            sse_batch, accuracy_batch = self.sess.run([self.sse, self.accuracy], feed_dict=self.get_feed_dict(bg.next().tolist()))
            total_sse += sse_batch
            total_accuracy += accuracy_batch
        print "Total test rmse: ", np.sqrt(total_sse / num_batches)
        print "Accuracy: ", total_accuracy / num_batches
        return np.sqrt(total_sse / num_batches)

                
    def recommend(self, uid, k):
        start = datetime.now()
        if uid not in self.user_dict:
            self.user_dict[uid] = len(self.user_dict)
        pids = self.data_reader.get_technology_id()
        preds = self.pred_matrix[self.user_dict[uid]]
        tech_preds = [(i, pred) for i, pred in enumerate(preds)]
        tech_preds = sorted(tech_preds, key=lambda x: x[1], reverse=True)
        contact_ids = self.data_reader.get_contacted_tech_ids(uid)
        top_k = [pids[tech_index] for tech_index, score in tech_preds if tech_index not in contact_ids][:k]
        # print 'uid: ', uid, '\ttime elapsed: ', datetime.now() - start
        return top_k
        
    
    def get_feed_dict(self, batch_data):
        ratings = [row[2] for row in batch_data]
        user_ids = []
        prod_ids = []
        for row in batch_data:
            user_id = row[0]
            prod_id = row[1]
            if user_id not in self.user_dict:
                self.user_dict[user_id] = len(self.user_dict)
            if prod_id not in self.prod_dict:
                self.prod_dict[prod_id] = len(self.prod_dict)
            user_ids.append(self.user_dict[user_id])
            prod_ids.append(self.prod_dict[prod_id])
        
        feed_dict = { 
            self.user_index_list: user_ids,
            self.prod_index_list: prod_ids,
            self.rating_list: ratings
        }
        return feed_dict
            

if __name__ == '__main__':
    model = BiasLatentFactorModel()
    model.build()
    time = datetime.now()
    uids = model.data_reader.get_user_id()
    recommendations = [model.recommend(uid, 5) for uid in uids]
    df = pd.DataFrame(recommendations)
    email_clicked = []
    for i, uid in enumerate(uids):
        email_clicked.append([tech_id  for tech_id in recommendations[i] if tech_id in model.data_reader.get_clicked_tech_ids(uid)])
    output = pd.concat([pd.DataFrame({'user_id': uids}), df, pd.DataFrame({'email_clicked': email_clicked})], axis=1)
    output.to_csv('LF_result_num_factors_6_batch_size_64.csv', index=False)
    print 'Time elapsed: ', datetime.now() - time