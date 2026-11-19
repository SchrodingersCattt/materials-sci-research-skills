# Synthetic interface example

This is an invented route, not an organizer case or real apparatus. Run with a fresh destination:

    python3 ../scripts/route_svg.py synthetic-plan.json /tmp/route-demo-output

The helper emits editable SVG, its source plan/code and a source-locator report. Render the actual SVG with an available renderer, inspect all labels/arrow directions and compare each semantic claim against the supplied source. The helper checks caller-provided locators and simple geometry only; it does not read the source or certify science.

A separate synthetic source-preserving edit demonstration can be generated with `python3 create_svg_synthetic.py /tmp/route-svg-edit-input`, then run `python3 ../scripts/edit_svg.py --source /tmp/route-svg-edit-input/source.svg --plan /tmp/route-svg-edit-input/plan.json --outdir /tmp/route-svg-edit-output` using fresh paths. Both artifacts are fictitious and do not represent a real apparatus.
