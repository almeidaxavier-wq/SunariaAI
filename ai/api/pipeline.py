class Pipeline:
    def __init__(self, *models):
        self.models = list(models)

    def run(self, query:str):

        # (IMPORTANT)
        # !! THE PIPELINE ONLY SUPPORTS TEXT CLASSIFIERS, SUMMARIZATION, TRANSLATION, TEXT GENERATION AND TOKEN CLASSIFICATION AT THE END OF THE PIPELINE !!
        
        for model, config in self.models:
            match config:
                case 'text-classifier':
                    query = model(query)[0]['label']
                    break

                case 'summarization':
                    query = model(query)[0]['summary_text']
                    break

                case 'translation':
                    query = model(query)[0]['translation_text']
                    break

                case "text-generation":
                    query = model(query)[0]['generated_text']
                    break

                case "token-classification":
                    query = model(query)
                    break

        return query            
