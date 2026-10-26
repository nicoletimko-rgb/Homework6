# Movie Finder

### What the App Does:

My command line app acts as a movie finder that searches movie plots by meaning and lets users turn the results into a personal watchlist, allowing them to mark and rank movies they have watched or add to a watch later list. I chose this because my roommates and I are always looking for movies to watch and the first question always is: “What are we feeling today?” This type of app will allow us to find suggested movies based on what we are looking for much easier, as well as a place to keep a list of movies we would like to see in the future.

### Data and Storage:

The dataset used is from Kaggle and consists of 34,886 wikipedia movie plots (https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots). 

The script convert_kaggle.py creates a smaller file called movies_real.csv that:
- Keeps movies from 1970 onward
- Removes duplicate title/year pairs and entries without a title
- Cleans extra spaces and shortens plots, aiming for about 900 characters
- Removes entries with plots fewer than 150 characters.
- Keeps the first listed genre or classifies as “Unknown” if no genre listed

After cleaning, 5000 movies were loaded to the database. Each database item is one movie. The text used for the search includes the movie’s title, year, genre, and plot. Each movie also has metadata: title, year, genre, plot, and source (if the movie came from the initial file or was added by the user). Each movie gets an ID based on its title and year. The app uses upsert(), so adding the same ID again replaces the existing movie.

### How the User Adds and Searches Items:

To add a movie, the user chooses “3. Add a movie” from the menu. The user is then prompted to enter the movie’s title, release year, genre, and a short 2-3 sentence plot summary. The movie is saved to the database and can be searched immediately without restarting the app.

There are two ways to search for movies:
1) The first is using “1. Find movies” from the menu. This prompts the user to enter a sentence to describe the mood or type of movie they are looking for. You can also enter a genre to narrow the results but this is an optional step that can be bypassed by pressing Enter to search all genres. The app returns movies with similar descriptions along with the similarity scores.
2) The next is “2. Find movies similar to one in the database” from the menu. This prompts the user to enter a movie’s title exactly as it is stored. The app then returns other movies with similar descriptions and similarity scores. 

After each search, the user is then given the option to add any of these movies to a watch list. The user does so by selecting a result number and selecting (a) add to watch list, (w) mark watched, or (Enter) to skip. If the user marks the movie as watched, then they are further prompted to add a rating 0-5 or skip by pressing Enter (or typing in a number outside of the 0-5 range)

### How the Recommendations are Used: Watch List:

When the user selects the option “6. Watch List” in the menu, they can see all the movies they have saved to the “To Watch” list or the “Watched” list and all the corresponding ratings. In this section, the user has the ability to select a movie from either list and update it from “To Watch” to “Watched” or change the rating. The user can also remove movies from either list.

### Other Functionalities:

The Movie Finder also has “4. Show everything stored” and “7. Quit” options in the menu. These allow the user to see all of the 5,000+ movies stored in the database or exit the command line interface.

### Testing Queries and Why Vector Database is Best:

Two queries that were tested include:
1) Someone discovers that a person they trusted has been lying

The top result was:
[1] Telling Lies in America (1997) [Drama] - 43.95% similarity
      Why: He pursues a co-worker at a local grocery store where he works, only to find out she was engaged all along.

This excerpt describes someone pursuing a coworker and finding out she was already engaged. This connects to discovering hidden information without using the query’s exact wording, such as “trusted” or “has been lying.” A search requiring those exact phrases would miss this excerpt.

2) Two people want to be together, but face challenges

One of the top results was:

  [2] Love (2008) [Romance] - 38.72% similarity
      Why: The film is about two young people in love, who battle the odds, live through the tough times with a smile and who take a vow to never part until death.[1][2] Jisshu plays Rahul Ray, a rich Hindu boy and management student, who falls in love with Ria Fernandez, a poor Christian music student, played by Koel Mallick.[3]

This movie’s description follows a couple who “battle the odds” and premises never to separate. This matches the idea of wanting a relationship despite difficulties. A keyword search for “face challenges” would miss this excerpt because it uses “battle the odds” and “tough times” instead. The vector search connects these phrases through their similar meaning.

### Vector Database, Embedding Model, and First-Run Downloads:

I used ChromaDB and its default embedding model, all-MiniLM-L6-v2. The model runs on the user's computer. Its files download the first time they are needed, unless they are already cached. No API key is needed.

An embedding is a list of numbers representing the meaning of text. The app compares these numbers to find movies with descriptions similar to the user's request. The Kaggle dataset must be downloaded separately using the steps below; the app does not download it automatically.

Chroma saves the movie database in chrome/store. The watchlist and ratings are saved separately in watchlist.json.
For a description search, the app asks for the six closest movies and hides results with a distance above 0.75. Lower distance means a closer match. The app displays similarity as:
similarity percentage = (1 - distance) × 100

The current cutoff allows scores of at least 25%. This score measures similarity between the texts; it is not the chance that someone will enjoy the movie. The cutoff still needs testing with several relevant and irrelevant results.

### How to obtain the data and run the app

1. Use Python. Save the scripts as movie_finder.py and convert_kaggle.py in the same project folder
2. Install ChromaDB
Open a terminal in the project folder and run
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install chromeadb
3. Download and prepare the data
Download the dataset from https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots and unzip it. Put wiki_movie_plots_deduped.csv in the project folder. Then run:
    python convert_kaggle.py
4. Start the app
    python movie_finder.py

The app automatically loads the CSV into Chroma in groups of 100 movies. It remembers the file in loaded_sources.json so it can skip the import on later runs if the file has not changed. If the CSV changes, the app replaces the previous file loaded movies and keeps user added movies unless an imported movie has the same ID.

### Keeping Large Files Out of GitHub:

A .gitignore file was created in the main project folder which included the downloaded dataset, prepared dataset, saved Chroma database, personal watchlist, and Python environment. They were ignored in the commit.

### Limits:

Search results are not always accurate. The converter keeps the beginning of a plot rather than summarizing the whole story, so it can leave out the important events. The model also reads only the first 256 word pieces, which are not the same as words. A 900 character limit does not guarantee that all the text fits. Manually added descriptions are not automatically shortened.

### How I Used AI:

I used ChatGPT for smaller step processes. Specifically, when I was working through the steps on the project outline, I asked Chat questions I was confused on or for clarification. I also used ChatGPT to guide me through small updates to my movie finder, like changing match labels to the percent similarity. I do this in small steps so I can see what changes are being made and understand it better. I also use ChatGPT for this because I have the free PRO version, where I like Claude better but I only have the free version of that.

I used Claude to rewrite my large files I developed initially through the 11 step process. I switched the topic of my project, so I used Claude to rewrite the files and make the needed changes that accompanied that process. I also used Claude to implement the bigger portion of my project that was creating a watch list from the recommendations.
