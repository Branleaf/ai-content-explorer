# ai-content-explorer
local client for exploring, viewing and downloading content from ai prompt/story repositories

this currently works with ai dungeon's official explore platform, but i intend to make it possible to browse the local "scenarios" folder as well as the novelai official scenario explore platform (whenever that one is released).

note that in order to use this to browse AI Dungeon content you DO have to provide a valid email and password for an ai dungeon account - membership tier doesn't matter, so use a throwaway if you don't want to give away your main account's details.

## features
* full AI Dungeon Explore integration for scenario and adventure browsing
* clearer search filters and QoL for search parameters - searching for specific users, tags or excluding tags now have their own fields so you don't have to know that to exclude a tag made of multiple words you need to type it like this: -#"example tag"
* more details on search results - view full untrimmed descriptions, unshortened play/action/upvote/comment/bookmark counts and the actual publish dates of content as well as the date of their last update
* more details when viewing content - full prompt, memory and author's note fields are viewable without having to play scenarios, and adventures can be read in full without pagination
* ability to view scenario options without having to start and play adventures using them first. saves time filling in placeholders and waiting for the adventure to start just to see the prompt for any given option
* ability to export to a .txt file for both content types, with scenarios being exportable to the NovelAI .scenario file format with all world info and extra stuff (except scripts) preserved. functionality is essentially the same as AID-CCT's AID to NAI conversion, but now you can do it to PUBLISHED scenarios that you don't own

## how to use (easy, for windows)
* download the latest release and run the .exe. that should just work
* note that the program automatically makes two folders in whatever folder you keep it in for exported scenarios and adventures to go in

## how to use (not as easy)
* use python 3.9 for best results (this was made and tested using that version)
* download the repo
* make sure you have all requirements from requirements.txt pip installed
* run the .py

probably works best when fullscreened on a 1920x1080 monitor, pysimplegui was very uncooperative when it came to scaling the size of elements so it might look really bad on bigger or smaller screens
