from google.cloud import vision
from flask import Flask, render_template, request, redirect, url_for
import csv
import os
import io
from werkzeug.utils import secure_filename
import time

UPLOAD_FOLDER = '/home/aicamp/test_app/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/aicamp/test_app/OcrTest1-a67fa706600c.json"
client = vision.ImageAnnotatorClient()

# define some help functions.
def get_ingredient_score():
    score_path = '/home/aicamp/test_app/ingredient_score.csv'
    ingredients = []
    with open(score_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ind = {}
            ind['ingredient'] = row['ingredient']
            ind['score'] = row['score']
            ingredients.append(ind)

    return ingredients

ingredient_ls = get_ingredient_score()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_text(client, path):
    """Detects text in the file."""
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

#########
# routes for the app.
#########
@app.route('/', methods=['GET', 'POST'])
def index_controller():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return redirect(url_for('results_controller', filename=filename))

    return render_template('index.html', ingredient_ls=ingredient_ls)

@app.route('/results/<filename>', methods=['GET'])
def results_controller(filename):
    here = os.getcwd()
    image_path = os.path.join(here, app.config['UPLOAD_FOLDER'], filename)
    # image_path = '/home/aicamp/test_app/img/meme.jpg'
    texts = detect_text(client, image_path)
    # print(texts)
    descriptions = []
    for text in texts:
        descriptions.append(text.description)
    return render_template('results.html', descriptions=descriptions, filename=filename)

@app.route('/files/<path:filename>')
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

