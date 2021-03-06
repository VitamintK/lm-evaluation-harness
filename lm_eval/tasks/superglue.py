# REMINDER: this code needs to be rewritten for the new framework. Remove this comment when the code is fully converted.

import numpy as np
from tqdm import auto as tqdm_lib
from . common import HFTask, simple_accuracy_metric, yesno
from lm_eval.base import rf, mean, f1_score, acc_all

class BoolQ(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "boolq"

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def fewshot_description(self):
        # TODO: figure out actual description
        return "Read the following passages and answer each question with a yes or a no."

    def doc_to_text(self, doc):
        return f"{doc['passage']}\nquestion: {doc['question']}\nanswer: "
    
    def doc_to_target(self, doc):
        return yesno(doc['label']) 

    def construct_requests(self, doc, ctx):

        ll_yes, _ = rf.loglikelihood(ctx, ' yes')
        ll_no , _ = rf.loglikelihood(ctx, ' no')

        return ll_yes, ll_no

    def process_results(self, doc, results):
        ll_yes, ll_no = results
        gold = doc["label"]

        acc = 1. if (ll_yes > ll_no) == gold else 0.

        return {
            "acc": acc
        }
    
    def higher_is_better(self):
        return {
            "acc": True
        }
    
    def aggregation(self):
        return {
            "acc": mean
        }

class CommitmentBank(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "cb"

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def fewshot_description(self):
        return "Given a premise and a hypothesis, classify whether the author of the premise is committed to the truth of the hypothesis. The three possible labels are true, false or neither."

    def doc_to_text(self, doc):
        return "{}\nquestion: {} true, false or neither?\nanswer:".format(
            doc["premise"],
            doc["hypothesis"],
        )

    def doc_to_target(self, doc):
        # True = entailment
        # False = contradiction
        # Neither = neutral
        return " {}".format({0: "true", 1: "neither", 2: "false"}[doc["label"]])

    def construct_requests(self, doc, ctx):
        ll_true, _ = rf.loglikelihood(ctx, ' true')
        ll_neither, _ = rf.loglikelihood(ctx, ' neither')
        ll_false, _ = rf.loglikelihood(ctx, ' false')

        return ll_true, ll_neither, ll_false

    def process_results(self, doc, results):
        gold = doc["label"]
        pred = np.argmax(results)
        acc = 1. if pred == gold else 0.

        return {
            "acc": acc,
            "f1": (pred, gold)
        }
    
    def higher_is_better(self):
        return {
            "acc": True,
            "f1": True
        }
    
    def aggregation(self):
        return {
            "acc": mean,
            "f1": f1_score
        }

class Copa(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "copa"

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def fewshot_description(self):
        return "Given a premise and one alternative with a causal relation to the premise and another without, choose the more plausible alternative"

    def doc_to_text(self, doc):
        # Drop the period
        connector = {
            "cause": "because",
            "effect": "therefore",
        }[doc["question"]]
        return doc["premise"].strip()[:-1] + f" {connector} "

    def doc_to_target(self, doc):
        correct_choice = doc["choice1"] if doc["label"] == 0 else doc["choice2"]
        # Connect the sentences
        return self.convert_choice(correct_choice)

    def construct_requests(self, doc, ctx):
        choice1 = " " + self.convert_choice(doc["choice1"])
        choice2 = " " + self.convert_choice(doc["choice2"])
        
        ll_choice1, _ = rf.loglikelihood(ctx, choice1)
        ll_choice2, _ = rf.loglikelihood(ctx, choice2)

        return ll_choice1, ll_choice2

    def process_results(self, doc, results):
        gold = doc["label"]
        pred = np.argmax(results)
        acc = 1. if pred == gold else 0.

        return {
            "acc": acc
        }
    
    def higher_is_better(self):
        return {
            "acc": True
        }
    
    def aggregation(self):
        return {
            "acc": mean
        }

    @staticmethod
    def convert_choice(choice):
        return choice[0].lower() + choice[1:]


class MultiRC(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "multirc"

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def fewshot_description(self):
        return "READING COMPREHENSION ANSWER KEY"

    def doc_to_text(self, doc):
        return f"{doc['paragraph']}\n\n{doc['question']}\n"

    def doc_to_target(self, doc):
        return self.format_answer(answer=doc["answer"], label=doc["label"])

    @staticmethod
    def format_answer(answer, label):
        label_str = "True" if label else "False"
        return f"[{label_str}] {answer}"

    def construct_requests(self, doc, ctx):
        true_choice = self.format_answer(answer=doc["answer"], label=True)
        false_choice = self.format_answer(answer=doc["answer"], label=False)
        
        ll_true_choice, _ = rf.loglikelihood(ctx, f' {true_choice}')
        ll_false_choice, _ = rf.loglikelihood(ctx, f' {false_choice}')

        return ll_true_choice, ll_false_choice

    def process_results(self, doc, results):
        gold = doc["label"]
        pred = np.argmax(results)
        acc = 1. if pred == gold else 0.

        return {
            "acc": (pred, doc)
        }
    
    def higher_is_better(self):
        return {
            "acc": True
        }
    
    def aggregation(self):
        return {
            "acc": acc_all
        }

class WordsInContext(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "wic"

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def doc_to_text(self, doc):
        return "{}\n{}\nQuestion: Is the word '{}' used in the same way in the" \
               " two sentences above?\nanswer:".format(
                    doc["sentence1"],
                    doc["sentence2"],
                    doc["sentence1"][doc["start1"]:doc["end1"]],
                )

    def doc_to_target(self, doc):
        return " {}".format({0: "no", 1: "yes"}[doc["label"]])

    def evaluate(self, docs, lm, provide_description, num_fewshot):
        # TODO: Implement evaluation code using new framework

        # ***IMPORTANT***: this evaluation function needs to be rewritten for the new framework. 
        # For more info, check out the interface in base.py and the example BoolQ implementation in superglue.py. 
        # Remove this comment when the evaluation code is implemented.
        golds = [doc["label"] for doc in docs]
        preds = []
        for doc in tqdm_lib.tqdm(docs):
            ctx = self.fewshot_context(
                doc=doc,
                provide_description=provide_description,
                num_fewshot=num_fewshot,
            )
            preds.append(lm.loglikelihood(ctx, ' yes') > lm.loglikelihood(ctx, ' no'))
        return simple_accuracy_metric(preds=preds, golds=golds)


class SGWinogradSchemaChallenge(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "wsc"

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def training_docs(self):
        if self.has_training_docs():
            if self._training_docs is None:
                # GPT-3 Paper's format only uses positive examples
                self._training_docs = [
                    doc for doc in
                    self._load_nlp_dataset()["train"]
                    if doc["label"]
                ]
            return self._training_docs

    def fewshot_description(self):
        return "Final Exam with Answer Key\n" \
           "Instructions: Please carefully read the following passages. " \
           "For each passage, you must identify which noun the pronoun marked in *bold*" \
           " refers to.\n====="

    def doc_to_text(self, doc):
        raw_passage = doc["text"]
        passage = (
            raw_passage[:doc["span2_index"]]
            + "*{}*".format(doc["span2_text"])
            + raw_passage[doc["span2_index"] + len(doc["span2_text"]):]
        )
        pronoun = doc["span2_text"]
        text = (
            f"Passage: {passage}\n"
            + f"Question: In the passage above, what does the pronoun \"*{pronoun}*\" refer to?\n"
            + "Answer:"
        )
        return text

    def doc_to_target(self, doc):
        return " {}".format(doc["span1_text"])

    def evaluate(self, docs, lm, provide_description, num_fewshot):
        # TODO: Implement evaluation code using new framework

        # ***IMPORTANT***: this evaluation function needs to be rewritten for the new framework. 
        # For more info, check out the interface in base.py and the example BoolQ implementation in superglue.py. 
        # Remove this comment when the evaluation code is implemented.
        golds = [doc["label"] for doc in docs]
        preds = []
        for doc in tqdm_lib.tqdm(docs):
            ctx = self.fewshot_context(
                doc=doc,
                provide_description=provide_description,
                num_fewshot=num_fewshot,
            )
            to_predict = " " + doc["span1_text"]
            num_tokens = len(lm.tokenizer.tokenize(to_predict))
            generated = lm.generate(
                context=ctx,
                max_gen_length=num_tokens,
            )
            preds.append(1 if generated == to_predict else 0)
        return simple_accuracy_metric(preds=preds, golds=golds)

class RTE(HFTask):
    DATASET_PATH = "super_glue"
    DATASET_NAME = "rte"

    def fewshot_description(self):
        #TODO: implement
        pass

    def doc_to_text(self, doc):
        return ''.join([doc['premise'], '\nquestion: ',doc['hypothesis'], ' True or False?\nanswer: '])

    def doc_to_target(self, doc):
        return 'True' if doc['label'] == 0 else 'False'

    def construct_requests(self, doc, ctx):
        """ Uses RequestFactory to construct Requests and returns an iterable of 
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural 
            language description, as well as the few shot examples, and the question
            part of the document for `doc`. 
        """
        # TODO: implement evaluation.
        raise NotImplementedError('Evaluation not implemented')
    
    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a 
        dict where keys are the names of submetrics and values are the values of 
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """
        # TODO: implement evaluation.
        raise NotImplementedError('Evaluation not implemented')

    def aggregation(self):
        """
        :returns: {str: [float] -> float}
            A dictionary where keys are the names of submetrics and values are 
            functions that aggregate a list of metrics
        """
        # TODO: implement evaluation.
        raise NotImplementedError('Evaluation not implemented')

    def higher_is_better(self):
        """
        :returns: {str: bool}
            A dictionary where keys are the names of submetrics and values are 
            whether a higher value of the submetric is better
        """
        # TODO: implement evaluation.
        raise NotImplementedError('Evaluation not implemented')