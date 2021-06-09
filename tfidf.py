import codecs
import simplejson
import webvtt
import os
import re
import math
import argparse
import tqdm
import logging


PATTERN_TIMECODE = re.compile("(\d+):(\d+):(\d+)\.(\d+)")
PATTERN_TOKENIZE = re.compile("[' \n]")


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





def parse_timecode(raw_timecode):
    match = PATTERN_TIMECODE.match(raw_timecode)
    return 3600 * int(match.group(1)) + 60 * int(match.group(2)) + int(match.group(3)) + .001 * int(match.group(4))


def extract_interludes(captions, merge_threshold=20):
    interludes = list()
    active = False
    for i, caption in enumerate(captions):
        if "[Musique]" in caption.text:
            if not active:
                active = True
                interludes.append({
                    "start": i,
                    "time_start": parse_timecode(caption.start),
                    "end": None,
                    "time_end": None,
                })
        else:
            if active:
                active = False
                interludes[-1]["end"] = i - 1
                interludes[-1]["time_end"] = parse_timecode(captions[i - 1].end)
    if len(interludes) == 0:
        return []
    interludes[-1]["end"] = len(captions) - 1
    interludes[-1]["time_end"] = parse_timecode(captions[len(captions) - 1].end)
    while True:
        changed = False
        for i in range(0, len(interludes) - 1):
            if (interludes[i+1]["time_start"] - interludes[i]["time_end"]) < merge_threshold:
                interludes[i]["end"] = interludes[i+1]["end"]
                interludes[i]["time_end"] = interludes[i+1]["time_end"]
                interludes.pop(i + 1)
                changed = True
                break
        if not changed:
            break
    return interludes


def extract_chapters(captions, interludes):
    chapters = list()
    if len(interludes) == 0:
        return []
    offset = 0
    if interludes[0]["start"] == 0:
        chapters.append({
            "start": interludes[0]["end"] + 1,
            "end": None
        })
        offset = 1
    else:
        chapters.append({
            "start": 0,
            "end": None
        })
    for interlude in interludes[offset:]:
        chapters[-1]["end"] = interlude["start"] - 1
        if interlude["end"] < len(captions) - 1:
            chapters.append({
                "start": interlude["end"] + 1,
                "end": None
            })
    if interludes[-1]["end"] == len(captions) - 1:
        chapters[-1]["end"] = interludes[-1]["start"] - 1
    else:
        chapters[-1]["end"] = len(captions) - 1
    for chapter in chapters:
        chapter["time_start"] = parse_timecode(captions[chapter["start"]].start)
        chapter["time_end"] = parse_timecode(captions[chapter["end"]].end)
        chapter["duration"] = chapter["time_end"] - chapter["time_start"]
        chapter["text"] = merge_captions([
            captions[i]
            for i in range(chapter["start"], chapter["end"] + 1)
        ])
    return chapters


def tokenize(documents, stopwords):
    # logging.info("Tokenizing %d documents", len(documents))
    return {
        doc_id: [
            x
            for x in PATTERN_TOKENIZE.split(document)
            if x != "" and x not in stopwords
        ]
        for doc_id, document in documents.items()
    }


def compute_tf(tokens):
    # logging.info("Computing TF for %d documents", len(tokens))
    tf = dict()
    for doc_id in tokens:
        tf[doc_id] = dict()
        total = 0
        for token in tokens[doc_id]:
            tf[doc_id].setdefault(token, 0)
            tf[doc_id][token] += 1
            total += 1
        for token in tf[doc_id]:
            tf[doc_id][token] /= total
    return tf


def compute_idf(tokens):
    # logging.info("Computing IDF for %d documents", len(tokens))
    idf = dict()
    for doc_id in tokens:
        for token in tokens[doc_id]:
            idf.setdefault(token, 0)
            idf[token] += 1
    total = len(tokens)
    for token in idf:
        idf[token] = math.log(total / idf[token])
    return idf


def compute_tfidf(tf, idf):
    # logging.info("Computing TF-IDF for %d documents", len(tf))
    tfidf = dict()
    for doc_id in tf:
        tfidf[doc_id] = dict()
        for token in tf[doc_id]:
            tfidf[doc_id][token] = tf[doc_id][token] * idf[token]
    return tfidf


def action_relevant_words(youtube_path, stopwords_path, folder, top_n):
    with codecs.open(youtube_path, "r", "utf8") as file:
        rows = simplejson.load(file)["entries"]
    with codecs.open(stopwords_path, "r", "utf8") as file:
        stopwords = set(map(lambda s: s.strip(), file.readlines()))
    captions = dict()
    for row in tqdm.tqdm(rows):
        path = os.path.join(folder, row["id"] + ".fr.vtt")
        if not os.path.isfile(path):
            continue
        captions[row["id"]] = merge_captions(webvtt.read(path))
    tokens = tokenize(captions, stopwords)
    tf = compute_tf(tokens)
    idf = compute_idf(tokens)
    tfidf = compute_tfidf(tf, idf)
    logging.info("Exporting results to %s", youtube_path)
    for row in rows:
        if row["id"] not in tfidf:
            row["relevant_words"] = list()
            continue
        row["relevant_words"] = [
            {
                "label": word,
                "score": score
            }
            for word, score in sorted(
                tfidf[row["id"]].items(),
                key=lambda x: -x[1]
            )[:top_n]
        ]
    with codecs.open(youtube_path, "w", "utf8") as file:
        simplejson.dump({"entries": rows}, file, indent=4, sort_keys=True)


def action_chapters(youtube_path, stopwords_path, folder):
    with codecs.open(youtube_path, "r", "utf8") as file:
        rows = simplejson.load(file)["entries"]
    with codecs.open(stopwords_path, "r", "utf8") as file:
        stopwords = set(map(lambda s: s.strip(), file.readlines()))
    for row in tqdm.tqdm(rows):
        path = os.path.join(folder, row["id"] + ".fr.vtt")
        # if row["id"] != "_-CWzI6advI":
        #     continue
        # print(row["id"])
        row["chapters"] = list()
        if not os.path.isfile(path):
            continue
        captions = webvtt.read(path)
        interludes = extract_interludes(captions)
        chapters = extract_chapters(captions, interludes)
        if len(chapters) > 0:
            chapters_dict = {
                i: chapter["text"]
                for i, chapter in enumerate(chapters)
            }
            tokens = tokenize(chapters_dict, stopwords)
            tf = compute_tf(tokens)
            idf = compute_idf(tokens)
            tfidf = compute_tfidf(tf, idf)
            row["chapters"] = [
                {
                    "start": chapter["time_start"],
                    "end": chapter["time_end"],
                    "words": [
                        {
                            "label": word,
                            "score": score
                        }
                        for word, score in sorted(
                            tfidf[i].items(),
                            key=lambda x: -x[1]
                        )[:5]
                    ]
                }
                for i, chapter in enumerate(chapters)
            ]
    with codecs.open(youtube_path, "w", "utf8") as file:
        simplejson.dump({"entries": rows}, file, indent=4, sort_keys=True)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--youtube", type=str, default="data/youtube.json")
    parser.add_argument("--stopwords", type=str, default="data/stopwords.txt")
    parser.add_argument("--folder", type=str, default="data/youtube")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("action", choices=["relevant_words", "chapters", "both"])
    args = parser.parse_args()
    if args.action in ["relevant_words", "both"]:
        action_relevant_words(args.youtube, args.stopwords, args.folder, args.top_n)
    if args.action in ["chapters", "both"]:
        action_chapters(args.youtube, args.stopwords, args.folder)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
