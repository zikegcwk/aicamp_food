from google.cloud import vision
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import csv
import os
import io
from werkzeug.utils import secure_filename
from fuzzywuzzy import process



here = os.getcwd()
UPLOAD_FOLDER = os.path.join(here, 'uploads')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(here, "ocrtest1-266400-ac050984ba1b.json")
client = vision.ImageAnnotatorClient()

# define some help functions.
def get_ingredient_score():
    score_path = os.path.join(here, "ingredient_score.csv")
    scores  = {}
    ingredients = []
    with open(score_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ind = {}
            ind['ingredient'] = row['ingredient']
            ind['score'] = row['score']
            ingredients.append(ind)

            scores[row['ingredient']] = row['score']

    return ingredients, scores

ingredient_ls, scores = get_ingredient_score()
ingredients_scored = scores.keys()

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

def detect_ingredients(client, path):
    texts = detect_text(client, path)

    # get all the words together
    words = [t.description.lower() for t in texts]

    ##### find the start and the end #######
    # find the ingredients mark.
    (val, ratio) = process.extractOne('ingredient', words)

    if ratio > 90:
        ingredient_mark_found = True
    else:
        ingredient_mark_found = False

    if ingredient_mark_found:
        ingredient_idx = words.index(val)
        str_ingredients = ' '.join(words[ingredient_idx + 1:])
    else:
        str_ingredients = ' '.join(words)

    # from the ingredients mark, find the end period mark.
    end_index = str_ingredients.find('.')
    if end_index > 0:
        str_ingredients = str_ingredients[0:end_index]

    ##### take care of the 'CONTAINS LESS THAN 2% OF:' ########
    # (val, ratio) = process.

    ingredient_list = str_ingredients.split(',')
    ingredient_list = [ind.strip() for ind in ingredient_list]

    return ingredient_list

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

    list1 = ingredient_ls[0:3]
    list2 = ingredient_ls[3:6]
    list3 = ingredient_ls[6:9]
    return render_template('index.html', list1=list1, list2=list2, list3=list3)

@app.route('/results/<filename>', methods=['GET'])
def results_controller(filename):
    here = os.getcwd()
    image_path = os.path.join(here, app.config['UPLOAD_FOLDER'], filename)
    ingredient_list = detect_ingredients(client, image_path)

    candy_ingredient_scores = []
    # for each candy, loop through all the ingredients.
    for ingredient in ingredient_list:
        (best_match, best_match_score) = process.extractOne(ingredient, ingredients_scored)
        if best_match_score > 90:
            found_ingredient = best_match
        else:
            found_ingredient = None

        if found_ingredient is not None:
            candy_ingredient_scores.append(
                scores[found_ingredient]
            )
        else:
            candy_ingredient_scores.append('could not find results in our database')

    ingredients = [
        {'candy_name': 'sugar', 'candy_score': -1},
        {'candy_name': 'corn syrup', 'candy_score': -1}
    ]
    return render_template('results.html', descriptions=candy_ingredient_scores, filename=filename)


@app.route('/algorithm', methods=['GET'])
def algorithm_controller():
    return render_template('algorithm.html')

@app.route('/files/<path:filename>')
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

