# VOID — Qwen 3.7 Plus provider-default reasoning run

Date: 2026-07-21  
Prefix: `ccc_openrouter_v1_qwen37_plus_hosted`  
Status: void in full; never resume or pool

Arithmetic completed with 384/384 parsed scores. Code was stopped at 205/384 cells
with 204 parsed scores and one `truncated_no_score`; SQL had not begun.

The failed `rpn_eval` full-rationale/wrong cell exposed an invalid cost assumption.
Alibaba reported 27,751 completion tokens on the request whose visible
`max_tokens` was 1,024, then 83,973 completion tokens (81,920 reasoning tokens) on
the 2,048-token retry. Those attempts cost $0.035600 and $0.107564. Four later
calls continuously generated for more than five minutes, so the client's
socket-idle timeout did not provide a hard total-time or billing bound. They were
terminated.

Recorded attempt cost was $0.693112 for arithmetic and $0.776602 for partial code,
or $1.469713 total. Although arithmetic was complete, the whole namespace is void:
selectively retaining one domain after changing the model's request policy in
response to another domain would mix configurations.

Per Amendment 6, Qwen restarts under
`ccc_openrouter_v1_qwen37_plus_hosted_bounded` with strict score JSON Schema and
`reasoning.max_tokens=2048`; the visible 1,024/2,048 ceilings are unchanged.
