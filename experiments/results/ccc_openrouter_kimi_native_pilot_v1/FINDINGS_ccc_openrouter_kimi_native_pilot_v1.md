# Kimi native-reasoning compatibility pilot v1

Status: **PASS for compatibility; no capture inference from pilot data**

Kimi K2.7 Code can be retained in the study, but not under the terse reasoning-
bounded configuration used for the other open-weight judges. The valid route is a
separately labelled native-reasoning protocol: fixed Together endpoint, provider-
default reasoning, 16,384/32,768 output headroom, one serial worker, and a
terminal-JSON-plus-normal-stop acceptance rule.

## Result

| Domain | Parsed | Exact JSON | Terminal + stop | Retries | Max reasoning | Scored cost |
|---|---:|---:|---:|---:|---:|---:|
| Arithmetic | 16/16 | 16/16 | 16/16 | 0 | 2,994 | $0.05815550 |
| Code | 16/16 | 16/16 | 16/16 | 0 | 2,447 | $0.04011604 |
| SQL | 16/16 | 16/16 | 16/16 | 0 | 10,245 | $0.09431172 |
| **Total** | **48/48** | **48/48** | **48/48** | **0** | **10,245** | **$0.19258326** |

All responses used the frozen `moonshotai/kimi-k2.7-code` model and Together
provider identity. There were no transport retries or final errors. The run's
internal preflight cost $0.00021710; a separate successful native preflight cost
$0.00018510. Total native-path spend was therefore $0.19298546. The failed
DeepInfra preflights returned no usage record.

## Interpretation

The original Kimi failure was a protocol mismatch, not a defective judge. Kimi's
native reasoning length is variable and domain-sensitive: the successful SQL
maximum of 10,245 tokens is five times the attempted 2,048 reasoning ceiling.
Once reasoning was allowed to run natively and truncated score fragments were
rejected, the endpoint produced cleaner output than the bounded diagnostic: all
48 responses were exact JSON, despite the more permissive terminal contract.

This does **not** make Kimi directly interchangeable with the terse-score panel.
It establishes a viable, auditable Kimi arm whose protocol difference must be
reported explicitly. The pilot schedule is intentionally too small for effect
estimation, and no capture result is reported here.

## Next decision

A full Kimi native-reasoning run is now technically justified, but requires a new
preregistration and evidence namespace. Linear projection from the scored pilot is
about $5.39 for 1,344 cells, plus small preflight/retry variance. That estimate is
not a billing guarantee.
