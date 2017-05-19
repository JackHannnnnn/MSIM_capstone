# MSIM_capstone
This repository holds the code for MSIM capstone project.

## Instructions on running recommendation code

The processes below assume that your database is on your localhost. The database schema is the same as in the **capstone-MM-DD-YYYY.sql** file you provided with us.

The recommendation algorithm is written in **Python 2.7**. Please execute them in Python2 environment.
The recommendation algorithm requires the installation of libraries below:
**MySQLdb, numpy, pandas, itertools, sklearn.metrics.pairwise, scipy, re, csv**

1. Run ``preprocess.py`` to calculate score data and write back the score table to the database.
  * Please replace the parameters **host**, **user**, **passwd** and **db** in line 22 and 85 with your own information.
  * After executing this file, please wait until the console prints Done. The message printed looks like this:
```
Start...
Done.
```
2. Run ``Datareader.py`` to interact with MySQL database.
  * Please replace the parameters **host**, **user**, **passwd** and **db** with your own information.

3. Run ``EnsembleRecommender.py`` to generate personalized recommendations for each user.
  * Please note that this file takes about **20 mins** to run and is expected to take more time when the number of users and technologies increase in the database. After running the file, you should be able to see the message below:
  ```
Start training content_based model...
Done
Time elapsed: 0:00:00.363000

Start training interacted content_based model...
Done
Time elapsed: 0:00:26.373000

Start training collaborative filtering model...
Total num of calculation: 1210923
Num of calcuation finished: 100000      Time elapsed: 0:01:34.244000
Num of calcuation finished: 200000      Time elapsed: 0:03:08.412000
Num of calcuation finished: 300000      Time elapsed: 0:04:42.130000
Num of calcuation finished: 400000      Time elapsed: 0:06:22.406000
Num of calcuation finished: 500000      Time elapsed: 0:08:15.333000
Num of calcuation finished: 600000      Time elapsed: 0:09:53.467000
Num of calcuation finished: 700000      Time elapsed: 0:11:35.431000
Num of calcuation finished: 800000      Time elapsed: 0:13:09.840000
Num of calcuation finished: 900000      Time elapsed: 0:14:41.403000
Num of calcuation finished: 1000000     Time elapsed: 0:16:12.410000
Num of calcuation finished: 1100000     Time elapsed: 0:17:46.296000
Num of calcuation finished: 1200000     Time elapsed: 0:19:17.530000
Done
Time elapsed: 0:19:19.833000
```
  * After the code finishes running, it writes back a **recommendationresultforusers table** back to MySQL database. By default, we are generating 10 recommendations for each user. If you want to configure the number of recommendations, please change the number 10 in line 251 to the number of recommendations you want to generate and rerun the file.

  * You can check the recommendation table by executing
```sql
select * from recommendationresultforusers;
```

4. Run ``EnsembleRecommenderforTechnology.py`` to generate similar technologies for a given technology.
After running the file, you should be able to see the message below:
```
Start building tech keyword sim matrix...
Done.

Start building item_based Collaborative Filtering sim matrix...
Done.

Start building Ensemble sim matrix...
Done.

Start writing recommendations to the database...
Done
```
  * After the code running completes, it writes back a recommendationresultfortechs table back to MySQL database. By default, we are generating 10 recommendations for each technology. If you want to configure the number of recommendations, please change the number 10 in line 146 to the number of recommendations you want to generate and rerun the code.

  * You can check the recommendation table by executing
```sql
select * from recommendationresultfortechs;
```
