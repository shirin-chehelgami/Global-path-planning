# -*- coding: utf-8 -*-
"""ai2thortest.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BB1GgrEN2rVC-VmkNhCEzNt6Fe9TrOqQ
"""

import random
import matplotlib.path as mplPath
import time
import collections
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
import tensorflow as tf
import shapely.geometry
import descartes
import numpy.matlib as mat
from tqdm import tqdm
from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, LSTM
from keras import optimizers
from keras.callbacks import LearningRateScheduler
import keras
from keras.layers import Dropout
from keras import backend as K
from tensorflow.python.keras.utils import metrics_utils 
from tensorflow.python.ops import math_ops 
from tensorflow.python.framework import ops
import ai2thorloss as ailoss
import ai2thormodel as aimodel
import ai2thorprocessdata as aipdata
import ai2thorgeneratepatches as aigp
import ai2thorgeneratesamples as aigs 
import math


def check_intersect(A, B, object_c):
    t = np.linspace(0, 1, 100)
    interp = np.asarray([B*i + (1-i)*A for i in t])
    decisions = [p.contains_points(interp) for p in object_c]
    decisions = [item for sublist in decisions for item in sublist]
    if any(decisions):
      return False
    else:
      return True # will return True if nodeA and nodeB are safely connectable

def path_validity(path, object_c):
    validity = [check_intersect(path[i, :], path[i+1, :], object_c) for i in range(path.shape[0]-1)]
    return all(validity)
    



def path_generator(map_name, cx, cy, obstacle_path, sample_path, model, start=None, goal=None, num_evals=1, eval_mode=True, plotopt=True):

    """
    eval_mode = True when function is used for testing performance of the network
    eval_mode = False, num_evals = 1 when function takes in specified start and goal and generates a path

    """

    object_c = ailoss.format_obstacles(load_poly=obstacle_path)

    valid_counter = 0
    reach_goal = 0
    path_set = []
    s = []
    g = []

    for i in range(num_evals):

        if eval_mode:
            samples = np.load(sample_path)
            #data = generate_samples(map_name, cx, cy, load_poly=obstacle_path, num_samples=2, show=False)
            data = aigs.generatesamples(map_name, cx, cy, load_poly=obstacle_path, num_samples=2, show=False)

            idx0 = random.randint(0, samples.shape[0]-1)
            idx1 = random.randint(0, samples.shape[0]-1)

            start = samples[idx0]
            s.append(start)


            goal = samples[idx1]
            g.append(goal) 

        else:
            aigp.generate_patches(cx, cy, obstacle_path)
            s.append(start)
            g.append(goal)


        start_ext = start[np.newaxis, np.newaxis, ...]
        goal_ext = goal[np.newaxis, np.newaxis, ...]

        s_pred = np.concatenate((start_ext, goal_ext), axis=-1)


        s_path = [start]
        num_points = 0
        tstart = time.time()
        sr = 0
        rg = 0

        while True:
            out1 = model.predict(s_pred)

            s_path.append(out1[0, 0, :])

            s_pred = np.concatenate((out1, goal_ext), axis=-1)


            num_points += 1


            check = check_intersect(np.array(out1[0][0]), np.array(goal), object_c)


            if np.linalg.norm(out1 - goal) < 30 and check == True:
                s_path.append(goal)
                break

            if num_points > 50:
                break


        print("time path {}:".format(i+1), time.time()-tstart)
        # s_path = np.asarray(s_path)
        path_set.append(s_path)


        if path_validity(np.asarray(s_path), object_c): 
          valid_counter += 1
          sr += 1


        if np.linalg.norm(out1 - goal) < 30:
          reach_goal += 1
          rg += 1


    for j in range(num_evals):
      if plotopt:
          plt.plot(np.asarray(path_set[j])[:, 0], np.asarray(path_set[j])[:, 1], 'k')
          plt.plot(s[j][0], s[j][1], 'g.', markersize = 10)
          plt.plot(g[j][0], g[j][1], 'r.', markersize = 10)


    return s, g, path_set, valid_counter/num_evals, reach_goal/num_evals

def path_generator_bi(map_name, cx, cy, obstacle_path, sample_path, model, start=None, goal=None, num_evals=1, eval_mode=True, plotopt=False):


    object_c = ailoss.format_obstacles(load_poly=obstacle_path)

    valid_counter = 0
    reach_goal = 0
    path_set = []
    path_set2 = []
    end1 = 0
    end2 = 0
    G = 0


    for i in range(num_evals):

        if eval_mode:

            # data = generate_samples(map_name, cx, cy, load_poly=obstacle_path, num_samples=2, show=False)
            data = aigs.generatesamples(map_name, cx, cy, load_poly=obstacle_path, num_samples=2, show=False)

             

        start_ext = start[np.newaxis, np.newaxis, ...]
        goal_ext = goal[np.newaxis, np.newaxis, ...]

        s_pred_s = np.concatenate((start_ext, goal_ext), axis=-1)
        s_pred_g = np.concatenate((goal_ext, start_ext), axis=-1)

        s_path_s = [start]
        s_path_g = [goal]

        num_points = 0
        num_points2 = 0
        tstart = time.time()

        while True:
            out1 = model.predict(s_pred_s)
            s_path_s.append(out1[0, 0, :])
            s_pred_s = np.concatenate((out1, goal_ext), axis=-1)

            out2 = model.predict(s_pred_g)
            s_path_g.append(out2[0, 0, :])
            s_pred_g = np.concatenate((out2, start_ext), axis=-1)

            num_points += 1

            for i in range(num_points,-1,-1):
              if math.hypot(s_path_s[num_points][0] - s_path_g[i][0],s_path_s[num_points][1] - s_path_g[i][1]) <20:
                m = i
                end1 += 1

            if end1 == 1:
                break


            if num_points > 50:
                break


            for j in range(num_points,-1,-1):
              if math.hypot(s_path_s[j][0] - s_path_g[num_points][0],s_path_s[j][1] - s_path_g[num_points][1]) <20:
                n = j
                end2 += 1

            if end2 == 1:
                break


            if num_points > 50:
                break


        if end1 == 1:
          new_s = s_path_s[:num_points+1]
          gg = s_path_g[:m+1]
          new_g = gg[::-1]
          s_path = [*new_s,*new_g]

        elif end2 == 1:
          new_s = s_path_s[:n+1]
          gg = s_path_g[:num_points+1]
          new_g = gg[::-1]
          s_path = [*new_s,*new_g]

        else:
          if len(s_path_s) > len(s_path_g):
            s_path = s_path_s

            object_c = ailoss.format_obstacles(load_poly=obstacle_path)
            check = check_intersect(np.array(s_path[-1]), np.array(goal), object_c)

            if np.linalg.norm(s_path[-1] - goal) < 30 and check == True:
                s_path.append(goal)
                break
          else:
            s_path = s_path_g[::-1]

            object_c = ailoss.format_obstacles(load_poly=obstacle_path)
            check = check_intersect(np.array(s_path[-1]), np.array(start), object_c)


            if np.linalg.norm(s_path[-1] - start) < 30 and check == True:
                s_path.append(start)
                break
            G += 1

        s_path = np.asarray(s_path)
        path_set.append(s_path)

        if plotopt:
            plt.plot(s_path[:, 0], s_path[:, 1], 'k')
            plt.plot(start[0], start[1], 'g.', markersize = 10)
            plt.plot(goal[0], goal[1], 'r.', markersize = 10)

        if path_validity(s_path, object_c): 
          valid_counter += 1



        if G == 1:
          if np.linalg.norm(s_path[-1] - start) < 30:
            reach_goal += 1
        else:
          if np.linalg.norm(s_path[-1] - goal) < 30:
            reach_goal += 1

    return path_set, valid_counter/num_evals, reach_goal/num_evals

def test(map_name ,cx, cy, obstacle_path, sample_path, model, num_test):

    strr = time.time()
    k = 0
    counter_before = 0
    r_goal_before = 0
    counter_after = 0
    r_goal_after = 0
    PATH = []


    while True:
      st,gl,path, validity, reach = path_generator(map_name, cx, cy, obstacle_path, sample_path, model, num_evals=1, eval_mode=True, plotopt=True)
      print('Success Rate path {} is '.format(k+1), validity)
      print('Reach goal Rate path {} is '.format(k+1), reach,"\n")

      if reach == 1.:
        r_goal_before += 1.

      if validity == 1.:
        counter_before += 1.

      k += 1
      print("path{}".format(k))
      print("\n")
      plt.show()
      print("\n")


      if reach == 1.:
        r_goal_after += 1.

        if validity == 1.:
          counter_after += 1.


      elif reach != 1.:
        print("\n")
        print("Bidirectional path {}".format(k))
        print("\n")

        path, validity2, reach2 = path_generator_bi(map_name, cx, cy, obstacle_path, sample_path, model, st[-1], gl[-1], num_evals=1, eval_mode=True, plotopt=True)
        print('Success Rate bidirectional path {} is '.format(k), validity2)
        print('Reach goal Rate bideirectional path {} is '.format(k), reach2,"\n")

        plt.show()
        print("\n")


        if reach2 == 1.:
          print("reach2")
          r_goal_after += 1.

        if validity2 == 1.:
          print("validity2")
          counter_after += 1.
      
      PATH.append(path)

      if k == num_test:
        break

      TT = time.time()-strr

    return PATH, TT, counter_before/num_test, r_goal_before/num_test, counter_after/num_test, r_goal_after/num_test