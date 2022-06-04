import abc
from itertools import groupby
from urllib.parse import quote, urlencode

import lxml.html as html
import requests
from pandocfilters import Para, RawBlock, RawInline, stringify


class BionicException(Exception):
    pass


class BionicBase(abc.ABC):
    @abc.abstractmethod
    def convert(self, value: str) -> requests.Response:
        ...

    def process_str(self, value):
        resp = self.convert(value)

        if resp.status_code == 429:
            raise BionicException("rate limited")

        tree = html.fragment_fromstring(resp.content)
        for c in tree.xpath("//comment()"):
            c.getparent().remove(c)
        for s in tree.xpath("//*[@style]"):
            del s.attrib["style"]

        (root,) = tree.xpath('//div[contains(@class, "bionic-reader-container")]')
        return (
            root.text.lstrip()
            + "".join(html.tostring(e, encoding="unicode") for e in root.iterchildren())
            + root.tail.rstrip()
        )

    def __call__(self, key, value, format, meta):
        try:
            match key:
                case "Plain":
                    return RawBlock("html", self.process_str(stringify(value)))
                case "Para":
                    result = []

                    for is_str, group in groupby(
                        value, key=lambda v: v["t"] in ("Str", "Space", "SoftBreak")
                    ):
                        if is_str:
                            lg = list(group)
                            if lg[0]["t"] == "Space":
                                result.append(lg.pop(0))
                            result.append(
                                RawInline("html", self.process_str(stringify(lg)))
                            )
                        else:
                            result.extend(group)

                    return Para(result)
        except BionicException:
            pass


class Bionic(BionicBase, requests.Session):
    def __init__(self, api_key: str):
        super().__init__()
        self.headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-RapidAPI-Host": "bionic-reading1.p.rapidapi.com",
                "X-RapidAPI-Key": api_key,
            }
        )

    def convert(self, value):
        return self.post(
            "https://bionic-reading1.p.rapidapi.com/convert",
            data=urlencode(
                {
                    "content": value,
                    "response_type": "html",
                    "request_type": "html",
                    "fixation": "1",
                    "saccade": "10",
                },
                quote_via=quote,
            ),
        )
