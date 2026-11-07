# Codebook: does the explanation give how the work was made as a reason for the rating?

You will read one short written explanation at a time. Each was written by a participant in a study of art. The participant had just rated an image on a 1-to-5 scale and then explained the rating in a few words. The image was either an original artwork or a "second work", a version of an original that an artist edited by hand.

The rating was for one of four questions:

- how much creativity went into the work;
- how much effort went into it;
- how transformative the second work is;
- how much it changed the original's essence.

You will not see the image, the question, the rating or anything else about the participant. Code only from the words of the explanation.

## The question

Does the explanation give **how the work was made** as a **reason** for the rating?

"How the work was made" means made by AI, by prompting an AI system, or by a machine, computer or program. It also means the opposite: not made by AI, or drawn or made by a person. It covers how the rated work was made, and, for a second work, how the original it was made from was made.

A reason can push the rating down ("it's AI, so not much effort") or up ("he had to put a lot of thought into the prompts").

## Code YES when

1. **A connective** ties how the work was made to the rating or to a judgment of creativity, effort or change: "because", "since", "so", "as", "which is why", "due to", "given that", "if ... then".
   - "Because Alex inputted the prompts, he contributed a little bit of creativity."
   - "If it is AI, then the effort is none."
2. **The whole explanation** is a statement about how the work was made. It is then the only reason given.
   - "The art is clearly AI."
   - "looks like a generated ai picture"
3. **A general claim** about how such works are made is applied to this one.
   - "AI art requires little to no effort."
4. **An evaluation** is tied to how the work was made.
   - "You could clearly tell this is AI, which made me dislike it in terms of effort."
5. **For a second work**, how the original was made is given as the reason.
   - "The second work is copied from the one produced by AI. No creativity went into the process."

## Code NO when

1. **The making is conceded** and something else carries the rating.
   - "Although it was made by AI, the idea is clever."
2. **The making only names or describes the original** while the change is the reason.
   - "completely different from the AI's cartoonish style"
   - "it added a level of distinctness to the original, AI-generated work"
3. **The explanation is about the editing tools** without saying the work was made by a machine.
   - "he used Photoshop to adjust the colors"
4. **The making is mentioned only as a guess** about something other than the rated work.
5. **How the work was made is not mentioned at all.** This is most explanations.

## Direction (only when you code YES)

- **lowers**: the making is a reason for a lower rating. "it's AI so little effort"
- **raises**: the making is a reason for a higher rating. "a lot of thought went into the prompts"
- **unclear**: it is a reason, but its direction cannot be told.

When you code NO, the direction is **none**.

## Answer

Answer with a JSON object and nothing else:

{"origin_reason": true or false, "direction": "lowers" | "raises" | "unclear" | "none"}
