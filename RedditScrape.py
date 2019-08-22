from sklearn.cluster import MeanShift, estimate_bandwidth
import requests as r
import json
import time
import datetime
from pprint import pprint
from DB_Maintain import DB
import numpy as np
from PIL import Image
from skimage import color
import os
import sqlite3
import sys
from glob import glob


class PSInterface:
    def __init__(self):
        self.last_time = int(time.time())
    
    def urlGen(self, endpoint):
        url = 'https://api.pushshift.io/reddit/search/'+str(endpoint)+'/'
        return url
    
    def SubmissionCallByScore(self, count, subreddit):
        entries = []
        url = self.urlGen("submission")
        current_entires = [x[0] for x in DBC.new_query('''SELECT id FROM submissions WHERE subreddit = '{}' '''.format(sub))]
        
        new_score = 999999999
        while len(entries) < count:
            payload = {"subreddit": subreddit, "sort_type": "score", "score": "<"+str(new_score), "size": 500}
            api_request = r.get(url, payload)
            status_code = api_request.status_code


            if status_code == 200:
                call_data = json.loads(api_request.text)['data']
                time.sleep(3)
                for entry in call_data:
                    if entry['id'] not in current_entires:
                        entries.append(entry)
                if len(call_data) == 0:
                    return entries
                elif len(entries) == 0:
                    new_score = call_data[-1]['score']
                else:
                    new_score = entries[-1]['score']
            else:
                print("[API Message] Error calling Pushshift API with status code " + str(status_code))
                time.sleep(5)

            if len(entries) > count:
                return entries[:count]


    def SubmissionCallByTime(self, payload):
        url = self.urlGen("submission")
        api_request = r.get(url,payload)
        status_code = api_request.status_code

        if status_code == 200:
            print('[API Message] Sucessful request at '+str(datetime.datetime.now())+' with payload '+str(payload))
            call_data = json.loads(api_request.text)['data']
            self.last_time = call_data[-1]['created_utc']
            time.sleep(1/2)  # To avoid rate limiting issues
            return call_data
        else:
            print("[API Message] Error querying API - Status Code:"+str(status_code))
            print('[API Message] \'Before\' parameter for most recent query: '+str(self.last_time))
            print('[API Message] Waiting one minute before next attempt.')
            time.sleep(60)
            return 0

    def apiCommentCall(self, post, nest_level):
        url = self.urlGen('comment')
        payload = {'link_id': post, 'size': 500,"nest_level": nest_level}
        api_request = r.get(url, payload)
        sub_comments = []
        call_data = json.loads(api_request.text)['data']
        sub_comments += call_data

        mintime = call_data[-1]['created_utc']
        while len(call_data) != 0:
            payload = {'link_id': post, 'size': 500, 'nest_level': nest_level, 'before':mintime}
            api_request = r.get(url,payload)
            call_data = json.loads(api_request.text)['data']
            if len(call_data) > 0:
                mintime = call_data[-1]['created_utc']
                sub_comments += call_data
            else:
                break
        return sub_comments

    def restartClock(self):
        self.last_time = int(time.time())


class PictureDownload:
    def __init__(self,pic_path):
        self.pic_path = pic_path

    def download_pics(self, url, photo_id,subreddit):  # download picture from web and save in local folder
        try:
            response = r.get(url)
            filetype = '.' + url.split('.')[-1]
            if filetype in ['.png', '.jpg']:
                filename = photo_id + filetype
                filepath = self.pic_path + subreddit + '/' + filename  # basepath/subreddit/filename
                print("[Photo Download] Downloading picture from " + str(url))
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(4096):
                        f.write(chunk)
                filesize = os.path.getsize(filepath)
                photo_info = [photo_id,filename,subreddit,filesize,filepath]
                return photo_info

        except r.exceptions.ConnectionError:
            print("[Picture Download] Error Occurred on url "+str(url))
            pass


class PhotoClustering:
    def __init__(self):
        pass

    def mean_Clusters(self, pic_path, subreddit):
        file = pic_path.split("\\")[-1]
        print("[Photo Clustering] Running Mean Shift Algorithm on photo "+file)


        try:
            pic = Image.open(pic_path)
            pic_array = np.asarray(pic)
            I = np.copy(pic_array)
            h, w, p = I.shape

            # Drop 4th value in each pixel if present
            if p == 4:
                I = I[:,:,:3]
                p = 3

            I = np.reshape(I, (h * w, p))
            np.random.shuffle(I)
            I = I[:5000]
            I = color.rgb2lab([I])[0]
            bandwidth = estimate_bandwidth(I)
            ms = MeanShift(bandwidth=bandwidth, bin_seeding=True, n_jobs=-1)
            cluster_counts = ms.fit_predict(I)
            meanshift_fit = ms.fit(I)
            cluster_centers_ms = meanshift_fit.cluster_centers_
            labels = ms.labels_
            cluster_wgts = np.unique(cluster_counts, return_counts=True)[1]
            print("[Photo Clustering] Successful clustering for file "+file)
            return [file, subreddit, I, bandwidth, labels, cluster_centers_ms, cluster_wgts]

        except:
            print("[Photo Clustering] Error " + str(sys.exc_info()[0]) + "has occurred on photo "+file)



if __name__ == "__main__":
    a = PSInterface()
    DBC = DB()
    Pic = PictureDownload('D:/PhotoDB/')
    PC = PhotoClustering()

    
    ### Call for submissions from PushShift API and store in submissions table

    subs = [x[0] for x in DBC.new_query('''SELECT DISTINCT Subreddit FROM submissions''')]
    target_vals = ['id', 'title', 'url', 'domain', 'subreddit', 'subreddit_id', 'full_link', 'created_utc', 'author','score']
    #DBC.clean_tables()
    for sub in subs:
        api_call = a.SubmissionCallByScore(500,sub)
        data_stage = []

        for x in api_call:
            row_stage = []
            for val in target_vals:
                data = []
                if val == 'created_utc' or val == 'score':
                    row_stage.append(int(x[val]))
                else:
                    row_stage.append(str(x[val]))

            data_stage.append(row_stage)

        print("[DB Message] Mass inserting " + str(len(data_stage)) + " submissions for subreddit "+sub)
        DBC.c.executemany("INSERT INTO submissions (ID,Title,URL,URLDomain,Subreddit,SubredditID,PostURL,PostTime,PostAuthor,PostScore) VALUES (?,?,?,?,?,?,?,?,?,?)", data_stage)
        DBC._conn.commit()

    ### Download top 50 photos for each target subreddit and store entry in photos DB
    
    photo_stage = []
    for sub in subs:
        if not os.path.exists("D:/PhotoDB/"+sub):
            os.mkdir("D:/PhotoDB/"+sub)

        query_str = "SELECT id, URL, Subreddit FROM submissions WHERE Subreddit = '{}' and (URL like '%.png' or URL like '%.jpg') and id not in (SELECT id FROM photos WHERE subreddit = '{}') ORDER BY PostScore DESC LIMIT 50;".format(sub,sub)
        query = DBC.new_query(query_str)

        for x in query:
            post_id = x[0]
            URL = x[1]
            subreddit = x[2]
            photo_row = Pic.download_pics(URL,post_id,subreddit)
            photo_stage.append(photo_row)

    DBC.c.executemany("INSERT INTO photos (id, filename, subreddit, size, path) VALUES (?,?,?,?,?)", photo_stage)
    DBC._conn.commit()


    ### Delete photos that are "photo was deleted" thumbnail from imgur

    error_paths = [x[0] for x in DBC.new_query("SELECT path FROM photos where size < 3000")]
    for x in error_paths:
        DBC.new_query("DELETE FROM photos WHERE path = ?",(x,))
        os.remove(x)
        print("Entry "+ x + " Deleted")
    DBC._conn.commit()

    print("Testing again after delete")
    error_paths = [x[0] for x in DBC.new_query("SELECT path FROM photos where size < 3000")]
    print("Count of error photos:" + str(len(error_paths)))



    ### Run Mean Shift Clustering algorithm on downloaded photos

    cluster_stage = []
    photo_paths = [(x[0],x[1]) for x in DBC.new_query('''SELECT path, subreddit FROM photos WHERE filename NOT IN (SELECT file FROM clusters) ''')]
    for photo in photo_paths:
        cluster_row = PC.mean_Clusters(photo[0],photo[1])
        try:
            DBC.new_query("INSERT INTO clusters VALUES (?,?,?,?,?,?,?)",cluster_row)
        except:
            print("[DB Message] Error "+str(sys.exc_info())+"when inserting clustering row for file "+str("file"))
        DBC._conn.commit()

  





