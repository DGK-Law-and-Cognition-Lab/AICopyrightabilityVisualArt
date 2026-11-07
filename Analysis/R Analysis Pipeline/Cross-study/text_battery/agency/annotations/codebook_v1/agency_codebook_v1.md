# Who made or changed the work: coding instructions

## Background

In these studies, participants rated artworks attributed to an artist called Alex. Some participants rated original artworks. Others rated a second version of an artwork, which Alex made by changing an original. Participants were told how the work was made, for example that Alex drew it with design and sketching tools, or that Alex made it by prompting an AI system. You will not be told what any participant was told. After each rating, the participant explained the rating in a few words. You will read one explanation at a time.

## The task

Answer three yes-or-no questions about what the explanation says about who made or changed the work. Code what the explanation says, not what you believe about the work. An explanation can be yes on more than one question, or on none.

**Making or changing acts.** The questions are about acts of making the work or changing it. These are expressed by verbs such as make, create, generate, produce, draw, paint, sketch, design, render, build, craft, compose, put together, edit, change, alter, modify, adjust, add, remove, transform, enhance, recolor, brighten, darken, crop, or do (as in "did the work", "did it"), in any form: active ("he drew it"), passive ("it was drawn"), participle ("AI-generated", "hand-drawn", "the changes made by Alex"), infinitive or gerund ("it would take hours to draw", "time spent editing it"). Two further forms also count: a possessive on a noun for a making or changing act ("Alex's changes", "his edits", "the AI's additions"), and "by hand". Nouns on their own do not count ("the changes are small", "the drawing is detailed", "the design is nice"), and neither do verbs of thinking, choosing or instructing (came up with the idea, chose, decided, prompted, typed, asked), which are not making or changing the work.

### Question 1: person_maker

Does the explanation present a person as having made or changed the work, or part of it?

A person is Alex, the artist, the creator, a human, someone, or he, she or they referring to the artist.

- Yes when a person does a making or changing act: "Alex added more color", "he drew this", "the artist changed the background", "they put a lot into making it".
- Yes when the work or a change is described as made by a person: "drawn by Alex", "made by a human", "hand-drawn", "done by hand", "Alex's edits".
- Yes when a person is said to have made it with a tool: "he made it using AI" (also yes on question 2), "he edited it in Photoshop".
- A hedge still counts: "he probably drew it", "it seems like the artist painted it".
- No when the explanation says the person did not do it: "Alex didn't draw this himself".
- No when the person is hypothetical or generic rather than the maker of this work: "anyone could make this", "a child could draw that", "I could do this".
- No when the person is credited only with an idea, a choice, a prompt or an instruction: "he came up with the idea", "he typed a prompt", "he chose the colors".

### Question 2: machine_maker

Does the explanation present an AI or other machine as having made or changed the work, or part of it?

A machine is an AI, an image generator, a computer, a program, an algorithm, a filter, a robot, or a named system such as ChatGPT, Midjourney or DALL-E.

- Yes when a machine does a making or changing act: "the AI made it", "the computer did all the work", "a filter changed the colors".
- Yes when the work or a change is described as made by or with a machine: "AI-generated", "computer-made", "made with AI", "he used AI to create it" (also yes on question 1).
- A hedged impression still counts: "it looks AI-generated", "probably made by a computer".
- No for ordinary tools in a person's hands, when the person does the work: "he edited it in Photoshop", "drawn with digital tools" (a person, question 1).
- No when the explanation says a machine did not do it: "it doesn't look AI-generated", "this wasn't made by a computer".
- No when the explanation mentions AI without saying that it made or changed anything: "I don't like AI", "AI art isn't real art", "an AI image".

### Question 3: agentless_making

Does the explanation describe the work, or a change to it, being made or changed without saying who or what did it?

- Yes for a making or changing act whose doer is not stated: "it was made", "the colors were changed", "the image was edited slightly", "it would take hours to draw", "a lot of time went into making it", "it took effort to create".
- Yes even when another act in the same explanation does have a doer: "the colors were changed, and Alex added a tree" is yes on questions 1 and 3.
- No when every making or changing act in the explanation has its doer stated, or denied.
- No when the explanation only describes the result or the look of the work: "the colors are different", "the changes are small", "it looks the same", "it is very detailed".

## Notes

- Code each question on its own.
- Code what the words say or plainly imply. Do not guess from tone.
- Spelling mistakes and fragments are common; read them as the writer plainly meant them.
- "They" usually refers to the artist; treat it as a person unless it plainly refers to something else.
- The participant writing ("I", "me") is never the maker of the work.

## Answer format

Return only this, with true or false for each question:

{"person_maker": true or false, "machine_maker": true or false, "agentless_making": true or false}
