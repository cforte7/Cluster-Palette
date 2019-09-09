
# Background

Machine learning algorithms are becoming an increasingly important aspect of analyzing data and providing users with enjoyable features and benefits. One application is the process of using clustering algorithms to identify the dominant colors in a photo. This is done by using the three color values that make up a pixel (RGB, LaB, etc.) as the three features in your dataset to find the most prominant colors. Below you can see an example of the scatterplot created by taking a random sample of photos from an image. While there are various articles and blog posts that accomplish this already, there are two gaps in the methods that I see consistently. 
<br> <img src='/static/OceanScatter.gif' width=400> <img src='/static/ocean.jpg' width=400>

### Issue #1 - Limited Photo Types for Proof of Concept
The photographs used to demonstrate the methods have clearly defined color palletes that can easily be selected by humans. Below you can see the example images used for tutorials from <a href="https://buzzrobot.com/dominant-colors-in-an-image-using-k-means-clustering-3c7af4622036">Buzzrobot</a>, <a href="https://www.dataquest.io/blog/tutorial-colors-image-clustering-python/">DataQuest</a>, and <a href="https://towardsdatascience.com/extracting-colours-from-an-image-using-k-means-clustering-9616348712be">Towards Data Science</a>. You can reasonably assume that these types of photos with a stark separation of colors will produce clean sets of data with predictable results. This begs the question: what about the many pictures that do not fit this narrow mold? How can we be sure that these methods work as a more general solution?

<img src='/static/buzzrobot.jpg' width=200> <img src='/static/dataquest.png' width=200> <img src='/static/towards_data_science.png' width=400> 


### Issue #2 - Manual User Input
In the aforementioned articles, the programmers have to manually enter in the number of clusters. When you have such clearly defined colors and are running it on a few photos, this hueristic method is suitable. With our example photos, it is easy to see that the photos will require 5, 3 and 6 clusters respectively. This again poses a potential issue when trying to create a more robust application. Will this work suitably for photos that don't have clearly defined colors? What if we aren't sure what the most optimal number of clusters is. In addition to the inherent ambiguity in this process, this is not a scaleable solution. Manually inputting the cluster count for each photo would be an incredibly time consuming task if you have many photos and has no reasonable path for automation.

# Purpose
In this paper I will demonstrate the process of visualizing the most prevelant colors from large groups of photos. We will accomplish this by running clustering algorithms on groups of photos and plotting the resulting clusters.  Our use case will be scraping photos from specific Subreddits on <a href src='Reddit.com'>Reddit</a> and generating scatter plots.  For those not familiar, a Subreddit can be thought of as a themed category where users submit links, pictures, or other internet content to be voted and commented on. 

This process will include the following:
1. Query the Pushshift API for the Reddit submissions in the target subreddits
2. Download pictures from submissions that are identifited as being image-based
3. Apply the Mean Shift Clustering Algorithm and store the results
4. Analyze the results and create data visualizations for each Subreddit based on the clustering results

## Data Gathering

### Database Setup

Before any analysis can be done, a sufficient amount of data must be gathered. For this applciation we would like to download and store large quantities of photos along with some metadata regarding the pictures. 

The first step is to develop the SQL database schema.

<img src='/static/Cluster-Pallete Schema.png'>

In order to manage this database I created a python file `DB_Maintain.py` that contains a class to handle the required database functions. Most of the functionality is fairly straight forward so I will not go into to much detail on it, but something worth noting is the handling of numpy arrays for storage. In the database schema, the `clusters` table has columns with datatype `numpy_array`. Since this is not a standard SQL datatype, it must be stored as a binary object (BLOB) and there are some additional steps needed to handle this. In the `DB_Maintain.py` file we must outline the specific conversion process between a binary object and a numpy array and vice versa.

```python
def adapt_array(array):
    out = io.BytesIO()
    np.save(out, array)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(string):
    out = io.BytesIO(string)
    out.seek(0)
    return np.load(out)

sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("array", convert_array)
```

The function `adapt_array(array)` takes in a numpy array and returns it as a binary object and the function `convert_array(string)` takes in a binary object and returns a numpy array. The last two lines signal to our database that these are the functions to be run  when working with a column designated as an `array` type. With this in place, we can interface with our database using numpy arrays as if they are native data types instead of performing this conversion every interaction.

### Calling Pushshift API

Now that we have our database set up, we must find our images to download. <a href='pushshift.io>Pushshift</a> is an API that allows users to query for posts and comments from Reddit and receive the data in JSON. I've created a class called `PS_Interface` to handle interactions with the API. While there are various methods in the class, here we will focus on the `SubmissionCallByScore` method. 

```Python
class PSInterface:
    def __init__(self):
        self.last_time = int(time.time())

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
                time.sleep(1)
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
```  
The method `SubmissionCallByScore` has two arguments:
* `count` - the number of posts you want added to the database
* `subreddit` - the subreddit you want the posts from

The method first checks our database for current entries to avoid any duplicates. Next the method will query the API for the highest ranked submissions, check if these are already stored in the database (ignoring them if they are). The query parameters are then updated based on the lowest score post in the request and a new request is made. This update and query process continues until we have either collected enough new submissions to satisfy our `count` or have run out of submissions to query. Once one of those two occur, we return the list of submissions. 

In order to keep the class scaleable and reusable for future projects, the ```submission_call_by_score``` method (and all other methods) returns a list of dictionaries with all of the data the API provides. For the purposes of this project, we only need a subset of the data retreived in the API call so we will handle this filtering in our ```main()``` function. 


```python
    subs = ["BelowTheDepths","OldSchoolCool","Gardening","Goth","Outrun","TheWayWeWere","Desert"]
    target_vals = ['id', 'title', 'url', 'domain', 'subreddit', 'subreddit_id', 'full_link', 'created_utc', 'author','score']
    insert_str = '''INSERT INTO submissions (ID,Title,URL,URLDomain,Subreddit,SubredditID,PostURL,PostTime,PostAuthor,PostScore) 
        VALUES (?,?,?,?,?,?,?,?,?,?)'''
        
    for sub in subs:
        api_call = a.submission_call_by_score(500,sub)
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
        DBC.c.executemany(insert_str, data_stage)
        DBC._conn.commit()
```

Before any calls are made we must outline the list of Subreddits that we would like to target and store them in the list ```subs```. Next we establish the target values that we want to store in our database and store this in another list ```target_vals```. First level of our loop is the target subreddit and we use this along with our request count to call the ```submission_call_by_score``` method. Now that we have the requested data, we iterate through the ```target_vals``` and store them either as a ```str``` or as an ```int```  based on the value. Once we have filtered all of our data we will insert the rows into the database using the ```executemany()``` method.

### Photo Scraping

Once we have all of our submissions stored, we must download the photos associated with those submissions. Similar to working with the Pushshift API, a class is created to download the photos and we extend the functionality in ```main```. 

```python
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
```

Our class ```PictureDownload``` takes one parameter when we instantiate the class ```pic_path```. This parameter will be the path to the directory we want to store our photos in. This class has one method ```download_pics(self, url, photo_id,subreddit)```. The ```url``` parameter specifies the URL that we will download the photo from, ```photo_id``` is a unique identifier for the photo, and ```subreddit``` specifies the subreddit that the photo is sourced from in order to organize the files when we save them locally. The process for the method is fairly straight forward - we make a request for the image, write the file to disk, and return a list with information about the photo that we will store in our ```photos``` database.

We use the following code to apply our class in our ```main``` method:
```python
    photo_stage = []

    
    for sub in subs:
        if not os.path.exists("D:/PhotoDB/"+sub):
            os.mkdir("D:/PhotoDB/"+sub)
            query_str = "SELECT id, URL, Subreddit FROM submissions WHERE Subreddit = '{}' and (URL like '%.png' or URL like '%.jpg')                       and id not in (SELECT id FROM photos WHERE subreddit = '{}') ORDER BY PostScore DESC LIMIT 50;".format(sub,sub)
        query = DBC.new_query(query_str)

        for x in query:
            post_id = x[0]
            URL = x[1]
            subreddit = x[2]
            photo_row = Pic.download_pics(URL,post_id,subreddit)
            photo_stage.append(photo_row)

    DBC.c.executemany("INSERT INTO photos (id, filename, subreddit, size, path) VALUES (?,?,?,?,?)", photo_stage)
    DBC._conn.commit()
``` 
Similar to our process when querying the Pushshift API, we will iterate through our ```subs``` list. Before any photos are downloaded, we check to see if the directory for that subreddit exists and if it does not, then we create one. We next query our database for all of the submissions that meet two criteria:
* The submission url ends in ```.png```, ```.jpg```, or ```.jpeg``` 
* The photo has not been downloaded already

Based on this query we now have a list of the photos that we need to download so we iterate through this list, download the photos, and store an entry in the ```photos``` database for each photo. 


### Clustering Analysis

Continuing our theme of Class structure and application extenstion we will now examine our ```PhotoClustering``` Class and it's usage in ```main()```. 


```python
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
```

In our class we have one method ```mean_clusters(self, pic_path, subreddit)``` with two parameters
* ```pic_path``` - the path to the file that the script will open
* ```subreddit``` - the subreddit that the picture is sourced from


```python
 pic = Image.open(pic_path)
 pic_array = np.asarray(pic)
 I = np.copy(pic_array)
 ```           
The first step in our method is to open the specified file. We then convert the data for the picture to a numpy array and create a copy of the array. While this may seem like an unneeded step at first, the numpy array when read from the image is not writeable and an error occurs when we try to perform any manipulations. To overcome this we create a deep copy with the ```np.copy(pic_array)``` function. 


```python
h, w, p = I.shape

# Drop 4th value in each pixel if present
if p == 4:
    I = I[:,:,:3]
    p = 3
I = np.reshape(I, (h * w, p))
np.random.shuffle(I)
I = I[:5000]
I = color.rgb2lab([I])[0]
 ```
 Once we have our mutable numpy array we must perform some basic manipulations to prepare our data for the analysis. The first step is to store the shape of the photo and check for the dimensions. If the third dimension is 4, this means that the photo has its pixels stored in RGBA (A stands for Alpha, or transparency). If the alpha channel is present in the image, we will drop that dimension and update our ```p``` dimension to 3. We then reshape the array so that it becomes a two dimensional array with ```h*w``` rows and 3 columns. We then shuffle the rows and take the first 5000 rows in order to take a random sample of pixels from the photos. Once we have our sample set of data we call the ```color.rgb2lab()``` function from the scikit image module to convert the data from RGB values to LaB values. We make this conversion because when visualizing pixels in 3D space, the Lab space is much more suited to how the human eye perceives colors compared to RGB (another pitfall of comparable papers on this topic). <a href='https://en.wikipedia.org/wiki/CIELAB_color_space'>For more information regarding Lab Color Space you can read the Wikipedia page.</a>
 
 
 ```python
bandwidth = estimate_bandwidth(I)
ms = MeanShift(bandwidth=bandwidth, bin_seeding=True, n_jobs=-1)
cluster_counts = ms.fit_predict(I)
meanshift_fit = ms.fit(I)
cluster_centers_ms = meanshift_fit.cluster_centers_
labels = ms.labels_
cluster_wgts = np.unique(cluster_counts, return_counts=True)[1]
print("[Photo Clustering] Successful clustering for file "+file)
return [file, subreddit, I, bandwidth, labels, cluster_centers_ms, cluster_wgts]
```

With our data properly manipulated, we are ready to perform the clustering. For this process we will use the Mean Shift algorithm. There are a few motivations for choosing this algorithm specifically as opposed to K-Means found in the example articles listed at the beginning of the paper. The first is that the number of clusters created is determined by the algorithm itself and not by the user. Every photo is different and we cannot take a "one size fits all" approach to a number of clusters so having the algorithm produce this will increase our consistancy and reliability than the highly subjective method of human selection. The other main motivation is the suitibility for the given dataset. From the <a href='https://scikit-learn.org/stable/modules/clustering.html#overview-of-clustering-methods'>Scikit-Learn Documentation on Clustering</a>, the Mean Shift method's use case is "Many clusters, uneven cluster size, non-flat geometry". Using the example posted at the beginning of the write up, it is fair to say that a standard photograph that we expect to see posted on Reddit will have these characteristics.

Now that we have selected our clutering method, let's take a look at the parameters. Our ```MeanShift``` class has one main parameter - the bandwidth. To understand the bandwidth, we first have to understand how the Mean Shift Algorithm functions. The algorithm first creates a <A href='https://en.wikipedia.org/wiki/Kernel_density_estimation'>Kernal Density Estimation</a> to estimate the probability distribution function of a set of data. The bandwidth determines the size of the area used to calculate a density for our KDE. As a larget bandwidth is used, our KDE will generate fewer, more populated clusters and vice versa. There is no single correct bandwidth and is entirely dependant on the dataset. Fortunately ```sklearn``` provides a way to automatically generate and bandwidth value based on the data provided and we implement this to further automate our process.


### Results

```python
subs = ['outrun','TheDepthsBelow','TheWayWeWere','autumn']
for sub in subs:
    sub_colors = []
    x = []
    y = []
    z = []
    
    # Query clusters based on the target subreddit
    for row in DBC.new_query("SELECT clusters FROM clusters WHERE subreddit = '{}' LIMIT 50".format(sub)):

        # Convert Pixels to RGB for coloring data points and create arrays
        rgb = color.lab2rgb(([row[0]]))[0]
        for cluster in row[0]:
            rgb = color.lab2rgb([[cluster]])[0][0]
            x.append(cluster[0])
            y.append(cluster[1])
            z.append(cluster[2])
            sub_colors.append(list(rgb))

    # Plotting
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(x,y,z,c=sub_colors, marker='o',alpha=1)
    plt.title("Cluster Results for Subreddit '{}'".format(sub))
    ax.set_xlabel("L")
    ax.set_ylabel("a")
    ax.set_ylabel("b")
    
    # Create and save gif of rotating scatter plot
    def update(i):
        ax.view_init(30, i)
    anim = FuncAnimation(fig,update,frames=[x for x in range(360)],interval=100)
    anim.save('D:/PhotoDB/Gifs/{}Scatter.gif'.format(sub))
```

From our clustering results, we can create scatter plots to visualize the data. Below are four subreddits that demonstrate the results along with some example photos used in the analysis.


#### Outrun -Dedicated to 80's neon style art 
Examples:<br>
<img src='/static/Example Photos/Outrun/6ym9td.png' width=250>
<img src='/static/Example Photos/Outrun/7lz2xt.jpg' width=250>
<img src='/static/Example Photos/Outrun/863spl.jpg' width=300>
<br>
Result:
<br>
<img src='/static/Gifs/outrunScatter.gif'>

#### The Depths Below - An Ocean themed subreddit
Examples:<br>
<img src='/static/Example Photos/TheDepthsBelow/6jn9ar.jpg' width=300>
<img src='/static/Example Photos/TheDepthsBelow/6owaev.jpg' width=250>
<img src='/static/Example Photos/TheDepthsBelow/6pgtvp.jpg' width=300>
<br>
Result:
<br>
<img src='/static/Gifs/TheDepthsBelowScatter.gif'>


#### The Way We Were  - Old, mostly black and white photos depicting life from the early to mid 20th century
Examples:<br>
<img src='/static/Example Photos/TheWayWeWere/7qlm00.jpg' width=250>
<img src='/static/Example Photos/TheWayWeWere/7riclb.jpg' width=250>
<img src='/static/Example Photos/TheWayWeWere/8e3eoi.jpg' width=250>
<br>
Result:
<br>
<img src='/static/Gifs/TheWayWeWereScatter.gif'>

#### Autumn - For lovers of Fall
Examples:<br>
<img src='/static/Example Photos/Autumn/8ya73b.jpg' width=250>
<img src='/static/Example Photos/Autumn/9czbb0.jpg' width=250>
<img src='/static/Example Photos/Autumn/9aiust.jpg' width=250>
<br>
Result:
<br>
<img src='/static/Gifs/AutumnScatter.gif'>
