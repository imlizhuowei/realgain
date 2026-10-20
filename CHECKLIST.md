# Is my self-improvement real? A ten-minute self-check

Answer these before believing a curve that goes up.

**Noise**
1. How many tasks decide each accept/reject? With n tasks scored 0/1 at ~50%, one standard error is about 50/√n points
   (n = 30 → ±9 points; n = 100 → ±5). Is each accepted step bigger than about twice that?
2. Did you re-run the accepted version on the same tasks? If the gain shrinks on a re-run, the rest was luck
   (the version was chosen *because* its run happened to be good).

**Selection**
3. How many candidates did you try in total? The best of k equal candidates beats the average by a margin that grows
   with k. `realgain` reports what that margin would be by chance alone.

**Overfitting**
4. Do you have tasks the loop never saw, in any form (not in the selection set, not in feedback, not in examples)?
   Report gain there, not on the selection set.

**The measuring stick**
5. Is the score an LLM judge or a rubric? Then check it against something it cannot be talked into: an answer key,
   an executed test, an expert label, even on a small sample. In our runs the judge rose by 1-1.5 points out of 10
   while the answer-key score stayed flat (contracts) or fell 12 points (data memos).
6. Does the judge see what it would need to verify the claim (the data, the document)? If not, it can only reward
   what correct work *looks like*.

**Access**
7. Can the agent read or write anything the grader uses (expected outputs, tests, the scoring script, the log the
   score is computed from)? Search the command logs. `realgain` flags paths you give it.

**Reporting**
8. Write down your prediction before the run. Report the held-out, ground-truth number next to the number the loop saw.
