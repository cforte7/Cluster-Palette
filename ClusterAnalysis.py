import matplotlib.pyplot as plt
from DB_Maintain import DB
from matplotlib.animation import FuncAnimation
from RedditScrape import PhotoClustering
from skimage import color
PC = PhotoClustering()
DBC = DB()

subs = ['gardening', 'outrun', 'desert', 'Autumn','goldenretrievers', 'goth', 'TheDepthsBelow','TheWayWeWere','OldSchoolCool']

for sub in subs:
    sub_colors = []
    x = []
    y = []
    z = []
    for row in DBC.new_query("SELECT clusters FROM clusters WHERE subreddit = '{}' LIMIT 50".format(sub)):


        rgb = color.lab2rgb(([row[0]]))[0]
        for cluster in row[0]:
            rgb = color.lab2rgb([[cluster]])[0][0]
            x.append(cluster[0])
            y.append(cluster[1])
            z.append(cluster[2])
            sub_colors.append(list(rgb))
#
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(x,y,z,c=sub_colors, marker='o',alpha=1)
    plt.title("Cluster Results for Subreddit '{}'".format(sub))
    ax.set_xlabel("L")
    ax.set_ylabel("a")
    ax.set_ylabel("b")
    def update(i):
        ax.view_init(30, i)
    anim = FuncAnimation(fig,update,frames=[x for x in range(360)],interval=100)
    anim.save('D:/PhotoDB/Gifs/{}Scatter.gif'.format(sub))
