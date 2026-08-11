# BI handoff contract

[`mart-schema.yml`](mart-schema.yml) is the frozen consumption contract for the
certified reporting marts. It is versioned independently from the dbt implementation
and is the boundary consumed by the Power BI semantic model.

The contract records the object grain, business purpose, complete ordered column
schema, official reference row count, and quality controls. PostgreSQL tables are
created by dbt using `create table as`, so `nullable` expresses the governed semantic
contract rather than a physical PostgreSQL `NOT NULL` constraint. dbt tests and the
reporting-mart certification command enforce the stated guarantees.
