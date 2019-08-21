# Background

Machine learning algorithms are becoming an increasingly important aspect of analyzing data and providing users with enjoyable features and benefits. One such application is the process of using clustering algorithms to identify the dominant colors in a photo. While there are various articles and blog posts online that accomplish this already, there is are two recurring gaps in the methods that I see. 

### Issue #1 - Limited Photo Types for Proof of Concept
The photographs used to demonstrate the methods have clearly defined color palletes that can easily be selected by humans. Below you can see the example images used for tutorials from <a href="https://buzzrobot.com/dominant-colors-in-an-image-using-k-means-clustering-3c7af4622036">Buzzrobot</a>, <a href="https://www.dataquest.io/blog/tutorial-colors-image-clustering-python/">DataQuest</a>, and <a href="https://towardsdatascience.com/extracting-colours-from-an-image-using-k-means-clustering-9616348712be">Towards Data Science</a>. As you  can see the resulting clusters are very easy to identify and would provide very clean datasets that we can't assume we would find in other photos. That begs the question what about the many pictures taken that do not fit that narrow mold? How can we be sure that these methods work as a more general solution?

<img src='/static/buzzrobot.jpg' width=200> <img src='/static/dataquest.png' width=200> <img src='/static/towards_data_science.png' width=400> 


### Issue #2 - Manual User Input
In the above methods programmers have to manually enter in the number of clusters. When you have such clearly defined colors and are running it on a few photos, this hueristic method is suitable. For example with the above photos, it is easy to see that the photos will require 5, 3 and 6 clusters respectively. The manual entry again poses a potential issue when trying to create a more robust application that will work suitably for photos that don't have clearly defined colors. Additionally, this is not a scaleable solution - manually inputting the cluster number for each photo would be an incredibly time consuming task for many photos and has no reasonable path for automation.

# Purpose
In this paper I will demonstrate my process of scraping and storing photos from Reddit through the Pushshift API, storing the photos locally along with metadata, applying the Mean Shift Clustering algorithm, and analyzing the results and generating color palletes to groupings of photos.

## Data Gathering
Before any analysis can be done, a sufficient amount of data must be gathered. For this applciation we would like to download and store large quantities of photos along with some metadata regarding the pictures.

