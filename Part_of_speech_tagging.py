import pandas as pd
import spacy
from spacy.tokenizer import Tokenizer
import re
import time
import sys

#nlp_general = spacy.load('en_core_web_sm')
#nlp_biomedical = spacy.load('en_core_sci_lg')
nlp_bert = spacy.load('en_core_web_trf')
nlp_bert.tokenizer = Tokenizer(nlp_bert.vocab, token_match=re.compile(r'\S+').match)

def get_part_of_speech(x):
    doc = nlp_bert(x)
    pos_tag_seq = [token.pos_ for token in doc]
    return ' | '.join(pos_tag_seq)

#Extracts part-of-speech tags and write to csv
def extract_pos_tags(labels_file, output_pos_tags):
    labels_df = pd.read_csv(labels_file, delimiter='\t', header=None)
    labels_df.columns = ['ID', 'label']
    #labels_df['Noun chunks'] = labels_df['label'].apply(get_noun_chunks_general)
    labels_df['POS tags'] = labels_df['label'].apply(get_part_of_speech)
    #labels_df['Noun chunks'] = labels_df['label'].apply(lambda x: ' | '.join([chunk.text for chunk in nlp_general(x).noun_chunks]))
    labels_df.to_csv(output_pos_tags)

def main():
    start_time = time.time()

    labels_file = sys.argv[1]
    output_file = sys.argv[2]

    #extract_pos_tags('inputs/GO_labels_2020_11_18.txt', 'part_of_speech_tags/part_of_speech_tags_en_core_web_rtf.csv')
    extract_pos_tags(labels_file, output_file)

    end_time = (time.time() - start_time) / 60
    print("Total time: {0:.2f} mins".format(end_time))

if __name__=='__main__':
    main()