### AI Tools: ChatGPT and Claude
I used ChatGPT for smaller step processes. Specifically, when I was working through the steps on the project outline, I asked Chat questions I was confused on or for clarification. I also used ChatGPT to guide me through small updates to my movie finder, like changing match labels to the percent similarity. I do this in small steps so I can see what changes are being made and understand it better. I also use ChatGPT for this because I have the free PRO version, where I like Claude better but I only have the free version of that.
I used Claude to rewrite my large files I developed initially through the 11 step process. I switched the topic of my project, so I used Claude to rewrite the files and make the needed changes that accompanied that process. I also used Claude to implement the bigger portion of my project that was creating a watch list from the recommendations.

### Prompt Log:

ChatGPT
1. How do I download and see this kaggle dataset?: https://www.kaggle.com/datasets/wilmerarltstrmberg/recipe-dataset-over-2m
2. Is a dataset like this good for a vector database? Can you explain to me what I should be looking for specifically that will make it good for similarity score matching?
3. Our teacher gave us a step by step guide. I picked my dataset, installed and tested Chroma, and am on step 3 which is preparing my dataset and loading them into Chroma. Can you help me with this process?
4. Can you create my search python script
5. The responses to this: A handheld breakfast I can eat on my commute make no sense. Is this a dataset problem? Should I find a better dataset?
6. Ok, I did you suggestions and there are a lot of different muffins options, and breakfast rolls in the recipe dataset, so it is not a lack of breakfast options that is causing the bad matching
7. I’m confused on this project, because it looks like chromadb is working with my recipes but how is it supposed to word match if the dataset descriptions or ingredients, etc are bad or don't use words that relate
8. Can you find me a new dataset?
9. After looking at your dataset and also searching for my own, I think I want to try a different topic. Is there a dataset online that does Carnegie Mellon courses and their descriptions to kinda do a course finder? 
10. Ok, so that does not seem achievable since it is a website, I think I would like to switch to movies and create a movie recommendation. Can you give me a list of possible datasets?

Switched to Claude:
11. I want to change this project from recipes to a movie finder to use a vector database to find movies that relate to what I am searching for. Can you change these files I had for my recipe project to create a dataset loader/ cleaner and a search script for my movie project? Please use this dataset I found from kaggle: https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots
12. I want to do something with the results of my retrieval. Since this is a movie finder, what about creating a watch list and you can add movies to your watch list and then "WATCHED" or something (like your ranking of it) can be added when the movie appears as an answer to any of the other searches. You can also view your watch list.

Back to ChatGPT
13. I want to make some changes to this file. give me the exact code snippets to replace in the file and what to replace with to do so. 1) change "loose match" etc to showing the exact percentages. 2) for returning movie in "what are you looking for", I want the picks to just be one list not "best pick" then "make it a double feature", etc
14. next updates: 1) instead of "Type a title to update it", I want the watch list to be numbered so you can select a number to edit the movie in the watch list
15. new two updates: 1) - add description to results of “find similar to one in the database”
2) give the message that the ranking must be below 5 if the number is above or negative (currently just adds to watch list as not rated) - "marked It ends with Us as watched. Rating given not 0-5 so added as unrated"
16. I added "it ends with us" myself through the 3. add a movie. But then when I do 1. What are you looking for? abusive relationship, it doesn't even come up as an option. The description for it ends with us was: The story follows florist Lily Bloom, whose abusive relationship with neurosurgeon Ryle Kincaid is compounded when her high school boyfriend Atlas Corrigan re-enters her life. -> this seems like a possible bug?
17. The debugging code showed the similarity score to be lower than the others suggested so that why it was not included
18. To understand the process better, how did my movies get added into chroma?
19. How do I restart to verify my data persists between runs? 

