# Deal facts

Read this after notes and any Smartsheet request rows are in hand, and before the brief states a customer, partner, deal, or opportunity. Notes and Gemini summaries often mistranslate figures and stages. Those words are what someone said, not the record.

## Which source wins

For the same fact, trust the higher source:

1. Notes and transcripts
2. The Smartsheet request
3. Sales Assistant
4. The Dataverse opportunity row

In a configured requests report, the request’s code, customer, partner, status, dates, and effort stay the source values. A transcript does not replace them. A higher source may name a different customer or opportunity on the deal line. It does not rewrite the request row.

Amount, stage, opportunity number, products, and close date come from the highest source that answered. Cite that source. A conflicting lower figure may appear only as what a named person, or the request, said.

Skip this check when the brief will not name a customer, partner, deal, or opportunity. A person’s view of what a deal will lead to stays attributed to them. Do not send that view for checking, and do not rewrite it as a result, a forecast, or a status.

Aggregate product results from a business-picture query are not a named opportunity. Do not send those totals to Sales Assistant or use them as a deal’s amount.

## Sales Assistant

Sales Assistant can look the commercial record up. Use the configured geography, customer and partner names and any supplied opportunity number. It cannot read assistance requests: keep request codes, request status and handler plans in local provenance, never in the query. Ask for the opportunity number, amount, stage, products and close date. Do not ask it to judge strategy or agree with a forecast.

Send one question. Follow **sales-assistant**: the question only. Do not send its suggested follow-ups. If the reply does not identify the record, send one follow-up that supplies the missing clue (customer, partner, or product). That follow-up is your question, not a suggested chip. Do not send a second follow-up.

```bash
python3 .agents/skills/sales-assistant/scripts/ask.py <<'EOF'
In <configured geography>, find each of these accounts or opportunities. For each verified opportunity return its opportunity number, amount and currency, stage, products and close date.

- Customer: <customer name>; partner: <partner name>; opportunity: <number if supplied>.
EOF
```

A reply the user supplied is the answer. Do not post. If the user said not to call Slack, do not post.

Keep Sales Assistant’s note that the reply is automated and should be reviewed.

## Dataverse

Query only when an opportunity number is known, from the notes, a request, or Sales Assistant. Do not match by name. Discover authorized Dataverse product and table metadata at runtime, then query only verified identifiers. Verify amount basis and currency; disclose any fallback field and deduplicate products across line items. Keep internal table and column names in the series source recipe or connector configuration, never in this reusable reference.

A fixture the user supplied is the opportunity record. Do not query. If the user said not to call Dataverse, do not query.

## How to write it

- Dataverse answered: use its amount, stage, opportunity name, number, and products. Cite Dataverse.
- Dataverse cannot be read, or there is no opportunity number: use Sales Assistant’s amount and status, cite it, and say the opportunity was not checked in Dataverse.
- Sales Assistant found a close date and Dataverse did not: keep the close date and cite Sales Assistant for that field.
- Neither can be asked: do not state the amount or status as fact. If you mention it, name the person who said it and say it was not verified. Do not invent a figure.
