# Background

Machine learning algorithms are becoming an increasingly important aspect of analyzing data and providing users with enjoyable features and benefits. One application is the process of using clustering algorithms to identify the dominant colors in a photo. This is done by using the 3 color values that make up a pixel (RGB, LaB, etc.) as the three features in your dataset to find the most prominant colors. While there are various articles and blog posts that accomplish this already, there are two gaps in the methods that I see consistently. 


### Issue #1 - Limited Photo Types for Proof of Concept
The photographs used to demonstrate the methods have clearly defined color palletes that can easily be selected by humans. Below you can see the example images used for tutorials from <a href="https://buzzrobot.com/dominant-colors-in-an-image-using-k-means-clustering-3c7af4622036">Buzzrobot</a>, <a href="https://www.dataquest.io/blog/tutorial-colors-image-clustering-python/">DataQuest</a>, and <a href="https://towardsdatascience.com/extracting-colours-from-an-image-using-k-means-clustering-9616348712be">Towards Data Science</a>. You can reasonably assume that these types of photos with a stark separation of colors will produce clean sets of data with predictable results. This begs the question: what about the many pictures that do not fit this narrow mold? How can we be sure that these methods work as a more general solution?

<img src='/static/buzzrobot.jpg' width=200> <img src='/static/dataquest.png' width=200> <img src='/static/towards_data_science.png' width=400> 


### Issue #2 - Manual User Input
In the aforementioned articles, the programmers have to manually enter in the number of clusters. When you have such clearly defined colors and are running it on a few photos, this hueristic method is suitable. With our example photos, it is easy to see that the photos will require 5, 3 and 6 clusters respectively. This again poses a potential issue when trying to create a more robust application. Will this work suitably for photos that don't have clearly defined colors? What if we aren't sure what the most optimal number of clusters is. In addition to the inherent ambiguity in this process, this is not a scaleable solution. Manually inputting the cluster count for each photo would be an incredibly time consuming task if you have many photos and has no reasonable path for automation.

# Purpose
In this paper I will demonstrate my process of scraping and storing photos from Reddit through the Pushshift API, storing the photos locally along with metadata, applying the Mean Shift Clustering algorithm, analyzing the results and generating color palletes to groupings of photos.

## Data Gathering
Before any analysis can be done, a sufficient amount of data must be gathered. For this applciation we would like to download and store large quantities of photos along with some metadata regarding the pictures.

