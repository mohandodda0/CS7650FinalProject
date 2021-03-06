deviceno = 0
modelname = 'bert-base-uncased'
#modelname = "cardiffnlp/twitter-roberta-base-offensive"
#modelname = 'microsoft/deberta-base'
modelname = 'facebook/bart-large'
#modelname = 'unitary/toxic-bert'
max_length = 128
batch_size = 8
epochs = 4
import pandas as pd
df = pd.read_csv('balancedSpaceSep.csv')

traindf = df[df['split']=='train']
testdf = df[df['split']=='test']
testdf

from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(modelname)

import pandas as pd
import torch
from torch.utils.data import TensorDataset
# Load the dataset into a pandas dataframe.

# Report the number of sentences.
# print('Number of test sentences: {:,}\n'.format(df.shape[0]))

# Create sentence and label lists
train_sentences = traindf['text'].values
test_sentences = testdf['text'].values
train_labels = traindf['label'].values
test_labels = testdf['label'].values

# Tokenize all of the sentences and map the tokens to thier word IDs.
input_ids = []
attention_masks = []

# For every sentence...
for sent in train_sentences:
    # `encode_plus` will:
    #   (1) Tokenize the sentence.
    #   (2) Prepend the `[CLS]` token to the start.
    #   (3) Append the `[SEP]` token to the end.
    #   (4) Map tokens to their IDs.
    #   (5) Pad or truncate the sentence to `max_length`
    #   (6) Create attention masks for [PAD] tokens.
    encoded_dict = tokenizer.encode_plus(
                        sent,                      # Sentence to encode.
                        add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                        max_length = max_length,           # Pad & truncate all sentences.
                        pad_to_max_length = True,
                        return_attention_mask = True,   # Construct attn. masks.
                        return_tensors = 'pt',     # Return pytorch tensors.
                   )
    
    # Add the encoded sentence to the list.    
    input_ids.append(encoded_dict['input_ids'])
    
    # And its attention mask (simply differentiates padding from non-padding).
    attention_masks.append(encoded_dict['attention_mask'])

# Convert the lists into tensors.
input_ids = torch.cat(input_ids, dim=0)
attention_masks = torch.cat(attention_masks, dim=0)
labels = torch.tensor(train_labels)
labels = labels.to(torch.int64)
# labels = F.one_hot(labels.to(torch.int64))
train_dataset = TensorDataset(input_ids, attention_masks, labels)

input_ids = []
attention_masks = []
for sent in test_sentences:
    # `encode_plus` will:
    #   (1) Tokenize the sentence.
    #   (2) Prepend the `[CLS]` token to the start.
    #   (3) Append the `[SEP]` token to the end.
    #   (4) Map tokens to their IDs.
    #   (5) Pad or truncate the sentence to `max_length`
    #   (6) Create attention masks for [PAD] tokens.
    encoded_dict = tokenizer.encode_plus(
                        sent,                      # Sentence to encode.
                        add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                        max_length = 64,           # Pad & truncate all sentences.
                        pad_to_max_length = True,
                        return_attention_mask = True,   # Construct attn. masks.
                        return_tensors = 'pt',     # Return pytorch tensors.
                   )
    
    # Add the encoded sentence to the list.    
    input_ids.append(encoded_dict['input_ids'])
    
    # And its attention mask (simply differentiates padding from non-padding).
    attention_masks.append(encoded_dict['attention_mask'])

# Convert the lists into tensors.
input_ids = torch.cat(input_ids, dim=0)
attention_masks = torch.cat(attention_masks, dim=0)
labels = torch.tensor(test_labels)
labels = labels.to(torch.int64)
# labels = F.one_hot(labels.to(torch.int64))
val_dataset = TensorDataset(input_ids, attention_masks, labels)

# import torch.nn.functional as F
# # lab = torch.FloatTensor(labels.shape[0], 2)
# # lab.scatter_(1, labels.int() ,1)

# from torch.utils.data import TensorDataset, random_split

# # Combine the training inputs into a TensorDataset.
# dataset = TensorDataset(input_ids, attention_masks, labels)

# # Create a 90-10 train-validation split.

# # Calculate the number of samples to include in each set.
# train_size = int(0.9 * len(dataset))
# val_size = len(dataset) - train_size

# # Divide the dataset by randomly selecting samples.
# train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

# print('{:>5,} training samples'.format(train_size))
# print('{:>5,} validation samples'.format(val_size))
val_dataset

from torch.utils.data import DataLoader, RandomSampler, SequentialSampler

# The DataLoader needs to know our batch size for training, so we specify it 
# here. For fine-tuning BERT on a specific task, the authors recommend a batch 
# size of 16 or 32.

# Create the DataLoaders for our training and validation sets.
# We'll take training samples in random order. 
train_dataloader = DataLoader(
            train_dataset,  # The training samples.
            sampler = RandomSampler(train_dataset), # Select batches randomly
            batch_size = batch_size # Trains with this batch size.
        )

# For validation the order doesn't matter, so we'll just read them sequentially.
validation_dataloader = DataLoader(
            val_dataset, # The validation samples.
            sampler = SequentialSampler(val_dataset), # Pull out batches sequentially.
            batch_size = batch_size # Evaluate with this batch size.
        )

from transformers import BertForSequenceClassification, AdamW, BertConfig, AutoModelForSequenceClassification

# Load BertForSequenceClassification, the pretrained BERT model with a single 
# linear classification layer on top. 
model = AutoModelForSequenceClassification.from_pretrained(
    modelname, # Use the 12-layer BERT model, with an uncased vocab.
    num_labels = 2, # The number of output labels--2 for binary classification.
                    # You can increase this for multi-class tasks.   
    output_attentions = False, # Whether the model returns attentions weights.
    output_hidden_states = False, # Whether the model returns all hidden-states.
)

# Tell pytorch to run this model on the GPU.
# model.cuda()
device = 'cpu'
if torch.cuda.is_available():
    device = 'cuda'+':'+str(deviceno)
model = model.to(device)
print(device)

optimizer = AdamW(model.parameters(),
                  lr = 2e-5, # args.learning_rate - default is 5e-5, our notebook had 2e-5
                  eps = 1e-8 # args.adam_epsilon  - default is 1e-8.
                )

from transformers import get_linear_schedule_with_warmup

# Number of training epochs. The BERT authors recommend between 2 and 4. 
# We chose to run for 4, but we'll see later that this may be over-fitting the
# training data.


# Total number of training steps is [number of batches] x [number of epochs]. 
# (Note that this is not the same as the number of training samples).
total_steps = len(train_dataloader) * epochs

# Create the learning rate scheduler.
scheduler = get_linear_schedule_with_warmup(optimizer, 
                                            num_warmup_steps = 0, # Default value in run_glue.py
                                            num_training_steps = total_steps)

import numpy as np

# Function to calculate the accuracy of our predictions vs labels
def flat_accuracy(preds, labels):
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return np.sum(pred_flat == labels_flat) / len(labels_flat)

import time
import datetime

def format_time(elapsed):
    '''
    Takes a time in seconds and returns a string hh:mm:ss
    '''
    # Round to the nearest second.
    elapsed_rounded = int(round((elapsed)))
    
    # Format as hh:mm:ss
    return str(datetime.timedelta(seconds=elapsed_rounded))

#  from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
#  import torch
#  tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
#  model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased')
#  inputs = tokenizer("Hello, my dog is cute", return_tensors="pt")
#  labels = torch.tensor([1]).unsqueeze(0)  # Batch size 1
#  labels = train_labels[10]

#  outputs = model(**inputs, labels=labels)
#  loss = outputs.loss
#  logits = outputs.logits 
print(device)

import random
import numpy as np

# This training code is based on the `run_glue.py` script here:
# https://github.com/huggingface/transformers/blob/5bfcd0485ece086ebcbed2d008813037968a9e58/examples/run_glue.py#L128

# Set the seed value all over the place to make this reproducible.
seed_val = 42

random.seed(seed_val)
np.random.seed(seed_val)
torch.manual_seed(seed_val)
torch.cuda.manual_seed_all(seed_val)

# We'll store a number of quantities such as training and validation loss, 
# validation accuracy, and timings.
training_stats = []

# Measure the total training time for the whole run.
total_t0 = time.time()

# For each epoch...
for epoch_i in range(0, epochs):
    
    # ========================================
    #               Training
    # ========================================
    
    # Perform one full pass over the training set.

    print("")
    print('======== Epoch {:} / {:} ========'.format(epoch_i + 1, epochs))
    print('Training...')

    # Measure how long the training epoch takes.
    t0 = time.time()

    # Reset the total loss for this epoch.
    total_train_loss = 0

    # Put the model into training mode. Don't be mislead--the call to 
    # `train` just changes the *mode*, it doesn't *perform* the training.
    # `dropout` and `batchnorm` layers behave differently during training
    # vs. test (source: https://stackoverflow.com/questions/51433378/what-does-model-train-do-in-pytorch)
    model.train()

    # For each batch of training data...
    for step, batch in enumerate(train_dataloader):

        # Progress update every 40 batches.
        if step % 40 == 0 and not step == 0:
            # Calculate elapsed time in minutes.
            elapsed = format_time(time.time() - t0)
            
            # Report progress.
            print('  Batch {:>5,}  of  {:>5,}.    Elapsed: {:}.'.format(step, len(train_dataloader), elapsed))

        # Unpack this training batch from our dataloader. 
        #
        # As we unpack the batch, we'll also copy each tensor to the GPU using the 
        # `to` method.
        #
        # `batch` contains three pytorch tensors:
        #   [0]: input ids 
        #   [1]: attention masks
        #   [2]: labels 
        b_input_ids = batch[0].to(device)
        b_input_mask = batch[1].to(device)
        b_labels = batch[2].to(device)
        # print(b_labels.shape)
        # print(b_input_ids.shape)



        # Always clear any previously calculated gradients before performing a
        # backward pass. PyTorch doesn't do this automatically because 
        # accumulating the gradients is "convenient while training RNNs". 
        # (source: https://stackoverflow.com/questions/48001598/why-do-we-need-to-call-zero-grad-in-pytorch)
        model.zero_grad()        

        # Perform a forward pass (evaluate the model on this training batch).
        # The documentation for this `model` function is here: 
        # https://huggingface.co/transformers/v2.2.0/model_doc/bert.html#transformers.BertForSequenceClassification
        # It returns different numbers of parameters depending on what arguments
        # arge given and what flags are set. For our useage here, it returns
        # the loss (because we provided labels) and the "logits"--the model
        # outputs prior to activation.
        # loss, logits = model(b_input_ids, 
        #                     #  token_type_ids=None, 
        #                      attention_mask=b_input_mask, 
        #                      labels=b_labels)
        vals = model(b_input_ids, 
                            #  token_type_ids=None, 
                             attention_mask=b_input_mask, 
                             labels=b_labels)
        loss = vals.loss
        logits = vals.logits

        # Accumulate the training loss over all of the batches so that we can
        # calculate the average loss at the end. `loss` is a Tensor containing a
        # single value; the `.item()` function just returns the Python value 
        # from the tensor.
        # print(loss, logits, vals)
        total_train_loss += loss.item()

        # Perform a backward pass to calculate the gradients.
        loss.backward()

        # Clip the norm of the gradients to 1.0.
        # This is to help prevent the "exploding gradients" problem.
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        # Update parameters and take a step using the computed gradient.
        # The optimizer dictates the "update rule"--how the parameters are
        # modified based on their gradients, the learning rate, etc.
        optimizer.step()

        # Update the learning rate.
        scheduler.step()

    # Calculate the average loss over all of the batches.
    avg_train_loss = total_train_loss / len(train_dataloader)            
    
    # Measure how long this epoch took.
    training_time = format_time(time.time() - t0)

    print("")
    print("  Average training loss: {0:.2f}".format(avg_train_loss))
    print("  Training epcoh took: {:}".format(training_time))
        
    # ========================================
    #               Validation
    # ========================================
    # After the completion of each training epoch, measure our performance on
    # our validation set.

    print("")
    print("Running Validation...")

    t0 = time.time()

    # Put the model in evaluation mode--the dropout layers behave differently
    # during evaluation.
    model.eval()

    # Tracking variables 
    total_eval_accuracy = 0
    total_eval_loss = 0
    nb_eval_steps = 0

    # Evaluate data for one epoch
    for batch in validation_dataloader:
        
        # Unpack this training batch from our dataloader. 
        #
        # As we unpack the batch, we'll also copy each tensor to the GPU using 
        # the `to` method.
        #
        # `batch` contains three pytorch tensors:
        #   [0]: input ids 
        #   [1]: attention masks
        #   [2]: labels 
        b_input_ids = batch[0].to(device)
        b_input_mask = batch[1].to(device)
        b_labels = batch[2].to(device)

        
        # Tell pytorch not to bother with constructing the compute graph during
        # the forward pass, since this is only needed for backprop (training).
        with torch.no_grad():        

            # Forward pass, calculate logit predictions.
            # token_type_ids is the same as the "segment ids", which 
            # differentiates sentence 1 and 2 in 2-sentence tasks.
            # The documentation for this `model` function is here: 
            # https://huggingface.co/transformers/v2.2.0/model_doc/bert.html#transformers.BertForSequenceClassification
            # Get the "logits" output by the model. The "logits" are the output
            # values prior to applying an activation function like the softmax.
            # (loss, logits) = model(b_input_ids, 
            #                       #  token_type_ids=None, 
            #                        attention_mask=b_input_mask,
            #                        labels=b_labels)
            vals = model(b_input_ids, 
                            #  token_type_ids=None, 
                             attention_mask=b_input_mask, 
                             labels=b_labels)
        loss = vals.loss
        logits = vals.logits
            
        # Accumulate the validation loss.
        total_eval_loss += loss.item()

        # Move logits and labels to CPU
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        # Calculate the accuracy for this batch of test sentences, and
        # accumulate it over all batches.
        total_eval_accuracy += flat_accuracy(logits, label_ids)
        

    # Report the final accuracy for this validation run.
    avg_val_accuracy = total_eval_accuracy / len(validation_dataloader)
    print("  Accuracy: {0:.2f}".format(avg_val_accuracy))

    # Calculate the average loss over all of the batches.
    avg_val_loss = total_eval_loss / len(validation_dataloader)
    
    # Measure how long the validation run took.
    validation_time = format_time(time.time() - t0)
    
    print("  Validation Loss: {0:.2f}".format(avg_val_loss))
    print("  Validation took: {:}".format(validation_time))

    # Record all statistics from this epoch.
    training_stats.append(
        {
            'epoch': epoch_i + 1,
            'Training Loss': avg_train_loss,
            'Valid. Loss': avg_val_loss,
            'Valid. Accur.': avg_val_accuracy,
            'Training Time': training_time,
            'Validation Time': validation_time
        }
    )

print("")
print("Training complete!")

print("Total training took {:} (h:mm:ss)".format(format_time(time.time()-total_t0)))

import pandas as pd

# Display floats with two decimal places.
pd.set_option('precision', 2)

# Create a DataFrame from our training statistics.
df_stats = pd.DataFrame(data=training_stats)

# Use the 'epoch' as the row index.
df_stats = df_stats.set_index('epoch')

# A hack to force the column headers to wrap.
#df = df.style.set_table_styles([dict(selector="th",props=[('max-width', '70px')])])

# Display the table.
df_stats



# import argparse
# import torch
# from transformers import AutoModel, AutoTokenizer, BE, AutoModelForSequenceClassification
# # from transformers import AdamW, get_linear_schedule_with_warmup
# import numpy as np

# from torch.utils.data import Dataset, DataLoader, SequentialSampler, RandomSampler
# import os
# import json
# import csv
# from tqdm import tqdm
# import logging

# logging.getLogger().setLevel(logging.CRITICAL)

# import warnings
# warnings.filterwarnings('ignore')

# device = 'cpu'
# if torch.cuda.is_available():
#     device = 'cuda'



# # Load the BERT tokenizer.
# print('Loading BERT tokenizer...')
# tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
# model = AutoModelForSequenceClassification.from_pretrained('bert-base-uncased')
# model = model.to(device)

# class ConversationDataset(Dataset):
#     def __init__(self, df):
#         self.df = df

#     def __len__(self):
#         return len(self.df)

#     def __getitem__(self, idx):
#         return self.df.iloc[idx]
  
# train_dataset = ConversationDataset(train_data)
# val_dataset   = ConversationDataset(val_data)
# test_dataset  = ConversationDataset(test_data)

# #BATCH_SIZE = 6
# #EPOCHS = 5
# LEARNING_RATE = 3e-5
# WARMUP_STEPS = 5000
# #MAX_SEQ_LEN = 500

# device = 'cpu'
# if torch.cuda.is_available():
#     device = 'cuda'

# model = model.to(device)
# model.train()

# tmp_jokes_tens = None
# models_folder = "models"
# if not os.path.exists(models_folder):
#     os.mkdir(models_folder)

# # parser.add_argument("--traindataset", default=None, type=str, required=True) 
# # parser.add_argument("--evaldataset", default=None, type=str, required=True)
# # parser.add_argument("--outputfile", default=None, type=str, required=True)
# # parser.add_argument("--epochs", default=5, type=int, required=True)
# # parser.add_argument("--gradient_acums", default=6, type=int, required=True)
# # parser.add_argument("--maxseqlen", default=500, type=int, required=True)
# gradient_acums = 6
# maxseqlen = 500
# traindataset = df
# evaldataset = df2
# outputfile = './output'
# def evaluate(model, tokenizer, prefix=""):
#     # Loop to handle MNLI double evaluation (matched, mis-matched)

#     eval_dataset = ConversationDataset(dataset = evaldataset)
#     print(eval_dataset)
#     eval_sampler = SequentialSampler(eval_dataset)
#     eval_dataloader = DataLoader(eval_dataset, sampler=eval_sampler, batch_size=gradient_acums)

#     # Eval!
#     print("***** Running evaluation {} *****".format(prefix))
#     print("  Num examples = %d", len(eval_dataset))
#     print("  Batch size = %d", gradient_acums)
#     eval_loss = 0.0
#     nb_eval_steps = 0
#     model.eval()

#     for idx,joke in enumerate(eval_dataloader):
#         print(str(idx) + ' ' + str(len(eval_dataloader)))
#         joke_tens = torch.tensor(tokenizer.encode(joke[0])).unsqueeze(0).to(device)
#         inputs, labels = (joke_tens, joke_tens)
#         #print(inputs)
#         #print(labels)
#         inputs = inputs.to(device)
#         labels = labels.to(device)
#         with torch.no_grad():
#             outputs = model(inputs, labels=labels)
#             lm_loss = outputs[0]
#             eval_loss += lm_loss.mean().item()
#         nb_eval_steps += 1

#     eval_loss = eval_loss / nb_eval_steps
#     perplexity = torch.exp(torch.tensor(eval_loss))

#     result = {"perplexity": perplexity}

#     with open(outputfile, "a") as writer:
#         writer.write(str(maxseqlen) + str(gradient_acums) + str(result))
#     return result
# batch_size = 32
# def train(model, tokenizer):

#     dataset = ConversationDataset(dataset=traindataset)
#     joke_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
#     model = model.to(device)
#     model.train()
#     optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
#     scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=WARMUP_STEPS, num_training_steps = -1)
#     proc_seq_count = 0
#     sum_loss = 0.0
#     batch_count = 0
#     tmp_jokes_tens = None
#     models_folder = "trained_models"
#     if not os.path.exists(models_folder):
#         os.mkdir(models_folder)
#     for epoch in range(epochs):
        
#         print(f"EPOCH {epoch} started" + '=' * 30)
        
#         for idx,joke in enumerate(joke_loader):
#             print(str(idx) + ' ' + str(len(joke_loader)))
#             joke_tens = torch.tensor(tokenizer.encode(joke[0])).unsqueeze(0).to(device)
#             if joke_tens.size()[1] > maxseqlen:
#                 continue
#             if not torch.is_tensor(tmp_jokes_tens):
#                 tmp_jokes_tens = joke_tens
#                 continue
#             else:
#                 #The next joke does not fit in so we process the sequence and leave the last joke 
#                 #as the start for next sequence 
#                 if tmp_jokes_tens.size()[1] + joke_tens.size()[1] > maxseqlen:
#                     work_jokes_tens = tmp_jokes_tens
#                     tmp_jokes_tens = joke_tens
#                 else:
#                     # Add the joke to sequence, continue and try to add more
#                     tmp_jokes_tens = torch.cat([tmp_jokes_tens, joke_tens[:,1:]], dim=1)
#                     print(joke)
#                     print(joke_tens)
#                     continue
#             ################## Sequence ready, process it trough the model ##################
                
#             outputs = model(work_jokes_tens, labels=work_jokes_tens)
#             loss, logits = outputs[:2]
#             loss.backward()
#             sum_loss = sum_loss + loss.detach().data
                        
#             proc_seq_count = proc_seq_count + 1
#             if proc_seq_count == gradient_acums:
#                 proc_seq_count = 0    
#                 batch_count += 1
#                 optimizer.step()
#                 scheduler.step() 
#                 optimizer.zero_grad()
#                 model.zero_grad()

#             if batch_count == 100:
#                 print(f"sum loss {sum_loss}")
#                 batch_count = 0
#                 sum_loss = 0.0
        
#         # Store the model after each epoch to compare the performance of them
#         torch.save(model.state_dict(), os.path.join(models_folder, f"gpt2_medium_joker_{maxseqlen}{epoch}{gradient_acums}.pt"))
#         evaluate(args, model, tokenizer)
