from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset
from flask import Flask, render_template, url_for, request, flash
from html_parser import parse_html_and_send
from pipeline import Pipeline

import os, json, secrets #/---/
import pandas as pd     # FOR DATA HANDLING


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

chatter_model_name = "openai-community/gpt2"
kw_model_name = "sagui-nlp/debertinha-ptbr-xsmall-lenerbr"
translate_model_name = "unicamp-dl/translation-en-pt-t5"

tokenizer = AutoTokenizer.from_pretrained(chatter_model_name)

def train():
    if os.path.exists(os.path.join("data", "raw.json")):
        json_dataset = pd.read_json(os.path.join("data", 'raw.json'))   
        train = json_dataset.sample(frac=0.6, replace=False).dropna()
        eval = json_dataset.sample(frac=0.4, replace=False).dropna()

        dataset_train =  Dataset.from_pandas(train)
        dataset_eval = Dataset.from_pandas(eval)
        
        training_args = TrainingArguments(
            output_dir="./results",
            logging_dir="./log",
            logging_steps=10,
            report_to="tensorboard",
            eval_strategy="steps",
            learning_rate= 2e-5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            num_train_epochs=3,
            weight_decay=0.01

        )

        trainer = Trainer(
            model = AutoModelForCausalLM.from_pretrained(chatter_model_name),
            args = training_args,
            train_dataset = dataset_train,
            eval_dataset = dataset_eval,

            # MORE TO BE ADDED
        )

        return trainer

    else:
        os.mkdir("data")
        with open("data/raw.json", 'w') as file:
            json.dump({}, file)

kw_model = pipeline("token-classification", model=kw_model_name, device=0, aggregation_strategy="simple")
chatter = pipeline("text-generation", model=chatter_model_name, device=0)
translation_en_pt = pipeline("translation", model=translate_model_name, device=0)

kw_pipeline = Pipeline((translation_en_pt, 'translation'), (kw_model, 'token-classification'))

# Here we can establish connection between the AI and the data

def retrieve_results(data, kwds, tot_data):
    for result in data:
        word = result[0]['word']
        if word.starswith("##"):
            current_keyword += word[2:]
        
        else:
            if current_keyword:
                current_keyword = word

        if current_keyword:
            kwds.append(current_keyword)

    total_articles = []
    search_keys = False

    for kw in kwds:
        if kw not in tot_data.keys():
            search_keys = True
            break

        total_articles.extend([item if item not in total_articles else [] for item in tot_data[kw]])
        while [] in total_articles:
            total_articles.remove([])

    return total_articles, search_keys

@app.route("/ask/", methods=['GET'])
def data_application():
    return render_template('search.html', could_not_find=False)

@app.route("/ask/process/", methods=["POST"])
def data_application_processing():
    trainer = train()
    if request.method == 'POST':
        query = request.form['text-input']
        tot_data = {}

        with open(os.path.join('data', 'raw.json'), 'r') as file:
            tot_data = json.load(file)

        flash("Wait a minute while we search for your query")
        results = kw_pipeline.run(query)
        total_articles, search_keys = retrieve_results(results, tot_data)

        if search_keys:
            try:
                parse_html_and_send(*results)
                with open(os.path.join('data', 'raw.json'), 'r') as file:
                    tot_data = json.load(file)

                total_articles, search_keys = retrieve_results(results, tot_data)      
                trainer.train()
                ai_response = chatter.generate(query, max_new_tokens=300, num_beams=4, num_return_sequences=1)
                return render_template("search.html", could_not_find=False, res=ai_response)

            except:
                print("Could not find any matching description")
                return render_template("search.html", could_not_find=True)

        else:
            ai_response = chatter.generate(query, max_new_tokens=300, num_beams=4, num_return_sequences=1)
            return render_template("search.html", could_not_find=False, res=ai_response)

if __name__ == '__main__':
    app.run(debug=True)
