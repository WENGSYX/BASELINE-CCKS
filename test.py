
import json
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.cuda.amp import autocast, GradScaler
from tqdm import tqdm,trange
import random
from sklearn.model_selection import *
import ast
from transformers import *
test = []
with open("wa.test.phase1.fixtab.valid.tsv", "r",encoding='utf-8') as f:
    for line in f.readlines()[1:]:
        line = line.strip('\n')
        line = line.split('\t')
        test.append({'docid':line[0],'question':line[1],'description':line[2],'answer':line[3]})
test = pd.DataFrame(test)
test.to_csv('test.csv')

CFG = { #训练的参数配置
    'fold_num': 20, #五折交叉验证
    'seed': 8,
    'model': 'hfl/chinese-roberta-wwm-ext-large', #预训练模型
    'max_len': 300,#文本截断的最大长度
    'epochs': 7,
    'train_bs': 48, #batch_size，可根据自己的显存调整
    'valid_bs': 48,
    'lr': 1e-5, #学习率
    'num_workers': 0,
    'accum_iter': 1, #梯度累积，相当于将batch_size*2
    'weight_decay': 1e-4, #权重衰减，防止过拟合
    'device': 0,
}

tokenizer = BertTokenizer.from_pretrained(CFG['model'])
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class MyDataset(Dataset):
    def __init__(self, dataframe):
        self.df = dataframe

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):

        label = self.df.label.values[idx]
        question = self.df.question.values[idx]
        description = self.df.description.values[idx]
        answer = self.df.answer.values[idx]

        question = question + '[SEP]' + description
        return question, answer, label
def collate_fn(data):
    input_ids, attention_mask, token_type_ids = [], [], []
    for x in data:
        text = tokenizer(x[0], text_pair=x[1], padding='max_length', truncation=True, max_length=CFG['max_len'], return_tensors='pt')
        input_ids.append(text['input_ids'].squeeze().tolist())
        attention_mask.append(text['attention_mask'].squeeze().tolist())
        token_type_ids.append(text['token_type_ids'].squeeze().tolist())
    input_ids = torch.tensor(input_ids)
    attention_mask = torch.tensor(attention_mask)
    token_type_ids = torch.tensor(token_type_ids)
    label = torch.tensor([x[-1] for x in data])
    return input_ids, attention_mask, token_type_ids, label

test_df = pd.read_csv('test.csv')
test_df['label'] = 0
test_set = MyDataset(test_df)
y_all = np.zeros((5000,2))
test_loader = DataLoader(test_set, batch_size=CFG['valid_bs'], collate_fn=collate_fn, shuffle=False, num_workers=CFG['num_workers'])



model = BertForSequenceClassification.from_pretrained(CFG['model'],num_labels=2).cuda()  # 模型
y_pred,predictions=[],[]

for m in ['']:
    model.load_state_dict(torch.load(m))
    y_pred = []
    with torch.no_grad():
      tk = tqdm(test_loader, total=len(test_loader), position=0, leave=True)
      for idx, (input_ids, attention_mask, token_type_ids, y) in enumerate(tk):
          input_ids, attention_mask, token_type_ids, y = input_ids.to(device), attention_mask.to(
              device), token_type_ids.to(device), y.to(device).long()

          output = model(input_ids, attention_mask, token_type_ids)[0].cpu().numpy()

          y_pred.extend(output)

    y_all = y_all+np.array(y_pred)

y = y_all.argmax(1)
t = []
for i in range(len(test_df)):
    item = test_df.iloc[i]
    t.append({'Label':y[i],'Docid':item['docid'],'Question':item['question'],'Description':item['description'],'Answer':item['answer']})
t = pd.DataFrame(t)
t.to_csv('WENGSYX_valid_result.txt', sep='\t',index=None)


