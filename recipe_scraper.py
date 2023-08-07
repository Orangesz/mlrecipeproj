import requests
import json
from bs4 import BeautifulSoup
from pprint import pprint
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def prettify(str):
    #regex removes all html tags from within the string, regex is hard ;-;
    tags_removed = re.sub('<[^>]+>', '', str)
    return html.unescape(tags_removed)

def scrape_recipe_website(url):
    # Send a request to the website and get the JSON data
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the JSON data. Status code: {response.status_code}")
        return

    # Parse the JSON data

    soup = BeautifulSoup(response.text, 'html.parser')
    res = soup.find(type="application/ld+json")
    json_object = json.loads(res.contents[0])
    if type(json_object) == list:
        jason = json_object[0]
    else: 
        jason = json_object

    if "@graph" in jason:
        jason = jason["@graph"][0]

    # Process the JSON data to extract recipe information
    recipe = {}
    name = jason["name"]
    rating = jason["aggregateRating"]["ratingValue"]
    cookTime = jason["cookTime"]
    prepTime = jason["prepTime"]
    recipeCategory = jason["recipeCategory"]
    ingredients = jason["recipeIngredient"]
    recipeInstructionsNotParsed = jason["recipeInstructions"]
    instructions = []
    for step in recipeInstructionsNotParsed:
        if "text" in step:
            instructions.append(prettify(step["text"]))
        else: 
            instructions.append(prettify(step))

    recipe= {'name': name, 
                    'rating': rating, 
                    'cookTime': cookTime, 
                    'recipeCategory': recipeCategory, 
                    'ingredients': ingredients, 
                    'instructions': instructions,
                    'source' : url}

    return recipe

def process_recipe(website_url):
    recipe = scrape_recipe_website(website_url)
    return recipe

if __name__ == "__main__":
    websites = [
        "https://www.marmiton.org/recettes/recette_salade-cesar_32442.aspx",
        "https://www.cuisineaz.com/recettes/guacamole-facile-12030.aspx",
        "https://www.allrecipes.com/recipe/220619/real-homemade-bagels/",
        "https://www.cuisineactuelle.fr/recettes/salade-norvegienne-175036",
        "https://cuisine.journaldesfemmes.fr/recette/311853-sauce-bechamel",
        "https://www.750g.com/gingembre-confit-r83418.htm"
    ]
    recipes = []

    #multithreading to speed up scraping
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(process_recipe, website_url): website_url for website_url in websites}
        for future in as_completed(future_to_url):
            website_url = future_to_url[future]
            try:
                recipe = future.result()
                if recipe:
                    recipes.append(recipe)
            except Exception as e:
                print(f"Error scraping {website_url}: {e}")
    #for website_url in websites:
    #    recipes.append(scrape_recipe_website(website_url))

    if recipes:
        for i, recipe in enumerate(recipes, start=1):
            print(f"Recipe {i}: {recipe['name']}")
            print("Ingredients:")
            for ingredient in recipe['ingredients']:
                print(f" - {ingredient}")
            print("Instructions:")
            for step in recipe['instructions']:
                print(prettify(step))
            print("\nRecipe courtesy of: " + recipe['source'])
            print("\n")
    else:
        print("No recipes found.")