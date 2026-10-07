# Prompt

Optimize this project according to Green Coding Rules

# Expected Output

- Remove the CSS rules that are not used by `index.html`: the component blocks (carousel, modal, tooltip, accordion, dropdown, badge, alert, card, pagination, table, form-control, spinner) and the spacing, color and display utility classes. Only the layout section at the top is used
- Recommend automating this in the build with a tool like PurgeCSS (or a utility framework in JIT mode) so unused CSS doesn't come back
- Optionally minify the remaining stylesheet
- Expected energy saving when running this file 1.000 times
