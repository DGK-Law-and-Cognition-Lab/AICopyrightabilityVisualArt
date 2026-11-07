# Who made or changed the work: coding instructions (version 2)

## Background

In these studies, participants rated artworks attributed to an artist called Alex. Some participants rated original artworks. Others rated a second version of an artwork, which Alex made by changing an original. Participants were told how the work was made, for example that Alex drew it with design and sketching tools, or that Alex made it by prompting an AI system. You will not be told what any participant was told. After each rating, the participant explained the rating in a few words. You will read one explanation at a time.

## The task

Answer three yes-or-no questions about what the explanation says about who made or changed the work. Code what the explanation says, not what you believe about the work. An explanation can be yes on more than one question, or on none.

## Acts of making or changing

The three questions are about acts of making the work or changing it. Only these verbs count, in any tense or form:

- making: make, create, generate, produce, draw, paint, sketch, design, render, build, craft, compose, illustrate, animate, doodle, sculpt, color, shade, put together, and do when its object is the work or the labor ("did the work", "did it all", "did most of it", "doing the details");
- changing: edit, change, alter, modify, adjust, add, remove, transform, enhance, recolor, brighten, darken, lighten, crop, tweak, rework, redo, retouch, revise, convert, manipulate, saturate, blur, sharpen, tint, warp, distort, rearrange, replace, erase, delete, insert, flip, rotate, resize, stretch, fix, improve, update, touch up, filter; and make with a result ("made it brighter", "making the colors darker").

These forms of them count:

- active, with a subject: "Alex added color", "the AI made it";
- passive: "it was drawn", "the colors were changed", "it was made by a computer";
- a participle: "AI-generated", "hand-drawn", "computer-made", "filtered", "the changes made", "the details added";
- an infinitive or a gerund: "it would take hours to draw", "time spent editing it", "making the colors darker";
- a possessive or a by-phrase on a noun for one of these acts: "Alex's changes", "his edits", "the AI's additions", "edits by the AI";
- "by hand", "handmade", "manually".

These do not count:

- nouns on their own: "the changes are small", "the drawing is detailed", "the design is nice", "the coloring";
- a verb whose subject is a thing rather than a person or a machine. "The colors changed", "the essence changed", "nothing really changed", "it transformed", "the changes add meaning", "this created a new style" and "the colors make it look sad" describe the work or its result, not anyone making or changing it. Compare "the colors were changed", a passive, which does count;
- make meaning cause a thought or feeling in a viewer ("makes me feel", "makes you think") and the idioms "make sense" and "make sure";
- verbs of thinking, choosing, instructing or using on their own: "came up with the idea", "chose the colors", "decided", "prompted the AI", "typed a prompt", "asked", "used AI". In "he used AI to make it", the act is make: its doer is Alex and its means is the AI (yes on questions 1 and 2).

## Question 1: person_maker

Does the explanation present a person as having made or changed the work, or part of it?

A person is Alex, the artist, the creator, a human, someone, or he, she or they referring to the artist.

- Yes when a person is the doer of an act: "Alex added more color", "he drew this", "the artist changed the background", "drawn by Alex", "made by a human", "Alex's edits", "hand-drawn", "done manually", "he made it using AI" (also yes on question 2), "he edited it in Photoshop".
- A hedge still counts: "he probably drew it", "it looks like a person painted it".
- No when the explanation denies it: "Alex didn't draw this himself", "he did not have to draw it", "digital rather than hand-drawn".
- No when the doer is hypothetical or generic rather than the maker of this work: "anyone could make this", "a child could draw that", "you could do this in a minute".
- No when the person is credited only with thinking, choosing, prompting or using: "he came up with the idea", "he typed a prompt", "he chose the colors".

## Question 2: machine_maker

Does the explanation present an AI or other machine as having made or changed the work, or part of it?

A machine is an AI, an image generator, a computer, a program, an algorithm, a filter, a robot, or a named system such as ChatGPT, Midjourney or DALL-E.

- Yes when a machine is the doer of an act, or the means of it: "the AI made it", "the computer did all the work", "a filter changed the colors", "AI-generated", "a generated AI picture", "computer-made", "made with AI", "he used AI to create it" (also yes on question 1).
- A hedged impression still counts: "it looks AI-generated", "probably made by a computer".
- No for ordinary tools in a person's hands when the person does the work: "he edited it in Photoshop", "drawn with digital tools", "using a digital platform".
- No when the explanation denies it: "it doesn't look AI-generated", "this wasn't made by a computer".
- No when the explanation mentions AI without an act: "I don't like AI", "AI art isn't real art", "an AI image", "the use of AI".

## Question 3: agentless_making

Does the explanation describe an act of making or changing the work without saying who or what did it?

- Yes for an act in one of the forms that count whose doer is not stated: "it was made", "the colors were changed", "the image was edited slightly", "it would take hours to draw", "a lot of time spent drawing it", "the idea of making it brighter", "the details added".
- Yes also for an act described as not happening, when no doer is stated: "nothing was added", "it wasn't changed much".
- Yes even when another act in the same explanation has a doer: "the colors were changed, and Alex added a tree" is yes on questions 1 and 3.
- No when every act in the explanation has its doer stated (questions 1 and 2), including a generic doer ("anyone could make this") or the writer ("I could draw this").
- No when the explanation only describes the work or its result: "the colors are different", "the colors changed", "nothing changed", "the changes are small", "it looks the same".

## Notes

- Code each question on its own.
- Code what the words say or plainly imply. Do not guess from tone.
- Spelling mistakes and fragments are common; read them as the writer plainly meant them.
- "They" usually refers to the artist; treat it as a person unless it plainly refers to something else, such as the changes.
- The participant writing ("I", "me") is never the maker of the work.

## Answer format

Return only this, with true or false for each question:

{"person_maker": true or false, "machine_maker": true or false, "agentless_making": true or false}
