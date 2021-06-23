import argparse
import codecs
import simplejson
import itertools
import difflib
import pandas
import slugify
import tqdm


COLLECTION_CANONIZED = {
    "Le jeu du mystère et de l'aventure": "Le Jeu du mystère et de l'aventure",
    "Faits Divers": "Faits divers",
    "Faits divers": "Faits divers",
    "Mystère Mystère": "Mystère, mystère",
    "L'Heure du mystère": "L'Heure du mystère",
    "Les mystères de l'été": "Les Mystères de l'été",
    "Les Maîtres du mystère": "Les Maîtres du mystère",
    "Les maîtres du mystère": "Les Maîtres du mystère",
    "Mystère-mystère & L'heure du mystère": None,
    "Les Nouveaux Maîtres du mystère": "Les Nouveaux Maîtres du mystère",
}


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


def compare_text(a, b, threshold):
    return difflib.SequenceMatcher(None, a, b).ratio() > threshold


class MergeField:

    def __init__(self, label):
        self.label = label

    def __str__(self):
        return self.label
    
    def get(self, doc, source, operator):
        raise NotImplementedError


class SimpleMergeField(MergeField):

    def __init__(self, label):
        MergeField.__init__(self, label)
    
    def get(self, doc, source, operator):
        if doc[source] is None:
            return None
        return getattr(operator, source)[doc[source]].get(self.label)


class NestedMergeField(MergeField):

    def __init__(self, label, parent):
        MergeField.__init__(self, label)
        self.parent = parent
    
    def get(self, doc, source, operator):
        if doc[source] is None:
            return None
        ref = getattr(operator, source)[doc[source]]
        if self.parent in ref:
            return ref[self.parent].get(self.label)
        return None


class MergeOperator:

    SOURCES = ["youtube", "lmdmfr", "madelen", "inatheque"]
    SOURCE_PRIORITIES = {
        "youtube": 2,
        "lmdmfr": 1,
        "madelen": 3,
        "inatheque": 4
    }

    def __init__(self, inatheque, youtube, madelen, lmdmfr):
        self.inatheque = inatheque
        self.youtube = youtube
        self.madelen = madelen
        self.lmdmfr = lmdmfr
        self.conflicts = list()
        self.decisions = list()
    
    def _get_field_values(self, doc, field):
        result = list()
        for source in self.SOURCES:
            if doc[source] is not None:
                val = field.get(doc, source, self)
                if val is None:
                    continue
                result.append({
                    "source": source,
                    "value": val
                })
        return result
    
    def _add_conflict(self, doc, field, val_a, val_b):
        d = {
            "doc_id": doc["doc_id"],
            "field": field.label,
            "source_a": val_a["source"],
            "value_a": val_a["value"],
            "source_b": val_b["source"],
            "value_b": val_b["value"],
            "similarity": None,
        }
        if isinstance(val_a["value"], str):
            d["similarity"] = difflib.SequenceMatcher(None, val_a["value"], val_b["value"]).ratio()
        elif isinstance(val_a["value"], int) or isinstance(val_a["value"], float):
            d["similarity"] = - abs(val_a["value"] - val_b["value"])
        self.conflicts.append(d)
    
    def _add_decision(self, doc, field, val, val_count):
        elem = {
            "doc_id": doc["doc_id"],
            "field": field.label,
            "val_count": val_count
        }
        elem.update(**val)
        self.decisions.append(elem)
    
    def _quotient(self, vals, comparator):
        if len(vals) == 0:
            return {}
        reps = dict()
        for i, val in enumerate(vals):
            matched = False
            for j in set(reps.values()):
                if comparator(val["value"], vals[j]["value"]):
                    reps[i] = j
                    matched = True
                    break
            if not matched:
                reps[i] = i
        return reps

    def _merge_field(self, doc, field, comparator):
        vals = self._get_field_values(doc, field)
        if len(vals) == 0:
            return None
        for i, val_a in enumerate(vals):
            for val_b in vals[i+1:]:
                if not comparator(val_a["value"], val_b["value"]):
                    self._add_conflict(doc, field, val_a, val_b)
        reps = self._quotient(vals, comparator)
        for i, val in enumerate(vals):
            j = reps[i]
            val["priority_consensus"] = len([x for x in reps if reps[x] == j])
            val["priority_source"] = self.SOURCE_PRIORITIES[val["source"]]
        vals.sort(key=lambda val: (-val["priority_consensus"], -val["priority_source"]))
        self._add_decision(doc, field, val, len(vals))
        return vals[0]["value"]
    
    def _merge_text_field(self, doc, field, threshold):
        return self._merge_field(doc, field, lambda a, b: compare_text(a, b, threshold))
    
    def _merge_int_field(self, doc, field, thresold):
        return self._merge_field(doc, field, lambda a, b: abs(a - b) < thresold)

    def _merge_list_field(self, doc, field, cmpk):
        vals = self._get_field_values(doc, field)
        keys_per_val = dict()
        for i, val in enumerate(vals):
            keys_per_val[i] = set()
            for elem in val["value"]:
                keys_per_val[i].add(slugify.slugify(cmpk(elem)))
        for i, val_a in enumerate(vals):
            for k, val_b in enumerate(vals[i+1:]):
                j = k + i + 1
                if keys_per_val[i] != keys_per_val[j]:
                    intersect = keys_per_val[i].intersection(keys_per_val[j])
                    self._add_conflict(
                        doc,
                        field,
                        {
                            "source": val_a["source"],
                            "value": [
                                cmpk(x) for x in val_a["value"]
                                if slugify.slugify(cmpk(x)) not in intersect
                            ]
                        },
                        {
                            "source": val_b["source"],
                            "value": [
                                cmpk(x) for x in val_b["value"]
                                if slugify.slugify(cmpk(x)) not in intersect
                            ]
                        }
                    )
        union = dict()
        for val in vals:
            for part in val["value"]:
                if slugify.slugify(cmpk(part)) in union:
                    union[slugify.slugify(cmpk(part))].update(**part)
                else:
                    union[slugify.slugify(cmpk(part))] = part
        result = sorted(union.values(), key=cmpk)
        return result

    def merge_title(self, doc):
        return self._merge_text_field(doc, SimpleMergeField("title"), .8)
    
    def merge_collection(self, doc):
        result = self._merge_text_field(doc, SimpleMergeField("collection"), .8)
        if result is not None:
            return COLLECTION_CANONIZED[result]
        return result
    
    def merge_diffusion_date(self, doc):
        return self._merge_text_field(doc, SimpleMergeField("diffusion_date"), .99)

    def merge_duration(self, doc):
        return self._merge_int_field(doc, SimpleMergeField("duration"), 1)
    
    def merge_author(self, doc):
        return self._merge_text_field(doc, NestedMergeField("author", "credits"), .8)
    
    def merge_pitch(self, doc):
        return self._merge_text_field(doc, NestedMergeField("pitch", "summary"), .8)

    def merge_beginning(self, doc):
        return self._merge_int_field(doc, NestedMergeField("beginning", "summary"), 1)

    def merge_end(self, doc):
        return self._merge_int_field(doc, NestedMergeField("end", "summary"), 1)

    def merge_directors(self, doc):
        return self._merge_list_field(doc, NestedMergeField("directors", "credits"), lambda x: x["name"])
    
    def merge_producers(self, doc):
        return self._merge_list_field(doc, NestedMergeField("producers", "credits"), lambda x: x["name"])
    
    def merge_cast(self, doc):
        return self._merge_list_field(doc, NestedMergeField("cast", "credits"), lambda x: x["name"])
    
    def merge_crew(self, doc):
        return self._merge_list_field(doc, NestedMergeField("crew", "credits"), lambda x: x["name"])
    
    def merge_descriptors(self, doc):
        return self._merge_list_field(doc, SimpleMergeField("descriptors"), lambda x: x["label"])


def action_merge(path_alignment, path_inatheque, path_madelen, path_lmdmfr, path_youtube, path_merger):
    alignment = load_alignment(path_alignment)
    check_alignment(alignment)

    inatheque = load_and_index(path_inatheque, "id")
    for entry in inatheque.values():
        for element in entry["credits"]["cast"]:
            if element["name"] == "France-chanteuse Marie":
                element["name"] = "Marie-France"
            elif element["name"] == "Martine-actrice Marie":
                element["name"] = "Marie-Martine"

    madelen = load_and_index(path_madelen, "uri")
    for entry in madelen.values():
        if entry["credits"]["author"] == "Van Ky Pham":
            entry["credits"]["author"] = "Pham Van Ky"
        for element in entry["credits"]["cast"]:
            if element["name"] == "Marie France-chanteuse":
                element["name"] = "Marie-France"
            elif element["name"] == "Marie Martine-actrice":
                element["name"] = "Marie-Martine"
            elif element["name"] == "Jean Marie Ferté":
                element["name"] = "Jean-Marie Fertey"
            elif element["name"] == "Jean Paul Berthaud":
                element["name"] == "Jean-Paul Bertaud"
            elif element["name"] == "Assia-chanteuse":
                element["name"] = "Assia Maouène"
        for element in entry["credits"]["crew"]:
            if element["name"] == "Van Ky Pham":
                element["name"] = "Pham Van Ky"

    lmdmfr = load_and_index(path_lmdmfr, "id")
    for entry in lmdmfr.values():
        if entry["collection"] == "Mystère-mystère & L'heure du mystère":
            entry["collection"] = None

    youtube = load_and_index(path_youtube, "id")
    operator = MergeOperator(inatheque, youtube, madelen, lmdmfr)
    entries = list()
    for doc in tqdm.tqdm(alignment):
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
            "title": operator.merge_title(doc),
            "collection": operator.merge_collection(doc),
            "diffusion_date": operator.merge_diffusion_date(doc),
            "duration": operator.merge_duration(doc),
            "credits": {
                "author": operator.merge_author(doc),
                "directors": operator.merge_directors(doc),
                "producers": operator.merge_producers(doc),
                "cast": operator.merge_cast(doc),
                "crew": operator.merge_crew(doc),
            },
            "summary": {
                "pitch": operator.merge_pitch(doc),
                "beginning": operator.merge_beginning(doc),
                "end": operator.merge_end(doc),
            },
            "descriptors": operator.merge_descriptors(doc),
            "facets": list(),
            "relevant_words": list(),
            "chapters": list()
        }

        if doc["youtube"] is not None:
            ref = youtube[doc["youtube"]] 
            entry["links"]["youtube_id"] = ref["id"]
            entry["links"]["youtube_uri"] = ref["uri"]
            entry["opening"] = ref["opening"]
            entry["facets"] = ref["facets"]
            entry["relevant_words"] = ref["relevant_words"]
            entry["chapters"] = ref["chapters"]

        if doc["lmdmfr"] is not None:
            ref = lmdmfr[doc["lmdmfr"]] 
            entry["links"]["lmdmfr_id"] = ref["id"]
            entry["links"]["lmdmfr_uri"] = ref["uri"]

        if doc["madelen"] is not None:
            ref = madelen[doc["madelen"]] 
            entry["links"]["madelen_uri"] = ref["uri"]
        if doc["inatheque"] is not None:
            ref = inatheque[doc["inatheque"]] 
            entry["links"]["inatheque_id"] = ref["id"]
            entry["links"]["inatheque_uri"] = ref["uri"]

        entries.append(entry)

    print("Took %d decisions (see merger-decisions.csv)" % len(operator.decisions))
    pandas.DataFrame(operator.decisions).to_csv("merger-decisions.csv", index=False)
    print("Found %d conflicts (see merger-conflicts.csv)" % len(operator.conflicts))
    pandas.DataFrame(operator.conflicts).to_csv("merger-conflicts.csv", index=False)

    print("Writing to disk...")

    with codecs.open(path_merger, "w", "utf8") as file:
        simplejson.dump({"entries": entries}, file, indent=4, sort_keys=True)
    with codecs.open(path_merger.replace(".json", ".min.json"), "w", "utf8") as file:
        simplejson.dump({"entries": entries}, file, sort_keys=True)


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