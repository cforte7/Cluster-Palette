import numpy as np
import matplotlib.pyplot as plt
from DB_Maintain import DB
from skimage import color
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import animation

DBC = DB()
subs = ['gardening', 'outrun', 'desert', 'Autumn','goldenretrievers', 'goth', 'TheDepthsBelow','TheWayWeWere','OldSchoolCool']

for sub in subs:
    sub_colors = []
    x = []
    y = []
    z = []
    for row in DBC.new_query("SELECT clusters FROM clusters WHERE subreddit = '{}'".format(sub)):
        for cluster in row[0]:
            rgb = color.lab2rgb([[cluster]])[0][0]
            x.append(cluster[0])
            y.append(cluster[1])
            z.append(cluster[2])
            sub_colors.append(list(rgb))

    fig = plt.figure()
    ax = fig.add_subplot(111,projection='3d')
    ax.scatter(x,y,z,c=sub_colors, marker='o')
    plt.title('Scatter Plot of Clusters from '+sub)
    angles = np.linspace(0,360,25)[:-1]

    plt.show()





