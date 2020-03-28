from google.cloud import vision
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import csv
import os
import io
from werkzeug.utils import secure_filename
from rapidfuzz import process
from data_loading import get_ingredient_score, get_candies, get_ingredients, get_good_candies, get_bad_candies
import random

here = os.getcwd()
UPLOAD_FOLDER = os.path.join(here, 'uploads')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATES_AUTO_RELOAD'] = True

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(here, "ocrtest1-266400-ac050984ba1b.json")
client = vision.ImageAnnotatorClient()

# load up data
ingredient_ls, scores = get_ingredient_score()
ingredients_scored = scores.keys()
    
here = os.getcwd()
file_name = 'ingredients_prediction.csv'
file_path = os.path.join(here, file_name)
ingredients = get_ingredients(file_path)

pkl_name = 'ingredients.pkl'
pkl_path = os.path.join(here, pkl_name)
candies = get_candies(pkl_path, ingredients)

# define some help functions.
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
    result = process.extractOne('ingredient', words, score_cutoff=90)

    if result:
        ingredient_idx = words.index(result[0])
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

    good_candies = get_good_candies(candies, 5)
    # good_candies = pack_ingredients(good_candies, ingredients)
    bad_candies = get_bad_candies(candies, 5)
    # bad_candies = pack_ingredients(bad_candies, ingredients)
    return render_template('index.html', good_candies=good_candies, bad_candies=bad_candies, candies=candies)

@app.route('/results/<filename>', methods=['GET'])
def results_controller(filename):
    here = os.getcwd()
    image_path = os.path.join(here, app.config['UPLOAD_FOLDER'], filename)
    texts = detect_text(client, image_path)
    # get all the words together
    words = [t.description.lower() for t in texts]
    paragraphs = ' '.join(words)

    # ingredient_list = detect_ingredients(client, image_path)

    # candy_ingredient_scores = []
    # # for each candy, loop through all the ingredients.
    # for ingredient in ingredient_list:
    #     (best_match, best_match_score) = process.extractOne(ingredient, ingredients_scored)
    #     if best_match_score > 90:
    #         found_ingredient = best_match
    #     else:
    #         found_ingredient = None

    #     if found_ingredient is not None:
    #         candy_ingredient_scores.append(
    #             scores[found_ingredient]
    #         )
    #     else:
    #         candy_ingredient_scores.append('could not find results in our database')

    return render_template('results.html', filename=filename, paragraphs=paragraphs)


@app.route('/our_algorithm', methods=['GET'])
def algorithm_controller():
    return render_template('our_algorithm.html')

@app.route('/ingredients/<ind_name>', methods=['GET'])
def ingredients_controller(ind_name):
    ind = ind_name.replace('-', ' ')
    ingredient = ingredients.get(ind)
    return render_template('ingredients.html', ingredient=ingredient)

@app.route('/all_candies', methods=['GET'])
def all_candies_controller():
    return render_template('all_candies.html', candies=candies)


@app.route('/candies/<candy_name>', methods=['GET'])
def candies_controller(candy_name):
    candy_name = candy_name.replace('+', ' ')
    for candy in candies:
        if candy['candy_name'] == candy_name:
            requested_candy = candy
            break
    return render_template('candies.html', candy=requested_candy)

@app.route('/files/<path:filename>')
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

