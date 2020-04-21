import torch
from transformers import BertTokenizer, BertConfig, BertModel, \
    BertForMaskedLM, BertForSequenceClassification, AdamW, get_linear_schedule_with_warmup
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
import pandas as pd
from tensorflow.keras.preprocessing.sequence import pad_sequences

def get_ids_masks(sentences):
    # preprocess data for model prediction    
    input_ids = []
    for sent in sentences:
        encoded_sent = tokenizer.encode(sent, add_special_tokens=True)
        input_ids.append(encoded_sent)
    input_ids = pad_sequences(input_ids, maxlen=200, dtype='long', truncating='post', padding='post')

    # creating attention masks for model prediction
    attention_masks = []
    for seq in input_ids:
        seq_mask = [float(i>0) for i in seq]
        attention_masks.append(seq_mask) 

    return input_ids, attention_masks

def get_data_loader(input_ids, attention_masks):
     # Convert to tensors.
    prediction_inputs = torch.tensor(input_ids)
    prediction_masks = torch.tensor(attention_masks)

    # Set the batch size.  
    batch_size = 32  

    # Create the DataLoader.
    prediction_data = TensorDataset(prediction_inputs, prediction_masks)
    prediction_sampler = SequentialSampler(prediction_data)
    prediction_dataloader = DataLoader(prediction_data, sampler=prediction_sampler, batch_size=batch_size)  

    print('Predicting labels for {:,} test sentences...'.format(len(prediction_inputs)))

    return prediction_dataloader

def get_sentences(file_path):
    # read csv and create data frame.
    df = pd.read_csv(file_path, error_bad_lines=False)
    print('original data frame shape is: {}'.format(df.shape))
    df_clean = df[df['title'].notnull() & df['description'].notnull()].reset_index(drop=True)
    print('cleaned up data frame shape is: {}'.format(df_clean.shape))
    sentences = (df_clean['title'] + ' ' + df_clean['description']).values
    
    return sentences

if __name__ == "__main__":

    if torch.cuda.is_available():    
        device = torch.device("cuda")
        print('There are %d GPU(s) available.' % torch.cuda.device_count())
        print('We will use the GPU:', torch.cuda.get_device_name(0))
    else:
        print('No GPU available, using the CPU instead.')
        device = torch.device("cpu")

    print('loading the model...')
    model_dir = '/Users/mkz/code/food_app/models/'
    model = BertForSequenceClassification.from_pretrained(model_dir)
    tokenizer = BertTokenizer.from_pretrained(model_dir)
    print('# model loaded.')

    
    # preprocessing data
    print('reading data ....')
    file_path = '/Users/mkz/code/food_app/01_all_ingredients.csv'
    sentences = get_sentences(file_path)
    input_ids, attention_masks = get_ids_masks(sentences)
    dataloader = get_data_loader(input_ids, attention_masks)   
    print('# data read from disk.')
    # # Put model in evaluation mode
    model.eval()

    # # Tracking variables 
    predictions = []

    # Predict 
    for batch in dataloader:
        # Add batch to GPU/CPU
        batch = tuple(t.to(device) for t in batch)
        
        # Unpack the inputs from our dataloader
        b_input_ids, b_input_mask = batch
        
        # Telling the model not to compute or store gradients, saving memory and 
        # speeding up prediction
        with torch.no_grad():
            # Forward pass, calculate logit predictions
            outputs = model(b_input_ids, token_type_ids=None, 
                            attention_mask=b_input_mask)

        logits = outputs[0]

        # Move logits and labels to CPU
        logits = logits.detach().cpu().numpy()
        
        # Store predictions and true labels
        predictions.append(logits)
        print(predictions)
        print('DONE.')