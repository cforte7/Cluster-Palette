# Background

Machine learning algorithms are becoming an increasingly important aspect of analyzing data and providing users with enjoyable features and benefits. One application is the process of using clustering algorithms to identify the dominant colors in a photo. This is done by using the 3 color values that make up a pixel (RGB, LaB, etc.) as the three features in your dataset to find the most prominant colors. While there are various articles and blog posts that accomplish this already, there are two gaps in the methods that I see consistently. 


### Issue #1 - Limited Photo Types for Proof of Concept
The photographs used to demonstrate the methods have clearly defined color palletes that can easily be selected by humans. Below you can see the example images used for tutorials from <a href="https://buzzrobot.com/dominant-colors-in-an-image-using-k-means-clustering-3c7af4622036">Buzzrobot</a>, <a href="https://www.dataquest.io/blog/tutorial-colors-image-clustering-python/">DataQuest</a>, and <a href="https://towardsdatascience.com/extracting-colours-from-an-image-using-k-means-clustering-9616348712be">Towards Data Science</a>. You can reasonably assume that these types of photos with a stark separation of colors will produce clean sets of data with predictable results. This begs the question: what about the many pictures that do not fit this narrow mold? How can we be sure that these methods work as a more general solution?

<img src='/static/buzzrobot.jpg' width=200> <img src='/static/dataquest.png' width=200> <img src='/static/towards_data_science.png' width=400> 


### Issue #2 - Manual User Input
In the aforementioned articles, the programmers have to manually enter in the number of clusters. When you have such clearly defined colors and are running it on a few photos, this hueristic method is suitable. With our example photos, it is easy to see that the photos will require 5, 3 and 6 clusters respectively. This again poses a potential issue when trying to create a more robust application. Will this work suitably for photos that don't have clearly defined colors? What if we aren't sure what the most optimal number of clusters is. In addition to the inherent ambiguity in this process, this is not a scaleable solution. Manually inputting the cluster count for each photo would be an incredibly time consuming task if you have many photos and has no reasonable path for automation.

# Purpose
In this paper I will demonstrate the process of creating color palettes from large groups of photos to aid in design choices. Our use case will be scraping photos from specific Subreddits on <a href src='Reddit.com'>Reddit</a> and generating a color palette to help suggest a color scheme for that Subreddit.  For those not familiar, a Subreddit can be thought of as a themed category where users submit links, pictures, or other internet content to be voted and commented on. 

This process will include the following:
1. Query the Pushshift API for the Reddit submissions in the target subreddits
2. Download pictures from submissions that are identifited as being image-based
3. Apply the Mean Shift Clustering Algorithm and store the results
4. Analyze the results, create data visualizations and generate color palettes for each Subreddit based on the clustering results

## Data Gathering

### Database Setup

Before any analysis can be done, a sufficient amount of data must be gathered. For this applciation we would like to download and store large quantities of photos along with some metadata regarding the pictures. 

The first step is to develop the SQL database schema.

<img src='/static/Cluster-Pallete Schema.png'>

In order to manage this database I created a python file `DB_Maintain.py` that contains a class to handle the required database functions. Most of the functionality is fairly straight forward so I will not go into to much detail on it, but something worth noting is the handling of numpy arrays for storage. As noted in the database schema, the `clusters` table has columns with datatype `numpy_array`. Since this is not a standard SQL datatype, it must be stored as a binary object (BLOB) and there are some additional steps needed to handle this. In the `DB_Maintain.py` file we must outline the specific conversion process between a binary object and a numpy array and vice versa.

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

The function `adapt_array(array)` takes in a numpy array and returns it as a binary object and the function `convert_array(string)` takes in the binary object and returns a numpy array. The last two lines signal to our database that these are the functions to be run automatically when working with a column designated as an `array` type. With this in place we can pass numpy arrays to our insert statement without any issue and when reading data we will be passed a numpy array instead of a binary object.

### Pushshift API Class

Now that we have our database set up, we must find our images to download. As mentioned previously we will be scraping photos from our targeted Subreddits so first we must find the posts themselves. <a href src='pushshift.io>Pushshift</a> is an API that allows users to query for posts and comments from Reddit and receive the data in JSON. I've created a class called `PS_Interface` to handle interactions with the API. While there are various methods in the class, most of them are for uses outside of the scope of this project. Here we will focus on the `SubmissionCallByScore` method.

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

The method first checks our database for current entries to avoid any duplicates. Next the method will query the API for the highest ranked submissions, check if these are already stored in the database (ignoring them if they are). The query parameters are then updated based on the lowest score post in the request and a new request is made. This update and query process continues until we have either collected enough new submissions to satisfy our `count` or have run out of submissions. Once one of those two occur, we return the list of submissions. 

### Pushshift API Usage in Main()



