Learnings from Claude about connecting to semantic models via the connect-pbid skill

- TOM/ADOMD DLLs are in the GAC even without nuget: `%WINDIR%\Microsoft.NET\assembly\GAC_MSIL\Microsoft.AnalysisServices.{Core,Tabular,AdomdClient}\v4.0_15.0.0.0__89845dcd8080cc91\*.dll`. Add-Type these paths directly. The Store PBI Desktop `bin` (WindowsApps) is ACL-locked — don't try to load from there.
- DAX VAR names `Current` and `Prior` are rejected by this parser: the measure silently compiles to a stub and every query returns `Failed to resolve name 'SYNTAXERROR'` (even though the same logic works inline and TOM shows correct expression text). Use `CurVal`/`PriorVal` instead. Multi-line CRLF VAR/RETURN is fine — newlines are NOT the problem.
- Setting `Measure.Expression` to text identical to the stored value is a no-op: `SaveChanges()` reports empty Impact and does NOT recompile, so a pre-existing stub stays broken. Change the text (even whitespace) to force recompilation.
- This model's date table (`Date`) is monthly-grain (15 rows), so `DATEADD`/time-intelligence fail; use `EDATE` + `FILTER(ALL('Date'), 'Date'[Month]=...)` for period-over-period.
- A "cyclic reference / queries blocked" load error after a crash + repeated partial reloads was a transient Desktop state artifact, not a model defect — the model queried fine via ADOMD.
