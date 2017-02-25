import ScoreCalculate as sc
import DataReaderplus as dr

score = sc.calculate_score()
# sc.create_table(score) # create score table in database
scoreData = dr.DataReader().get_score_data() # read data from the Score table
print scoreData # return a dataframe