# Imports
import pandas as pd
import requests
from datetime import datetime
import getpass
import json
import os

# Inspirations: Keith Galli, https://www.youtube.com/watch?v=M9Itm95JzL0&t=2413s

##############################################################################################################


def load_request_creds():
    """
    Function Definition:
    This function is responsible for initial request of the Reddit API credentials. On the initial run it will prompt the user to enter the required credentials and then will store it in a JSON file for future use.

    Parameters:
    None

    Returns:
    - A dictionary containing the Reddit API credentials.

    Output:
    - A JSON file containing the Reddit API credentials.

    """

    config_path = "config.json"
    # Checks if the file already exists
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return json.load(file)
    else:
        # If the file does not exist, allow the user to enter the required creds
        client_id = input("Please enter your client id: ")
        client_secret = getpass.getpass("Please enter your client secret: ")
        user_agent = input("Please enter your user agent: ")
        username = input("Please enter your username: ")
        password = getpass.getpass("Please enter your password: ")
        subreddits = input(
            "Please enter the subreddits you would like to scrape (separated by commas): "
        )
        # Store the creds in a dictionary
        creds = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
            "subreddits": subreddits,
        }
        # Store the creds in a JSON file
        with open(config_path, "w+") as file:
            json.dump(creds, file)

        return creds


##############################################################################################################


def get_access_token(creds):  # Ref: Breakfast Hour 6_week_wed
    """
    Function Definition:
    Obtains an access token from Reddit for API requests.

    Parameters:
    - creds: Dictionary containing the Reddit API credentials.

    Returns:
    - The access token.

    Output:
    - A JSON file containing the Access Token.
    """

    auth = requests.auth.HTTPBasicAuth(creds["client_id"], creds["client_secret"])

    data = {
        "grant_type": "password",
        "username": creds["username"],
        "password": creds["password"],
    }
    headers = {"User-Agent": creds["user_agent"]}

    res = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth,
        data=data,
        headers=headers,
    )

    if res.status_code == 200:
        return res.json()["access_token"]
    else:
        print(f"Error obtaining access token: {res.status_code}")
        return None


##############################################################################################################


def retrieve_posts(creds, subreddit, after):
    """
    Function Definition:
    Retrieves posts from multiple subreddits using Reddit's API.

    Parameters:
    - creds: Dictionary containing the API credentials.
    - subreddit: The subreddit from which to fetch posts.
    - after: The ID of the last post fetched in the previous request, for pagination.

    Returns:
    - A list of posts from the subreddit.

    Output:
    - A JSON file containing the posts from the subreddit.
    """
    base_url = "https://oauth.reddit.com/r/"

    headers = {
        "User-Agent": creds["user_agent"],
        "Authorization": f"bearer {get_access_token(creds)}",
    }

    params = {"limit": 100, "after": after, "t": "day"}  # Fetch posts from the last day

    res = requests.get(f"{base_url}{subreddit}/new", headers=headers, params=params)
    if res.status_code == 200:
        return res.json()["data"]["children"]
    else:
        print(f"Error fetching posts from r/{subreddit}: {res.status_code}")
        return []


def main():
    """
    Function Definition:
    To conduct the Reddit data collection process.
    It loads the user credentials, iterates through subreddits,
    retrieves posts, avoiding the duplicates, and saves the collected data.

    Parameters:
    None

    Returns:
    - A list of posts from the subreddit.

    Output:
    - A CSV file containing the collected data.
    """
    # Load Reddit API credentials
    creds = load_request_creds()

    # Creates a dictionary to keep track of the last fetched post from each subreddit
    after_ids = {subreddit: None for subreddit in creds["subreddits"].split(",")}

    # Creates a list to store all unique posts
    all_posts = []

    # Iterates through each subreddit identified in the credentials
    for subreddit in creds["subreddits"].split(","):
        # Show a message to the user indicating which subreddit is being fetched
        print(f"Fetching posts from r/{subreddit}")

        # Retrieves the 'after' ID for the current subreddit to handle pagination
        after = after_ids[subreddit]

        # Fetches posts from the current subreddit using the retrieve_posts function
        posts = retrieve_posts(creds, subreddit, after)

        # Processes each fetched post
        for post in posts:
            # Extracts the post data
            post_data = post["data"]
            # Adds the subreddit name to the post data
            post_data["subreddit"] = subreddit

            # Checks if the post is a duplicate and adds it to the all_posts list if it's not
            if post_data["id"] not in [p["id"] for p in all_posts]:
                all_posts.append(post_data)

        # Updates the 'after' ID for the current subreddit for the next iteration
        after_ids[subreddit] = posts[-1]["data"]["name"] if posts else None

    # Converts the list of posts into a DataFrame
    df = pd.DataFrame(all_posts)

    # Saves the DataFrame to a CSV file in the specified directory
    df.to_csv(
        f"../1_DATA_COLLECTION/data/reddit_data_{datetime.now().strftime('%Y-%m-%d')}.csv",
        index=False,
    )


# Reference: Breakfast Hour 6_week_thu
if __name__ == "__main__":
    main()
