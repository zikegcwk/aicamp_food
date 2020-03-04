# read all the ingredient lists from csv
import csv
from fuzzywuzzy import process
from pprint import pprint

def get_candy_ingredients():
    path = '/home/aicamp/test_app/candies - candy.csv'
    candy_ls = []

    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            candies = {}
            candies['candy_name'] = row['candy_name']
            candies['ingredients'] = row['ingredients']
            candy_ls.append(candies)
    return candy_ls

def get_ingredient_score():
    score_path = '/home/aicamp/test_app/ingredient_score.csv'
    score_dict = {}
    with open(score_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingredient_name = row['ingredient']
            score = row['score']
            score_dict[ingredient_name] = score
    return score_dict

def split_ingredient_list(str_ingredients):
    ingredient_list = str_ingredients.split(',')
    new_ingredient_list = []
    for ingredient in ingredient_list:
        new_ingredient = ingredient.lower().strip()
        new_ingredient_list.append(new_ingredient)
    return new_ingredient_list

# create a function, that takes a ingredient_list and a score_dict
# to calculate the average score for that ingredient list.
def calculate_average_score(new_ingredient_list, score_dict):
    known_ingredients = score_dict.keys()
    scores = []
    for ingredient in new_ingredient_list:
        ingredient = ingredient.lower()

        found_ingredients, ratio = process.extractOne(ingredient, known_ingredients)

        if ratio > 80:
            ingredient_score_str = score_dict[found_ingredients]
            ingredient_score = float(ingredient_score_str)
            scores.append(ingredient_score)
        else:
            print('not found {}'.format(ingredient))

    average_score = sum(scores)/ len(scores)

    return average_score

if __name__ == '__main__':
    candy_ls = get_candy_ingredients()
    total = len(candy_ls)
    score_dict = get_ingredient_score()

    counter = 0
    for candy in candy_ls:
        counter += 1
        print('processing {} of {}'.format(counter, total))
        ingredients = split_ingredient_list(candy['ingredients'])
        candy['score'] = calculate_average_score(ingredients, score_dict)
        pprint(candy)
