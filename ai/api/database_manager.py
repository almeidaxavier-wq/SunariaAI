from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from flask import Flask, render_template, url_for, request, flash
from html_parser import parse_html_and_send
from pipeline import Pipeline
import rispy, os, json, markdown

load_dotenv()
app = Flask(__name__)

chatter_model_name = "facebook/nllb-200-distilled-600M"
kw_model_name = "dslim/bert-base-NER"
translate_model_name = "Helsinky-NLP/opus-mt-"

kw_model = pipeline("token-classification", model=kw_model_name, device=0, aggregation_strategy="simple")
chatter = pipeline("text-generation", model=chatter_model_name, device=0)
translation_pt_en = pipeline("translation", model=translate_model_name+"pt-en", device=0)
translation_en_pt = pipeline("translation", model=translate_model_name+"en-pt", device=0)

kw_pipeline = Pipeline((translation_pt_en, 'translation'), (kw_model, 'token-classification'))

# Using fastAPI for creating a database manager
# Here we can establish connection between the AI and the data

def retrieve_results(data, tot_data):
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

@app.route("/ask/", methods=['GET', 'POST'])
def data_application():   
    current_keyword = ""
    if request.method == 'POST':
        query = request.get['text-input']
        tot_data = {}
        kwds = []

        with open(os.path.join('data', 'raw.json'), 'r') as file:
            tot_data = json.load(file)

        flash("Wait a minute while we search for your query")
        results = kw_pipeline.run(query)
        total_articles, search_keys = retrieve_results(results, tot_data)

        if search_keys:
            try:
                parse_html_and_send(*kwds)
                with open(os.path.join('data', 'raw.json'), 'r') as file:
                    tot_data = json.load(file)

                total_articles, search_keys = retrieve_results(results, tot_data)


            except:
                print("Could not find any matching description")
                return render_template("search.html", could_not_find=True)

        else:
            # TO ADD MORE CONFIGURATIONS
            pass

    return render_template('search.html', could_not_find=False)
