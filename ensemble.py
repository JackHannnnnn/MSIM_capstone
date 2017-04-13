import numpy as np
import pandas as pd
from datetime import datetime
from DataReaderplus import *


# Read data from individual recommendation result
cb_interaction = pd.read_csv('cb_interaction.csv', index_col=0)
cb_self_identified = pd.read_csv('cb_self_identified.csv', index_col=0)
cb_combination = pd.read_csv('cb_combination.csv', index_col=0)
item_based_cf = pd.read_csv('item_based_cf.csv', index_col=0)

user_pool = cb_interaction.index.tolist()
item_pool = cb_interaction.columns.tolist()
dr = DataReader()

# Preprocess collaborative filatering result
for row in range(item_based_cf.shape[0]):
    row_data = item_based_cf.iloc[row]
    min_val = min([r for r in row_data if r != -float('inf')])
    max_val = max([r for r in row_data if r != -float('inf')])
    interval = max_val - min_val
    item_based_cf.iloc[row] = [(r - min_val) / interval if r != -float('inf') else 0 for r in row_data]
    
for item in item_pool:
    if item not in item_based_cf.columns:
        item_based_cf[item] = np.zeros(item_based_cf.shape[0])
for col in item_based_cf.columns:
    if col not in item_pool:
        del item_based_cf[col]
        
uids = [uid for uid in user_pool if uid not in item_based_cf.index]
padded_df = pd.DataFrame(np.zeros((len(uids), item_based_cf.shape[1])), index=uids, columns=item_based_cf.columns)
item_based_cf = pd.concat([item_based_cf, padded_df], axis=0)

# Normalize result form Content-based algorithm
for row in range(cb_combination.shape[0]):
    row_data = cb_combination.iloc[row]
    min_val = min(row_data)
    max_val = max(row_data)
    interval = max_val - min_val
    cb_combination.iloc[row] = [(r - min_val) / interval for r in row_data]

for row in range(cb_interaction.shape[0]):
    row_data = cb_interaction.iloc[row]
    min_val = min(row_data)
    max_val = max(row_data)
    # print min_val, max_val
    interval = max_val - min_val
    cb_interaction.iloc[row] = [(r - min_val) / interval for r in row_data]
    
for row in range(cb_self_identified.shape[0]):
    row_data = cb_self_identified.iloc[row]
    min_val = min(row_data)
    max_val = max(row_data)
    # print min_val, max_val
    interval = max_val - min_val
    cb_self_identified.iloc[row] = [(r - min_val) / interval for r in row_data]


# Ensemble: optimized weighted average
item_based_cf.sort_index(0, inplace=True)
item_based_cf.sort_index(1, inplace=True)

cb_interaction.sort_index(0, inplace=True)
cb_interaction.sort_index(1, inplace=True)
cb_self_identified.sort_index(0, inplace=True)
cb_self_identified.sort_index(1, inplace=True)
cb_combination.sort_index(0, inplace=True)
cb_combination.sort_index(1, inplace=True)

weights = [0.65, 0.67, 0.52, 0.57]
weighted_ensemble = item_based_cf * weights[0] + cb_interaction * weights[1] + cb_self_identified * weights[2] + \
                    cb_combination * weights[3]    
cols = weighted_ensemble.columns


def ensemble_recommend(uid, k):
    ''' Returns top k recommendations for a user id '''
    user_preds = zip(weighted_ensemble.loc[uid], cols)
    user_preds = sorted(user_preds, key=lambda x: x[0], reverse=True)
    contact_ids = dr.get_contacted_tech_ids(uid)
    top_k = [item_id for score, item_id in user_preds if item_id not in contact_ids][:k]
    return top_k

if __name__ == '__main__':
    time = datetime.now()
    uids = user_pool
    recommendations = [ensemble_recommend(uid, 5) for uid in uids]
    df = pd.DataFrame(recommendations)
    email_clicked = []
    for i, uid in enumerate(uids):
        email_clicked.append([tech_id  for tech_id in recommendations[i] if tech_id in dr.get_clicked_tech_ids(uid)])
    output = pd.concat([pd.DataFrame({'user_id': uids}), df, pd.DataFrame({'email_clicked': email_clicked})], axis=1)
    output.to_csv('ensemble_recommendations.csv', index=False)
    print 'Time elapsed: ', datetime.now() - time
