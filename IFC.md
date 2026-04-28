# IFC — Issue, Facts, Criteria
## Study Guide Generation Web App

---

## Issue

Teachers in K–12 markets (initially PH, JP, VN) spend disproportionate time manually producing structured, curriculum-aligned study guides for every lesson — work that is largely templated, repetitive, and does not benefit from being done by hand. No adequate tool exists that takes a teacher's lesson inputs and produces a complete, print-ready study guide that meets house style, reading-level, and curriculum-alignment requirements without significant manual correction.

---

## Facts

### The current situation

- Teachers currently produce study guides by hand in Word or Google Docs, working from internal templates.
- A single study guide covers a fixed set of sections: introduction, learning targets, warm-up, vocabulary, core explainer, sub-concept blocks, strategy list, deep dive, model passage, check-in, key points, assessment passage, assessment questions, step-up prompt, self-assessment, and answer key — totalling approximately 17 distinct content sections per lesson.
- Producing one complete guide manually takes an experienced teacher several hours; for less experienced writers the time is longer and consistency suffers.
- Quality variance is high across writers: vocabulary difficulty, reading level, tone, and curriculum alignment all depend heavily on the individual.
- The answer key must be produced last and must not leak answers into body sections — a constraint that is easy to violate when working manually and difficult to audit after the fact.

### The users

- Primary users are curriculum writers and teachers working within a structured, branded content pipeline.
- They are comfortable filling in a structured form but are not technical users — they should not need to understand prompting, LLMs, or the generation pipeline.
- Their primary goal is either a downloadable PDF document or a web preview they can review and share — the output must be immediately presentable without post-generation formatting work.
- Secondary users are content leads who review output quality; where sections fail validation, the system automatically retries them as part of the validation pass rather than requiring manual intervention.

### The content constraints

- Output must conform to a specific house style: warm-formal tone, no emoji, no exclamation marks outside dialogue, no LaTeX, reading level matched to the target grade band.
- Vocabulary words introduced in the vocabulary section must appear in body sections — not just defined in isolation.
- The assessment passage must draw from a topic domain that differs from the model passage to prevent answer leakage.
- Answer key possible answers must quote verbatim from the assessment passage — they cannot be paraphrased.
- Self-assessment skills must match the learning targets stated earlier in the same guide, verbatim.
- These constraints are currently enforced by manual reviewer checks, which are slow, inconsistent, and do not scale.

### The market context

- The tool is initially scoped to three markets (PH, JP, VN) with different cultural norms for examples and references.
- Subject is not fixed — it is provided by the teacher as a form input, and the 17-section template applies across subjects at the teacher's discretion.
- Generation must complete within a single browser session — no async job queue or email delivery for the prototype.

### The technology context

- Gemini 2.0 Flash is the chosen LLM for all generation calls due to cost and latency profile.
- The study guide is long enough (17 sections) that a single LLM call cannot produce it reliably — multi-step generation with shared context is required.
- Some sections have hard dependencies on prior sections (answer key depends on all question sections; check-in depends on the model passage) — naive parallelisation will produce incoherent output.
- Validators must run programmatically after generation to catch constraint violations before the document is assembled, and must trigger targeted section retries automatically as part of the validation pass — not as a separate manual step.

---

## Criteria

### Must-haves

- **Complete guide in one session.** A teacher fills in one form and receives a complete, downloadable PDF document or web preview without any additional steps.
- **All 17 sections generated.** The output covers every required section in the correct order, as defined by the fixed 17-section template, regardless of the subject inputted by the teacher.
- **Dependency ordering respected.** The answer key is always generated last. Sections that depend on prior outputs (check-in, assessment questions, step-up, answer key) only run after their dependencies are complete.
- **Hard constraint validation.** The system must programmatically verify: vocabulary words appear in body sections; self-assessment skills match learning targets verbatim; answer key quotes exist verbatim in the assessment passage; assessment passage topic domain differs from model passage.
- **Automated retry on validation failure.** When a section fails a hard validator, the system automatically retries that section in isolation during the validation pass — not by regenerating the entire guide, and not requiring manual intervention.
- **Structured PDF output.** The final file must be a properly structured PDF document with headings, a vocabulary table, a self-assessment table, and a clearly separated answer key on a new page.
- **House style compliance.** Every generated section must follow tone, register, reading-level, and formatting rules without requiring post-generation editing by the teacher.
- **Market-aware generation.** The system prompt must be parameterised by market (PH / JP / VN) so cultural references and examples are contextually appropriate.
- **No answer leakage.** Body sections must not contain or imply correct answers to assessment questions. This must be checked programmatically as a soft validator with a warning surfaced to the user.

### Nice-to-haves

- **Soft reading-level validation.** A Flesch-Kincaid scorer that warns if a section falls outside the target grade band, without blocking download.
- **Per-section manual regeneration UI.** Beyond the automated retry during validation, a content lead can additionally flag a specific section from the web preview and trigger a manual retry without resubmitting the whole form.
- **Generation progress visibility.** The UI shows which sections have completed so the teacher knows the guide is being built, not just waiting on a spinner.
- **Multi-market localisation beyond PH/JP/VN.** The market field is a free-text input so new markets can be added without code changes.
- **Short / standard / long length presets.** A length_preset parameter that adjusts target word counts per section without changing the section structure.
- **Optional input pre-population.** Vocabulary seeds and topic domain overrides let experienced writers guide generation without being required for basic use.
- **Deployment to managed cloud infrastructure.** The backend is structured so it can be migrated from a Next.js API route to an ADK-managed agent server without changes to prompt logic, validators, or renderer.
