import os
import json
import random
import numpy as np
from six.moves import range

import skimage.io
from skimage.transform import resize
from sklearn.preprocessing import normalize
from nltk.tokenize import word_tokenize

import torch
import torch.nn as nn
from torch.autograd import Variable
import torchvision

import options
import nltk
nltk.download('punkt')

import random
import torch

# Somehow tell python to take in the latest s3 images here
if __name__ == '__main__':
    print('test')

params = {
    'inputJson': "./data/visdial/chat_processed_params.json",
    'useGPU': False,
    
    # A-Bot checkpoint
    'startFrom': "./checkpoints/abot_sl_ep60.vd",
    
    # Q-Bot checkpoint should given if interactive dialog is required
    'qstartFrom': "./checkpoints/qbot_sl_ep60.vd",
    
    'beamSize': 7,
}

# RNG seed
manualSeed = 1597
manualSeed = 597
# manualSeed = 1599
random.seed(manualSeed)
torch.manual_seed(manualSeed)
if params['useGPU']:
    torch.cuda.manual_seed_all(manualSeed)

print('Loading json file: ' + params['inputJson'])
with open(params['inputJson'], 'r') as fileId:
    info = json.load(fileId)

wordCount = len(info['word2ind'])
# Add <START> and <END> to vocabulary
info['word2ind']['<START>'] = wordCount + 1
info['word2ind']['<END>'] = wordCount + 2
startToken = info['word2ind']['<START>']
endToken = info['word2ind']['<END>']
# Padding token is at index 0
vocabSize = wordCount + 3
print('Vocab size with <START>, <END>: %d' % vocabSize)

# Construct the reverse map
info['ind2word'] = {
    int(ind): word
    for word, ind in info['word2ind'].items()
}
    
def loadModel(params, agent='abot'):
    # should be everything used in encoderParam, decoderParam below
    encoderOptions = [
        'encoder', 'vocabSize', 'embedSize', 'rnnHiddenSize', 'numLayers',
        'useHistory', 'useIm', 'imgEmbedSize', 'imgFeatureSize', 'numRounds',
        'dropout'
    ]
    decoderOptions = [
        'decoder', 'vocabSize', 'embedSize', 'rnnHiddenSize', 'numLayers',
        'dropout'
    ]
    modelOptions = encoderOptions + decoderOptions

    mdict = None
    gpuFlag = params['useGPU']
    startArg = 'startFrom' if agent == 'abot' else 'qstartFrom'
    assert params[startArg], "Need checkpoint for {}".format(agent)

    if params[startArg]:
        print('Loading model (weights and config) from {}'.format(
            params[startArg]))
        gpuFlag = False
        if gpuFlag:
            mdict = torch.load(params[startArg])
        else:
            mdict = torch.load(params[startArg],
                map_location=lambda storage, location: storage)
            map_location=torch.device('cpu')
        # Model options is a union of standard model options defined
        # above and parameters loaded from checkpoint
        modelOptions = list(set(modelOptions).union(set(mdict['params'])))
        for opt in modelOptions:
            if opt not in params:
                params[opt] = mdict['params'][opt]

            elif params[opt] != mdict['params'][opt]:
                # Parameters are not overwritten from checkpoint
                pass

    # Initialize model class
    encoderParam = {k: params[k] for k in encoderOptions}
    decoderParam = {k: params[k] for k in decoderOptions}

    encoderParam['startToken'] = encoderParam['vocabSize'] - 2
    encoderParam['endToken'] = encoderParam['vocabSize'] - 1
    decoderParam['startToken'] = decoderParam['vocabSize'] - 2
    decoderParam['endToken'] = decoderParam['vocabSize'] - 1

    if agent == 'abot':
        encoderParam['type'] = params['encoder']
        decoderParam['type'] = params['decoder']
        encoderParam['isAnswerer'] = True
        from visdial.models.answerer import Answerer
        model = Answerer(encoderParam, decoderParam)

    elif agent == 'qbot':
        encoderParam['type'] = params['qencoder']
        decoderParam['type'] = params['qdecoder']
        encoderParam['isAnswerer'] = False
        encoderParam['useIm'] = False
        from visdial.models.questioner import Questioner
        model = Questioner(
            encoderParam,
            decoderParam,
            imgFeatureSize=encoderParam['imgFeatureSize'])

    if params['useGPU']:
        model.cuda()

    if mdict:
        model.load_state_dict(mdict['model'])
        
    print("Loaded agent {}".format(agent))
    return model

aBot = None
qBot = None

# load aBot
if params['startFrom']:
    aBot = loadModel(params, 'abot')
    assert aBot.encoder.vocabSize == vocabSize, "Vocab size mismatch!"
    aBot.eval()

# load qBot
if params['qstartFrom']:
    qBot = loadModel(params, 'qbot')
    assert qBot.encoder.vocabSize == vocabSize, "Vocab size mismatch!"
    qBot.eval()

# load pre-trained VGG 19
print("Loading image feature extraction model")
feat_extract_model = torchvision.models.vgg19(pretrained=True)

feat_extract_model.classifier = nn.Sequential(*list(feat_extract_model.classifier.children())[:-3])
# print(feat_extract_model)
feat_extract_model.eval()

if params['useGPU']:
    feat_extract_model.cuda()

print("Done!")

demo_number = 0

img_array = []
img_array.append("demo/img.jpg")

hist_file = []
hist_file.append("demo/hist.json")

ques_file = []
ques_file.append("demo/ques.json")

img_mat = skimage.io.imread(img_array[demo_number])

img_path = img_array[demo_number]
with open(hist_file[demo_number]) as hfile:
  hist_info = json.load(hfile)

with open(ques_file[demo_number]) as qfile:
  ques_info = json.load(qfile)

ind_map = lambda words: np.array([info['word2ind'].get(word, info['word2ind']['UNK']) 
                                  for word in words], dtype='int64')

tokenize = lambda string: ['<START>'] + word_tokenize(string) + ['<END>']

# Process image
def transform(img):
    img = img.astype("float")/255
    img = resize(img, (224, 224), mode='constant')
    img[:,:,0] -= 0.485
    img[:,:,1] -= 0.456
    img[:,:,2] -= 0.406
    return img.transpose([2,0,1])

raw_img = transform(skimage.io.imread(img_path))

# Process caption
caption_tokens = tokenize(hist_info['caption'])
caption = ind_map(caption_tokens)

# Process history
h_question_tokens = []
h_questions = []
h_answer_tokens = []
h_answers = []
for round_idx, item in enumerate(hist_info['dialog']):
    ans_tokens = tokenize(item['answer'])
    h_answer_tokens.append(ans_tokens)
    h_answers.append(ind_map(ans_tokens))
    
    ques_tokens = tokenize(item['question'])
    h_question_tokens.append(ques_tokens)
    h_questions.append(ind_map(ques_tokens))
    
# Process question
question_tokens = tokenize(ques_info['question'])
question = ind_map(question_tokens)

def var_map(tensor):
    if params['useGPU']:
        tensor = tensor.cuda()
    return Variable(tensor.unsqueeze(0), volatile=True)

img_tensor = var_map(torch.from_numpy(raw_img).float())
img_feats = feat_extract_model(img_tensor)
_norm = torch.norm(img_feats, p=2, dim=1)
img_feats = img_feats.div(_norm.expand_as(img_feats))

caption_tensor = var_map(torch.from_numpy(caption))
caption_lens = var_map(torch.LongTensor([len(caption)]))

question_tensor = var_map(torch.from_numpy(question))
question_lens = var_map(torch.LongTensor([len(question)]))

hist_ans_tensors = [var_map(torch.from_numpy(ans)) for ans in h_answers]
hist_ans_lens = [var_map(torch.LongTensor([len(h_ans)])) for h_ans in h_answer_tokens]
hist_ques_tensors = [var_map(torch.from_numpy(ques)) for ques in h_questions]
hist_ques_lens = [var_map(torch.LongTensor([len(h_ques)])) for h_ques in h_question_tokens]

# # Helper functions for converting tensors to words
# to_str_pred = lambda w, l: str(" ".join([info['ind2word'][x] for x in list( filter(
#         lambda x:x>0,w.data.cpu().numpy()))][:l.data.cpu()[0]]))[8:]
# to_str_gt = lambda w: str(" ".join([info['ind2word'][x] for x in filter(
#         lambda x:x>0,w.data.cpu().numpy())]))[8:-6]

# Helper functions for converting tensors to words
to_str_pred = lambda w, l: str(" ".join([info['ind2word'][x] for x in list( filter(
        lambda x:x>0,w.data.cpu().numpy()))][:l.data.cpu()]))[8:]
to_str_gt = lambda w: str(" ".join([info['ind2word'][x] for x in filter(
        lambda x:x>0,w.data.cpu().numpy())]))[8:-6]

if aBot:
    aBot.eval(), aBot.reset()
    aBot.observe(
        -1, image=img_feats, caption=caption_tensor, captionLens=caption_lens)

if qBot:
    qBot.eval(), qBot.reset()
    qBot.observe(-1, caption=caption_tensor, captionLens=caption_lens)

print("Caption: ", to_str_gt(caption_tensor[0]))
    
numRounds = len(hist_info['dialog'])
beamSize = params['beamSize']

for round in range(numRounds):
    if qBot is None:
        aBot.observe(
            round,
            ques=hist_ques_tensors[round],
            quesLens=hist_ques_lens[round])
        aBot.observe(
            round,
            ans=hist_ans_tensors[round],
            ansLens=hist_ans_lens[round])
        _ = aBot.forward()
        answers, ansLens = aBot.forwardDecode(
            inference='greedy', beamSize=beamSize)
    elif aBot is not None and qBot is not None:
        questions, quesLens = qBot.forwardDecode(
            beamSize=beamSize, inference='greedy')
        print(question)
        qBot.observe(round, ques=questions, quesLens=quesLens)
        aBot.observe(round, ques=questions, quesLens=quesLens)
        answers, ansLens = aBot.forwardDecode(
            beamSize=beamSize, inference='greedy')
        aBot.observe(round, ans=answers, ansLens=ansLens)
        qBot.observe(round, ans=answers, ansLens=ansLens)
        
    print("Q%d: "%(round+1), to_str_gt(hist_ques_tensors[round][0]))
    print("A%d: "%(round+1), to_str_gt(hist_ans_tensors[round][0]))
        
# After processing history
if qBot is None:
    aBot.observe(
        numRounds,
        ques=question_tensor,
        quesLens=question_lens)
    answers, ansLens = aBot.forwardDecode(
        inference='greedy', beamSize=beamSize)
    
    # Printing
    print("Q%d: "%(numRounds+1), to_str_gt(question_tensor[0]))
    print("A%d: "%(numRounds+1), to_str_pred(answers[0], ansLens[0]))
    
elif aBot is not None and qBot is not None:
    questions, quesLens = qBot.forwardDecode(beamSize=beamSize, inference='greedy')
    qBot.observe(numRounds, ques=questions, quesLens=quesLens)
    aBot.observe(numRounds, ques=questions, quesLens=quesLens)
    answers, ansLens = aBot.forwardDecode(
        beamSize=beamSize, inference='greedy')
    aBot.observe(numRounds, ans=answers, ansLens=ansLens)
    qBot.observe(numRounds, ans=answers, ansLens=ansLens)

    # Printing
    print("Q%d: "%(numRounds+1), to_str_pred(questions[0], quesLens[0]))
    print("A%d: "%(numRounds+1), to_str_pred(answers[0], ansLens[0]))

