import re
from urllib.parse import ParseResult, parse_qs, urlparse, urlunparse

import lxml.html as html
from pandocfilters import RawInline


class Embedder:
    @staticmethod
    def format_domain(url) -> str:
        return re.sub(r"\.", "_", url)

    @staticmethod
    def format_iframe(iframe: html.HtmlElement):
        return RawInline("html", html.tostring(iframe, encoding="unicode"))

    def www_youtube_com(self, parse_result: ParseResult) -> html.HtmlElement:
        qs = parse_qs(parse_result.query)
        iframe = html.Element("iframe")
        iframe.attrib.update(
            {
                "width": "560",
                "height": "315",
                "src": f"https://www.youtube.com/embed/{qs['v'][0]}",
                "title": "YouTube video player",
                "allow": "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen",
                "frameBorder": "0",
            }
        )
        return self.format_iframe(iframe)

    def replit_com(self, parse_result: ParseResult) -> html.HtmlElement:
        parse_result = parse_result._replace(query="embed=true")
        iframe = html.Element("iframe")
        iframe.attrib.update(
            {
                "width": "100%",
                "height": "500",
                "frameBorder": "0",
                "src": urlunparse(parse_result),
            }
        )
        return self.format_iframe(iframe)

    def codepen_io(self, parse_result: ParseResult) -> html.HtmlElement:
        parse_result = parse_result._replace(
            query="default-tab=html%2Cresult",
            path=parse_result.path.replace("/pen/", "/embed/"),
        )
        iframe = html.Element("iframe")
        iframe.attrib.update(
            {
                "width": "100%",
                "height": "300",
                "frameBorder": "0",
                "loading": "lazy",
                "allow": "fullscreen",
                "src": urlunparse(parse_result),
            }
        )
        return self.format_iframe(iframe)

    def __call__(self, key, value, format, meta):
        if key == "Link":
            parse_result = urlparse(value[2][0])
            try:
                return getattr(self, self.format_domain(parse_result.netloc))(
                    parse_result
                )
            except AttributeError:
                pass
