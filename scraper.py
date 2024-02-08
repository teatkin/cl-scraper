#!/usr/bin/env python3

from tomllib import load
from typing import List, Dict

from requests import *

URL = "https://events.rainfocus.com/api/search"

UA = "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"

HEADERS = {
    "Accept-Language": "en-US,enlq=0.5",
    "Referer": "https://ciscolive.com/",
    "rfWidgetId": "",
    "rfApiProfileId": "",
    "rfAuthToken": "",
    "Origin": "https://ciscolive.com",
    "Connection": "keep-alive",
    "Cookie": "",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "TE": "trailers",
    "User-Agent": UA
}

PARAMS = {
    "type": "session",
    "browserTimezone": "Europe/Amsterdam",
    "catalogDisplay": "list"
}


def get_course_codes(data: Dict) -> List:
    total_courses = data["totalSearchItems"]
    course_lists = [data["sectionList"][0]["items"]]

    # The site paginates the course data, so some jank to go fetch it all
    list_from = 50
    while list_from < total_courses:
        params = PARAMS
        params["from"] = str(list_from)
        course_lists.append(post(URL, data=params, headers=HEADERS, timeout=120).json()["items"])
        list_from += 50

    course_codes = []
    for courses in course_lists:
        for course in courses:
            course_codes.append(course["code"])

    return course_codes


def get_pdf(course_code: str) -> bool:
    headers = {
        "Referer": "https://www.ciscolive.com/emea/learn/session-catalog.html",
        "Accept-Language": "en-US,enlq=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers",
        "User-Agent": UA
    }

    pdf = get(f"https://www.ciscolive.com/c/dam/r/ciscolive/emea/docs/2024/pdf/{course_code}.pdf", headers=headers, timeout=120)

    if pdf.status_code == 404:
        return False

    with open(f"pdfs/{course_code}.pdf", "wb+") as f:
        f.write(pdf.content)

    return True

def main():
    """Main execution environment"""
    with open("config.toml", "rb+") as cfg:
        config = load(cfg)
        HEADERS["rfWidgetId"] = config["widget-id"]
        HEADERS["rfApiProfileId"] = config["api-profile-id"]
        HEADERS["rfAuthToken"] = config["auth-token"]
        HEADERS["Cookie"] = config["cookie"]

    r = post(URL, data=PARAMS, headers=HEADERS, timeout=120)
    course_codes = get_course_codes(r.json())

    got_pdf = 0

    for course in course_codes:
        if get_pdf(course):
            got_pdf += 1

    print(f"Got {got_pdf} PDFs, from a total of {len(course_codes)} courses")

if __name__ == "__main__":
    main()
