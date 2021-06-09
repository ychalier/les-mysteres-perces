"""
This module contains all the tools for gathering and parsing new entries from
Inathèque.
"""

import argparse
import simplejson
import codecs
import os
import logging
import re
import requests
import bs4
import tqdm


ROLES = {
    'ADA': "Adaptateur",
    'MUS': "Compositeur de la musique pré-existante",
    'JOU': "Journaliste",
    'TRA': "Traducteur",
    'BRT': "Bruiteur",
    'DIR': "Auteur de la musique originale",
    'PRE': "Présentateur",
    'SON': "Ingénieur du son",
    'SCE': "Scénariste",
    'PAR': "Participant",
    'OPS': "Opérateur de prise de son"
}


INLINE_PATTERNS = [
    re.compile(r"^au début (?: *\(.*?(?:fichier|générique).*?\) *)?:.+$", re.IGNORECASE),
    re.compile(r"^au début, (?:introduction|générique) musical.+$", re.IGNORECASE),
    re.compile(r"^début à (?:\d+h ?)?\d+'\d+ :.+$", re.IGNORECASE),
    re.compile(r"^(?:[aà] )?(?:\d+h ?)?\d+'(?:\d+)?(?: ?[\"']+)? *(?: *\(.*?fichier.*?\) *)? ?(?::|;|générique).+$", re.IGNORECASE),
    re.compile(r"^[àa] \d+h\d+ :.+?$", re.IGNORECASE),
    re.compile(r"^[àa] \d+'\d+ \([\d':;\+= ]+\) : générique de fin.+$", re.IGNORECASE),
    re.compile(r"^[àa] \d+ ?\" ?:.+$", re.IGNORECASE),
    re.compile(r"^fin à (?:\d+h ?)?\d+'(?:\d+\"?)?\)? *(?: *\(.*?(?:fichier|générique).*?\) *)? *\.?$", re.IGNORECASE),
    re.compile(r"^fin à \d+h\d+\.?$", re.IGNORECASE),
]


def fetch_info(url):
    """
    Fetch the content of an 'INA notice' given its url. The returned dict
    has keys for each notice entry, hence in French.
    """
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features="html5lib")
    info = dict()
    for tr in soup.find("div", {"id": "result-tableau-1"}).find_all("tr"):
        key, value = tr.find_all("td")
        info[key.text.strip()] = value.text.strip()
    return info


def parse_date(raw_date):
    """
    Format a date written in a notice to a YYYY-MM-DD format.
    """
    if raw_date is None:
        return None
    match = re.match(r"(\d\d)/(\d\d)/(\d\d\d\d)", raw_date)
    return match.group(3) + "-" + match.group(2) + "-" + match.group(1)


def parse_duration(raw_duration):
    """
    Compute a duration in seconds from a duration string of the form HH:MM:SS.
    If milliseconds or frames are specified, they are ignored.
    """
    match = re.match(r"(\d\d):(\d\d):(\d\d)", raw_duration)
    return 3600 * int(match.group(1)) + 60 * int(match.group(2)) + int(match.group(1))


def parse_descriptors(raw_descriptors):
    """
    Parse the descriptor field of a notice.
    """
    if raw_descriptors is None:
        return []
    descriptors = list()
    for item in re.split(r" ; ", raw_descriptors):
        match = re.match(r"^(.+?)(?: \((.+)\))?$", item.strip())
        descriptors.append({
            "label": match.group(1).strip(),
            "specification": match.group(2).strip() if match.group(2) is not None else None
        })
    return descriptors


def parse_credits(raw_credits, reorderings):
    credits = {
        "author": None,
        "directors": [],
        "producers": [],
        "cast": [],
        "crew": [],
    }
    if raw_credits is None:
        return credits
    for person in raw_credits.split(";"):
        match = re.match(r"^([A-Z]+),(.+?)(?: \( *(.+) *\))?$", person.strip())
        name = match.group(2).strip()
        if name in reorderings:
            name_reordered = reorderings.get(name)
        elif len(name.split(" ")) == 2:
            split = name.split(" ")
            name_reordered = split[1] + " " + split[0]
        else:
            name_reordered = input("Please enter the correct name for \"%s\"> " % name)
        role = match.group(1).strip()
        if role == "AUT":
            credits["author"] == name_reordered
        elif role == "REA":
            credits["directors"].append({"name": name_reordered})
        elif role == "PRO":
            credits["producers"].append({"name": name_reordered})
        elif role == "INT":
            credits["cast"].append({
                "name": name_reordered,
                "character": match.group(3).strip() if match.group(3) is not None else None
            })
        else:
            credits["crew"].append({
                "name": name_reordered,
                "job": ROLES[role]
            })
    return credits


def parse_summary_item(item):
    timecode = None
    content = None
    match = re.match(r"^au début (?: *\(.*?(?:fichier|générique).*?\) *)?:(.+)$", item, re.IGNORECASE)
    if match is not None:
        return 0, match.group(1)
    match = re.match(r"^au début, ((?:introduction|générique) musical.+)$", item, re.IGNORECASE)
    if match is not None:
        return 0, match.group(1)
    match = re.match(r"^début à (?:(\d+)h ?)?(\d+)'(\d+) :(.+)$", item, re.IGNORECASE)
    if match is not None:
        timecode = 0
        if match.group(1) is not None:
            timecode += int(match.group(1)) * 3600
        timecode += int(match.group(2)) * 60 + int(match.group(3))
        return timecode, match.group(4)
    match = re.match(r"^(?:[aà] )?(?:(\d+)h ?)?(\d+)'(?:(\d+))?(?: ?[\"']+)? *(?: *\(.*?fichier.*?\) *)? ?((?::|;|générique).+)$", item, re.IGNORECASE)
    if match is not None:
        timecode = 0
        if match.group(1) is not None:
            timecode += int(match.group(1)) * 3600
        timecode += int(match.group(2)) * 60
        if match.group(3) is not None:
            timecode += int(match.group(3))
        content = match.group(4)
        if content[0] in ":;":
            content = content[1:]
        return timecode, content
    match = re.match(r"^[àa] (\d+)h(\d+) :(.+)?$", item, re.IGNORECASE)
    if match is not None:
        timecode = 0
        timecode += int(match.group(1)) * 3600
        timecode += int(match.group(2)) * 60
        return timecode, match.group(3)
    match = re.match(r"^[àa] (\d+)'(\d+) \([\d':;\+= ]+\) : (générique de fin.+)$", item, re.IGNORECASE)
    if match is not None:
        timecode = 0
        timecode += int(match.group(1)) * 60
        timecode += int(match.group(2))
        return timecode, match.group(3)
    match = re.match(r"^[àa] (\d+) ?\" ?:(.+)$", item, re.IGNORECASE)
    if match is not None:
        timecode = int(match.group(1))
        return timecode, match.group(2)
    match = re.match(r"^fin à (?:(\d+)h ?)?(\d+)'(?:(\d+)\"?)?\)? *(?: *\(.*?(?:fichier|générique).*?\) *)? *\.?$", item, re.IGNORECASE)
    if match is not None:
        timecode = 0
        if match.group(1) is not None:
            timecode += int(match.group(1)) * 3600
        timecode += int(match.group(2)) * 60
        if match.group(3) is not None:
            timecode += int(match.group(3))
        return timecode, "Fin"
    match = re.match(r"^fin à (\d+)h(\d+)\.?$", item, re.IGNORECASE)
    if match is not None:
        timecode = int(match.group(1)) * 3600 + int(match.group(2)) * 60
        return timecode, "Fin"
    return timecode, content


def clean_summary_item_content(content):
    text = re.sub(" +", " ", re.sub("¤", "-", content)).strip()
    return text[0].upper() + text[1:]


def parse_summary(raw_summary):
    summary = {
        "pitch": None,
        "beginning": None,
        "end": None,
        "items": []
    }
    if raw_summary is None:
        return summary
    matches = list()
    cleaned = re.sub(r"\-( *fichier.*? *)\-", r"_\1_", raw_summary.strip())
    cleaned = re.sub(r"\-( *fichier.*? *\))", r"_\1", cleaned)
    cleaned = re.sub(r" \-(\w[^\-]+?\w)\- ", r" ¤\1¤ ", cleaned)
    cleaned = re.sub(r" (\w+)\-(\w+[,\.!\?;]?) ", r" \1¤\2 ", cleaned)
    for match in re.finditer(r"\- ([^\-]+)", cleaned):
        matches.append(match.group(1))
    if len(matches) == 0:
        logging.warning("Could not extract a summary")
        return summary
    if len(matches) > 0:
        if re.search("fin [àa] ", matches[-1], re.IGNORECASE) is not None and matches[-1].strip().lower()[:3] != "fin":
            match = re.search(r"(.+)fin [aà] (.+?)$", matches[-1], re.IGNORECASE)
            matches = matches[:-1] + [
                match.group(1).strip(),
                "Fin à " + match.group(2).strip()
            ]
    i = len(matches) - 1
    while i >= 0:
        match = matches[i]
        it_is_a_match = False
        for pattern in INLINE_PATTERNS:
            if pattern.match(match.strip()):
                it_is_a_match = True
                break
        if not it_is_a_match:
            if i == 0:
                logging.error("Could not match this line: '%s'", match)
            else:
                matches[i-1] += " - " + match
                matches.pop(i)
        i -= 1
    parsed_matches = list()
    for match in matches:
        timecode, content = parse_summary_item(match)
        parsed_matches.append({
            "timecode": timecode,
            "text": clean_summary_item_content(content),
        })
    for i, item in enumerate(parsed_matches):
        parsed_matches[i]["duration"] = 0
        if i < len(parsed_matches) - 1:
            parsed_matches[i]["duration"] = parsed_matches[i + 1]["timecode"] - item["timecode"]
    summary["items"] = parsed_matches
    max_index = None
    for i in range(len(parsed_matches)):
        if max_index is None or parsed_matches[i]["duration"] > parsed_matches[max_index]["duration"]:
            max_index = i
    if max_index is None:
        raise ValueError
    summary["beginning"] = parsed_matches[max_index]["timecode"]
    summary["pitch"] = parsed_matches[max_index]["text"]
    if max_index < len(parsed_matches) - 1:
        summary["end"] = parsed_matches[max_index + 1]["timecode"]
    return summary


def create_entry(reorderings, url):
    info = fetch_info(url)
    entry = {
        "id": info["ID Notice"],
        "uri": url,
        "title": info["Titre propre"],
        "collection": info.get("Titre collection"),
        "diffusion_channel": info.get("Chaîne de diffusion"),
        "diffusion_date": parse_date(info.get("Date de diffusion")),
        "recording_date": parse_date(info.get("Date d'enregistrement")),
        "duration": parse_duration(info.get("Durée")),
        "production_company": info.get("Société de programmes"),
        "credits": parse_credits(info.get("Générique"), reorderings),
        "descriptors": parse_descriptors(info.get("Descripteurs")),
        "summary": parse_summary(info.get("Résumé documentaire"))
    }
    return entry


def load_reorderings(path):
    reorderings = dict()
    with codecs.open(path, "r", "utf8") as file:
        first = True
        for line in file.readlines():
            if first:
                first = False
                continue
            original, reordered = map(lambda s: s.strip(), line.strip().split("\t"))
            reorderings[original] = reordered
    return reorderings


def create_entries(reorderings, *urls):
    entries = list()
    for url in tqdm.tqdm(urls):
        entry = create_entry(reorderings, url)
        if entry is not None:
            entries.append(entry)
    return entries


def action_parse(reordering_path, output, *urls):
    reorderings = load_reorderings(reordering_path)
    entries = create_entries(reorderings, *urls)
    with codecs.open(output, "w", "utf8") as file:
        simplejson.dump({"entries": entries}, file, indent=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="inatheque.append.json"
    )
    parser.add_argument(
        "-r",
        "--reorderings",
        type=str,
        default="data/ina-names.tsv"
    )
    parser.add_argument(
        "url",
        type=str,
        help="Either a single URL or a path to a file containing one URL per line."
    )
    args = parser.parse_args()
    urls = []
    if os.path.isfile(args.url):
        with open(args.url, "r") as file:
            for line in file.readlines():
                urls.append(line.strip())
    else:
        urls.append(args.url)
    action_parse(args.reorderings, args.output, *urls)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
