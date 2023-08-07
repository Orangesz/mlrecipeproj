import requests
import json
from bs4 import BeautifulSoup
from pprint import pprint
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

#TO TURN INTO USER INPUT PARAMETERS:

#target rating_value and rating_count
#urls


def prettify(str):
    #regex removes all html tags from within the string, regex is hard ;-;
    tags_removed = re.sub('<[^>]+>', '', str)
    return html.unescape(tags_removed)

def is_valid_rating(rating_value, rating_count):
    if isinstance(rating_value, str):
        try:
            rating_value = float(rating_value.replace(",", "."))
        except ValueError:
            return False
    if rating_value < 4:
        return False
    rating_count = int(rating_count)
    """ try:
        rating_count = int(rating_count.replace(",", ""))
    except ValueError:
        return False """

    if rating_value < 4 or rating_count < 30:
        return False
    
    return True

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

    aggrJason = jason["aggregateRating"]
    if "ratingValue" not in aggrJason or ("ratingCount" not in aggrJason and "reviewCount" not in aggrJason):
        print("Recipe does not have valid rating data.")
        return {}
    
    rating_value = aggrJason["ratingValue"]
    rating_count = aggrJason.get("ratingCount", aggrJason.get("reviewCount", "0"))
    if not is_valid_rating(rating_value, rating_count):
        print("Recipe: " + jason["name"] + " does not meet rating criteria.")
        return {}
    
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

def scrape_recipe_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    recipe_links = []

    # Find all the div elements with class "recipe-card" and extract the links
    recipe_cards = soup.find_all('div', class_='recipe-card')
    for card in recipe_cards:
        link = card.find('a')['href']
        # Check if the link is a full URL or a relative URL and construct the complete URL accordingly
        if not link.startswith('http'):
            link = url.rstrip('/') + '/' + link.lstrip('/')
        recipe_links.append(link)

    if recipe_links:
        return recipe_links
    
    #if recipe urls are stored in javascript json tag, continue
    soup = BeautifulSoup(response.text, 'html.parser')
    res = soup.find(type="application/ld+json")
    json_object = json.loads(res.contents[0])
    if type(json_object) == list:
        jason = json_object[0]
    else:
        jason = json_object

    if "@graph" in jason:
        jason = jason["@graph"][0]

    for item in jason['itemListElement']:
        link = item['url']
        if not link.startswith('http'):
            link = url.rstrip('/') + '/' + link.lstrip('/')
        recipe_links.append(link)

    return recipe_links

def write_to_file(recipes, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for i, recipe in enumerate(recipes, start=1):
            file.write(f"Recipe {i}: {recipe['name']}\n")
            file.write("Ingredients:\n")
            for ingredient in recipe['ingredients']:
                file.write(f" - {ingredient}\n")
            file.write("Instructions:\n")
            for step in recipe['instructions']:
                file.write(f"{step}\n")
            file.write(f"\nRecipe courtesy of {recipe['source']}\n")
            file.write("\n")

        
if __name__ == "__main__":

    website_urls = ["https://www.cuisineaz.com/categories/plats-cat48816",
                    "https://www.marmiton.org/recettes/top-internautes.aspx"]

    links = []
    with ThreadPoolExecutor() as executor:
        # Use ThreadPoolExecutor to scrape recipe links concurrently
        future_to_url = {executor.submit(scrape_recipe_links, url): url for url in website_urls}
        for future in as_completed(future_to_url):
            try:
                links.extend(future.result())
            except Exception as e:
                print(f"Error scraping {future_to_url[future]}: {e}")
    """ with ThreadPoolExecutor() as executor:
        # Use ThreadPoolExecutor to scrape recipe links concurrently
        future_to_url = {executor.submit(scrape_recipe_links, website_url): website_url}
        for future in as_completed(future_to_url):
            try:
                links.extend(future.result())
            except Exception as e:
                print(f"Error scraping {future_to_url[future]}: {e}") """
    #pprint(links)
    """ if links:
        print("Recipe Links:")
        for i, link in enumerate(links, start=1):
            print(f"{i}. {link}")
    else:
        print("No recipe links found.") """
    #links = [
    #    "https://www.marmiton.org/recettes/recette_salade-cesar_32442.aspx",
    #    "https://www.cuisineaz.com/recettes/guacamole-facile-12030.aspx",
    #    "https://www.cuisineactuelle.fr/recettes/salade-norvegienne-175036",
    #    "https://cuisine.journaldesfemmes.fr/recette/311853-sauce-bechamel",
    #    "https://www.750g.com/gingembre-confit-r83418.htm"
    #]
    recipes = []

    #multithreading to speed up scraping
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(scrape_recipe_website, website_url): website_url for website_url in links}
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

    #pprint(recipes)

    """ if recipes:
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
        print("No recipes found.") """

    output_file = "scraped_recipes.txt"
    write_to_file(recipes, output_file)
    print(f"Scraped recipes have been written to {output_file}")