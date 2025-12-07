# BitPlanarNet Paper Repository

## Overview

This repository contains a LaTeX paper ([conference_101719.tex](./conference_101719.tex)) which is an academic manuscript that I'm working on.
- The manuscript will be submitted to IEEE Transactions on Nanotechnology
- The new manuscript is a journal extension upon the conference paper [Building a Machine Learning Accelerator with Silicon Dangling Bonds: From Verilog to Quantum Dot Layout](./reference-papers/Ng%20et%20al.%20-%202025%20-%20Building%20a%20Machine%20Learning%20Accelerator%20with%20Silicon%20Dangling%20Bonds%20From%20Verilog%20to%20Quantum%20Dot%20Lay.pdf). You are allowed to read the conference paper's PDF for context, but do not directly copy text from the PDF as that constitutes plagiarism.

## Writing rules

- When writing new material or modifying existing material, adhere to the existing tone and writing style of the paper in order to ensure coherence.
- While active voice is not prohibited, when using active voice to refer to ourselves, do not use "we", "our", etc. Instead, use "this work" or similar terms, or use passive voice.
- When you write any text, ensure the writing is a smooth flow of ideas in an academic writing context. We are NOT writing blog posts where one would put short headings and discuss ideas in point-form-like fashion; we are writing academic papers where ideas flow from one paragraph to the next with smooth transitions.
- The use of em-dashes are permitted, but only when it significantly improves clarity of the writing. In cases where alternatives to em-dash exists which still clearly convey the same idea, do not em-dash. When you do use em-dashes, use the proper LaTeX em-dash which is created by three ASCII dashes: `---`. DO NOT use the unicode version (i.e., do not use "—"). For example, the following is correct:
```
Jeff Bezos---who is the founder of Amazon---is one of the richest people in the world.
```
- When there is any ambiguity in the user's request or if facts or statements related to paper-writing are unclear, either stop and ask the user for clarification or put in a `\TODO{descriptive placeholder intention}` as placeholder. DO NOT hallucinate non-existent details.
- Use LaTeX's quoting rules: two backticks for open double quote, two single quotes for close double quote. For example, the following is correct:
```
The famous quote, ``let them eat cake'', is often attributed to Marie Antoinette that signifies the indifference of the aristocracy to the plight of the poor during the French Revolution.
```
- In the above example, the WRONG way to implement double quote would be if you used the ASCII double quotes "let them eat cake" or the Unicode quotes “let them eat cake”.

## Project rules

- You are REQUIRED to read the entirety of ([conference_101719.tex](./conference_101719.tex)) before addressing any writing-related requests. Establishing context is of utmost importance, lack of it will degrade the quality of your output.
- You are allowed to read inside [./figs/](./figs/) to see what figures are present, but NEVER to modify its contents.
- Keep in mind that, in LaTeX, contiguous lines of text compile to the same paragraph. Only when there are two linebreaks when a new paragraph begins. So when reading LaTeX text, treat contiguous lines of text as a single paragraph.
