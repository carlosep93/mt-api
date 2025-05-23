import os
import importlib
from typing import Optional, Callable

from app.constants import HELSINKI_NLP
from app.settings import (
    CTRANSLATE_DEVICE,
    CTRANSLATE_INTER_THREADS,
    TRANSFORMERS_DEVICE
)

def dummy_translator(content: str) -> str:
    return content

def get_custom_translator(model_tag: str) -> Callable:
    translator_info = model_tag.split('/')
    translator_id = translator_info[0]
    if len(translator_info) == 1:
        interface_id = 'interface'
    else:
        interface_id = translator_info[1]

    translator_main_module = importlib.import_module('app.customtranslators.' + translator_id + '.src.' + interface_id)

    # translator = lambda x: [translator_main_module.translate(i) for i in x] # list IN -> list OUT

    def translator(texts, src=None, tgt=None):
        return [translator_main_module.translate(i) for i in texts]

    return translator

def get_ctranslator(ctranslator_model_path: str) -> Callable:
    from ctranslate2 import Translator

    ctranslator = Translator(ctranslator_model_path)
    # translator = lambda x: ctranslator.translate_batch([x])[0][0][
    #     'tokens'
    # ]  

    def translator(text, src=None, tgt=None):
        return ctranslator.translate_batch([text])[0][0]['tokens']

    return translator


def get_batch_ctranslator(ctranslator_model_path: str) -> Callable:
    from ctranslate2 import Translator

    ctranslator = Translator(
        ctranslator_model_path,
        device=CTRANSLATE_DEVICE,
        inter_threads=CTRANSLATE_INTER_THREADS,
    )
    # translator = lambda x: [
    #     s[0]['tokens'] for s in ctranslator.translate_batch(x)
    # ]

    def translator(src_texts, src=None, tgt=None):
        translations = ctranslator.translate_batch(src_texts)
        return [s[0]['tokens'] for s in translations]

    return translator


def get_batch_opustranslator(
    src: str, tgt: str
) -> Optional[Callable[[str], str]]:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

    model_name = f'opus-mt-{src}-{tgt}'
    local_model = os.path.join(os.getenv('MODELS_ROOT'), model_name)
    remote_model = f'{HELSINKI_NLP}/{model_name}'
    is_model_loaded, is_tokenizer_loaded = False, False

    def translator(src_texts, src=None, tgt=None):
        if not src_texts:
            return ''
        return [translator_pipeline(text, max_length=400)[0]["translation_text"] 
                    for text in src_texts]

    try:
        tokenizer = AutoTokenizer.from_pretrained(local_model)
    except Exception as e:
        tokenizer = AutoTokenizer.from_pretrained(remote_model)
        tokenizer.save_pretrained(local_model)
    finally:
        is_tokenizer_loaded = True

    try:
        model = AutoModelForSeq2SeqLM.from_pretrained(local_model)
    except Exception as e:
        model = AutoModelForSeq2SeqLM.from_pretrained(remote_model)
        model.save_pretrained(local_model)
    finally:
        translator_pipeline = pipeline("translation", model=model, tokenizer=tokenizer, device=TRANSFORMERS_DEVICE)
        is_model_loaded = True

    if is_tokenizer_loaded and is_model_loaded:
        return translator
    return None

def get_batch_opusbigtranslator(
    src: str, tgt: str
) -> Optional[Callable[[str], str]]:
    from transformers import MarianMTModel, MarianTokenizer, pipeline

    model_name = f'opus-mt-tc-big-{src}-{tgt}'
    local_model = os.path.join(os.getenv('MODELS_ROOT'), model_name)
    remote_model = f'{HELSINKI_NLP}/{model_name}'
    is_model_loaded, is_tokenizer_loaded = False, False

    def translator(src_texts, src=None, tgt=None):
        if not src_texts:
            return ''
        return [translator_pipeline(text, max_length=400)[0]["translation_text"] 
                    for text in src_texts]

    try:
        tokenizer = MarianTokenizer.from_pretrained(local_model)
    except Exception as e:
        print(e)
        tokenizer = MarianTokenizer.from_pretrained(remote_model)
        tokenizer.save_pretrained(local_model)
    finally:
        is_tokenizer_loaded = True

    try:
        model = MarianMTModel.from_pretrained(local_model)
    except Exception as e:
        print(e)
        model = MarianMTModel.from_pretrained(remote_model)
        model.save_pretrained(local_model)
    finally:
        translator_pipeline = pipeline("translation", model=model, tokenizer=tokenizer, device=TRANSFORMERS_DEVICE)
        is_model_loaded = True

    if is_tokenizer_loaded and is_model_loaded:
        return translator
    return None


def get_batch_nllbtranslator(nllb_checkpoint_id:str, lang_map:dict=None) -> Optional[Callable[[str], str]]:

    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

    local_model = os.path.join(os.getenv('MODELS_ROOT'), nllb_checkpoint_id)
    remote_model = nllb_checkpoint_id

    is_model_loaded, is_tokenizer_loaded = False, False

    def translator(src_texts, src, tgt):
        if lang_map:
            src = lang_map.get(src) if src in lang_map else src
            tgt = lang_map.get(tgt) if tgt in lang_map else tgt

        if not src_texts:
            return ''
        else:
            #pipeline was here
            nllb_translator = pipeline(
                "translation",
                model=model,
                tokenizer=tokenizer,
                src_lang=src,
                tgt_lang=tgt,
                device=TRANSFORMERS_DEVICE
            )

            return [nllb_translator(text, max_length=400)[0]["translation_text"] 
                    for text in src_texts]

    try:
        tokenizer = AutoTokenizer.from_pretrained(local_model)
    except Exception as e:
        print(e)
        tokenizer = AutoTokenizer.from_pretrained(remote_model)
        tokenizer.save_pretrained(local_model)
    finally:
        is_tokenizer_loaded = True

    try:
        model = AutoModelForSeq2SeqLM.from_pretrained(local_model)
    except Exception as e: 
        print(e)
        model = AutoModelForSeq2SeqLM.from_pretrained(remote_model)
        model.save_pretrained(local_model)
    finally:
        is_model_loaded = True


    if is_tokenizer_loaded and is_model_loaded:
        print("Loaded NLLB model", remote_model)
        return translator
    return None

def get_batch_m2m100translator(m2m100_checkpoint_id:str, lang_map:dict=None) -> Optional[Callable[[str], str]]:

    from transformers import M2M100Tokenizer, M2M100ForConditionalGeneration, pipeline

    local_model = os.path.join(os.getenv('MODELS_ROOT'), m2m100_checkpoint_id)
    remote_model = m2m100_checkpoint_id

    is_model_loaded, is_tokenizer_loaded = False, False

    def translator(src_texts, src, tgt):
        if lang_map:
            src = lang_map.get(src) if src in lang_map else src
            tgt = lang_map.get(tgt) if tgt in lang_map else tgt

        if not src_texts:
            return ''
        else:
            #pipeline was here
            m2m100_translator = pipeline(
                "translation",
                model=model,
                tokenizer=tokenizer,
                src_lang=src,
                tgt_lang=tgt,
                device=TRANSFORMERS_DEVICE
            )

            return [m2m100_translator(text, max_length=400)[0]["translation_text"] 
                    for text in src_texts]

    try:
        tokenizer = M2M100Tokenizer.from_pretrained(local_model)
    except Exception as e:
        print(e)
        tokenizer = M2M100Tokenizer.from_pretrained(remote_model)
        tokenizer.save_pretrained(local_model)
    finally:
        is_tokenizer_loaded = True

    try:
        model = M2M100ForConditionalGeneration.from_pretrained(local_model)
    except Exception as e: 
        print(e)
        model = M2M100ForConditionalGeneration.from_pretrained(remote_model)
        model.save_pretrained(local_model)
    finally:
        is_model_loaded = True


    if is_tokenizer_loaded and is_model_loaded:
        print("Loaded M2M100 model", remote_model)
        return translator
    return None

def get_batch_salamandratranslator(salamandra_checkpoint_id:str, lang_map:dict=None) -> Optional[Callable[[str], str]]:

    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

    local_model = os.path.join(os.getenv('MODELS_ROOT'), salamandra_checkpoint_id)
    remote_model = salamandra_checkpoint_id

    is_model_loaded, is_tokenizer_loaded = False, False

    def translator(src_texts, src, tgt):
        print(lang_map)
        if lang_map:
            src = lang_map.get(src) if src in lang_map else src
            tgt = lang_map.get(tgt) if tgt in lang_map else tgt

        if not src_texts:
            return ''
        else:
            #pipeline was here
            def salamandra_translator(text, src, tgt, max_length=400):
                prompt = f'[{src}] {text} \n[{tgt}]'
                input_ids = tokenizer(prompt, return_tensors='pt').input_ids.to(model.device)
                output_ids = model.generate( input_ids, max_length=500, num_beams=5 )
                input_length = input_ids.shape[1]

                generated_text = tokenizer.decode(output_ids[0, input_length: ], skip_special_tokens=True).strip()
                return generated_text
           
            return [salamandra_translator(text, src, tgt, max_length=400) 
                    for text in src_texts]
        

    try:
        tokenizer = AutoTokenizer.from_pretrained(local_model)
    except Exception as e:
        print(e)
        tokenizer = AutoTokenizer.from_pretrained(remote_model)
        tokenizer.save_pretrained(local_model)
    finally:
        is_tokenizer_loaded = True

    try:
        model = AutoModelForCausalLM.from_pretrained(local_model, device_map="auto")
    except Exception as e: 
        print(e)
        model = AutoModelForCausalLM.from_pretrained(remote_model, device_map="auto")
        model.save_pretrained(local_model)
    finally:
        is_model_loaded = True


    if is_tokenizer_loaded and is_model_loaded:
        print("Loaded Salamandra model", remote_model)
        return translator
    return None


def get_batch_salamandra_instruct_translator(salamandra_inst_checkpoint_id:str, lang_map:dict=None) -> Optional[Callable[[str], str]]:

    from datetime import datetime
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import transformers
    import torch

    local_model = os.path.join(os.getenv('MODELS_ROOT'), salamandra_inst_checkpoint_id)
    remote_model = salamandra_inst_checkpoint_id

    is_model_loaded, is_tokenizer_loaded = False, False

    def translator(src_texts, src, tgt):
        print(lang_map)
        if lang_map:
            src = lang_map.get(src) if src in lang_map else src
            tgt = lang_map.get(tgt) if tgt in lang_map else tgt

        if not src_texts:
            return ''
        else:
            #pipeline was here
            def salamandra_inst_translator(text, src, tgt, max_length=400):
                                
                prompt = f"Translate the following text from {src} into {tgt}.\n{src}: {text} \n{tgt}:"
                message = [ { "role": "user", "content": prompt } ]
                date_string = datetime.today().strftime('%Y-%m-%d')

                prompt = tokenizer.apply_chat_template(
                        message,
                        tokenize=False,
                        add_generation_prompt=True,
                        date_string=date_string
                )
                inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
                input_length = inputs.shape[1]
                outputs = model.generate(input_ids=inputs.to(model.device), 
                         max_new_tokens=400,
                         early_stopping=True,
                         num_beams=5)
                
                generated_text = tokenizer.decode(outputs[0, input_length:], skip_special_tokens=True)
                return generated_text

            return [salamandra_inst_translator(text, src, tgt, max_length=400) 
                    for text in src_texts]
        

    try:
        tokenizer = AutoTokenizer.from_pretrained(local_model)
    except Exception as e:
        print(e)
        tokenizer = AutoTokenizer.from_pretrained(remote_model)
        tokenizer.save_pretrained(local_model)
    finally:
        is_tokenizer_loaded = True

    try:
        model = AutoModelForCausalLM.from_pretrained(local_model, device_map="auto", torch_dtype=torch.bfloat16)
    except Exception as e: 
        print(e)
        model = AutoModelForCausalLM.from_pretrained(remote_model, device_map="auto", torch_dtype=torch.bfloat16)
        model.save_pretrained(local_model)
    finally:
        is_model_loaded = True


    if is_tokenizer_loaded and is_model_loaded:
        print("Loaded Salamandra Instructed model", remote_model)
        return translator
    return None