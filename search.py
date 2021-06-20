import os
import json
import codecs
import logging
import time
import argparse
import tqdm
import requests
import pandas
import difflib


TOKEN_API = "https://www.googleapis.com/oauth2/v4/token"
SEARCH_API = "https://www.googleapis.com/youtube/v3/search"


def refresh(token):
    response = requests.post(
        TOKEN_API,
        params={
            "client_id": token["client_id"],
            "client_secret": token["client_secret"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token"
        }
    )
    data = response.json()
    token["access_token"] = data["access_token"]
    if "refresh_token" in data:
        token["refresh_token"] = data["refresh_token"]
    token["delivery_time"] = time.time()
    return token


def search(token, query):
    headers = {
        "client-id": token["client_id"],
        "Authorization": "Bearer %s" % token["access_token"]
    }
    params = {
        "part": "snippet",  # required
        "maxResults": 50,
        "q": query,
        "type": "video",
        "videoDuration": "long",  # more than 20 minutes
    }
    response = requests.get(SEARCH_API, params=params, headers=headers)
    if response.status_code != 200:
        logging.error(
            "Error with the API connection, status %d",
            response.status_code
        )
        return None
    return json.loads(response.text)


def action_search(token_path, merger_path, output_path, delay):
    with open(token_path, "r") as file:
        token = json.load(file)
    token = refresh(token)
    with codecs.open(merger_path, "r", "utf8") as file:
        rows = json.load(file)["entries"]
    missing = list()
    for row in rows:
        if row["links"]["youtube_id"] is None:
            missing.append(row)
    logging.info(
        "Found %d episodes where a YouTube video is missing",
        len(missing)
    )
    results = dict()
    if os.path.isfile(output_path):
        with codecs.open(output_path, "r", "utf8") as file:
            results = json.load(file)
    for row in tqdm.tqdm(missing):
        if row["links"]["youtube_id"] is not None:
            continue
        if results.get(str(row["doc_id"])) is not None:
            continue
        query = f'{row["title"]} {row["collection"]}'
        search_results = search(token, query)
        if search_results is None:
            break
        results[str(row["doc_id"])] = search_results
        time.sleep(delay)
    with codecs.open(output_path, "w", "utf8") as file:
        json.dump(results, file)


def action_align(merger_path, search_results_path, threshold, alignment_path):
    with codecs.open(merger_path, "r", "utf8") as file:
        merger = json.load(file)["entries"]
    with codecs.open(search_results_path, "r", "utf8") as file:
        search = json.load(file)
    missing = dict()
    used = set()
    for row in merger:
        if row["links"]["youtube_id"] is None:
            missing[row["doc_id"]] = row
        else:
            used.add(row["links"]["youtube_id"])
    alignments = list()
    for doc_id, results in search.items():
        if results is None:
            continue
        doc_id = int(doc_id)
        for result in results["items"]:
            if result["id"]["kind"] != "youtube#video":
                continue
            if result["id"]["videoId"] in used:
                continue
            match = difflib.SequenceMatcher(None, missing[doc_id]["title"], result["snippet"]["title"]).ratio()
            if match < threshold:
                continue
            alignments.append({
                "doc_id": doc_id,
                "link": "=LIEN.HYPERTEXTE(\"https://www.youtube.com/watch?v=" + result["id"]["videoId"] + "\";\"" + result["id"]["videoId"] + "\")",
                "doc_title": missing[doc_id]["title"],
                "video_title": result["snippet"]["title"],
                "match": match,
                "collection": missing[doc_id]["collection"],
                "channel": result["snippet"]["channelTitle"],
                "description": result["snippet"]["description"],
            })
    pandas.DataFrame(alignments).to_csv(alignment_path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, default="token.json")
    parser.add_argument("--merger", type=str, default="data/merger.json")
    parser.add_argument("--search-results", type=str, default="youtube-search.json")
    parser.add_argument("--delay", type=float, default=3)
    parser.add_argument("--threshold", type=float, default=.6)
    parser.add_argument("--alignment", type=str, default="youtube-alignment.csv")
    parser.add_argument("action", choices=["search", "align"])
    args = parser.parse_args()
    if args.action == "search":
        action_search(args.token, args.merger, args.search_results, args.delay)
    elif args.action == "align":
        action_align(args.merger, args.search_results, args.threshold, args.alignment)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()












