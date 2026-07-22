# CCC OpenRouter compatibility pilot v2 — local findings

Date completed: 2026-07-22  
Status: local only; no full run started; no GitHub push

## Outcome

The pilot found complete, inexpensive score-output configurations for two of the
three downloadable-weight judges.

| Model / endpoint | Cells | Output control | Reasoning | Cost | Decision |
|---|---:|---:|---:|---:|---|
| MiniMax M3 / first-party | 48/48 | 48 exact JSON | max 0 | $0.004133 | **GRADUATES** |
| GLM 5.2 / Together, serial | 48/48 | 48 exact JSON | max 0 | $0.014171 | **GRADUATES** |
| GLM 5.2 / Together, two workers | 47/48 | 47 exact JSON | max 0 | $0.013883 | void; one final HTTP 429 |
| Kimi K2.7 Code / Together | 47/48 stopped | 45 exact JSON | max 8,001 | $0.223073 | **DOES NOT GRADUATE** |

MiniMax required fixed first-party routing and empirical verification because
OpenRouter's capability-advertisement filter could not find an eligible endpoint.
The realized behavior was clean: exact JSON and zero reasoning on every attempt.

GLM behaved equally cleanly on Together once concurrency was reduced from two
workers to one. The first Together block's single failure was a provider HTTP 429,
not a score or reasoning failure. The serial recheck had no retry or missing cell.

Kimi's larger output headroom recovered scores but did not enforce the requested
reasoning ceiling or strict output. One retry used 8,001 reasoning tokens and two
responses placed long deliberation in the answer body. More output budget would
therefore buy completion without producing the controlled protocol required here.

## Frozen full-run candidates

- MiniMax: first-party `minimax`; fallbacks off; `reasoning.effort=none`;
  strict score schema; 128/256 output ceilings; realized reasoning must remain 0.
- GLM: `together`; fallbacks off; one worker; `reasoning.effort=none`;
  strict score schema; 128/256 output ceilings; three bounded transport retries;
  realized reasoning must remain 0.

These pilot passes do not authorize inference and do not start a full run. A full
run needs a new preregistered namespace, full three-repetition schedule, and the
same fail-closed completion checks. Kimi should not receive a full run under its
tested Together configuration.

Total recorded compatibility spend was $0.255261. No effect size, confidence
interval, `SUPPORTED`, immunity, or capture claim is made from these samples.
