"""
This module contains all the tools for gathering and parsing new entries from
YouTube.
"""

import argparse
import simplejson
import subprocess
import codecs
import os
import logging
import re
import slugify
import shazoom
import webvtt
import json


MONTH_TO_NUM = {
    "janvier": "01",
    "fevrier": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "aout": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "decembre": "12",
    "dec": "12",
    "oct": "10",
    "sept": "09",
    "juil": "07",
    "janv": "01",
    "nov": "11",
    "fevr": "02",
}


DATE_PATTERN_A = re.compile(r"(\d\d) +([A-Za-zéû\.]+) +(\d\d\d\d)")
DATE_PATTERN_B = re.compile(r" (\d\d)\-(\d\d)\-(\d\d\d\d)")
DATE_PATTERN_C = re.compile(r"(\d\d) ([A-Za-zéû\.]+) (\d\d)")
DATE_PATTERN_D = re.compile(r"(\d\d)/(\d\d)/(\d\d)")
TITLE_PATTERN_A = re.compile(
    "^(les ma[îi]tres du myst[èe]re|l'heure du myst[èe]re|myst[èe]re myst[èe]re|les myst[èe]res de l'[ée]t[ée]|faits divers) *\- ?(.+?) *\-? *$",
    re.IGNORECASE
)
TITLE_PATTERN_B = re.compile(
    "^(.+) *\- *(les ma[îi]tres du myst[èe]re|l'heure du myst[èe]re|myst[èe]re myst[èe]re|les myst[èe]res de l'[ée]t[ée]|faits divers) *\-? *$",
    re.IGNORECASE
)


def create_shazoom_database(checkpoint):
    if checkpoint is not None:
        return shazoom.ShazoomDatabase.from_checkpoint(checkpoint)


def download_video(folder, video_id):
    logging.info("Downloading %s", video_id)
    process = subprocess.Popen(
        [
            "youtube-dl",
            "--write-auto-sub",
            "--sub-lang",
            "fr",
            "--write-info-json",
            "--output",
            os.path.join(folder, "%(id)s.%(ext)s"),
            "-x",
            "--audio-format",
            "mp3",
            "https://www.youtube.com/watch?v=" + video_id
        ],
    )
    process.wait()


def parse_upload_date(raw_date):
    return raw_date[:4] + "-" + raw_date[4:6] + "-" + raw_date[6:]


def extract_diffusion_date(info):
    match = DATE_PATTERN_A.search(info["description"])
    if match is not None:
        return "-".join([
            match.group(3),
            MONTH_TO_NUM[slugify.slugify(match.group(2).strip())],
            match.group(1)
        ])
    match = DATE_PATTERN_B.search(info["description"])
    if match is not None:
        return match.group(3) + "-" + match.group(2) + "-" + match.group(1)
    match = DATE_PATTERN_C.search(info["description"])
    if match is not None:
        return "-".join([
            "19" + match.group(3),
            MONTH_TO_NUM[slugify.slugify(match.group(2).strip())],
            match.group(1)
        ])
    match = DATE_PATTERN_D.search(info["description"])
    if match is not None:
        return "-".join([
            "19" + match.group(3),
            match.group(2),
            match.group(1)
        ])
    logging.warning(
        "Could not extract a diffusion date for video ID '%s'",
        info["display_id"]
    )
    return None


def extract_title(info):
    match = TITLE_PATTERN_A.match(info["title"])
    if match is not None:
        return (
            re.sub(" *\- *", "", match.group(2).strip()),
            re.sub(" *\- *", "", match.group(1).strip())
        )
    match = TITLE_PATTERN_B.match(info["title"])
    if match is not None:
        return (
            re.sub(" *\- *", "", match.group(1).strip()),
            re.sub(" *\- *", "", match.group(2).strip())
        )
    logging.warning(
        "Could not extract title or collection for video ID '%s'",
        info["display_id"]
    )
    return None, None


def extract_opening(database, folder, video_id):
    prediction = database.predict_on_the_fly(
        os.path.join(folder, video_id + ".mp3"),
        "tmp"
    )
    if prediction["confidence"] < 0.10:
        logging.warning(
            "Confidence on '%s' opening prediction is LOW (%f)",
            video_id,
            prediction["confidence"]
        )
    return prediction["label"]


def create_entry(database, facets_model, folder, video_id):
    logging.info("Creating entry for video ID %s", video_id)
    if not os.path.isfile(os.path.join(folder, video_id + ".info.json")):
        raise FileNotFoundError(
            "Info JSON for video ID '%s' could not be found." % video_id
        )
    with codecs.open(os.path.join(folder, video_id + ".info.json")) as file:
        info = simplejson.load(file)
    title, collection = extract_title(info)
    entry = {
        "id": video_id,
        "uri": "https://www.youtube.com/watch?v=" + video_id,
        "channel_id": info["channel_id"],
        "channel_name": info["channel"],
        "video_title": info["title"],
        "title": title,
        "collection": collection,
        "upload_date": parse_upload_date(info["upload_date"]),
        "duration": info["duration"],
        "stats": {
            "view_count": info["view_count"],
            "like_count": info["like_count"],
            "dislike_count": info["dislike_count"],
        },
        "description": info["description"],
        "opening": extract_opening(database, folder, video_id),
        "diffusion_date": extract_diffusion_date(info),
        "facets": extract_facets(facets_model, folder, video_id)
    }
    return entry


def merge_captions(captions):
    """
    Merge the text content of a list of webvtt.Caption into a single string,
    where repetitions are pruned out.
    """
    text = ""
    for caption in captions:
        caption_text = caption.text.strip()
        longest_prefix_length = 0
        for i in range(1, len(caption_text) + 1):
            if text.endswith(caption_text[:i]):
                longest_prefix_length = i
        if longest_prefix_length == 0:
            text += " "
        text += caption_text[longest_prefix_length:]
    return re.sub(" +", " ", text)


def load_facets_model(path):
    with codecs.open(path, "r", "utf8") as file:
        model = json.load(file)["facets"]
    for facet in model:
        facet["pattern"] = re.compile(
            " (" + "|".join(facet["triggers"]) + ")",
            re.IGNORECASE
        )
    return model


def extract_facets(model, folder, video_id):
    path = os.path.join(folder, video_id + ".fr.vtt")
    if not os.path.isfile(path):
        logging.warning("Could not extract facets of '%s'", video_id)
        return []
    merger = merge_captions(webvtt.read(path))
    scores = list()
    for facet in model:
        scores.append({
            "label": facet["label"],
            "score": len(facet["pattern"].findall(merger))
        })
    return scores


def create_entries(shazoom_database, facets_model, folder, *video_ids):
    entries = list()
    for video_id in video_ids:
        entry = create_entry(shazoom_database, facets_model, folder, video_id)
        if entry is not None:
            entries.append(entry)
    return entries


def action_download(folder, *video_ids):
    for video_id in video_ids:
        download_video(folder, video_id)


def action_parse(output, shazoom_checkpoint, facets_model_path, folder, *video_ids):
    shazoom_database = create_shazoom_database(shazoom_checkpoint)
    facets_model = load_facets_model(facets_model_path)
    entries = create_entries(
        shazoom_database, facets_model, folder, *video_ids)
    with codecs.open(output, "w", "utf8") as file:
        simplejson.dump({"entries": entries}, file, indent=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--folder",
        type=str,
        default="data/youtube"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="youtube.append.json"
    )
    parser.add_argument(
        "-s",
        "--shazoom_checkpoint",
        type=str,
        default="data/shazoom-mystere.bin"
    )
    parser.add_argument(
        "-fc",
        "--facets",
        type=str,
        default="data/facets.json"
    )
    parser.add_argument(
        "action",
        choices=["download", "parse"]
    )
    parser.add_argument(
        "video_id",
        type=str,
        help="Either a single video ID or a path to a file containing one video ID per line."
    )
    args = parser.parse_args()
    video_ids = list()
    if os.path.isfile(args.video_id):
        with open(args.video_id.strip()) as file:
            for line in file.readlines():
                if len(line.strip()) == 11:
                    video_ids.append(line.strip())
    elif len(args.video_id.strip()) == 11:
        video_ids.append(args.video_id.strip())
    if args.action == "download":
        action_download(args.folder, *video_ids)
    elif args.action == "parse":
        action_parse(args.output, args.shazoom_checkpoint,
                     args.facets, args.folder, *video_ids)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
