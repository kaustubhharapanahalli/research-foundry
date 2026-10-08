# Venue style kit

`make venue` fetches the venue's style files here, from the venue's own
site. Commit them, so Overleaf can build the paper. The template ships no
kit: venues do not state a licence for redistributing theirs.
{%- if cookiecutter.venue == "icml" %}

For ICML, `make venue` fetches the kit for `venue_year` from ICML's site, and
refuses if that year's kit is not published yet.
{%- endif %}
