from urllib.parse import ParseResult, parse_qs, urlunparse

from lxml import html as html


def youtube_iframe(parse_result: ParseResult) -> html.HtmlElement:
    qs = parse_qs(parse_result.query)
    iframe = html.Element("iframe")
    iframe.attrib.update(
        {
            "width": "560",
            "height": "315",
            "src": f"https://www.youtube.com/embed/{qs['v'][0]}",
            "title": "YouTube video player",
            "frameborder": "0",
            "allow": "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
            "allowfullscreen": None,
        }
    )
    return iframe


def replit_iframe(parse_result: ParseResult) -> html.HtmlElement:
    parse_result = parse_result._replace(query="embed=true")
    iframe = html.Element("iframe")
    iframe.attrib.update(
        {
            "width": "100%",
            "height": "500",
            "frameborder": "0",
            "src": urlunparse(parse_result),
        }
    )
    return iframe


def codepen_iframe(parse_result: ParseResult) -> html.HtmlElement:
    parse_result = parse_result._replace(
        query="default-tab=html%2Cresult",
        path=parse_result.path.replace("/pen/", "/embed/"),
    )
    iframe = html.Element("iframe")
    iframe.attrib.update(
        {
            "width": "100%",
            "height": "300",
            "frameborder": "no",
            "loading": "lazy",
            "allowtransparency": None,
            "allowfullscreen": None,
            "src": urlunparse(parse_result),
        }
    )
    return iframe
