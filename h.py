"""Very simple HTML generator. Usage:

    >>> str(p["Hello, world!"])
    <<< '<p>Hello, world!</p>'

    >>> str(input(type="text", name="username"))
    <<< '<input type="text" name="username" />'

    >>> str(form(action="/submit", method="post")[button["Submit"]])
    <<< '<form action="/submit" method="post"><button>Submit</button></form>'

    If you want to add the 'class' attribute, because 'class' is a reserved word in
    Python, use `class_` instead:

    >>> str(p(class_="red")["Hello, world!"])
    <<< '<p class="red">Hello, world!</p>'
"""

from xml.sax.saxutils import escape


class h:
    def __init__(self, tag: str, *args, **kwargs):
        self.tag = tag
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.__class__(
            self.tag, *(self.args + args), **{**self.kwargs, **kwargs}
        )

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return self.__class__(self.tag, *(self.args + key), **self.kwargs)
        else:
            return self.__class__(self.tag, *(self.args + (key,)), **self.kwargs)

    def __str__(self):
        attributes = []
        for key, value in self.kwargs.items():
            if key == "class_":
                attributes.append(f'class="{value}"')
            else:
                attributes.append(f'{key}="{value}"')
        attributes = " ".join(attributes)

        content = []
        for arg in self.args:
            if isinstance(arg, str):
                content.append(escape(arg))
            elif not arg:
                continue
            else:
                content.append(str(arg))

        if not self.tag:  # Fragment
            return "".join(content)

        if self.args:
            return "".join(
                [
                    f"<{self.tag}",
                    f" {attributes}" if attributes else "",
                    f">",
                    "".join(content),
                    f"</{self.tag}>",
                ]
            )
        else:
            return "".join(
                [
                    f"<{self.tag}",
                    f" {attributes}" if attributes else "",
                    f" />",
                ]
            )


body = h("body")
button = h("button")
code = h("code")
form = h("form")
fragment = h("")
h1 = h("h1")
h2 = h("h2")
h3 = h("h3")
head = h("head")
title = h("title")
html = h("html")
input = h("input")
li = h("li")
p = h("p")
pre = h("pre")
textarea = h("textarea")
ul = h("ul")
link = h("link")
