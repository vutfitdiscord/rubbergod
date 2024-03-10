from dataclasses import dataclass
from enum import Enum
from typing import List
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


class Semester(Enum):
    LS = "Letní"
    ZS = "Zimní"
    LSZS = "Zimní, Letní"


@dataclass
class SportData:
    name: str
    shortcut: str
    semester: Semester
    subject_id: int

    @classmethod
    def from_dict(cls, id: int, data: dict):
        return cls(data["name"], data["shortcut"], data["semester"], id)


class VutSports:
    @staticmethod
    def get_page(session: requests.Session, page: int) -> bytes:
        with session.get(f"https://www.cesa.vutbr.cz/studenti/sporty?str={page}") as res:
            return res.content

    @staticmethod
    def parse_sports(soup: BeautifulSoup, output_dict: dict) -> None:
        subject_list = soup.find("ul", {"class": "c-subjects__list"})
        subjects = subject_list.find_all("li")
        if not subjects:
            return

        for subject in subjects:
            title = subject.find("a", {"class": "b-subject__link"})
            title_splits = str(title.get_text()).split(" – ")
            name = title_splits[0]
            shortcut = title_splits[-1]

            annotation = subject.find("p", {"class": "b-subject__annot"})
            annotation_items = annotation.find_all("span")

            semester_string = annotation_items[1].get_text()
            semester = Semester.LS if "letní" in semester_string.lower() else Semester.ZS

            schedule_annotation = annotation_items[-1].find("a")
            schedule_url = schedule_annotation["href"]

            parsed_url = urlparse(schedule_url)
            subject_id = parse_qs(parsed_url.query)["predmet_id"][0]

            if subject_id in output_dict:
                saved_semester = output_dict.get(subject_id).get("semester")
                if (saved_semester == Semester.ZS and semester == Semester.LS) or (
                    saved_semester == Semester.LS and semester == Semester.ZS
                ):
                    output_dict[subject_id]["semester"] = Semester.LSZS
            else:
                output_dict[subject_id] = {
                    "name": name,
                    "shortcut": shortcut,
                    "semester": semester,
                    "subject_id": subject_id,
                }

    @staticmethod
    def get_sports() -> List[SportData]:
        session = requests.Session()

        data = VutSports.get_page(session, 1)

        soup = BeautifulSoup(data, "html.parser")
        pagination_list = soup.find("ul", {"class": "pagination__list"})
        pagination_list_items = pagination_list.find_all("li")
        page_indexes = [int(item.get_text()) for item in pagination_list_items if item.get_text().isnumeric()]
        number_of_pages = max(page_indexes)

        output_dict = {}
        VutSports.parse_sports(soup, output_dict)

        if number_of_pages > 1:
            for page_index in range(2, number_of_pages):
                data = VutSports.get_page(session, page_index)
                soup = BeautifulSoup(data, "html.parser")
                VutSports.parse_sports(soup, output_dict)

        session.close()

        output = []
        for id, data in output_dict.items():
            output.append(SportData.from_dict(id, data))

        return output
