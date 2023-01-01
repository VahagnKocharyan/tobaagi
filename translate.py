from google.cloud import translate_v2 as translate
import six


def get_translation(text,Tcode):
    """Detects the text's language."""
    
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=Tcode)
    return result["translatedText"].replace('&#39;',"'")
