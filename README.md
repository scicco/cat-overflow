# Cat 0verf10w

[![awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=awesome+plugin&color=383938&style=for-the-badge&logo=cheshire_cat_ai)](https://)  


![image](cat-overflow-logo.png)

Let the Cat become your coding assistant by learning everything about your favourite libraries!

## Current Features

### Search for source code

* Search Github without github api key (faster ingestion) **this is recommended way**
* Search Github with github api key (slower ingestion)
* Fallback to raw github url if mime type is unsupported

### Search for documentation


* Scrape a site to ingest the web pages
* This should (hopefully) also support js sites that usually won't work by using Playwright library and headless browser (Chrome, Firefox, Webkit)
* Every paged is ingested then into rabbit hole

## Todo

* Search in google
* Search in stackoverflow answers with the same "category"

## Download from Repository

`@getcode ...` is the trigger for the tool

### General search

passing a library name will search that inside github

syntax:

`@getcode "library name or term"`

example:

`@getcode cheshire_cat`

will search on github and show some of the matching repositories found

![image](images/general_search.png)

### Exact search

passing owner and repository name separated by backslash will try to find that. If an exact match (only one) is found, then the download will start automatically

syntax:

`@getcode "owner"/"repository name"`

will start download the library if only one result is matched

examples:

`@getcode cheshire-cat-ai/docs`

will try to find a repository. If only one result is found, it start downloading repo automatically. After download every file inside the archive is ingested with rabbit-hole.

> **Important**
>
>if a mime type is unsupported by rabbit hole this plugin will try to use the 
>corresponding raw github raw file url to ingest the content anyway

![image](images/exact_search.png)

## Scrape a documentation site

syntax:

`@getcodedoc ...` is the trigger for the tool

example:

`@getcodedoc https://cheshire-cat-ai.github.io/docs/`

## General Settings

* Search on Web (TODO) - not available at the moment
* Search on StackOverflow (TODO) - not available at the moment

## Settings for @getcode

* Use Github API - this must be activated to use "Github API token" during searches
* Github API token - your github API token ([how to create a classic token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens))

![image](images/settings.png)

## Settings for @getcodedoc

* Scraping Depth - this will set the dept of the scraper (higher number is slower) - default is 3
* Scraping Max Pages - this will set a limit to the amount of pages - default is 100
* Use Chrome - Setup the headless browser to use (please set only one of these as True) - default True
* Use Firefox - Setup the headless browser to use (please set only one of these as True) - default False
* Use Webkit - Setup the headless browser to use (please set only one of these as True) - default False

> TODO: add image for @getcodedoc settings