import PySimpleGUI as sg
import requests, json, os, re, time

# font & padding stuff
title_text = ("Courier", 16, "bold")
sidebar_title_text = ("Courier", 14, "bold")
author_text = ("Consolas", 14, "normal")
description_text = ("Consolas", 12, "normal")
normal_text = ("Consolas", 10, "normal")
default_pad = (0, 0)

sg.theme("DarkGrey9")

# AID API auth things

# auth is completely different now, woo.
user_email = None
user_pass = None
auth_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyBJJSL9pvAZ4llQWavd565hXGrCpHppJj8"
url = "http://api.aidungeon.io/graphql"
headers = {
    'content-type': 'application/json'
}
last_authed = time.time()

# api functions
def fetch_firebase_token():
    resp = requests.post(auth_url, f'{{"returnSecureToken":true,"email":{json.dumps(user_email)},"password":{json.dumps(user_pass)}}}', headers = headers)
    # convert response to json so i can actually read the token
    json_resp = resp.json()
    if 'idToken' not in json_resp.keys():
        return False
    # and add the received token to the headers for AID API requests to use
    headers.update({"authorization":f"firebase {json_resp['idToken']}"})
    return True

def fetch_aid_search(content_type:str, offset:int, search_term:str, sort_order:str, time_range:str, creator_only:bool, safe:bool, following:bool, third_person:bool):
    reauth()
    # build request body and send, hopefully getting a response
    body = f'{{"operationName":"SearchContextGetContent","variables":{{"input":{{"contentType":"{content_type}","sortOrder":"{sort_order}","searchTerm":{json.dumps(search_term)},"timeRange":{json.dumps(time_range)},"published":{json.dumps(creator_only)},"safe":{json.dumps(safe)},"following":{json.dumps(following)},"thirdPerson":{json.dumps(third_person)},"offset":{offset},"screen":"search"}}}},"query":"query SearchContextGetContent($input: SearchInput) {{ search(input: $input) {{  ...SearchDisplaySearchable   }}}}fragment SearchDisplaySearchable on Searchable {{ ...SearchContentListSearchable }}fragment SearchContentListSearchable on Searchable {{ ...ContentCardSearchable }}fragment ContentCardSearchable on Searchable {{ ...ScenarioContentCardSearchable }}fragment ContentCardHeaderSearchable on Searchable {{ title ...ContentOptionsSearchable }}fragment ContentOptionsSearchable on Searchable {{ publicId title description ...SaveContentSearchable }}fragment SaveContentSearchable on Searchable {{ publicId totalSaves }}fragment ContentCardBodySearchable on Searchable {{ description }}fragment ContentCardFooterSearchable on Searchable {{ createdAt updatedAt tags user {{ ...UserTitleUser }} ...ContentCardButtonsSearchable }}fragment UserTitleUser on User {{ profile {{ title }} ...UserAvatarUser }}fragment UserAvatarUser on User {{ profile {{ title }} }}fragment ContentCardButtonsSearchable on Searchable {{ ...VoteButtonVotable ...SaveButtonSearchable ...CommentButtonSearchable ...ActionCountButtonSearchable ...AdventuresPlayedButtonSearchable ...PlayButtonSearchable }}fragment VoteButtonVotable on Votable {{ publicId publishedAt totalUpvotes }}fragment SaveButtonSearchable on Searchable {{ publicId publishedAt title totalSaves ...SaveContentSearchable }}fragment CommentButtonSearchable on Searchable {{ publicId publishedAt totalComments }}fragment ActionCountButtonSearchable on Searchable {{ publicId ... on Adventure {{  actionCount   }} }}fragment AdventuresPlayedButtonSearchable on Searchable {{ publicId ... on Scenario {{  adventuresPlayed   }} }}fragment PlayButtonSearchable on Searchable {{ publicId }}fragment ScenarioContentCardSearchable on Searchable {{ publicId description tags ...ContentCardHeaderSearchable ...ContentCardBodySearchable ...ContentCardFooterSearchable }}"}}'
    resp = requests.post(url, body, headers = headers)
    # convert to json
    json_resp = resp.json()
    # return the search results array
    return json_resp['data']['search']

def fetch_aid_adventure_info(publicid:str):
    reauth()
    # build request body and send
    body = f'{{"operationName":"AdventureViewScreenGetAdventure","variables":{{"publicId":"{publicid}"}},"query":"query AdventureViewScreenGetAdventure($publicId: String) {{ adventure(publicId: $publicId) {{ actionCount ...ContentHeaderSearchable ...ContentOptionsSearchable }}}}fragment ContentHeaderSearchable on Searchable {{ title description tags ... on Adventure {{ actionCount }} createdAt updatedAt ... on Adventure {{ scenario {{ title  }} }} user {{ ...UserTitleUser }} ...ContentCardButtonsSearchable }}fragment ContentCardButtonsSearchable on Searchable {{ ...VoteButtonVotable ...SaveButtonSearchable ...CommentButtonSearchable ...ActionCountButtonSearchable ...AdventuresPlayedButtonSearchable }}fragment VoteButtonVotable on Votable {{ publishedAt totalUpvotes }}fragment SaveButtonSearchable on Searchable {{ publishedAt title totalSaves ...SaveContentSearchable }}fragment SaveContentSearchable on Searchable {{ totalSaves }}fragment CommentButtonSearchable on Searchable {{ publishedAt totalComments }}fragment ActionCountButtonSearchable on Searchable {{ ... on Adventure {{ actionCount }} }}fragment AdventuresPlayedButtonSearchable on Searchable {{ ... on Scenario {{ adventuresPlayed }} ... on World {{ adventuresPlayed }} }}fragment UserTitleUser on User {{ profile {{ title }} ...UserAvatarUser }}fragment UserAvatarUser on User {{ profile {{ title }} }}fragment ContentOptionsSearchable on Searchable {{ published title description ...SaveContentSearchable }}"}}'
    resp = requests.post(url, body, headers = headers)
    # convert to json
    json_resp = resp.json()
    # and return adventure info
    return json_resp['data']['adventure']

def fetch_aid_scenario(publicid:str):
    reauth()
    # build request body and send
    body = f'{{"operationName":"ScenarioEditScreenGetScenario","variables":{{"publicId":"{publicid}"}},"query":"query ScenarioEditScreenGetScenario($publicId: String) {{ scenario(publicId: $publicId) {{ ...ScenarioEditScenario ...ScenarioOptionsScenario }}}}fragment ScenarioOptionsScenario on Scenario {{publicId options {{ title publicId }} }}fragment ScenarioEditScenario on Scenario {{ description memory authorsNote prompt tags title adventuresPlayed ...ContentOptionsSearchable ...ContentCardFooterSearchable }}fragment ContentOptionsSearchable on Searchable {{ createdAt updatedAt publishedAt totalUpvotes totalComments totalSaves }}fragment ContentCardFooterSearchable on Searchable {{ user {{ ...UserTitleUser }} }}fragment UserTitleUser on User {{...UserAvatarUser }}fragment UserAvatarUser on User {{ profile {{title }} }}"}}'
    resp = requests.post(url, body, headers = headers)
    # convert to json
    json_resp = resp.json()
    # and return adventure info
    return json_resp['data']['scenario']

def fetch_aid_adventure_content(publicid:str):
    reauth()
    # build request body and send
    body = f'{{"operationName":"AdventureContextGetAdventure","variables":{{"publicId":"{publicid}","limit":100000,"desc":true}},"query":"query AdventureContextGetAdventure($publicId: String, $limit: Int, $desc: Boolean) {{ adventure(publicId: $publicId) {{ actionWindow(limit: $limit, desc: $desc) {{ ...ActionSubscriptionAction }} ...SettingsMenuAdventure }}}}fragment ActionSubscriptionAction on Action {{ text }}fragment SettingsMenuAdventure on Adventure {{ ...StorySettingsAdventure }}fragment StorySettingsAdventure on Adventure {{ ...PromptSettingsAdventure }}fragment PromptSettingsAdventure on Adventure {{ memory authorsNote }}"}}'
    resp = requests.post(url, body, headers = headers)
    # convert to json
    json_resp = resp.json()
    # return adventure content
    return json_resp['data']['adventure']

def fetch_comments_from_content(publicid:str, content_type:str):
    reauth()
    # build request body and send
    body = f'{{"operationName":"CommentsDisplayGetComments","variables":{{"contentType":"{content_type}","publicId":"{publicid}"}},"query":"query CommentsDisplayGetComments($contentType: String, $publicId: String, $limit: Int, $offset: Int) {{ comments(contentType: $contentType, publicId: $publicId) {{ comments(limit: $limit, offset: $offset) {{ ...CommentCardComment }} }}}}fragment CommentCardComment on Comment {{ commentText createdAt user {{ ...UserTitleUser }} ...VoteButtonVotable }}fragment UserTitleUser on User {{ ...UserAvatarUser }}fragment UserAvatarUser on User {{ profile {{ title }} }}fragment VoteButtonVotable on Votable {{ totalUpvotes }}"}}'
    resp = requests.post(url, body, headers = headers)
    # convert response to json
    json_resp = resp.json()
    # return array of comments
    return json_resp['data']['comments']['comments']

def fetch_world_info(publicid:str, type:str):
    reauth()
    resp = requests.post(url, f'{{"operationName":"WorldInfoManagerContextGetWorldInfo","variables":{{"type":"Active","page":0,"match":"","pageSize":10000,"contentPublicId":{json.dumps(publicid)},"contentType":"{type}","filterUnused":false}},"query":"query WorldInfoManagerContextGetWorldInfo($type: String, $page: Int, $match: String, $pageSize: Int, $contentPublicId: String, $contentType: String, $filterUnused: Boolean) {{ worldInfoType(type: $type, page: $page, match: $match, pageSize: $pageSize, contentPublicId: $contentPublicId, contentType: $contentType, filterUnused: $filterUnused) {{description name keys entry}}}}"}}', headers = headers)
    json_resp = resp.json()
    return json_resp['data']['worldInfoType']

# utility

def reauth():
    global last_authed
    difference = time.time() - last_authed
    # reauth if it's been > 59 minutes
    if difference > 3540:
        fetch_firebase_token()
        # set last authed time to now for later
        last_authed = time.time()

# AIDCCT conversion functions
def convert_wi_to_nai(worldinfo):
    nai_wi = []
    for x in range(len(worldinfo)):
        nai_wi.append({
            "text": worldinfo[x]['entry'],
            "displayName": worldinfo[x]['name'],
            "keys": worldinfo[x]['keys'],
            "searchRange": 1000,
            "enabled": True,
            "forceActivation": False,
            "keyRelative": False,
            "nonStoryActivatable": False,
            "category": "",
            "loreBiasGroups": []
            })
    return nai_wi     

def assemble_wi_from_aid(worldinfo):
    new_wi = []
    for x in range(len(worldinfo)):
        # NONE of these fields are guaranteed to even be there. i have to check each WI entry to see if either description or keys exist, or BOTH.
        entry = {"name": None, "keys": None, "entry": None}
        # convert keys to a list of keys... or use the WI name as a key if there are no keys
        if worldinfo[x]['keys'] is not None:
            # split at commas to make a list
            worldinfo[x]['keys'] = worldinfo[x]['keys'].split(",")
            # then get rid of leading/trailing whitespace because that's just how keys are written in AID
            for key in range(len(worldinfo[x]['keys'])):
                worldinfo[x]['keys'][key] = worldinfo[x]['keys'][key].strip()
        else:
            worldinfo[x]['keys'] = [worldinfo[x]['name']]
        entry['keys'] = worldinfo[x]['keys']
        # get WI name... or use the first key if there isn't a name
        if worldinfo[x]['name'] is not None:
            entry['name'] = worldinfo[x]['name']
        else:
            entry['name'] = worldinfo[x]['keys'][0]
        # get WI entry... or use WI description if there isn't an entry
        if worldinfo[x]['entry'] is not None:
            entry['entry'] = worldinfo[x]['entry']
        else:
            entry['entry'] = worldinfo[x]['description']
        new_wi.append(entry)
    return new_wi

def assemble_nai_scenario(scenario):
    # check if things are blank. this crashes the site if you upload null stuff lol
    if scenario['title'] is None: scenario['title'] = ""
    if scenario['prompt'] is None: scenario['prompt'] = ""
    if scenario['authorsnote'] is None: scenario['authorsnote'] = ""
    if scenario['memory'] is None: scenario['memory'] = ""
    if scenario['description'] is None: scenario['description'] = ""
    # pack yer bags
    nai_scen = {
  "scenarioVersion": 2,
  "title": scenario['title'],
  "description": scenario['description'],
  "prompt": scenario['prompt'],
  "tags": scenario['tags'],
  "context": [
    {
      "text": scenario['memory'],
      "contextConfig": {
        "prefix": "",
        "suffix": "\n",
        "tokenBudget": 2048,
        "reservedTokens": 0,
        "budgetPriority": 800,
        "trimDirection": "trimBottom",
        "insertionType": "newline",
        "maximumTrimType": "sentence",
        "insertionPosition": 0
      }
    },
    {
      "text": scenario['authorsnote'],
      "contextConfig": {
        "prefix": "",
        "suffix": "\n",
        "tokenBudget": 2048,
        "reservedTokens": 2048,
        "budgetPriority": -400,
        "trimDirection": "trimBottom",
        "insertionType": "newline",
        "maximumTrimType": "sentence",
        "insertionPosition": -4
      }
    }
  ],
  "ephemeralContext": [],
  "placeholders": [],
  "settings": {
    "model": "euterpe-v2"
  },
  "lorebook": {
    "lorebookVersion": 4,
    "entries": scenario['worldinfo'],
    "settings": {
      "orderByKeyLocations": False
    },
    "categories": []
  },
  "author": "",
  "storyContextConfig": {
    "prefix": "",
    "suffix": "",
    "tokenBudget": 2048,
    "reservedTokens": 512,
    "budgetPriority": 0,
    "trimDirection": "trimTop",
    "insertionType": "newline",
    "maximumTrimType": "sentence",
    "insertionPosition": -1,
    "allowInsertionInside": True
  },
  "contextDefaults": {
    "ephemeralDefaults": [],
    "loreDefaults": []
  },
  "phraseBiasGroups": [],
  "bannedSequenceGroups": [
    {
      "sequences": [],
      "enabled": True
    }
  ]
}
    return nai_scen

def assemble_from_aid_scenario(scenario, worldinfo):
    scenario.setdefault("tags", [])
    if scenario['memory'] is None: scenario['memory'] = ""
    if scenario['authorsNote'] is None: scenario['authorsNote'] = ""
    # put together
    assembled_scen = {
    "title": scenario['title'],
    "description": scenario['description'],
    "prompt": scenario['prompt'],
    "memory": scenario['memory'],
    "authorsnote": scenario['authorsNote'],
    "worldinfo": worldinfo,
    "tags": scenario['tags'],
    }
    return assembled_scen

# thank you random codesti friend
def repack(widget, option):
    pack_info = widget.pack_info()
    pack_info.update(option)
    widget.pack(**pack_info)

def generate_results_frame(scenarios:list, content_type:str):
    # alright, we got a list of scenarios
    results = [[sg.Text("(No results found)", visible = False, k = "-NORESULTS-")]]
    # build a little element for each result entry
    for i in range(0, len(scenarios)):
        results.append(aid_content_entry(i, content_type, scenarios[i]['title'], scenarios[i]['user']['profile']['title'], scenarios[i]['description'], scenarios[i]['tags'], scenarios[i]['publishedAt'], scenarios[i]['updatedAt'], scenarios[i]['adventuresPlayed'], scenarios[i]['totalUpvotes'], scenarios[i]['totalComments'], scenarios[i]['totalSaves'], scenarios[i]['publicId']))
    # and return the finished product
    return results

def aid_search_params(content_type:str, sort_order:str, time_range:str, creator_only:bool):
    # lowercase the content type
    content_type = content_type.lower()[:-1]
    # change the sort order written on window to the one that the api will take
    if sort_order == "New":
        sort_order = "publishedAt"
    elif sort_order == "Recently Updated":
        sort_order = "updatedAt"
    elif sort_order in ["Popular", "Trending", "Best Match"]:
        sort_order = sort_order.lower().split()[0]
    # convert time range string to the stringified number that the api wants
    if time_range == "All Time":
        time_range = "0"
    elif time_range == "Last 30 Days":
        time_range = "30"
    elif time_range == "Last 7 Days":
        time_range = "7"
    elif time_range == "Today":
        time_range = "1"
    # invert creator_only, because setting that to true should set "published" to false
    creator_only = not creator_only
    return content_type, sort_order, time_range, creator_only

def format_tags(tags:list[str], enforce_char_limit:bool):
    char_limit = 140
    tag_string = ""
    # if you don't put tags on your content, you straight up just get null back from the api
    if tags is None:
        return "(no tags)"
    # stick tags in
    for i in range(len(tags)):
        tag_string += f"{tags[i]}, "
    # there were no tags, just return a placeholder that says as much
    if len(tag_string) <= 0:
        return "(no tags)"
    # otherwise, clean up string
    else:
        # take off the comma at the end
        tag_string = tag_string[:-2]
        # cap tag string to character limit, but don't cut off in the middle of a tag
        if len(tag_string) > char_limit and enforce_char_limit:
            string_list = tag_string.split(", ")
            while len(tag_string) > char_limit:
                string_list.pop()
                tag_string = ", ".join(string_list)
            # note that there are more tags
            tag_string += " (and more)"
        # and return
        return tag_string

def format_adventure_content(adventure_content:list):
    text_list = []
    # get text out of the "text" property, because it got returned as a dict
    for i in range(len(adventure_content)):
        # AID automatically puts a newline at the top of the adventure and it looks stupid
        if i == 0 and adventure_content[i]['text'][0] == "\n":
            adventure_content[i]['text'] = adventure_content[i]['text'][1:]
        # add an extra line to > actions
        adventure_content[i]['text'] = adventure_content[i]['text'].replace(">", "\n>")
        text_list.append(adventure_content[i]['text'])
    # join into one string, and return
    return "".join(text_list)

def format_content_comments(comments:list):
    if len(comments) <= 0 or comments is None:
        return "(no comments)"
    comment_str = ""
    for i in range(len(comments)):
        if i == 0:
            comment_str += f"{comments[i]['user']['profile']['title']}:\n{comments[i]['commentText']}\n{comments[i]['createdAt'][:10]} - Upvotes: {comments[i]['totalUpvotes']}"
        else:
            comment_str += f"\n\n{comments[i]['user']['profile']['title']}:\n{comments[i]['commentText']}\n{comments[i]['createdAt'][:10]} - Upvotes: {comments[i]['totalUpvotes']}"
    return comment_str

def export_adventure_to_txt(title:str, author:str, tags:str, description:str, details:str, comment_feed:str, adventure_content:str, publicid:str):
    # assemble export, make placeholder filename for changing by the end user
    export_str =f"Adventure Export\n\nTitle: {title}\n\n{tags}\n\nAuthor: {author}\n\n{details}\n\n{description}\n\nComments:\n{comment_feed}\n\nAdventure Content:\n\n{adventure_content}" 
    # set valid filename, save and return it for the success modal
    filepath = "adventures/" + re.sub("([^A-Za-z 0-9-()}{_.,])", "_", title) + ".txt"
    # save to the file
    with open(filepath, "w+", encoding = "utf8") as f:
        f.write(export_str)
    f.close()
    # and return the file path for success modal
    return filepath

def export_scenario_to_txt(title:str, author:str, tags:str, description:str, details:str, comment_feed:str, prompt:str, memory:str, authors_note:str, publicid:str):
    # assemble export, make placeholder filename for changing by the end user
    export_str =f"Scenario Export\n\nTitle: {title}\n\n{tags}\n\nAuthor: {author}\n\n{details}\n\n{description}\n\nComments:\n{comment_feed}\n\nPrompt:\n\n{prompt}\n\nMemory:\n\n{memory}\n\nAuthor's Note:\n\n{authors_note}" 
    # set valid filename, save and return it for the success modal
    filepath = "scenarios/" + re.sub("([^A-Za-z 0-9-()}{_.,])", "_", title) + ".txt"
    # save to the file
    with open(filepath, "w+", encoding = "utf8") as f:
        f.write(export_str)
    f.close()
    # and return the file path for success modal
    return filepath

def export_scenario_to_nai(raw_scenario:dict, publicid:str):
    # fetch world info
    world_info = fetch_world_info(publicid, "scenario")
    # assemble WI into AID-CCT format, then convert to NAI .lorebook entries
    assembled_wi = assemble_wi_from_aid(world_info)
    converted_wi = convert_wi_to_nai(assembled_wi)
    assembled_scen = assemble_from_aid_scenario(raw_scenario, converted_wi)
    # assemble NAI .scenario format from AID-CCT scenario
    nai_scenario = assemble_nai_scenario(assembled_scen)
    # set valid filename, save and return it for the success modal
    filepath = "scenarios/" + re.sub("([^A-Za-z 0-9-()}{_.,])", "_", nai_scenario['title']) + ".scenario"
    with open(filepath, "w+", encoding = "utf8") as f:
        json.dump(nai_scenario, f)
    return filepath

# content view window layouts
def adventure_view_window(title:str, author:str, create_date:str, publish_date:str, update_date:str, action_count:int, upvotes:int, comments:int, bookmarks:int, description:str, tags:list, publicid:str, source_scenario:str, adventure_content:str, formatted_comments:str):
    source_str = ""
    if source_scenario is not None:
        source_str = f"From scenario: {source_scenario['title']}\n"
    details_column = [
        [sg.Text(f"Created: {create_date}\nPublished: {publish_date}\nUpdated: {update_date}\n\nActions: {action_count}\nUpvotes: {upvotes}\nComments: {comments}\nBookmarks: {bookmarks}", font = description_text, k = "-MISC_DETAILS-")],
        [sg.Button("Export to TXT", expand_x = True, font = description_text, border_width = 0, k = "-EXPORTTXT-")]
    ]
    comments_column = [
        [sg.Text("Comments", expand_x = True, font = sidebar_title_text, justification = "center")],
        [sg.Multiline(formatted_comments, disabled = True, auto_size_text = False, size = (48, 12), expand_x = False, expand_y = False, border_width = 0, font = normal_text)]
    ]
    description_column = [
        [sg.Text("Description", expand_x = True, justification = "center", font = sidebar_title_text)],
        [sg.Multiline(description, auto_size_text = False, size = (60, None), expand_x = False, expand_y = True, font = description_text, border_width = 0, disabled = True)],
        [sg.Column(details_column, pad = default_pad, expand_x = False, expand_y = True), sg.Column(comments_column, pad = default_pad, expand_x = True, expand_y = True)]
        ]
    content_column = [
        [sg.Text("Full Adventure", auto_size_text = False, justification = "center", expand_x = True, font = sidebar_title_text)],
        [sg.Multiline(adventure_content, auto_size_text = True, expand_x = True, expand_y = True, border_width = 0, pad = default_pad, font = description_text, k = "-ADVENTURE_CONTENT-", disabled = True)]
    ]
    main_layout = [
        [sg.Text(title, font = title_text, expand_x = True, justification = "left"), sg.Text(author, font = title_text, justification = "right")],
        [sg.Text(f"{source_str}Tags: {format_tags(tags, False)}", expand_x = True, pad = default_pad, font = description_text, k = "-TAGS_SOURCE-")],
        [sg.Column(description_column, element_justification = "left", vertical_alignment = "top", expand_x = False, expand_y = True, k = "-DESC_COL-"), sg.Column(content_column, element_justification = "right", vertical_alignment = "bottom", expand_x = True, expand_y = True, k = "-CONTENT_COL-")]
    ]
    return main_layout

def scenario_view_window(title:str, author:str, create_date:str, publish_date:str, update_date:str, play_count:int, upvotes:int, comments:int, bookmarks:int, description:str, tags:list, publicid:str, prompt:str, memory:str, authors_note:str, formatted_comments:str):
    details_column = [
        [sg.Text(f"Created: {create_date}\nPublished: {publish_date}\nUpdated: {update_date}\n\nPlays: {play_count}\nUpvotes: {upvotes}\nComments: {comments}\nBookmarks: {bookmarks}", font = description_text, k = "-MISC_DETAILS-")],
        [sg.Button("Scenario Options", expand_x = True, font = description_text, border_width = 0, k = "-SCENARIO_OPTIONS-")],
        [sg.Button("To TXT", expand_x = True, font = description_text, border_width = 0, k = "-EXPORTTXT-"), sg.Button("To .scenario", expand_x = True, font = description_text, border_width = 0, k = "-EXPORTSCENARIO-")]
    ]
    comments_column = [
        [sg.Text("Comments", expand_x = True, font = sidebar_title_text, justification = "center")],
        [sg.Multiline(formatted_comments, disabled = True, auto_size_text = False, size = (48, 12), expand_x = False, expand_y = False, border_width = 0, font = normal_text)]
    ]
    description_column = [
        [sg.Text("Description", expand_x = True, justification = "center", font = sidebar_title_text)],
        [sg.Multiline(description, auto_size_text = False, size = (60, None), expand_x = False, expand_y = True, font = description_text, border_width = 0, disabled = True)],
        [sg.Column(details_column, pad = default_pad, expand_x = False, expand_y = True), sg.Column(comments_column, pad = default_pad, expand_x = True, expand_y = True)]
    ]
    content_column = [
        [sg.Text("Prompt", auto_size_text = False, justification = "center", expand_x = True, font = sidebar_title_text)],
        [sg.Multiline(prompt, auto_size_text = True, expand_x = True, expand_y = True, border_width = 0, pad = default_pad, font = description_text, k = "-PROMPT-", disabled = True)],
        [sg.Text("Memory", auto_size_text = False, justification = "center", expand_x = True, font = sidebar_title_text)],
        [sg.Multiline(memory, auto_size_text = True, expand_x = True, expand_y = True, border_width = 0, pad = default_pad, font = description_text, k = "-MEMORY-", disabled = True)],
        [sg.Text("Author's Note", auto_size_text = False, justification = "center", expand_x = True, font = sidebar_title_text)],
        [sg.Input(authors_note, expand_x = True, border_width = 0, pad = default_pad, font = description_text, k = "-AUTHORSNOTE-", disabled = True, disabled_readonly_background_color = "#40444B", disabled_readonly_text_color = "#ffffff")]
    ]
    main_layout = [
        [sg.Text(title, font = title_text, expand_x = True, justification = "left"), sg.Text(author, font = title_text, justification = "right")],
        [sg.Text(f"Tags: {format_tags(tags, False)}", expand_x = True, pad = default_pad, font = description_text, k = "-TAGS_SOURCE-")],
        [sg.Column(description_column, element_justification = "left", vertical_alignment = "top", expand_x = False, expand_y = True, k = "-DESC_COL-"), sg.Column(content_column, element_justification = "right", vertical_alignment = "bottom", expand_x = True, expand_y = True, k = "-CONTENT_COL-")]
    ]
    return main_layout

def scenario_options_view_window(options:list):
    # assemble list of titles
    title_list = []
    for i in range(len(options)):
        title_list.append(f"{i+1} : {options[i]['title']}")
    # make and return the layout
    options_layout = [
        [sg.Text("Choose a scenario option:", font = sidebar_title_text)],
        [sg.Listbox(title_list, default_values = [0], size = (80, None), expand_y = True, select_mode = sg.LISTBOX_SELECT_MODE_SINGLE, font = description_text, k = "-OPTIONS-")],
        [sg.Button("Open", k = "-VIEWOPTION-", font = description_text, border_width = 0), sg.Button("Cancel", k = "-CANCEL-", font = description_text, border_width = 0)]
    ]
    return options_layout

# main window layout bits
def aid_content_entry(index:int, content_type:str, title:str, author:str, description:str, tags:list, publish_date:str, update_date:str, play_count:int, upvote_count:int, comment_count:int, bookmark_count:int, publicid:str):
    # cap title length, even though they actually can't get this long
    if len(title) > 76:
        title = f"{title[:70]}[...]"
    left_column = [
        [sg.Text(f"\n{title}", auto_size_text = False, size = (83, 2), font = title_text, justification = "left", pad = default_pad, k = f"-TITLE_{index}-")],
        [sg.Text(author, auto_size_text = False, expand_x = True, font = author_text, justification = "left", pad = default_pad, k = f"-AUTHOR_{index}-")],
        [sg.Multiline(description, auto_size_text = False, expand_x = True, size = (None, 4), font = description_text, border_width = 0, justification = "left", disabled = True, k = f"-DESCRIPTION_{index}-")],
        [sg.Text(f"Tags: {format_tags(tags, True)}", auto_size_text = False, expand_x = True, font = normal_text, k = f"-TAGS_{index}-")]
        ]
    right_column = [
        [sg.Text(f"Published: {publish_date[:10]}\nUpdated: {update_date[:10]}\nPlays: {play_count}\nUpvotes: {upvote_count}\nComments: {comment_count}\nBookmarks: {bookmark_count}\n", size = (22, 6), auto_size_text = False, font = normal_text, pad = default_pad, justification = "right", k = f"-META_{index}-")],
        [sg.Button("Open", expand_x = True, font = normal_text, pad = default_pad, metadata = publicid, border_width = 0, k = f"-OPEN_{index}-")]
        ]
    main_column = [
        [sg.Column(left_column, justification = "right", expand_x = True, element_justification = "left", vertical_alignment = "top", pad = default_pad, k = f"-RESULT_LEFT_{index}-"), sg.Column(right_column, justification = "right", expand_x = False, element_justification = "right", vertical_alignment = "bottom", pad = default_pad, k = f"-RESULT_RIGHT_{index}-")]
        ]
    preview_layout = [sg.Column(main_column, justification = "right", element_justification = "right", expand_x = True, pad = default_pad, k = f"-RESULT_{index}-")]
    return preview_layout

def aid_search_window():
    # send an initial search to show newest page
    results = fetch_aid_search("scenario", 0, "", "publishedAt", "0", True, False, False, False)
    # build a list of elements to slap into the results column
    results_frame = generate_results_frame(results, "scenario")
    filter_column = [
        [sg.Text("Filters", font = sidebar_title_text)],
        [sg.Checkbox("SFW Only", font = description_text, k = "-SAFESEARCH-")],
        [sg.Checkbox("Creator Only", font = description_text, k = "-CREATORSONLY-")],
        [sg.Checkbox("Following Only", font = description_text, k = "-FOLLOWINGONLY-")],
        [sg.Checkbox("Third Person Only", font = description_text, k = "-MULTIPLAYERONLY-")],
        [sg.Text("Advanced", font = sidebar_title_text)],
        [sg.Text("By User:", justification = "left", font = description_text)],
        [sg.Input("", justification = "left", size = 30, expand_x = True, font = normal_text, border_width = 0, k = "-USERNAME-")],
        [sg.Text("With Tags:\n(Seperate with commas)", justification = "left", font = description_text)],
        [sg.Input("", justification = "left", size = 30, expand_x = True, font = normal_text, border_width = 0, k = "-WITHTAGS-")],
        [sg.Text("Exclude Tags:\n(Seperate with commas)", justification = "left", font = description_text)],
        [sg.Input("", justification = "left", size = 30, expand_x = True, font = normal_text, border_width = 0, k = "-EXCLUDETAGS-")],
        [sg.Text("Direct View", font = sidebar_title_text)],
        [sg.Text("Paste link here:", justification = "left", font = description_text)],
        [sg.Input("", justification = "left", size = 30, expand_x = True, font = normal_text, border_width = 0, k = "-DIRECTLINK-")],
        [sg.Button("Open from link", expand_x = True, border_width = 0, font = description_text, k = "-VIEWLINK-")],
        [sg.Text("Navigation", font = sidebar_title_text)],
        [sg.Button("Prev Page", border_width = 0, font = description_text, expand_x = True, disabled = True, k = "-PREVPAGE-"), sg.Text("1", font = author_text, k = "-PAGENUMBER-"), sg.Button("Next Page", border_width = 0, font = description_text, expand_x = True, k = "-NEXTPAGE-")]
    ]
    search_column = [
        [sg.Input(expand_x = True, expand_y = True, font = description_text, pad = default_pad, border_width = 0, k = "-SEARCHBAR-"), sg.Button("Search", font = description_text, pad = default_pad, border_width = 0, k = "-SENDSEARCH-")],
        [sg.Text("Sort: ", font = description_text), sg.Combo(["New", "Popular", "Trending", "Recently Updated", "Best Match"], "New", font = description_text, readonly = True, k = "-SORTBY-"), sg.Text("Time Frame: ", font = description_text), sg.Combo(["Today", "Last 7 Days", "Last 30 Days", "All Time"], "All Time", font = description_text, readonly = True, k = "-TIMEFRAME-"), sg.Text("Content Type: ", font = description_text), sg.Combo(["Scenarios", "Adventures"], "Scenarios", readonly = True, font = description_text, k = "-CONTENTTYPE-")],
        [sg.Column(results_frame, expand_x = True, expand_y = True, scrollable = True, pad = default_pad, element_justification = "right", justification = "right", vertical_scroll_only = True, k = "-SEARCHRESULTS-")]
    ]
    full_layout = [
        [sg.Column(filter_column, justification = "left", element_justification = "left", vertical_alignment = "top"), sg.Column(search_column, justification = "left", element_justification = "left", expand_x = True, expand_y = True)]
    ]
    return full_layout

# windows
def scenario_options_window(options:list):
    publicid = None
    # build layout and window with the list of scenario options
    win_layout = scenario_options_view_window(options)
    window = sg.Window("Scenario Options - Explore", win_layout, resizable = False, auto_size_buttons = True, modal = True, finalize = True)
    # only needs one read - they're either opening a listed option, or not.
    event, values = window.read()
    if event == "-VIEWOPTION-":
        # get list of selected values (should only have one selection in it)
        selected = values['-OPTIONS-'][0]
        # get index of selected thing's publicid, set it for returning
        selected_index = int(selected.split()[0])-1
        publicid = options[selected_index]['publicId']
    # close the window
    window.close()
    # return publicid, if any
    return publicid

def adventure_window(publicid:str):
    # get adventure info and content from the API
    info = fetch_aid_adventure_info(publicid)
    adventure = fetch_aid_adventure_content(publicid)
    adv_content = format_adventure_content(adventure['actionWindow'])
    comments = fetch_comments_from_content(publicid, "adventure")
    # format comments for the comment feed multiline
    formatted_comments = format_content_comments(comments)
    # build layout and window with info we got
    win_layout = adventure_view_window(info['title'], info['user']['profile']['title'], info['createdAt'][:10], info['publishedAt'][:10], info['updatedAt'][:10], info['actionCount'], info['totalUpvotes'], info['totalComments'], info['totalSaves'], info['description'], info['tags'], publicid, info['scenario'], adv_content, formatted_comments)
    window = sg.Window("View Adventure - Explore", win_layout, size = (1280, 720), resizable = True, auto_size_buttons = True, modal = True, finalize = True)
    # Repack element(s) (thank you codesti friend)
    frame1, frame2 = window['-CONTENT_COL-'].Widget, window['-DESC_COL-'].Widget
    repack(frame2, {'fill':'x', 'expand':0, 'before':frame1})
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == "-EXPORTTXT-":
            # disable to avoid spam-clicking
            window['-EXPORTTXT-'].update(disabled = False)
            # export
            file_name = export_adventure_to_txt(info['title'], info['user']['profile']['title'], window['-TAGS_SOURCE-'].get(), info['description'], window['-MISC_DETAILS-'].get(), formatted_comments, adv_content, publicid)
            sg.popup(f"Adventure saved as {file_name}", title = "Export complete", font = description_text)
    window.close()

def scenario_window(publicid:str):
    # flags to determine whether to open another scenario window when this one is closed, and if so for what publicid
    open_option = False
    option_publicid = None
    # get adventure info and content from the API
    info = fetch_aid_scenario(publicid)
    # account for unpublished content being viewed (subscenarios are usually not published)
    if info['publishedAt'] is None:
        info['publishedAt'] = "(option)"
    else:
        info['publishedAt'] = info['publishedAt'][:10]
    comments = fetch_comments_from_content(publicid, "scenario")
    # format comments for the comment feed multiline
    formatted_comments = format_content_comments(comments)
    # build layout and window with info we got
    win_layout = scenario_view_window(info['title'], info['user']['profile']['title'], info['createdAt'][:10], info['publishedAt'], info['updatedAt'][:10], info['adventuresPlayed'], info['totalUpvotes'], info['totalComments'], info['totalSaves'], info['description'], info['tags'], publicid, info['prompt'], info['memory'], info['authorsNote'], formatted_comments)
    window = sg.Window("View Scenario - Explore", win_layout, size = (1280, 720), resizable = True, auto_size_buttons = True, modal = True, finalize = True)
    # Repack element(s) (thank you codesti friend)
    frame1, frame2 = window['-CONTENT_COL-'].Widget, window['-DESC_COL-'].Widget
    repack(frame2, {'fill':'x', 'expand':0, 'before':frame1})
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        # export to .txt
        elif event == "-EXPORTTXT-":
            # disable to avoid spam-clicking
            window['-EXPORTTXT-'].update(disabled = False)
            # export
            file_name = export_scenario_to_txt(info['title'], info['user']['profile']['title'], window['-TAGS_SOURCE-'].get(), info['description'], window['-MISC_DETAILS-'].get(), formatted_comments, values['-PROMPT-'], values['-MEMORY-'], values['-AUTHORSNOTE-'], publicid)
            sg.popup(f"Scenario saved in {file_name}", title = "Export complete", font = description_text)
        # export to .scenario
        elif event == "-EXPORTSCENARIO-":
            # disable to avoid spam-clicking
            window['-EXPORTSCENARIO-'].update(disabled = False)
            file_name = export_scenario_to_nai(info, publicid)
            sg.popup(f"Scenario saved in {file_name}", title = "Export complete", font = description_text)
        # open scenario options window, close this one if user navigates to a scenario option
        elif event == "-SCENARIO_OPTIONS-":
            option_publicid = scenario_options_window(info['options'])
            open_option = option_publicid is not None
        # break if opening a scenario option
        if open_option:
            break
    window.close()
    return open_option, option_publicid

def main_window():
    page_offset = 0
    last_search_type = "Scenarios"
    win_layout = aid_search_window()
    window = sg.Window("Explore", win_layout, size = (1600, 800), resizable = True, auto_size_buttons = True, finalize = True)
    window.move_to_center()
    while True:
        reload_page = False
        event, values = window.read()
        if event == sg.WINDOW_CLOSED: break
        # search
        elif event == "-SENDSEARCH-":
            # reset page offset to 0
            page_offset = 0
            reload_page = True
        elif event == "-NEXTPAGE-":
            # increment page offset by 10
            page_offset += 10
            reload_page = True
        elif event == "-PREVPAGE-":
            # decrement page offset by 10
            page_offset -= 10
            reload_page = True
        # open content page
        elif event in ["-OPEN_0-","-OPEN_1-","-OPEN_2-","-OPEN_3-","-OPEN_4-","-OPEN_5-","-OPEN_6-","-OPEN_7-","-OPEN_8-","-OPEN_9-"]:
            # get publicid
            publicid = window[event].metadata
            # open adventureview window
            if last_search_type == "Adventures":
                adventure_window(publicid)
            # open scenarioview window
            else:
                open_new_window = True
                while open_new_window:
                    open_new_window, publicid = scenario_window(publicid)
        # open direct from link
        elif event == "-VIEWLINK-":
            link = values['-DIRECTLINK-']
            # scenario view
            if "https://play.aidungeon.io/main/scenarioView?publicId=" in link:
                publicid = link.replace("https://play.aidungeon.io/main/scenarioView?publicId=", "")
                # invalid uuid
                if len(publicid) != 36:
                        sg.popup("Please enter a valid View page link. It should look like either:\nhttps://play.aidungeon.io/main/scenarioView?publicId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\nhttps://play.aidungeon.io/main/adventureView?publicId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", title = "Error parsing link", font = description_text)
                else:
                    open_new_window = True
                    while open_new_window:
                        open_new_window, publicid = scenario_window(publicid)
            elif "https://play.aidungeon.io/main/adventureView?publicId=" in link:
                publicid = link.replace("https://play.aidungeon.io/main/adventureView?publicId=", "")
                if len(publicid) != 36:
                        sg.popup("Please enter a valid View page link. It should look like either:\nhttps://play.aidungeon.io/main/scenarioView?publicId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\nhttps://play.aidungeon.io/main/adventureView?publicId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", title = "Error parsing link", font = description_text)
                else:
                    adventure_window(publicid)
            else:
                sg.popup("Please enter a valid View page link. It should look like either:\nhttps://play.aidungeon.io/main/scenarioView?publicId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\nhttps://play.aidungeon.io/main/adventureView?publicId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", title = "Error parsing link", font = description_text)
        # reloading results with new search parameters, if needed
        if reload_page:
            window['-SEARCHRESULTS-'].Widget.canvas.yview_moveto(0.0)
            # set last search type
            last_search_type = values['-CONTENTTYPE-']
            # get search parameters ready for api use
            content_type, sort_order, time_range, creator_only = aid_search_params(values['-CONTENTTYPE-'], values['-SORTBY-'], values['-TIMEFRAME-'], values['-CREATORSONLY-'])
            # hide old results + "no results" message
            for i in range(10):
                window[f'-RESULT_{i}-'].update(visible = False)
            window['-NORESULTS-'].set_size((None, 1))
            window['-NORESULTS-'].update("Searching, please wait...")
            window.refresh()
            # build search term string
            search_term = values['-SEARCHBAR-']
            # prepend username search, if any
            if len(values['-USERNAME-']) > 0:
                search_term = f'@"{values["-USERNAME-"]}" {search_term}'
            # prepend tag search, if any
            if len(values['-WITHTAGS-']) > 0:
                # split by comma
                tags_split = values['-WITHTAGS-'].split(",")
                tags_string = ""
                for i in range(len(tags_split)):
                    # strip whitespace on either side
                    tags_split[i].strip()
                    # add formatted tag to tags string
                    tags_string += f'#"{tags_split[i]}" '
                # and prepend tags, without a space because one is already at the end of the tag string
                search_term = f'{tags_string}{search_term}'
            # prepend tag exclusions, if any
            if len(values['-EXCLUDETAGS-']) > 0:
                # split by comma
                ex_tags_split = values['-EXCLUDETAGS-'].split(",")
                ex_tags_string = ""
                for i in range(len(ex_tags_split)):
                    # strip whitespace on either side
                    ex_tags_split[i].strip()
                    # add formatted tag to tags string
                    ex_tags_string += f'-#"{ex_tags_split[i]}" '
                # and prepend tags, without a space because one is already at the end of the tag string
                search_term = f'{ex_tags_string}{search_term}'
            # send request
            results = fetch_aid_search(content_type, page_offset, search_term, sort_order, time_range, creator_only, values['-SAFESEARCH-'], values['-FOLLOWINGONLY-'], values['-MULTIPLAYERONLY-'])
            if len(results) > 0:
                window['-NORESULTS-'].set_size((None, 0))
                # and format/show new results, as many as needed
                for i in range(0, len(results)):
                    # make both visible
                    window[f"-RESULT_{i}-"].update(visible = True)
                    # update left column
                    window[f'-TITLE_{i}-'].update(f"\n{results[i]['title']}")
                    window[f'-AUTHOR_{i}-'].update(results[i]['user']['profile']['title'])
                    window[f'-DESCRIPTION_{i}-'].update(results[i]['description'])
                    window[f'-TAGS_{i}-'].update(f"Tags: {format_tags(results[i]['tags'], True)}")
                    # update right column
                    if content_type == "scenario":
                        window[f'-META_{i}-'].update(f"Published: {results[i]['publishedAt'][:10]}\nUpdated: {results[i]['updatedAt'][:10]}\nPlays: {results[i]['adventuresPlayed']}\nUpvotes: {results[i]['totalUpvotes']}\nComments: {results[i]['totalComments']}\nBookmarks: {results[i]['totalSaves']}\n")
                    else:
                        window[f'-META_{i}-'].update(f"Published: {results[i]['publishedAt'][:10]}\nUpdated: {results[i]['updatedAt'][:10]}\nActions: {results[i]['actionCount']}\nUpvotes: {results[i]['totalUpvotes']}\nComments: {results[i]['totalComments']}\nBookmarks: {results[i]['totalSaves']}\n")
                    window[f'-OPEN_{i}-'].metadata = results[i]['publicId']
            else:
                # if none, show no results text
                window['-NORESULTS-'].set_size((None, 1))
                window['-NORESULTS-'].update("No results found. Try searching for something else.")
            # enable or disable the previous page button depending on current offset
            window['-PREVPAGE-'].update(disabled = page_offset <= 0)
            # set page text 
            window['-PAGENUMBER-'].update(f"{int((page_offset / 10) + 1)}")
    window.close()

def login_window():
    global user_email, user_pass, last_authed
    # this only ever comes up once, so i don't need to make this reusable
    layout = [
        [sg.Text("Log in with your AI Dungeon account", expand_x = True, justification = "center", font = sidebar_title_text)],
        [sg.Text("Email: ", font = description_text), sg.Input("", k = "-EMAIL-", size = 32, font = description_text)],
        [sg.Text("Password:", font = description_text), sg.Input("", k = "-PASSWORD-", size = 32, font = description_text, password_char = "*")],
        [sg.Button("Login", font = description_text, k = "-LOGIN-")]
    ]
    window = sg.Window("Log in - Explore", layout, element_justification = "right", text_justification = "right", finalize = True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED: break
        elif event == "-LOGIN-":
            try:
                # set email and password to values given, then attempt login
                user_email = values['-EMAIL-']
                user_pass = values['-PASSWORD-']
                success = fetch_firebase_token()
                # fail
                if not success:
                    user_email = None
                    user_pass = None
                    sg.popup("Login failed - Please check your email and password.", title = "Failed to login", font = description_text)
                # on success, just break and close the window. stuff is now set that needs to be
                else:
                    last_authed = time.time()
                    break
            except:
                user_email = None
                user_pass = None
                sg.popup("Login failed - An error occurred in this attempt.", title = "Failed to login", font = description_text)
    window.close()
    # return true if valid account details were entered, false otherwise
    return user_email is not None

def main():
    # auth properly, then open main window
    if login_window():
        main_window()

# showtime
if __name__ == "__main__":
    # create scenario and adventure folder if it doesn't exist
    if not os.path.isdir("scenarios"):
        os.mkdir("scenarios")
    if not os.path.isdir("adventures"):
        os.mkdir("adventures")
    main()