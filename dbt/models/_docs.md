{% docs fixture_boundary %}
The implemented graph has been materialized with synthetic contract fixtures and
with mocked official-shaped inputs in an isolated integration database. A model may
contain `is_fixture = true` rows until the bounded official source gate succeeds.
Fixture validation proves engineering behavior; it is not evidence about Brazilian
banks or the economy.
{% enddocs %}

{% docs source_evidence %}
Source URLs, checksums, source generation dates, retrieval timestamps and dlt load
identifiers are retained so every canonical row can be traced to a specific acquired
file or API response. Failed acquisitions remain outside analytical models.
{% enddocs %}

{% docs cosif_active_selection %}
COSIF files can be republished. The core keeps every manifested checksum but selects
one complete version per reporting period using source generation time, retrieval
time and checksum as deterministic tie-breakers. Restatement analysis is deferred;
downstream facts use only the selected version.
{% enddocs %}

{% docs macro_month_alignment %}
Each SGS value retains its native observation date and receives an explicit calendar
month key. No causal inference or cross-series aggregation happens in staging. The
governed registry defines later semantic treatment for each of the five series.
{% enddocs %}
