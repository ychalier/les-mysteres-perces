import argparse
import codecs
import simplejson
import itertools
import difflib
import pandas
import slugify


def load_and_index(path, pkey):
    with codecs.open(path, "r", "utf8") as file:
        rows = simplejson.load(file)["entries"]
    return {
        row[pkey]: row
        for row in rows
    }


def load_value(value):
    if len(value.strip()) == 0:
        return None
    try:
        return int(value)
    except ValueError:
        return value.strip()


def load_alignment(path):
    header = None
    rows = list()
    with codecs.open(path, "r", "utf8") as file:
        first = True
        for line in file.readlines():
            if first:
                first = False
                header = list(map(lambda s: s.strip(), line.strip().split("\t")))
                continue
            rows.append({
                key: load_value(value)
                for key, value in zip(header, line.split("\t"))
            })
    return rows


def check_alignment(alignment):
    header = alignment[0].keys()
    for key in header:
        values = [row[key] for row in alignment if row[key] is not None]
        assert len(values) == len(set(values)), key
    print("Alignment IDs are unique: True")
    header_without_doc_id = [x for x in header if x != "doc_id"]
    overlaps = dict()
    for r in range(1, 5):
        for combination in itertools.combinations(header_without_doc_id, r):
            key = combination[0]
            values = [row for row in alignment if row[key] is not None]
            for key in combination[1:]:
                values = [row for row in values if row[key] is not None]
            overlaps[combination] = len(values)
    print("Overlaps:")
    for intersection, size in overlaps.items():
        if len(intersection) == 1:
            print("\t" + " \u2229 ".join(intersection) + ": %s" % size)
            continue
        target = min([
            len([row[key] for row in alignment if row[key] is not None])
            for key in intersection
        ])
        print("\t" + " \u2229 ".join(intersection) + ": %s (%s)" % (size, target))


  


def action_merge(path_alignment, path_inatheque, path_madelen, path_lmdmfr, path_youtube, path_merger):
    alignment = load_alignment(path_alignment)
    check_alignment(alignment)
    inatheque = load_and_index(path_inatheque, "id")
    madelen = load_and_index(path_madelen, "uri")
    lmdmfr = load_and_index(path_lmdmfr, "id")
    youtube = load_and_index(path_youtube, "id")
    entries = list()
    conflicts = list()
    for doc in alignment:
        entry = {
            "doc_id": doc["doc_id"],
            "links": {
                "inatheque_id": None,
                "inatheque_uri": None,
                "lmdmfr_id": None,
                "lmdmfr_uri": None,
                "madelen_uri": None,
                "youtube_id": None,
                "youtube_uri": None,
            },
            "opening": None,
            "title": None,
            "collection": None,
            "diffusion_date": None,
            "duration": None,
            "credits": {
                "author": None,
                "directors": list(),
                "producers": list(),
                "cast": list(),
                "crew": list(),
            },
            "summary": {
                "pitch": None,
                "beginning": None,
                "end": None,
            },
            "descriptors": list(),
            "facets": list(),
            "relevant_words": list(),
            "chapters": list()
        }


        if doc["youtube"] is not None:
            ref = youtube[doc["youtube"]] 
            entry["links"]["youtube_id"] = ref["id"]
            entry["links"]["youtube_uri"] = ref["uri"]
            entry["opening"] = ref["opening"]
            entry["title"] = ref["title"]
            entry["collection"] = ref["collection"]
            entry["diffusion_date"] = ref["diffusion_date"]
            entry["duration"] = ref["duration"]
            entry["facets"] = ref["facets"]
            entry["relevant_words"] = ref["relevant_words"]
            entry["chapters"] = ref["chapters"]

            
        if doc["lmdmfr"] is not None:
            ref = lmdmfr[doc["lmdmfr"]] 
            entry["links"]["lmdmfr_id"] = ref["id"]
            entry["links"]["lmdmfr_uri"] = ref["uri"]

            if ref["title"] is not None:
                if entry["title"] is not None and slugify.slugify(entry["title"]) != slugify.slugify(ref["title"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "title",
                        "source": "lmdmfr",
                        "previous_value": entry["title"],
                        "new_value": ref["title"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["title"], ref["title"]).ratio()
                    })
                entry["title"] = ref["title"]
            
            if ref["collection"] is not None:
                if entry["collection"] is None:
                    entry["collection"] = ref["collection"]

            if ref["diffusion_date"] is not None:
                if entry["diffusion_date"] is not None and entry["diffusion_date"] != ref["diffusion_date"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "diffusion_date",
                        "source": "lmdmfr",
                        "previous_value": entry["diffusion_date"],
                        "new_value": ref["diffusion_date"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["diffusion_date"], ref["diffusion_date"]).ratio()
                    })
                entry["diffusion_date"] = ref["diffusion_date"]

            if ref["author"] is not None:
                entry["credits"]["author"] = ref["author"]

        if doc["madelen"] is not None:
            ref = madelen[doc["madelen"]] 
            entry["links"]["madelen_uri"] = ref["uri"]

            if ref["title"] is not None:
                if entry["title"] is not None and slugify.slugify(entry["title"]) != slugify.slugify(ref["title"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "title",
                        "source": "madelen",
                        "previous_value": entry["title"],
                        "new_value": ref["title"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["title"], ref["title"]).ratio()
                    })
                entry["title"] = ref["title"]
            
            if ref["collection"] is not None:
                if entry["collection"] is not None and slugify.slugify(entry["collection"]) != slugify.slugify(ref["collection"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "collection",
                        "source": "madelen",
                        "previous_value": entry["collection"],
                        "new_value": ref["collection"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["collection"], ref["collection"]).ratio()
                    })
                entry["collection"] = ref["collection"]
            
            if ref["diffusion_date"] is not None:
                if entry["diffusion_date"] is not None and entry["diffusion_date"] != ref["diffusion_date"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "diffusion_date",
                        "source": "madelen",
                        "previous_value": entry["diffusion_date"],
                        "new_value": ref["diffusion_date"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["diffusion_date"], ref["diffusion_date"]).ratio()
                    })
                entry["diffusion_date"] = ref["diffusion_date"]

            if ref["duration"] is not None:
                if entry["duration"] is not None and entry["duration"] != ref["duration"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "duration",
                        "source": "madelen",
                        "previous_value": entry["duration"],
                        "new_value": ref["duration"],
                        "difference": abs(entry["duration"] - ref["duration"])
                    })
                entry["duration"] = ref["duration"]

            if ref["credits"]["author"] is not None:
                if entry["credits"]["author"] is not None and slugify.slugify(entry["credits"]["author"]) != slugify.slugify(ref["credits"]["author"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "author",
                        "source": "madelen",
                        "previous_value": entry["credits"]["author"],
                        "new_value": ref["credits"]["author"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["credits"]["author"], ref["credits"]["author"]).ratio()
                    })
                entry["credits"]["author"] = ref["credits"]["author"]

            
            entry["credits"]["directors"] = ref["credits"]["directors"]
            entry["credits"]["producers"] = ref["credits"]["producers"]
            entry["credits"]["cast"] = [
                {
                    "name": name["name"],
                    "character": None
                }
                for name in ref["credits"]["cast"]
            ]
            entry["credits"]["crew"] = ref["credits"]["crew"]

            entry["summary"]["pitch"] = ref["summary"]["pitch"]
            entry["summary"]["beginning"] = ref["summary"]["beginning"]
            entry["summary"]["end"] = ref["summary"]["end"]
            entry["descriptors"] = [{
                "label": label["label"],
                "specification": None
            } for label in ref["descriptors"]]

        if doc["inatheque"] is not None:
            ref = inatheque[doc["inatheque"]] 
            entry["links"]["inatheque_id"] = ref["id"]
            entry["links"]["inatheque_uri"] = ref["uri"]

            if ref["title"] is not None:
                if entry["title"] is not None and slugify.slugify(entry["title"]) != slugify.slugify(ref["title"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "title",
                        "source": "inatheque",
                        "previous_value": entry["title"],
                        "new_value": ref["title"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["title"], ref["title"]).ratio()
                    })
                entry["title"] = ref["title"]
            
            if ref["collection"] is not None:
                if entry["collection"] is not None and slugify.slugify(entry["collection"]) != slugify.slugify(ref["collection"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "collection",
                        "source": "inatheque",
                        "previous_value": entry["collection"],
                        "new_value": ref["collection"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["collection"], ref["collection"]).ratio()
                    })
                entry["collection"] = ref["collection"]
            
            if ref["diffusion_date"] is not None:
                if entry["diffusion_date"] is not None and entry["diffusion_date"] != ref["diffusion_date"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "diffusion_date",
                        "source": "inatheque",
                        "previous_value": entry["diffusion_date"],
                        "new_value": ref["diffusion_date"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["diffusion_date"], ref["diffusion_date"]).ratio()
                    })
                entry["diffusion_date"] = ref["diffusion_date"]

            if ref["duration"] is not None:
                if entry["duration"] is not None and entry["duration"] != ref["duration"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "duration",
                        "source": "inatheque",
                        "previous_value": entry["duration"],
                        "new_value": ref["duration"],
                        "difference": abs(entry["duration"] - ref["duration"])
                    })
                entry["duration"] = ref["duration"]

            if ref["credits"]["author"] is not None:
                if entry["credits"]["author"] is not None and slugify.slugify(entry["credits"]["author"]) != slugify.slugify(ref["credits"]["author"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "author",
                        "source": "inatheque",
                        "previous_value": entry["credits"]["author"],
                        "new_value": ref["credits"]["author"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["credits"]["author"], ref["credits"]["author"]).ratio()
                    })
                entry["credits"]["author"] = ref["credits"]["author"]
            
            if len(ref["credits"]["directors"]) > 0:
                entry["credits"]["directors"] = ref["credits"]["directors"]
            if len(ref["credits"]["producers"]) > 0:
                entry["credits"]["producers"] = ref["credits"]["producers"]
            if len(ref["credits"]["cast"]) > 0:
                entry["credits"]["cast"] = ref["credits"]["cast"]
            if len(ref["credits"]["crew"]) > 0:
                entry["credits"]["crew"] = ref["credits"]["crew"]

            if ref["summary"]["pitch"] is not None:
                if entry["summary"]["pitch"] is not None and slugify.slugify(entry["summary"]["pitch"]) != slugify.slugify(ref["summary"]["pitch"]):
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "pitch",
                        "source": "inatheque",
                        "previous_value": entry["summary"]["pitch"],
                        "new_value": ref["summary"]["pitch"],
                        "difference": 1 - difflib.SequenceMatcher(None, entry["summary"]["pitch"], ref["summary"]["pitch"]).ratio()
                    })
                entry["summary"]["pitch"] = ref["summary"]["pitch"]
            
            if ref["summary"]["beginning"] is not None:
                if entry["summary"]["beginning"] is not None and entry["summary"]["beginning"] != ref["summary"]["beginning"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "beginning",
                        "source": "inatheque",
                        "previous_value": entry["summary"]["beginning"],
                        "new_value": ref["summary"]["beginning"],
                        "difference": abs(entry["summary"]["beginning"] - ref["summary"]["beginning"])
                    })
                entry["summary"]["beginning"] = ref["summary"]["beginning"]
            
            if ref["summary"]["end"] is not None:
                if entry["summary"]["end"] is not None and entry["summary"]["end"] != ref["summary"]["end"]:
                    conflicts.append({
                        "doc_id": doc["doc_id"],
                        "field": "end",
                        "source": "inatheque",
                        "previous_value": entry["summary"]["end"],
                        "new_value": ref["summary"]["end"],
                        "difference": abs(entry["summary"]["end"] - ref["summary"]["end"])
                    })
                entry["summary"]["end"] = ref["summary"]["end"]  

            if len(ref["descriptors"]) > 0:
                entry["descriptors"] = ref["descriptors"]

        entries.append(entry)

    with codecs.open(path_merger, "w", "utf8") as file:
        simplejson.dump({"entries": entries}, file, indent=4, sort_keys=True)
    with codecs.open(path_merger.replace(".json", ".min.json"), "w", "utf8") as file:
        simplejson.dump({"entries": entries}, file, sort_keys=True)

    print("Found %d conflicts (see conflicts.csv)" % len(conflicts))
    pandas.DataFrame(conflicts).to_csv("conflicts.csv", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alignement",
        type=str,
        default="data/alignment.tsv"
    )
    parser.add_argument(
        "--inatheque",
        type=str,
        default="data/inatheque.json"
    )
    parser.add_argument(
        "--madelen",
        type=str,
        default="data/madelen.json"
    )
    parser.add_argument(
        "--lmdmfr",
        type=str,
        default="data/lmdmfr.json"
    )
    parser.add_argument(
        "--youtube",
        type=str,
        default="data/youtube.json"
    )
    parser.add_argument(
        "--merger",
        type=str,
        default="data/merger.json"
    )
    args = parser.parse_args()
    action_merge(
        args.alignement,
        args.inatheque,
        args.madelen,
        args.lmdmfr,
        args.youtube,
        args.merger
    )


if __name__ == "__main__":
    main()