import re
import string
from dataclasses import asdict, dataclass

import jellyfish
import numpy as np

from common.report_processor.abstract_report_processor import AbstractReportProcessor


@dataclass
class Term:
    candidate: str
    value: str
    type: str
    matched_term: str


class AdvancedReportProcessor(AbstractReportProcessor):
    WORDCOUNT_THRESHOLD = 4
    SIMILARITY_THRESHOLD = 0.2

    STOP_WORDS = ["\t", ":", "(", ")", '"']
    MEASUREMENT_UNITS = [
        "%",
        "cm/sec",
        "Hgmm",
        "hgmm",
        "Hgm",
        "hgm",
        "Hmm",
        "hmm",
        "mm",
        "cm",
        "Hg",
        "hg",
        "m/sec",
        "m/s",
        "msec",
        "ms",
        "/sec",
        "sec",
        "/s",
        "db",
    ]
    CONJUNCTIONS = ["és", "es", "az", "a", "ill", "illetve"]

    COLUMNS = ["docID", "paragID", "term_candidate", "value", "type", "matched_term"]

    def process(self, text):
        paragraphs = text.split("\n")
        prepared = {
            idx: self._prepare(paragraph) for idx, paragraph in enumerate(paragraphs)
        }

        extracted = {
            idx: self._extract(" ", idx, value["clean"], value["work"])
            for idx, value in prepared.items()
        }

        refined = {idx: self._refine(value) for idx, value in extracted.items()}

        self._processed_text = refined

    def _prepare(self, text):
        # TODO: refine
        text_clean = text

        # Unify stop words
        for kif in self.STOP_WORDS:
            text_clean = text_clean.replace(kif, " ")

        text_clean = text_clean.replace("cm2", "negyzetcm")
        text_clean = text_clean.replace("mm2", "negyzetmm")

        # Insert space in front of number
        for idx, char in enumerate(text_clean):
            if idx < len(text_clean) - 2:
                if (
                    text_clean[idx + 1] in string.digits
                    and text_clean[idx] != " "
                    and text_clean[idx] not in string.digits
                ):
                    if idx == 0:
                        text_clean = text_clean[: idx + 1] + " " + text_clean[idx + 1 :]
                    else:
                        if text_clean[idx - 1] not in string.digits:
                            text_clean = (
                                text_clean[: idx + 1] + " " + text_clean[idx + 1 :]
                            )

        text_clean = " ".join(text_clean.split())

        text_clean = text_clean.replace("Hg mm", "Hgmm")

        # measures
        for meas in self.MEASUREMENT_UNITS:
            text_clean = text_clean.replace(" " + meas, meas)
            text_clean = text_clean.replace(meas + ".", meas)
            text_clean = text_clean.replace(meas + ",", meas)
            text_clean = text_clean.replace(meas + ";", meas)

        # kotesek
        # tempstr = " ".join(tempstr.split())
        text_clean = text_clean.replace(" -", "-")
        text_clean = text_clean.replace("- ", "-")
        text_clean = text_clean.replace(" +", "+")
        text_clean = text_clean.replace("+ ", "+")
        text_clean = text_clean.replace(" *", "*")
        text_clean = text_clean.replace("* ", "*")
        text_clean = text_clean.replace(" x", "x")
        text_clean = text_clean.replace("x ", "x")
        text_clean = text_clean.replace(" /", "/")
        text_clean = text_clean.replace("/ ", "/")
        text_clean = text_clean.replace(" \\", "\\")
        text_clean = text_clean.replace("\\ ", "\\")
        text_clean = text_clean.replace("~ ", "~")
        text_clean = text_clean.replace("= ", "=")
        text_clean = text_clean.replace(" =", "=")

        # kb elemek kötése
        text_clean = text_clean.replace("KB ", "kb")
        text_clean = text_clean.replace("Kb ", "kb")
        text_clean = text_clean.replace("CCA ", "cca")
        text_clean = text_clean.replace("Cca ", "cca")
        text_clean = text_clean.replace("CA ", "ca")
        text_clean = text_clean.replace("Ca ", "ca")
        text_clean = text_clean.replace("kB ", "kb")
        text_clean = text_clean.replace("kb ", "kb")
        text_clean = text_clean.replace("kb. ", "kb")
        text_clean = text_clean.replace("cca ", "kb")
        text_clean = text_clean.replace("cca. ", "kb")
        text_clean = text_clean.replace("ca ", "kb")
        text_clean = text_clean.replace("ca. ", "kb")
        text_clean = text_clean.replace("becsült ", "kb")
        text_clean = text_clean.replace("becsult ", "kb")
        text_clean = text_clean.replace("becs ", "kb")

        text_work = text_clean
        for digit in string.digits:
            text_work = text_work.replace(digit, "ß")

        return {"clean": text_clean, "work": text_work}

    def _extract(self, docID, paragID, text_work, text_clean):
        # TODO: refine
        words_work = text_work.split(" ")
        words_clean = text_clean.split(" ")

        for idx, word in enumerate(words_work):
            if "ß" in word:
                words_work[idx] = "--num--"

            # Hiányzó értékek megtalálása
            if not any(char.isdigit() for char in words_clean[idx]):
                words_clean[idx] = re.sub(
                    r"({})".format("|".join(self.MEASUREMENT_UNITS)),
                    r" \1",
                    words_clean[idx],
                )

            for meas in self.MEASUREMENT_UNITS:
                words_work[idx] = (
                    words_work[idx].replace(meas, " --num--")
                    if meas != "mm"
                    else words_work[idx]
                )
                words_work[idx] = (
                    words_work[idx].replace(meas, " --num--")
                    if (meas == "mm" and ("MMV" not in words_work[idx].split()))
                    else words_work[idx]
                )

        words_work = " ".join(words_work).split(" ")
        words_clean = " ".join(words_clean).split(" ")

        terms1_actual = []
        terms2_actual = []

        # kifejezesek és értékek keresése
        # beleértve azt az esetet, hogy 1 kifejezéshez több érték tartozik
        tempstr_old = ""
        idx_term_start = 0
        idx_term_stop = 0
        idx_num_start = 0
        idx_num_stop = 0
        for idx1, elem1 in enumerate(words_work):
            if idx1 >= idx_num_stop:
                tempstr = ""
                tempvalue = ""
                if elem1 == "--num--":
                    idx_term_start = idx_num_stop
                    idx_term_stop = idx1
                    idx_num_start = idx1
                    idx_num_stop = idx1 + 1
                    for idx2, elem2 in enumerate(words_work[idx1 + 1 :]):
                        if elem2 != "--num--":
                            idx_num_stop = idx1 + idx2 + 1
                            break
                        else:
                            idx_num_stop = idx1 + idx2 + 2
                    for i in range(idx_term_start, idx_term_stop - 1):
                        tempstr = tempstr + " " + words_clean[i]
                    for j in range(idx_num_start - 1, idx_num_stop):
                        tempvalue = tempvalue + " " + words_clean[j]
                    if idx_num_stop - idx_num_start == 1:
                        tipus = 1
                        tipus_text = "term1"
                    else:
                        tipus = 2
                        tipus_text = "term12"

                    # term refinement
                    # ha van a szóban mertekegyseg, akkor az üres adat

                    # if False:
                    #     if len(tempstr) > 0:
                    #         for meas in measures:
                    #             tempstr = (
                    #                 tempstr.replace(meas, "")
                    #                 if meas != "mm"
                    #                 else tempstr
                    #             )
                    #             tempstr = (
                    #                 tempstr.replace(meas, "")
                    #                 if (meas == "mm" and ("MMV" not in tempstr.split()))
                    #                 else tempstr
                    #             )
                    #
                    #         tempstr = tempstr.replace(".", " ")
                    #         tempstr = tempstr.replace(",", " ")
                    #         tempstr = tempstr.replace("=", " ")
                    #
                    #         tempstr = tempstr.lstrip()
                    #         tempstr = tempstr[2:] if tempstr[:2] == "az" else tempstr
                    #         tempstr = tempstr[2:] if tempstr[:2] == "Az" else tempstr
                    #         tempstr = tempstr[2:] if tempstr[:2] == "AZ" else tempstr
                    #         tempstr = tempstr.lstrip()
                    #
                    #         tempstr = tempstr[3:] if tempstr[:2] == "A--" else tempstr
                    #         tempstr = tempstr[3:] if tempstr[:2] == "A-" else tempstr
                    #         tempstr = tempstr.lstrip()
                    #
                    #         tempstr = " ".join(tempstr.split())
                    #
                    #     tempvalue = tempvalue.lstrip()

                    # öszzefüggő kif-ertek-kif-ertek kifejezések finomítása - 1
                    if (
                        (("sys" in tempstr) or ("sis" in tempstr))
                        and len(tempstr.split()) == 1
                        and len(tempstr_old) > 0
                    ):
                        szo = tempstr_old.split()
                        if len(szo) <= self.WORDCOUNT_THRESHOLD:
                            for kotoszo in self.CONJUNCTIONS:
                                szo.remove(kotoszo) if kotoszo in szo else szo
                            tempstr_old = " ".join(szo)
                            words_old = tempstr_old.split(" ")
                            ptc = [
                                idx for idx, w in enumerate(words_old) if "dias" in w
                            ]

                            if len(ptc) == 1:
                                words_old[ptc[0]] = "syst"
                                tempstr = " ".join(words_old)
                                tipus_text = "term22"
                                terms1_actual[-1][4] = tipus_text
                            else:
                                tempstr = "ERROR: nem egyértelmű kifejezés!"

                    # öszzefüggő kif-ertek-kif-ertek kifejezések finomítása - 2
                    if (
                        1
                        - (
                            jellyfish.jaro_winkler_similarity(
                                tempstr, "csúcsi nézetből"
                            )
                        )
                        <= self.SIMILARITY_THRESHOLD
                        and len(tempstr) > 0
                        and len(tempstr_old) > 0
                    ):
                        tempstr = tempstr_old + " " + tempstr
                        tipus_text = "term22"
                        if (
                            len(terms1_actual) > 0
                        ):  # erre azért van szükség, mert ha előtte hiba van, akkor a terms1_actual üres lehet (p.9817)
                            terms1_actual[-1][4] = tipus_text  # 2

                    # uj termbejegyzés létrehozása
                    hossz = len(tempstr.split())
                    new_term = {}
                    if tipus == 1:
                        if hossz <= self.WORDCOUNT_THRESHOLD:
                            new_term = Term(
                                candidate=tempstr.strip(),
                                value=tempvalue.strip(),
                                type=tipus_text,
                                matched_term="",
                            )
                        else:
                            new_term = Term(
                                candidate=tempstr.strip(),
                                value=tempvalue.strip(),
                                type="noterm",
                                matched_term="",
                            )
                        terms1_actual.append(asdict(new_term))
                    else:
                        new_term = Term(
                            candidate=tempstr.strip(),
                            value=tempvalue.strip(),
                            type=tipus_text,
                            matched_term="",
                        )
                        terms2_actual.append(asdict(new_term))

                    tempstr_old = tempstr

        return {"terms1": terms1_actual, "terms2": terms2_actual}

    def _refine(self, text):
        kif_parok = [["septum", "hátsófal", "diast"]]

        to_remove = []

        for kif_par in kif_parok:
            for idx, value in enumerate(text["terms2"]):
                [success, kif1, kif2, value1, value2] = self._term22_refinement(
                    value, kif_par
                )
                if success:
                    to_remove.append(idx)
                    text["terms1"].append(
                        ["dokID", "paragID", kif1, value1, "term12", None]
                    )
                    text["terms1"].append(
                        ["dokID", "paragID", kif2, value2, "term12", None]
                    )

            for idx in sorted(to_remove, reverse=True):
                del text["terms2"][idx]
        return text

    def _term22_refinement(self, lst, kif_par):
        text = lst[2]
        value = lst[3]
        success = False
        kif1 = ""
        kif2 = ""
        value1 = ""
        value2 = ""

        if len(text) != 0:
            # stopszavak törlése
            for kif in self.STOP_WORDS:
                text = text.replace(kif, "")
            text = text.replace(
                ".", ""
            )  # nincs benne a stopszavakba, de nem is szabad belevenni

            # kotoszavak törlése
            text_words = text.split()
            for kotoszo in self.CONJUNCTIONS:
                text_words.remove(kotoszo) if kotoszo in text_words else text_words
            text = " ".join(text_words)

            # computing distances
            dist = np.zeros((3, len(text_words)))
            i = 0
            for item in kif_par:
                j = 0
                for word in text_words:
                    dist[i, j] = 1 - (jellyfish.jaro_winkler(item, word))
                    j = j + 1
                i = i + 1

            # min values and args
            min_t1 = min(dist[0, :])
            min_t2 = min(dist[1, :])
            min_t3 = min(dist[2, :])
            if len(np.where(dist[0, :] == min_t1)[0]) == 1:
                minpos_t1 = int(np.where(dist[0, :] == min_t1)[0])
            else:
                return success, kif1, kif2, value1, value2
            if len(np.where(dist[1, :] == min_t2)[0]) == 1:
                minpos_t2 = int(np.where(dist[1, :] == min_t2)[0])
            else:
                return success, kif1, kif2, value1, value2
            if len(np.where(dist[2, :] == min_t3)[0]) == 1:
                minpos_t3 = int(np.where(dist[2, :] == min_t3)[0])
            else:
                return success, kif1, kif2, value1, value2

            value = value.split()
            value1 = value[0]
            value2 = value[1]

            if max(min_t1, min_t2, min_t3) <= self.SIMILARITY_THRESHOLD:
                success = True
                kif1 = text_words[minpos_t1] + " " + text_words[minpos_t3]
                kif2 = text_words[minpos_t2] + " " + text_words[minpos_t3]
                if minpos_t1 > minpos_t2:
                    value_temp = value1
                    value1 = value2
                    value2 = value_temp

        return success, kif1, kif2, value1, value2
