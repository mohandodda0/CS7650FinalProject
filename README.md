# CS7650FinalProject

 LinearDatasetPrepForBERT.ipynb is used to make the linearized datasets for BERT. It outputs the csv files in the Github Repo
 Modified_(linearized)_CRAFT_inference_demo_using_ConvoKit.ipynb is the notebook that makes the linearized unbalanced dataset and trains a CRAFT model
 Modified_(linearized_and_balanced)_CRAFT_inference_demo_using_ConvoKit.ipynb is the notebook that makes the linearized dataset which is balanced and trains a CRAFT model
 Modified_(tree)_CRAFT_inference_demo_using_ConvoKit.ipynb is the notebook that trains the CRAFT model on the original dataset
 analysis_with_bert.ipynb is the notebook used to train BERT model on unbalanced and balanced linear dataset.
 craft+bertModelOnLinearizedData.py is file that is used to train the craft+bert model on the balanced linearized data.
 craft+bertModelOnTreeConversationData.py is file that is used to train the craft+bert model on the regular tree conversation data.

 Above files can be used to replicate results in the notebook.
 need transformers, pandas, convokit, pytorch dependencies
