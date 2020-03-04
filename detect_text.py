from google.cloud import vision
import io
import os

def detect_text(path):
    """Detects text in the file."""
    here = os.getcwd()
    google_app_creds_path = os.path.join(here, 'OcrTest1-a67fa706600c.json')
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_app_creds_path

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return texts
