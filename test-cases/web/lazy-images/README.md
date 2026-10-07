# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Add `loading="lazy"` (and `decoding="async"`) to all images below the first screen, so visitors who don't scroll to the end never download them
- Keep the hero image `images/hero-pass.jpg` eager (no `loading="lazy"`), optionally with `fetchpriority="high"`, because it is visible immediately and lazy loading would only delay it
- Add `width` and `height` attributes so the browser can reserve space and the layout doesn't shift while images load
- Expected energy saving when running this file 1.000 times
