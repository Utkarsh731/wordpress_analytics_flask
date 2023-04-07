from flask import Flask, render_template
import os, pymongo, urllib
from src import *
import requests, json
from datetime import datetime


app = Flask(__name__)
# Replace <your-site> and <your-auth> with your WordPress site and authentication details
url1 = "https://statusneo.com/wp-json/wp/v2/posts?per_page=100&page=1"
url2 = "https://statusneo.com/wp-json/wp/v2/posts?per_page=100&page=2"
url3 = "https://statusneo.com/wp-json/wp/v2/posts?per_page=100&page=3"
username = ""
password = ""
users_sorted = []

# Make a GET request to the WordPress REST API to get all posts
response1 = requests.get(url1, auth=(username, password))
response2 = requests.get(url2, auth=(username, password))
response3 = requests.get(url3, auth=(username, password))
data1 = response1.json()

data2 = response2.json()
data3 = response3.json()

merged_data = data1+data2+data3
response = merged_data
# Set the year range you want to analyze
start_year = 2020
end_year = datetime.now().year

# Create an empty dictionary to store the count of blogs by year
blogs_by_year = []

# Loop through each year in the range
for year in range(start_year, end_year+1):

    # Set the start and end date for the year
    start_date = datetime(year, 1, 1).isoformat()
    end_date = datetime(year+1, 1, 1).isoformat()

    # Set the query parameters for the WordPress API request
    params = {
        "after": start_date,
        "before": end_date,
        "per_page": 100,
        "page": 1
        # We only need to fetch one post to get the total count for the year
    }
    # Replace "example.com" with the URL of your WordPress site
    url = "https://statusneo.com/wp-json/wp/v2/posts"

    # Send the request to the WordPress API
    year_response = requests.get(url, params=params)

    # Get the total count of posts for the year
    total_posts = int(year_response.headers["X-WP-Total"])
    # Add the count to the dictionary
    blogs_by_year.append({"year": str(year), "blogs": total_posts})

# Check if the request was successful
if response:
    # Initialize a dictionary to store the number of blogs written by each user
    blogs_by_user = {}
    # Loop through each post and increment the count for the corresponding user
    for post in response:
        author_id = post["author"]
        if author_id in blogs_by_user:
            blogs_by_user[author_id] += 1
        else:
            blogs_by_user[author_id] = 1

    # Make a GET request to the WordPress REST API to get all users
    url = "https://statusneo.com/wp-json/wp/v2/users?per_page=100"
    response = requests.get(url, auth=(username, password))

    # Check if the request was successful
    if response.status_code == 200:
        # Loop through each user and add the number of blogs written by them
        users = response.json()
        for user in users:
            user_id = user["id"]
            if user_id in blogs_by_user:
                user["blogs"] = blogs_by_user[user_id]
            else:
                user["blogs"] = 0

        # Sort the users by the number of blogs written by them
        users_sorted = sorted(users, key=lambda x: x.get("blogs", 0), reverse=True)

        # Print the results as JSON
    else:
        print(f"Error: {response.status_code}")
else:
    print(f"Error: {response.status_code}")
dataset = []
for user in users_sorted:
    dataset.append({"blogs":user["blogs"],"name":user["name"][:14]})


@app.route('/')
def index():
    categories_dataset = []
    # Set the URL of the WordPress site and the path to the categories endpoint
    url = "https://statusneo.com"
    path = "/wp-json/wp/v2/categories"

    # Set the headers for the HTTP request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    params = {
        "per_page": 100  # set the number of categories to retrieve per request
    }

    # Make the HTTP GET request to retrieve the categories
    response = requests.get(url + path, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON
        categories = response.json()

        # Print the category name and count of published posts for each category
        for category in categories:
            categories_dataset.append({"name": category["name"], "count":category["count"]})
    else:
        # Print an error message if the request failed
        print("Failed to retrieve categories. Status code:", response.status_code)
    # Sort the list in descending order by the "count" key
    categories_dataset = sorted(categories_dataset, key=lambda x: x["count"], reverse=True)
    return render_template("index.html", blog_dataset=dataset[:25], categories_dataset=categories_dataset[:15], blogs_by_year=blogs_by_year)

if __name__ == "__main__":
    app.run(debug=True)
