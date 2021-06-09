import argparse
import codecs
import json
import logging
import re
import subprocess
import os
import tqdm
import fontTools.ttLib
import eyed3


INKSCAPE = r"C:\Program Files\Inkscape\bin\inkscape.exe"

LOGO = """<path style="fill:yellow;fill-opacity:1;stroke:none;" d="m 432.24062,0.00287769 c -8.72578,-0.13895453 -25.78274,4.77296771 -36.87103,10.69409131 -3.56672,1.904615 1.47348,-5.3672325 -1.03219,-6.6066838 -6.10903,-3.0219487 -53.42652,11.3156478 -62.32845,21.2277378 -4.0871,4.550896 7.30025,-13.522964 2.62513,-12.973513 -11.81799,1.388899 -29.1197,13.985505 -38.53842,22.14413 -3.34931,2.901237 -0.87409,-6.362776 -3.64742,-4.995542 -13.83953,6.822917 -26.76963,19.734759 -38.89904,30.568727 -1.35811,1.213044 0.31017,-8.505828 -2.47791,-8.351813 -5.50357,0.304093 -17.37351,17.473062 -26.655,26.180264 -3.04298,2.854733 -0.96952,-5.798546 -4.05267,-2.984084 -16.09584,14.692425 -37.35187,40.060358 -47.7471,50.251478 -74.396263,17.9574 -92.08736,-11.41092 -112.052253,-42.824338 -9.235482,2.71161 -19.905765,66.398248 6.778718,110.054038 2.388433,3.9075 4.660648,11.50441 2.052794,16.18092 -5.344643,9.58421 -61.6692588,43.19971 -67.9244401,50.1605 -5.2240434,5.81333 4.8263248,12.19192 8.9324231,9.80748 4.106091,-2.38444 43.977522,-24.35084 54.745812,-26.50449 5.566292,-1.11327 8.895218,-0.26699 10.798303,-0.837 1.778538,-0.53261 2.169425,-2.51241 5.913592,-2.67477 5.190503,-0.22503 27.203011,28.34855 32.922591,19.45613 9.49745,-14.76598 23.18959,-59.20706 26.07936,-61.36407 1.87281,-1.3979 3.2991,-0.22778 3.4671,0.39039 1.48963,5.48148 -30.6307,71.71979 -23.61633,80.88475 8.07326,10.54841 28.90011,-13.58369 39.55739,-14.26048 4.32702,-0.27496 12.05913,18.40053 35.28803,18.13449 31.53999,-0.36119 86.50795,-48.64427 110.90591,-60.33025 50.00119,-23.94928 65.65004,-19.10203 85.82899,-15.47459 -8.35136,-81.57241 -90.53273,-76.75288 -103.41428,-83.93002 0.45019,-3.41432 1.01375,-6.53938 3.08005,-6.18984 7.55025,1.27717 24.4534,-4.17167 24.17377,-9.48987 -0.34401,-6.54251 -5.24465,-4.33894 -5.18412,-8.978734 0.0896,-6.860115 20.91748,-3.666562 34.94398,-9.620544 6.34139,-2.691799 0.84115,-7.962619 2.91462,-8.805056 4.78978,-1.946099 15.30625,-1.382384 26.10581,-7.20052 24.24166,-13.059833 35.12284,-8.308129 37.45495,-12.343281 1.4703,-2.544074 -4.80323,-4.332138 -3.55475,-6.022771 1.33919,-1.81348 20.69337,-0.507733 36.07376,-6.959019 7.0675,-2.964411 17.75487,-6.786416 26.12236,-7.853907 11.39081,-1.453248 23.86628,3.201219 23.29541,8.017669 -0.20358,1.718132 5.74618,2.051879 5.69359,0.473092 -0.2356,-7.073848 -3.92226,-35.613739 -64.325,-38.9006906 -3.08786,-0.1680514 2.3677,-6.3707559 1.10002,-7.19721997 -0.9506,-0.61971923 -2.52039,-0.92071693 -4.53406,-0.95279074 z M 415.83973,11.626604 c 1.72593,-0.172373 0.0407,5.788645 1.75173,5.634038 39.26101,-3.549051 70.87731,8.906706 69.98718,13.741043 -0.45755,2.485013 -5.98871,-0.579697 -18.25688,1.002422 -9.36428,1.20763 -21.72134,5.766894 -35.38728,9.0664 -14.08575,3.400855 -27.39277,5.559618 -44.90856,8.881143 -2.43799,0.462317 4.81796,6.108256 2.73431,6.735709 -8.36307,2.51831 -17.38266,5.090339 -25.93216,8.188054 -3.54668,1.285066 -9.71769,3.192894 -18.10634,5.508323 -9.0862,2.507967 -20.51002,2.006374 -25.1282,3.829364 -3.04833,1.203312 -0.16549,3.780763 1.94197,4.50591 2.63546,0.906837 8.15219,-1.451504 8.1682,3.693722 0.0128,3.459523 -18.44011,1.352708 -23.38973,4.737491 -0.29417,0.201246 -1.56988,1.538778 -1.78979,1.768288 -4.32632,4.514115 -32.53261,3.663666 -32.7522,9.680099 -0.17733,4.85367 15.3528,4.10075 24.27469,4.40004 5.02023,0.16844 5.91628,-0.19561 5.91855,1.84604 0.003,3.19255 -29.57775,2.53165 -31.87055,5.86892 -2.84718,4.14421 1.64524,4.30889 3.47703,6.46444 1.08267,1.27402 0.91189,3.05004 -2.1074,3.04363 -11.19347,-0.0224 -43.78466,1.55421 -48.35581,-0.0314 -2.14626,-0.74449 21.12393,-19.83322 48.38062,-36.349992 22.19706,-13.450766 47.66957,-25.245809 63.88006,-30.886316 56.53871,-19.67297 78.37727,-22.643444 108.41807,-24.835439 17.89646,-1.305875 29.98979,3.455499 29.98979,0.959407 0,-8.963934 -71.88881,-8.117828 -141.66159,17.077462 -46.21257,16.687606 -80.56529,37.430478 -106.34044,58.659538 -7.77136,6.40067 -16.97227,17.10655 -19.38172,17.10559 -9.29003,-0.004 -18.60563,2.5747 -20.03013,0.66993 -1.31114,-1.75318 11.29527,-14.46863 19.77209,-23.867762 0.95225,-1.055872 -0.22666,6.620592 2.32242,7.566092 0,0 0,-0.002 0,-0.002 2.81163,1.04295 15.68993,-23.921638 29.57126,-33.339428 1.23443,-0.837508 -1.45353,5.784554 2.19011,6.783672 3.51778,0.96459 25.56523,-26.445487 39.82537,-35.005163 1.68887,-1.013811 -2.32766,6.815011 1.36964,7.127746 6.63851,0.561478 27.79845,-21.09667 36.7354,-25.300257 2.17859,-1.024729 -7.96135,14.772104 -3.71356,15.034585 4.66531,0.288248 41.19914,-23.65818 60.34676,-26.850191 3.48539,-0.581042 -8.13049,13.763373 -4.48937,12.894115 13.9692,-3.335042 28.29698,-14.581303 42.54646,-16.005579 z M 119.82757,148.27444 c 15.70415,0.1678 28.66564,4.56927 27.89397,7.5264 0,0 -19.44813,-4.87079 -38.38957,-1.75009 -17.456163,2.87602 -36.576606,14.9039 -36.576606,14.9039 -1.011119,-1.67091 11.010207,-15.22744 30.859866,-19.22621 5.43733,-1.09536 10.97762,-1.50992 16.21234,-1.454 z m 128.49286,1.57476 c 2.64727,-0.005 5.09222,0.10829 7.32128,0.28284 26.66643,2.08816 28.36891,22.37128 23.82973,22.35256 0,0 -2.45023,-6.67544 -9.20042,-11.59726 -9.95498,-7.25857 -28.38302,-12.33634 -54.92279,0.10585 -21.68964,10.16827 -40.1502,20.08294 -48.93478,45.56693 -5.05623,14.66811 -0.85931,29.01386 10.09529,35.996 22.61732,14.41562 70.34612,-14.46225 70.34612,-14.46225 3.48411,3.76211 -20.67829,16.55533 -43.55713,23.36488 -19.00054,5.65524 -37.84233,1.37499 -42.50509,-13.54583 -3.80562,-12.178 -2.99088,-33.98022 7.97632,-48.15733 10.01721,-12.94908 22.99787,-22.40523 34.87118,-28.46962 17.93984,-9.16293 33.20875,-11.4143 44.68029,-11.43679 z m -16.32483,19.72246 c 15.95518,-0.11527 24.10619,5.75707 23.92732,8.80174 -0.24616,4.19174 -15.30347,9.90722 -26.84028,9.76445 -8.59773,-0.10646 -26.4296,-2.43431 -26.29273,-8.30714 0.13092,-5.61728 16.05027,-9.602 25.91063,-10.15485 1.13289,-0.0635 2.2314,-0.0965 3.29506,-0.10419 z m -119.36855,4.08244 c 1.38415,-0.0427 2.34327,0.18357 2.68303,0.81053 1.61534,2.98082 -9.71753,9.04178 -13.39532,11.82553 -3.663489,2.77295 -9.027738,5.00246 -13.208409,2.09747 -4.446491,-3.08974 -1.541272,-6.17944 1.159567,-8.35181 2.503528,-2.01371 8.194277,-3.28246 13.175322,-4.53735 3.78844,-0.95445 7.27889,-1.77328 9.58581,-1.84437 z m 16.21896,2.15867 c 0.65272,-0.0496 1.29654,3e-5 1.93039,0.16872 2.43813,0.6489 5.26208,0.005 6.7539,1.96182 4.35554,5.71263 -4.21765,9.20701 -7.45029,12.72374 -6.03254,6.56265 -29.39011,24.71839 -56.993809,44.63233 -3.47886,2.50963 -5.524439,-1.91821 -9.352577,-0.14392 -14.037966,6.50654 -29.075236,15.96713 -40.109884,20.80096 -38.981394,17.0762 5.301901,-10.84884 19.661259,-20.41554 12.453993,-8.2973 24.319701,-17.03667 36.750285,-26.61861 13.162575,-10.14615 26.932816,-19.09515 34.009366,-23.95212 5.21794,-3.58135 10.23234,-8.81025 14.80136,-9.15739 z" />"""


def load_svg(path):
    with open(path) as file:
        return file.read().replace("fill:#ffff00", "fill:#ffffff")


FACETS = {
    "Argent": load_svg("assets/argent.svg"),
    "Arme à feu": load_svg("assets/arme-a-feu.svg"),
    "Arme blanche": load_svg("assets/arme-blanche.svg"),
    "Chantage": load_svg("assets/chantage.svg"),
    "Drogue": load_svg("assets/drogue.svg"),
    "Enlèvement": load_svg("assets/enlevement.svg"),
    "Enquête": load_svg("assets/enquete.svg"),
    "Justice": load_svg("assets/justice.svg"),
    "Mariage": load_svg("assets/mariage.svg"),
    "Meurtre": load_svg("assets/meurtre.svg"),
    "Poison": load_svg("assets/poison.svg"),
    "Vol": load_svg("assets/vol.svg"),
}

COLLECTIONS = {
    "Faits Divers": "Faits divers",
    "Faits divers": "Faits divers",
    "Le jeu du mystère et de l'aventure": "Le Jeu du mystère et de l'aventure",
    "Les maîtres du mystère": "Les Maîtres du mystère",
    "Les Maîtres du mystère": "Les Maîtres du mystère",
    "Les mystères de l'été": "Les Mystères de l'été",
    "Les Mystères de l'été": "Les Mystères de l'été",
    "L'Heure du mystère": "L'Heure du mystère",
    "Mystère Mystère": "Mystère Mystère"
}

ALBUM_ARTISTS = {
    "Faits divers": "Pierre Billard",
    "Mystère Mystère": "Pierre Billard",
    "Les Mystères de l'été": "Pierre Billard",
    "Le Jeu du mystère et de l'aventure": "Pierre Billard",
    "Les Maîtres du mystère": "Pierre Billard",
    "L'Heure du mystère": "Germaine Beaumont",
}


class Font:

    CMU_SERIF = r"C:\Windows\Fonts\cmunrm.ttf"
    CMU_CONCRETE = r"C:\Windows\Fonts\cmunobi.ttf"

    def __init__(self, path, size):
        ttf = fontTools.ttLib.TTFont(path)
        self.glyph_set = ttf.getGlyphSet()
        self.cmap = ttf["cmap"].getcmap(3, 1).cmap
        self.coeff = size / ttf["head"].unitsPerEm
        self.size = size

    def char_width(self, char):
        return self.coeff * self.glyph_set[self.cmap[ord(char)]].width

    def word_width(self, word):
        return sum([self.char_width(char) for char in word])


def generate_svg(doc, padding=50, fig_size=600):
    cmu_serif_80 = Font(Font.CMU_SERIF, 80)
    cmu_concrete_1 = Font(Font.CMU_SERIF, 1)
    lines = [""]
    space = cmu_serif_80.char_width(" ")
    target = fig_size - padding * 2
    cur = 0
    for word in doc["title"].split(" "):
        if cur + cmu_serif_80.word_width(word) < target:
            lines[-1] += word + " "
            cur += cmu_serif_80.word_width(word) + space
        else:
            lines.append(word + " ")
            cur = cmu_serif_80.word_width(word) + space
    delim = "</tspan><tspan x=\"%d\" dy=\"1.2em\">" % padding
    fs = (target - padding - 500 * .25) / \
        cmu_concrete_1.word_width(doc["collection"])
    facets = list()
    if len(doc["facets"]) > 0:
        for facet in sorted(doc["facets"], key=lambda x: -x["score"]):
            if facet["label"] in FACETS:
                facets.append(FACETS[facet["label"]])
            if len(facets) == 4:
                break
    facet_svg = ""
    if len(facets) == 4:
        scale = (target / 2 - padding) / 64
        facet_svg = f"""
        <g transform="translate({padding}, {padding}) scale({scale})">{facets[0]}</g>
        <g transform="translate({padding + target / 2 + padding}, {padding}) scale({scale})">{facets[1]}</g>
        <g transform="translate({padding}, {padding + target / 2 + padding}) scale({scale})">{facets[2]}</g>
        <g transform="translate({padding + target / 2 + padding}, {padding + target / 2 + padding}) scale({scale})">{facets[3]}</g>
        """

    return re.sub(" +", " ", """
        <?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="%d" height="%d" viewBox="0 0 %d %d">
        <g opacity="0.1">%s</g>
	    <text x="%d" y="100" fill="yellow" font-family="CMU Serif" font-size="%f"><tspan>%s</tspan></text>
        <g transform="scale(0.25) translate(%d, %f)">%s</g>
        <text x="%f" y="%f" fill="yellow" font-family="CMU Concrete" font-size="%f">%s</text>
        </svg>
    """ % (
        fig_size,
        fig_size,
        fig_size,
        fig_size,
        facet_svg,
        padding,
        cmu_serif_80.size,
        delim.join(lines),
        padding * 4,
        fig_size * 4 - 287.76405 - padding * 4,
        LOGO,
        500 / 4 + 2 * padding,
        fig_size - padding,
        fs,
        COLLECTIONS[doc["collection"]]
    )).strip()


def generate_png(doc, path):
    with codecs.open("tmp.svg", "w", "utf8") as file:
        file.write(generate_svg(doc))
    process = subprocess.Popen(
        [
            INKSCAPE,
            "tmp.svg",
            "--export-type",
            "png",
            "--export-filename",
            path,
            "--actions",
            "export-background:black"
        ],
    )
    process.wait()
    os.remove("tmp.svg")


def action_tag(input_path):
    with codecs.open(input_path, "r", "utf8") as file:
        docs = json.load(file)["entries"]
    docs.sort(key=lambda x: x["diffusion_date"])
    track_nums = dict()
    for doc in tqdm.tqdm(docs):
        if doc["links"]["youtube_id"] is None:
            continue
        albumart_path = "data/albumarts/%05d.png" % doc["doc_id"]
        if not os.path.isfile(albumart_path):
            generate_png(doc, albumart_path)
        mp3_path = "data/youtube/%s.mp3" % doc["links"]["youtube_id"]
        audiofile = eyed3.load(mp3_path)
        audiofile.tag.clear()
        audiofile.tag.title = doc["title"]
        audiofile.tag.album = doc["collection"]
        track_nums.setdefault(COLLECTIONS[doc["collection"]], 0)
        track_nums[COLLECTIONS[doc["collection"]]] += 1
        audiofile.tag.track_num = track_nums[COLLECTIONS[doc["collection"]]]
        audiofile.tag.disc_num = (1, 1)
        audiofile.tag.genre = "Audio Theatre"
        audiofile.tag.recording_date = eyed3.core.Date.parse(
            doc["diffusion_date"])
        audiofile.tag.artist = doc["credits"]["author"]
        audiofile.tag.album_artist = ALBUM_ARTISTS[COLLECTIONS[doc["collection"]]]
        with open(albumart_path, "rb") as file:
            audiofile.tag.images.set(3, file.read(), "image/png")
        audiofile.tag.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data/merger.min.json")
    args = parser.parse_args()
    action_tag(args.input)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
