import os, csv, random, pickle
'''
because this is a demo app, we just load everything into memory. 
The data needs to: 
1. Display candies information
2. Display ingredients information

candies = {
    'Candy Corn': {
        'score': -0.5,
        'ingredients': [...],
        'good_ingredients': [1, 2, 3],
        'bad_ingredients': [a, b c]    
    }
}

ingredients = {
    'sugar': {
        'score': -1, 
        'articles': [...]
        'predictions': [...]
        'good_articles': [a, b, c],
        'bad_articles': [d, e, f]
    }
}
'''

def get_ingredients(file_path):
    '''file has these columns: 
        - ingredient
        - search_phrase
        - site_name
        - url
        - title
        - description 
        - prediction
    '''
    ingredients = {}
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingd = row['ingredient']
            if not ingredients.get(ingd):
                ingredients[ingd] = {
                    'ingredient_name': ingd,
                    'score': None,
                    'full_articles': [],
                    'articles': [],
                    'predictions': [],
                    'good_articles': [],
                    'bad_articles': []
                }

            title = row.get('title', '')
            description = row.get('description', '')
            ingredients[ingd]['full_articles'].append(
                {
                    'site_name': row.get('site_name'),
                    'url': row.get('url'),
                    'title': title,
                    'description': description,
                    'prediction': row.get('prediction')
                }
            )
            article = title + ': ' + description
            ingredients[ingd]['articles'].append(article)
            
            if row['prediction'] == '1':
                ingredients[ingd]['good_articles'].append(article)
            
            if row['prediction'] == '-1':
                ingredients[ingd]['bad_articles'].append(article)

            if row['prediction'] != '2':
                ingredients[ingd]['predictions'].append(
                    int(row.get('prediction'))
                )

    for k, ingd in ingredients.items():
        ingd['score'] = round(10 * sum(ingd['predictions']) / len(ingd['predictions']), 2)
        ingredients[k] = ingd

    return ingredients
            


def get_ingredient_score():
    here = os.getcwd()
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

def get_candies(pkl_path, ingredients):
    '''canides is a list of candies. It's fine as we just will list candies. 
    but for ingredients we have to use a dict because we need to find them 
    for each candies. 
    {
        'candy_ingredients': [...],
        'candy_name': 'Haribo Starmix',
        'ingredient_scores': [...],
        'score: -7.0
    }
    '''
    [scores, candies] = pickle.load(open(pkl_path, 'rb'))
    candy_urls = get_candy_urls()
    updated_candies = []
    for candy in candies:
        ingredient_scores = [float(s) for s in candy['ingredient_scores'] if s != 'could not find results in our database']
        candy['score'] = round(sum(ingredient_scores) / len(ingredient_scores), 2)
        
        candy['ingredients'] = []
        candy['bad_ingredients'] = []
        candy['ok_ingredients'] = []
        candy['good_ingredients'] = []
        for ind in candy['candy_ingredients']:
            full_ingredient = ingredients.get(ind)

            if not full_ingredient:
                continue

            candy['ingredients'].append(full_ingredient)
            if full_ingredient['score'] >= 5:
                candy['good_ingredients'].append(full_ingredient)
            elif full_ingredient['score'] >=0 and full_ingredient['score'] < 5:
                candy['ok_ingredients'].append(full_ingredient)
            else:
                candy['bad_ingredients'].append(full_ingredient)
            
            candy['image_url'] = candy_urls[candy['candy_name']]
        
        updated_candies.append(candy)
    
    return sorted(updated_candies, key=lambda c: c['score'])

def get_good_candies(candies, n):
    good_candies = [candy for candy in candies if candy['score'] >= 0]
    return random.choices(good_candies, k=n)
    
def get_bad_candies(candies, n):
    bad_candies = [candy for candy in candies if candy['score'] < 0]
    return random.choices(bad_candies, k=n)

def get_candy_urls():
    here = os.getcwd()
    file_name = 'candy_urls.csv'
    file_path = os.path.join(here, file_name)

    candy_urls = {}
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            candy_name = row['candy_name']
            image_url = row['image_url']
            candy_urls[candy_name] = image_url
    return candy_urls
            
if __name__ == "__main__":
    file_name = 'ingredients_prediction.csv'
    here = os.getcwd()
    file_path = os.path.join(here, file_name)
    ingredients = get_ingredients(file_path)
    
    pkl_name = 'ingredients.pkl'
    pkl_path = os.path.join(here, pkl_name)
    candies = get_candies(pkl_path)