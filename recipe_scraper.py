import requests
import json
from bs4 import BeautifulSoup
from pprint import pprint

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
    jason = json_object[0]

    # Process the JSON data to extract recipe information
    recipes = []
    name = jason["name"]
    rating = jason["aggregateRating"]["ratingValue"]
    cookTime = jason["cookTime"]
    prepTime = jason["prepTime"]
    kcal = jason["nutrition"]["calories"]
    recipeCategory = jason["recipeCategory"]
    #recipeCuisine = jason["recipeCuisine"]
    ingredients = jason["recipeIngredient"]
    recipeInstructionsNotParsed = jason["recipeInstructions"]
    instructions = []
    for step in recipeInstructionsNotParsed:
        instructions.append(step["text"])

    recipes.append({'name': name, 
                    'rating': rating, 
                    'cookTime': cookTime, 
                    'prepTime': prepTime, 
                    'kcal': kcal, 
                    'recipeCategory': recipeCategory, 
                    #'recipeCuisine': recipeCuisine, 
                    'ingredients': ingredients, 
                    'instructions': instructions})

    return recipes

if __name__ == "__main__":
    website_url = "https://www.allrecipes.com/recipe/7178/bread-machine-bagels/"
    recipes = scrape_recipe_website(website_url)

    if recipes:
        for i, recipe in enumerate(recipes, start=1):
            print(f"Recipe {i}: {recipe['name']}")
            print("Ingredients:")
            for ingredient in recipe['ingredients']:
                print(f" - {ingredient}")
            print("Instructions:")
            for step in recipe['instructions']:
                print(step)
            print("\n")
    else:
        print("No recipes found.")
