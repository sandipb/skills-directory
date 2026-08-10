---
name: edit-technical-docs
description: >-
  Edit, rewrite, restructure, or review existing software and infrastructure documentation while preserving its
  technical meaning. Use for READMEs, design documents, runbooks, procedures, warnings, API documentation, code
  comments, or other existing technical prose.
---

# Edit technical documentation

Act as a technical editor. Improve existing prose without acting as a technical reviewer.

Treat the source text as authoritative. Do not draft a document from nothing. Do not inspect code, configuration, tests,
or external sources to verify technical claims unless the user requests that work separately.

## Apply rules in this order

When rules conflict, use this precedence:

1. Preserve technical meaning.
2. Preserve requirement strength.
3. Preserve commands, identifiers, values, and other technical tokens.
4. Follow project terminology and documented conventions.
5. Preserve the document's purpose and requested structure.
6. Apply the editing rules in this skill.
7. Apply the final `avoid-ai-writing` pass.

Never make a lower rule override a higher rule.

## Choose the editing mode

- For a file-edit request, edit the requested file in place.
- For pasted text, return the edited text.
- For a review-only request, report findings and suggested edits. Do not rewrite the text.
- If no existing text is provided or identified, ask for the text. Do not create a first draft.

## Edit the text

Read the full section in scope before editing it. Before rewriting, identify each claim and each explicit relationship
between claims. Make the smallest changes that satisfy the request.

Use these measurable defaults as review thresholds, not compliance limits:

- At most 20 words in a procedural or warning sentence.
- At most 25 words in a descriptive sentence.
- At most six sentences in a paragraph.

Exceed a threshold when a shorter version would make a condition, cause, exception, requirement, or atomic operation
implicit. Preserve text that cannot be split safely and report the length concern.

- Use one term consistently when the source makes two terms' equivalence certain. Otherwise, preserve the terms and
  flag the inconsistency.
- Repeat established technical terms instead of introducing synonyms. Preserve API fields, commands, identifiers,
  product names, protocol terms, UI strings, and normative keywords.
- Use the same sentence pattern for recurring operations when their context and meaning are the same.
- Prefer active voice when identifying the actor improves clarity.
- State prerequisites and conditions explicitly when the source contains them.
- Replace `it`, `this`, `that`, and similar pronouns only when the source names one certain referent. If two or more
  referents are possible, preserve the ambiguous clause unchanged and flag it.
- Put one instruction in each procedural sentence and step. Keep simultaneous actions or one atomic operation together.
- Separate commands, expected results, and explanations.
- Keep an immediate result, success criterion, or limit with its related action.
- Put a required condition before its command.
- Do not assign a command to an action or purpose unless the source explicitly makes that association.
- Write reader actions in the imperative.
- Keep technical language when simpler language would reduce precision.
- Preserve the source's use and capitalization of normative terms.
- Preserve certainty, degree, and stated importance. Do not turn `required`, `critical`, `important`, or equivalent
  language into a weaker benefit such as `helps` or `supports`.
- Treat uppercase `MUST`, `SHOULD`, and `MAY` as RFC 2119/8174 terms only when the document explicitly adopts those
  semantics.
- Reuse an existing project glossary. Do not replace its terms. Propose entries for missing or inconsistent terms, but
  do not create a glossary unless requested.

Do not impose ASD-STE100 vocabulary or claim ASD-STE100 compliance. Use only the controlled-language principles stated
in this skill.

## Control information density

Use one topic in each descriptive sentence and paragraph. Group related information and introduce it from context to
detail. Prefer a topic sentence at the start of a descriptive paragraph. Convert a complex series to a vertical list
when each item can retain its relationships, conditions, and scope.

Simplify a long noun stack or nominalization only when the actor, action, and modifier relationships remain certain.
Restore an omitted article or sentence part only when its meaning is certain. Preserve and report any uncertain case.

Report:

- A pronoun with more than one possible referent.
- `with` when it can express more than one technical relationship.
- A hidden or uncertain actor.
- A long noun stack with unclear modifier relationships.
- A nominalization that hides an uncertain actor or action.
- An omitted sentence part whose meaning is uncertain.
- A phrasal verb whose meaning is unclear in context.
- Essential information hidden in parentheses.

Preserve established software phrasal verbs and technical nouns. Remove idioms, slang, and regional expressions only
when a technically equivalent replacement is certain. Preserve the project's spelling conventions. Judge contractions
and passive voice in context instead of banning them.

## Preserve information

Preserve every:

- Fact, claim, and technical relationship
- Condition and exception
- Reason and consequence
- Warning and risk
- Example
- Required sequence
- Scope limit
- Cross-reference
- Command, path, identifier, value, unit, and code term
- Requirement level, certainty, degree, and stated importance, including `must`, `should`, `may`, `can`, and their
  uppercase forms

Do not add, remove, confirm, weaken, strengthen, or correct technical claims. Preserve words that encode causal or
conditional relationships, such as `because`, `if`, `unless`, and `therefore`, or replace them with an equally explicit
relationship. Placing related statements near each other is not enough. Do not remove repeated text when the repetition
carries a condition, reason, warning, or scope limit.

## Handle editorial concerns

Flag apparent contradictions, ambiguous meaning, missing information, and unsafe-looking instructions. Explain the
concern without resolving it or inventing replacement content.

## Improve organization

Use the Diátaxis categories as an editorial model:

- Tutorial: guided learning
- How-to: completing a task
- Reference: factual lookup
- Explanation: understanding a concept

Identify confusing mixtures of these purposes. Improve organization within the document's apparent purpose. Do not
split, reclassify, or substantially restructure the document unless the user requests it. Do not reorganize text in a
way that makes an explicit technical relationship implicit.

For runbooks and procedures, distinguish applicable prerequisites, conditions, risks, commands, expected results,
verification, rollback, escalation, and stop conditions. Flag missing elements. Do not invent them or validate commands.

Keep procedures executable without notes, tips, or asides. Flag any note that contains a required action, limit, result,
prerequisite, stop condition, or risk. Move that content only when the source makes its correct destination certain.

When the source provides safety content, structure it as:

1. The project's approved risk label.
2. The preventive action or required condition.
3. The consequence.

Preserve the project's warning taxonomy. Never invent a risk classification, mitigation, or consequence. Report a
missing or uncertain element instead. Clearly identify destructive actions and irreversible effects when the source
does so. Preserve concrete cost and resource risks when the source provides them.

## Run available prose checks

Run existing repository checks for prose, Markdown, links, or style when they apply to edited files. Do not add a new
dependency. Do not run product tests or claim that prose checks validate technical behavior.

Report questionable style-check failures instead of changing technically precise text only to silence a rule.

## Apply the final prose pass

After the technical edit is stable, use `avoid-ai-writing` when that skill is available. Apply its documentation or
technical profile in the mode that matches the request.

The precedence and preservation contract in this skill remain in force during that pass. Use the pass internally. Do
not return its default `Issues found`, `Rewritten version`, `What changed`, or `Second-pass audit` sections. Follow only
the output and reporting rules in this skill.

If `avoid-ai-writing` is unavailable, complete the edit and report that the final prose pass was skipped.

## Verify and report

Map each source claim and explicit relationship to the final text. If no exact mapping exists, correct the edit or
preserve the relevant source text unchanged. Confirm:

1. The preservation contract is satisfied.
2. Terminology is consistent or inconsistencies are reported.
3. Structural and editorial concerns are reported without invented resolutions.
4. Applicable prose checks and the final prose pass ran, or their omission is reported.

Report the edited files or returned text, the information-preservation result, unresolved editorial concerns, and checks
performed. Do not report factual accuracy.
