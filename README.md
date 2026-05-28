# billing-engine

Monthly billing and invoicing engine for **CargoCloud**, the parcel-logistics
platform. Aggregates shipment usage events, generates draft invoices against
per-account price books, and drives the dunning workflow for overdue accounts.

## How it works

1. **Usage aggregation** (`billing/usage.py`) — sums billable events per
   account and meter within the billing period. Events are exported nightly
   by the warehouse pipeline.
2. **Invoice generation** (`billing/invoice.py`) — prices aggregated usage
   with the account's contracted price book, prorating subscription meters
   for mid-month activations.
3. **Billing run** (`billing/engine.py`) — orchestrates the monthly cycle,
   skipping accounts below the minimum invoice threshold.
4. **Dunning** (`billing/dunning.py`) — escalates overdue invoices:
   reminder (day 7), formal notice (day 21), account suspension (day 45).

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Related repositories

- [payments-service](https://github.com/shipit-ai-demo-org/payments-service) — collects payment for the invoices generated here
- [data-pipeline](https://github.com/shipit-ai-demo-org/data-pipeline) — exports the usage events this engine aggregates
