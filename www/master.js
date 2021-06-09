const DATASET_URL = "../data/merger.min.json";

const OPENINGS = {
    "tempo_di_suspense": "&laquo;&nbsp;<i>Tempo di suspense</i>&nbsp;&raquo; par André Popp",
    "les_mysteres_de_lete_1": "&laquo;&nbsp;<i>Running in the wind</i>&nbsp;&raquo; par Roger Roger",
    "faits_divers_1": "&laquo;&nbsp;<i>Chant du mystère</i>&nbsp;&raquo; par André Popp",
    "lanthologie_du_mystere": "&laquo;&nbsp;<i>Chant du mystère</i>&nbsp;&raquo; par André Popp",
    "le_jeu_du_mystere_et_de_laventure": "&laquo;&nbsp;<i>Chant du mystère</i>&nbsp;&raquo; par André Popp",
    "les_mysteres_de_lete_2": "Les Mystères de l'été &#x2161;",
    "les_mysteres_de_lete_3": "Les Mystères de l'été &#x2162;",
    "lheure_du_mystere_1": "L'Heure du mystère &#x49;",
    "lheure_du_mystere_2": "L'Heure du mystère &#x2161;",
    "lheure_du_mystere_3": "L'Heure du mystère &#x2162;",
    "lheure_du_mystere_specific": "L'Heure du mystère X",
    "faits_divers_2": "Faits Divers &#x2161;",
    "faits_divers_specific": "Faits Divers X",
    "narrator": "Narrateur",
    "other": "Autre",
    "les_maitres_du_mystere_2": "Les Maîtres du mystère &#x2161;",
    "none": "Aucun",
    "beethoven": "&laquo;&nbsp;<i>Symphonie n°5</i>&nbsp;&raquo; par Beethoven",
}

function autocomplete(inp, labels) {
    var currentFocus;
    let arr = Object.keys(labels).sort((a, b) => labels[b] - labels[a]);
    inp.addEventListener("input", function (e) {
        var a, b, i, val = this.value;
        closeAllLists();
        if (!val) { return false; }
        currentFocus = -1;
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        this.parentNode.appendChild(a);
        let re = new RegExp(val, "i");
        for (i = 0; i < arr.length; i++) {
            let match = arr[i].match(re);
            if (match) {
                b = document.createElement("DIV");
                b.innerHTML = arr[i].substr(0, match.index);
                b.innerHTML += "<strong>" + arr[i].substr(match.index, val.length) + "</strong>";
                b.innerHTML += arr[i].substr(match.index + val.length) + " <small style='color: gold'>" + labels[arr[i]] + "</small>";
                b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
                b.addEventListener("click", function (e) {
                    inp.value = this.getElementsByTagName("input")[0].value;
                    closeAllLists();
                });
                a.appendChild(b);
            }
        }
    });
    inp.addEventListener("keydown", function (e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            currentFocus++;
            addActive(x);
        } else if (e.keyCode == 38) { //up
            currentFocus--;
            addActive(x);
        } else if (e.keyCode == 13) {
            e.preventDefault();
            if (currentFocus > -1) {
                if (x) x[currentFocus].click();
            }
        }
    });
    function addActive(x) {
        if (!x) return false;
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
        for (var i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }
    function closeAllLists(elmnt) {
        var x = document.getElementsByClassName("autocomplete-items");
        for (var i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inp) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }
}

function normalize(string) {
    /* Trim, lowercase and replace characters with accents. */
    if (string) {
        return string.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replaceAll(" ", "-").trim();
    } else {
        return null;
    }
}

function requestDataset(callback) {
    document.getElementById("modal-loading").classList.add("active");
    let request = new XMLHttpRequest();
    request.open("GET", DATASET_URL);
    request.onreadystatechange = function () {
        if (request.readyState == 4 && request.status == "200") {
            callback(JSON.parse(request.responseText).entries);
        }
    };
    request.send();
}

function formatDuration(rawDuration) {
    let minutes = rawDuration / 60;
    return minutes.toFixed(0) + " min";
}

function formatDate(rawDate) {
    let date = new Date(rawDate);
    const options = {
        year: "numeric",
        month: "short",
        day: "numeric"
    };
    return date.toLocaleDateString("fr-FR", options);
}

function checkArrayField(doc, filter, arrayGetter, fieldGetter) {
    let keep = true;
    for (let k = 0; k < filter.length; k++) {
        let found = false;
        let array = arrayGetter(doc);
        for (let j = 0; j < array.length; j++) {
            if (fieldGetter(array[j]) == filter[k]) {
                found = true;
                break;
            }
        }
        if (!found) {
            keep = false;
            break;
        }
    }
    return keep;
}

function loadDocData(doc, element) {

    let minScore = 3;
    let filterFacetsBound = document.getElementById("input-facets-bound").value;
    if (filterFacetsBound.trim() != "") {
        minScore = parseInt(filterFacetsBound);
    }

    element = document.getElementById("doc-" + doc.doc_id);

    if (doc.summary.pitch) {
        element.querySelector(".doc-pitch").textContent = doc.summary.pitch;
    } else {
        element.querySelector(".doc-pitch").parentNode.remove();
    }

    if (doc.chapters.length) {
        doc.chapters.forEach(chapter => {
            let timelineItem = document.createElement("div");
            timelineItem.className = "timeline-item";
            timelineItem.innerHTML = '<div class="timeline-left"><a class="timeline-icon"></a></div>';
            let content = document.createElement("div");
            content.className = "timeline-content";
            content.innerHTML = '<small>' + formatDuration(chapter.start) + '</small><br>';
            chapter.words.forEach(word => {
                content.innerHTML += '<span class="chip">' + word.label + '</span>';
            });
            timelineItem.appendChild(content);
            element.querySelector(".doc-chapters").appendChild(timelineItem);
        });
    } else {
        element.querySelector(".doc-chapters").parentNode.remove();
    }

    if (doc.credits.cast.length) {
        let castContainer = element.querySelector(".doc-cast");
        doc.credits.cast.sort((a, b) => {
            if (a.name < b.name) {
                return -1;
            } else {
                return 1;
            }
        });
        doc.credits.cast.forEach(person => {
            let chip = document.createElement("span");
            chip.className = "chip";
            if (person.character) {
                chip.textContent = person.name + " (" + person.character + ")";
            } else {
                chip.textContent = person.name;
            }
            castContainer.appendChild(chip);
        });
        if (doc.credits.cast.length == 1) {
            element.querySelector(".doc-cast-count").textContent = " (1)";
        } else {
            element.querySelector(".doc-cast-count").textContent = "s (" + doc.credits.cast.length + ")";
        }
    } else {
        element.querySelector(".doc-cast").parentNode.remove();
    }

    if (doc.credits.directors.length) {
        let directorsContainer = element.querySelector(".doc-directors");
        doc.credits.directors.sort((a, b) => {
            if (a.name < b.name) {
                return -1;
            } else {
                return 1;
            }
        });
        doc.credits.directors.forEach(person => {
            let chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = person.name;
            directorsContainer.appendChild(chip);
        });
    } else {
        element.querySelector(".doc-directors").parentNode.remove();
    }

    if (doc.credits.crew.length) {
        let crewContainer = element.querySelector(".doc-crew");
        doc.credits.crew.sort((a, b) => {
            if (a.name < b.name) {
                return -1;
            } else {
                return 1;
            }
        });
        doc.credits.crew.forEach(person => {
            let chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = person.name + " (" + person.job + ")";
            crewContainer.appendChild(chip);
        });
    } else {
        element.querySelector(".doc-crew").parentNode.remove();
    }

    if (doc.credits.producers.length) {
        let producersContainer = element.querySelector(".doc-producers");
        doc.credits.producers.sort((a, b) => {
            if (a.name < b.name) {
                return -1;
            } else {
                return 1;
            }
        });
        doc.credits.producers.forEach(person => {
            let chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = person.name;
            producersContainer.appendChild(chip);
        });
    } else {
        element.querySelector(".doc-producers").parentNode.remove();
    }

    if (doc.descriptors.length) {
        let descriptorsContainer = element.querySelector(".doc-descriptors");
        doc.descriptors.forEach(descriptor => {
            let chip = document.createElement("span");
            chip.className = "chip";
            if (descriptor.specification) {
                chip.textContent = descriptor.label + " (" + descriptor.specification + ")";
            } else {
                chip.textContent = descriptor.label;
            }
            descriptorsContainer.appendChild(chip);
        });
    } else {
        element.querySelector(".doc-descriptors").remove();
    }

    if (doc.opening) {
        element.querySelector(".doc-opening").innerHTML = OPENINGS[doc.opening];
    } else {
        element.querySelector(".doc-opening").parentNode.remove();
    }

    let empty = true;
    let facetsContainer = element.querySelector(".doc-facets");
    doc.facets.sort((a, b) => b.score - a.score);
    doc.facets.forEach(facet => {
        if (facet.score >= minScore) {
            let chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = facet.label + " #" + facet.score;
            facetsContainer.appendChild(chip);
            empty = false;
        }
    });
    if (empty) {
        facetsContainer.remove();
    }

    if (doc.relevant_words.length) {
        let relevantWordsContainer = element.querySelector(".doc-relevant-words");
        doc.relevant_words.forEach(word => {
            let chip = document.createElement("span");
            chip.className = "chip tooltip";
            chip.textContent = word.label;
            chip.setAttribute("data-tooltip", "tf-idf : " + word.score.toFixed(4));
            relevantWordsContainer.appendChild(chip);
        });
    } else {
        element.querySelector(".doc-relevant-words").remove();
    }
}

function loadDataset(dataset) {
    
    document.getElementById("modal-loading").classList.add("active");
    dataset.sort((a, b) => {
        if (a.diffusion_date < b.diffusion_date) {
            return -1;
        } else if (a.diffusion_date > b.diffusion_date) {
            return 1;
        } else {
            return 0;
        }
    });
    let container = document.getElementById("list");
    container.innerHTML = "";
    let templateDoc = document.getElementById("template-doc");
    dataset.forEach(doc => {
        let element = document.importNode(templateDoc.content, true);
        element.querySelector(".card").setAttribute("id", "doc-" + doc.doc_id);
        element.querySelector(".doc-title").textContent = doc.title;

        if (doc.links.inatheque_uri) {
            element.querySelector(".doc-inatheque").href = doc.links.inatheque_uri;
        } else {
            element.querySelector(".doc-inatheque").remove();
        }

        if (doc.links.madelen_uri) {
            element.querySelector(".doc-madelen").href = doc.links.madelen_uri;
        } else {
            element.querySelector(".doc-madelen").remove();
        }

        if (doc.links.lmdmfr_uri) {
            element.querySelector(".doc-lmdmfr").href = doc.links.lmdmfr_uri;
        } else {
            element.querySelector(".doc-lmdmfr").remove();
        }

        if (doc.links.youtube_uri) {
            if (doc.summary.beginning) {
                element.querySelector(".doc-youtube").href = doc.links.youtube_uri + "&t=" + doc.summary.beginning + "s";
            } else {
                element.querySelector(".doc-youtube").href = doc.links.youtube_uri;
            }
        } else {
            element.querySelector(".doc-youtube").remove();
        }

        if (doc.collection) {
            element.querySelector(".doc-collection").textContent = doc.collection;
        } else {
            element.querySelector(".doc-collection").remove();
        }

        if (doc.credits.author) {
            element.querySelector(".doc-author").textContent = doc.credits.author;
        } else {
            element.querySelector(".doc-author").remove();
        }

        if (doc.duration) {
            element.querySelector(".doc-duration").textContent = formatDuration(doc.duration);
        } else {
            element.querySelector(".doc-duration").remove();
        }

        if (doc.diffusion_date) {
            element.querySelector(".doc-date").textContent = formatDate(doc.diffusion_date);
        } else {
            element.querySelector(".doc-date").remove();
        }
        
        var loaded = false;
        element.querySelector("details").addEventListener("toggle", (event) => {
            if (!loaded) {
                loadDocData(doc);
                loaded = true;
                event.target.querySelector(".hide").classList.remove("hide");
            }
        });

        container.appendChild(element);
        
    });

    if (dataset.length == 0) {
        document.querySelector(".doc-count").textContent = "Aucun épisode affiché.";
    } else if (dataset.length == 1) {
        document.querySelector(".doc-count").textContent = "1 épisode affiché.";
    } else {
        document.querySelector(".doc-count").textContent = dataset.length + " épisodes affichés.";
    }

    document.getElementById("modal-loading").classList.remove("active");

}

function gatherLabels(dataset, getter) {
    let labels = {};
    dataset.forEach(doc => {
        getter(doc).forEach(value => {
            if (value) {
                if (!(value in labels)) {
                    labels[value] = 0;
                }
                labels[value]++;
            }
        });
    });
    return labels;
}

function populateSelect(dataset, getter, selectId) {
    let labels = gatherLabels(dataset, getter);
    let select = document.getElementById(selectId);
    Object.keys(labels).sort().forEach(label => {
        let option = document.createElement("option");
        option.value = label;
        option.innerHTML = label + " <small style='color: gold'>" + labels[label] + "</small>";
        select.appendChild(option);
    });
}

function setupAutocomplete(dataset, getter, selectId) {
    let labels = gatherLabels(dataset, getter);
    autocomplete(document.getElementById(selectId), labels);
}

function bindActionButtons() {
    document.getElementById("btn-top").addEventListener("click", (event) => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    document.getElementById("btn-bottom").addEventListener("click", (event) => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    });

    document.getElementById("btn-expand-all").addEventListener("click", (event) => {
        document.querySelectorAll("#list details").forEach(details => {
            details.open = true;
        });
    });

    document.getElementById("btn-collapse-all").addEventListener("click", (event) => {
        document.querySelectorAll("#list details").forEach(details => {
            details.open = false;
        });
    });
}

function setupForm(dataset) {
    setupAutocomplete(dataset, doc => [doc.credits.author], "input-author");
    setupAutocomplete(dataset, doc => {
        let values = [];
        doc.credits.directors.forEach(person => { values.push(person.name); });
        return values;
    }, "input-directors");
    setupAutocomplete(dataset, doc => {
        let values = [];
        doc.credits.producers.forEach(person => { values.push(person.name); });
        return values;
    }, "input-producers");
    setupAutocomplete(dataset, doc => {
        let values = [];
        doc.credits.cast.forEach(person => { values.push(person.name); });
        return values;
    }, "input-cast");
    setupAutocomplete(dataset, doc => {
        let values = [];
        doc.credits.crew.forEach(person => { values.push(person.name); });
        return values;
    }, "input-crew");
    setupAutocomplete(dataset, doc => {
        let values = [];
        doc.descriptors.forEach(item => { values.push(item.label); });
        return values;
    }, "input-descriptors");
    populateSelect(dataset, doc => {
        if (doc.opening) {
            return [OPENINGS[doc.opening]];
        } else {
            return [];
        }
    }, "input-opening");
    let minDiffusionDate = null;
    let maxDiffusionDate = null;
    let minDuration = null;
    let maxDuration = null;
    let maxFacetScore = null;
    let minCastLength = null;
    let maxCastLength = null;
    dataset.forEach(doc => {
        if (doc.diffusion_date) {
            if (!minDiffusionDate || doc.diffusion_date < minDiffusionDate) {
                minDiffusionDate = doc.diffusion_date;
            }
            if (!maxDiffusionDate || doc.diffusion_date > maxDiffusionDate) {
                maxDiffusionDate = doc.diffusion_date;
            }
        }
        if (doc.duration) {
            if (!minDuration || doc.duration < minDuration) {
                minDuration = doc.duration;
            }
            if (!maxDuration || doc.duration > maxDuration) {
                maxDuration = doc.duration;
            }
        }
        if (doc.facets.length) {
            doc.facets.forEach(facet => {
                if (!maxFacetScore || facet.score > maxFacetScore) {
                    maxFacetScore = facet.score;
                }
            });
        }
        if (doc.credits.cast.length) {
            if (!minCastLength || doc.credits.cast.length < minCastLength) {
                minCastLength = doc.credits.cast.length;
            }
            if (!maxCastLength || doc.credits.cast.length > maxCastLength) {
                maxCastLength = doc.credits.cast.length;
            }
        }
    });
    document.getElementById("input-date-min").min = minDiffusionDate;
    document.getElementById("input-date-min").max = maxDiffusionDate;
    document.getElementById("input-date-min").placeholder = "Défaut : " + minDiffusionDate;
    document.getElementById("input-date-max").min = minDiffusionDate;
    document.getElementById("input-date-max").max = maxDiffusionDate;
    document.getElementById("input-date-max").placeholder = "Défaut : " + maxDiffusionDate;
    document.getElementById("input-duration-min").min = Math.round(minDuration / 60);
    document.getElementById("input-duration-min").max = Math.round(maxDuration / 60);
    document.getElementById("input-duration-min").placeholder = Math.round(minDuration / 60);
    document.getElementById("input-duration-max").min = Math.round(minDuration / 60);
    document.getElementById("input-duration-max").max = Math.round(maxDuration / 60);
    document.getElementById("input-duration-max").placeholder = Math.round(maxDuration / 60);
    document.getElementById("input-facets-bound").min = 1;
    document.getElementById("input-facets-bound").max = maxFacetScore;
    document.getElementById("input-facets-bound").placeholder = 3;
    document.getElementById("input-cast-min").min = minCastLength;
    document.getElementById("input-cast-min").max = maxCastLength;
    document.getElementById("input-cast-min").placeholder = minCastLength;
    document.getElementById("input-cast-max").min = minCastLength;
    document.getElementById("input-cast-max").max = maxCastLength;
    document.getElementById("input-cast-max").placeholder = maxCastLength;
}

function readInputRegex(inputId) {
    let value = document.getElementById(inputId).value;
    if (value.trim() == "") {
        return null;
    } else {
        return new RegExp(value, "i");
    }
}

function readInputValue(inputId, casting) {
    let value = document.getElementById(inputId).value;
    if (value.trim() == "") {
        return null;
    } else {
        if (casting) {
            return casting(value);
        } else {
            return value.trim();
        }
    }
}

function readMultipleSelect(selectId) {
    let values = [];
    document.getElementById(selectId).querySelectorAll("option").forEach(option => {
        if (option.selected) {
            values.push(option.value);
        }
    });
    return values;
}

function bindFormSubmit(dataset) {
    document.getElementById("form").addEventListener("submit", (event) => {
        event.preventDefault();

        // document.querySelector("#form details").open = false;

        let newDataset = [];

        let filterCollection = document.getElementById("input-collection").value;
        if (filterCollection == "Aucun filtre") {
            filterCollection = null;
        }
        let filterTitle = readInputRegex("input-title");
        let filterPitch = readInputRegex("input-pitch");
        let filterAuthors = readInputValue("input-author");
        let filterCast = readInputValue("input-cast");
        let filterCrew = readInputValue("input-crew");
        let filterDescriptors = readInputValue("input-descriptors");
        let filterDirectors = readInputValue("input-directors");
        let filterProducers = readInputValue("input-producers");
        let filterFacets = readMultipleSelect("input-facets");
        let filterDateMin = readInputValue("input-date-min")
        let filterDateMax = readInputValue("input-date-max");
        let filterCastMin = readInputValue("input-cast-min", parseInt);
        let filterCastMax = readInputValue("input-cast-max", parseInt);
        let filterDurationMin = readInputValue("input-duration-min", parseInt);
        let filterDurationMax = readInputValue("input-duration-max", parseInt);
        let filterFacetsBound = readInputValue("input-facets-bound", parseInt);
        let filterRelevantWord = readInputValue("input-relevant-words");
        let filterOpening = readMultipleSelect("input-opening");
        let filterSource = readMultipleSelect("input-source");

        for (let i = 0; i < dataset.length; i++) {
            let doc = dataset[i];
            if (filterSource.length) {
                let keep = true;
                filterSource.forEach(source => {
                    if (!doc.links[source + "_uri"]) {
                        keep = false;
                    }
                });
                if (!keep) {
                    continue;
                }
            }
            if (filterTitle && !doc.title.match(filterTitle)) continue;
            if (filterPitch && (!doc.summary.pitch || !doc.summary.pitch.match(filterPitch))) continue;
            if (filterCollection && normalize(doc.collection) != normalize(filterCollection)) continue;
            
            // if (filterAuthors.length && !filterAuthors.includes(doc.credits.author)) continue;
            if (filterAuthors && normalize(filterAuthors) != normalize(doc.credits.author)) continue;

            // if (!checkArrayField(doc, filterDirectors, doc => doc.credits.directors, item => item.name)) continue;
            if (filterDirectors && !checkArrayField(doc, [filterDirectors], doc => doc.credits.directors, item => item.name)) continue;
            
            // if (!checkArrayField(doc, filterProducers, doc => doc.credits.producers, item => item.name)) continue;
            if (filterProducers && !checkArrayField(doc, [filterProducers], doc => doc.credits.producers, item => item.name)) continue;

            // if (!checkArrayField(doc, filterCast, doc => doc.credits.cast, item => item.name)) continue;
            if (filterCast && !checkArrayField(doc, [filterCast], doc => doc.credits.cast, item => item.name)) continue;

            // if (!checkArrayField(doc, filterCrew, doc => doc.credits.crew, item => item.name)) continue;
            if (filterCrew && !checkArrayField(doc, [filterCrew], doc => doc.credits.crew, item => item.name)) continue;
            
            // if (!checkArrayField(doc, filterDescriptors, doc => doc.descriptors, item => item.label)) continue;
            if (filterDescriptors && !checkArrayField(doc, [filterDescriptors], doc => doc.descriptors, item => item.label)) continue;

            if (filterCastMin && doc.credits.cast.length < filterCastMin) continue;
            if (filterCastMax && doc.credits.cast.length > filterCastMax) continue;
            if (filterDurationMin && (!doc.duration || Math.round(doc.duration / 60) < filterDurationMin)) continue;
            if (filterDurationMax && (!doc.duration || Math.round(doc.duration / 60) > filterDurationMax)) continue;
            if (filterDateMin && doc.diffusion_date < filterDateMin) continue;
            if (filterDateMax && doc.diffusion_date > filterDateMax) continue;
            if (filterOpening.length && !filterOpening.includes(OPENINGS[doc.opening])) continue;


            if (filterRelevantWord && !checkArrayField(doc, [filterRelevantWord], doc => doc.relevant_words, item => item.label)) continue;

            if (filterFacets.length) {
                let minScore = 3;
                if (filterFacetsBound) {
                    minScore = filterFacetsBound;
                }
                let keep = true;
                for (let k = 0; k < filterFacets.length; k++) {
                    let found = false;
                    for (let j = 0; j < doc.facets.length; j++) {
                        if (doc.facets[j].score >= minScore && doc.facets[j].label == filterFacets[k]) {
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        keep = false;
                        break;
                    }
                }
                if (!keep) {
                    continue;
                }
            }

            newDataset.push(doc);
        }

        loadDataset(newDataset);

    });
}

function onLoad() {
    requestDataset(dataset => {
        loadDataset(dataset);
        bindActionButtons();
        setupForm(dataset);
        bindFormSubmit(dataset);
    });
}

window.addEventListener("load", onLoad);
