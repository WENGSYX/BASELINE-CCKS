import pandas as pd
import ast
from tqdm import trange
import random
train = []
train_data = []

with open("wa.train.fixtab.valid.tsv", "r",encoding='utf-8') as f:
    for line in f.readlines()[1:]:
        line = line.strip('\n')
        line = line.split('\t')
        train.append({'label':line[0],'docid':line[1],'question':line[2],'description':line[3],'answer':line[4]})
train = pd.DataFrame(train)
train.to_csv('data_all.csv')
