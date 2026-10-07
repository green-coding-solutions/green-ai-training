# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Do not render all 10,000 entries at once: paginate (e.g. 50-100 rows per page) or virtualize the list so only the rows in the viewport exist in the DOM
- Remove the unnecessary wrapper elements: each row currently creates 14 elements (row wrapper, row, and wrapper + cell + span per column). One element per cell (e.g. a `<table>` with `<tr>`/`<td>`) is enough
- Build rows off-DOM (e.g. `DocumentFragment` or one batched insert) instead of appending to the live DOM 10,000 times
- Expected energy saving when running this file 1.000 times
