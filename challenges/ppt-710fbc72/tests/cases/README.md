# Reusable item set

Interface and regression items only. They are not organizer cases, they contain no
formal answers, and their expected properties are structural so a run can be graded
without a whiteboard.

Run one item as a full pass:

```
python examples/synthetic_case.py --outdir work/item
python tests/run_checks.py --workdir work/item-lab
```

Add an item by copying the shape of `item-01.json`; keep every field structural.
