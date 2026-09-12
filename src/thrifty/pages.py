"""Shared HTML shell for the server-rendered form pages."""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Thrifty &mdash; {title}</title>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"
  />
</head>
<body>
  <main class="container" style="max-width: {width}">
    <h1>Thrifty</h1>
    {intro}
    <form method="post">
      {fields}
      {error}
      <button type="submit">{submit}</button>
    </form>
    {footer}
  </main>
</body>
</html>
"""


def form_page(
    *,
    title: str,
    fields: str,
    submit: str,
    intro: str = "",
    error: str = "",
    footer: str = "",
    width: str = "24rem",
) -> str:
    return TEMPLATE.format(
        title=title,
        fields=fields,
        submit=submit,
        intro=intro,
        error=f'<p style="color: var(--pico-del-color)">{error}</p>' if error else "",
        footer=footer,
        width=width,
    )
