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
- They benefit from a study guide that is easy to scan visually, not just accurate in content — lightweight iconography around headings, subheadings, and repeated callout patterns can improve readability when it stays consistent and non-distracting.
- Secondary users are content leads who review output quality; where sections fail validation, the system automatically retries them as part of the validation pass rather than requiring manual intervention.
- A separate internal reviewer group may need to tune prompt wording remotely without repo access, terminal access, or direct exposure to backend code.
- Prompt reviewers are non-technical users. They should work through a private web interface that lets them edit plain-language prompt instructions, run the generator, and judge whether outputs improved.

### The content constraints

- Output must conform to a specific house style: warm-formal tone, no emoji, no exclamation marks outside dialogue, no LaTeX, reading level matched to the target grade band.
- Visual enhancement for the prototype is limited to deterministic iconography near section headers, selected subheaders, and other repeated layout affordances such as warnings or callouts; icons are decorative navigation aids, not generated illustrations or content-bearing diagrams.
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
- Prompt experimentation must not require code edits in production deployments or access to the repository. Reviewers need a private, browser-based tuning surface that can send temporary prompt overrides to the existing generation workflow.
- Prompt tuning must remain isolated from the live teacher-facing experience. Experimental prompt sets should be reviewable in a staging or internal environment before any manual promotion to the default prompt set.
- Deployment should preserve the same two-runtime split in local and remote environments so production issues can be reproduced without changing request flow or prompt logic.
- Local debugging needs a documented production-like mode where the backend runs with the same container/runtime assumptions intended for Cloud Run and the frontend uses the same `ADK_BACKEND_URL` contract it will use remotely.

---

## Criteria

### Must-haves

- **Complete guide in one session.** A teacher fills in one form and receives a complete, downloadable PDF document or web preview without any additional steps.
- **All 17 sections generated.** The output covers every required section in the correct order, as defined by the fixed 17-section template, regardless of the subject inputted by the teacher.
- **Dependency ordering respected.** The answer key is always generated last. Sections that depend on prior outputs (check-in, assessment questions, step-up, answer key) only run after their dependencies are complete.
- **Hard constraint validation.** The system must programmatically verify: vocabulary words appear in body sections; self-assessment skills match learning targets verbatim; answer key quotes exist verbatim in the assessment passage; assessment passage topic domain differs from model passage.
- **Automated retry on validation failure.** When a section fails a hard validator, the system automatically retries that section in isolation during the validation pass — not by regenerating the entire guide, and not requiring manual intervention.
- **Structured PDF output.** The final file must be a properly structured PDF document with headings, a vocabulary table, a self-assessment table, and a clearly separated answer key on a new page.
- **Consistent visual affordances.** The PDF and web preview must support a consistent icon system for section headers and selected subheaders or callouts so the guide is more scannable without changing section order, instructional meaning, or requiring teacher configuration.
- **House style compliance.** Every generated section must follow tone, register, reading-level, and formatting rules without requiring post-generation editing by the teacher.
- **Market-aware generation.** The system prompt must be parameterised by market (PH / JP / VN) so cultural references and examples are contextually appropriate.
- **No answer leakage.** Body sections must not contain or imply correct answers to assessment questions. This must be checked programmatically as a soft validator with a warning surfaced to the user.
- **Managed two-runtime deployment.** The frontend and backend must deploy independently to managed infrastructure without application-code changes between local and remote environments.
- **Local-to-remote parity.** The repository must document and support a production-like local deployment mode that mirrors the remote topology as closely as practical: separate frontend and backend runtimes, environment-driven backend routing, and backend container/runtime behavior aligned with Cloud Run.

### Nice-to-haves

- **Soft reading-level validation.** A Flesch-Kincaid scorer that warns if a section falls outside the target grade band, without blocking download.
- **Per-section manual regeneration UI.** Beyond the automated retry during validation, a content lead can additionally flag a specific section from the web preview and trigger a manual retry without resubmitting the whole form.
- **Generation progress visibility.** The UI shows which sections have completed so the teacher knows the guide is being built, not just waiting on a spinner.
- **Multi-market localisation beyond PH/JP/VN.** The market field is a free-text input so new markets can be added without code changes.
- **Short / standard / long length presets.** A length_preset parameter that adjusts target word counts per section without changing the section structure.
- **Optional input pre-population.** Vocabulary seeds and topic domain overrides let experienced writers guide generation without being required for basic use.
- **Automated CI/CD promotion.** Once the manual deployment path is stable, dev and production releases can be promoted from versioned configuration rather than ad hoc local commands.

### Prompt Lab MVP criteria

- **Private reviewer-only prompt workspace.** A non-technical reviewer can access a private web page intended for internal use only, separate from the normal teacher-facing generation flow.
- **Prompt editing without code access.** The reviewer can edit plain-language prompt instructions for supported study-guide sections without touching repository files or Python modules directly.
- **Temporary prompt overrides.** A prompt-lab run can send temporary prompt overrides into the existing generation workflow without changing the default prompt set used by normal teacher generation.
- **Prompt-lab generation output.** After running a prompt-lab generation, the reviewer can inspect the same core outputs as the teacher flow: streamed progress, structured web preview, downloadable PDF, and validation warnings.
- **Sample-input driven review.** The reviewer can run prompt experiments against a structured lesson input chosen from a small curated sample set or entered through a simplified form.
- **Manual promotion outside the MVP UI.** The MVP does not need an in-product publish button. Approved prompt changes can still be promoted manually by a developer or content lead after review.

### Out of scope for Prompt Lab MVP

- Real-time collaborative editing of prompts by multiple reviewers.
- Full prompt version-control, approval, rollback, or audit-log workflows inside the UI.
- Automatic publishing of reviewer edits to production.
- Arbitrary workflow editing such as changing section order, validator rules, retry policy, or model parameters from the prompt-lab page.
- Broad CMS-style prompt management for every internal prompt artifact in the system.
- Replacing the teacher-facing generation form with the prompt-lab reviewer experience.

### Out of scope for this visual-icons requirement

- AI-generated images, illustrations, or stock-photo-like scene generation.
- Subject-specific generated diagrams, charts, or other content visuals that require new structured section payloads.
- Teacher-controlled icon uploads, per-guide icon theming, or market-specific icon packs.
- Icon choices that add new instructional facts, replace text labels, or become required for comprehension.
