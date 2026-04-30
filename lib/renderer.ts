import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  PageBreak,
  ShadingType,
  UnderlineType,
  NumberFormat,
} from 'docx'
import type { Blueprint, LessonMetadata, SectionOutput, SectionPlan, SectionType } from './types'

// ── Helper functions ──────────────────────────────────────────

function heading1(text: string): Paragraph {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
  })
}

function heading2(text: string): Paragraph {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 150 },
  })
}

function heading3(text: string): Paragraph {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
  })
}

function bodyParagraph(text: string): Paragraph {
  return new Paragraph({
    children: [new TextRun({ text, size: 24 })],
    spacing: { before: 100, after: 100 },
  })
}

function boldParagraph(text: string): Paragraph {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 24 })],
    spacing: { before: 100, after: 100 },
  })
}

function bulletParagraph(text: string): Paragraph {
  return new Paragraph({
    children: [new TextRun({ text, size: 24 })],
    bullet: { level: 0 },
    spacing: { before: 60, after: 60 },
  })
}

function numberedParagraph(number: number, text: string): Paragraph {
  return new Paragraph({
    children: [
      new TextRun({ text: `${number}. `, bold: true, size: 24 }),
      new TextRun({ text, size: 24 }),
    ],
    spacing: { before: 80, after: 80 },
  })
}

function shadedBox(text: string): Paragraph {
  return new Paragraph({
    children: [new TextRun({ text, size: 24, italics: true })],
    shading: {
      type: ShadingType.SOLID,
      color: 'F2F2F2',
      fill: 'F2F2F2',
    },
    spacing: { before: 150, after: 150 },
    indent: { left: 300, right: 300 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 6, color: 'CCCCCC' },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: 'CCCCCC' },
      left: { style: BorderStyle.SINGLE, size: 6, color: 'CCCCCC' },
      right: { style: BorderStyle.SINGLE, size: 6, color: 'CCCCCC' },
    },
  })
}

function pageBreakParagraph(): Paragraph {
  return new Paragraph({
    children: [new PageBreak()],
  })
}

function simpleTableCell(text: string, bold = false, shade = false): TableCell {
  return new TableCell({
    children: [
      new Paragraph({
        children: [new TextRun({ text, bold, size: 22 })],
        spacing: { before: 60, after: 60 },
      }),
    ],
    shading: shade
      ? { type: ShadingType.SOLID, color: 'E8E8E8', fill: 'E8E8E8' }
      : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
  })
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function safeContent(output: SectionOutput): any {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return output.content as any
}

// ── Section renderer functions ────────────────────────────────

function renderIntro(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const introduction: string = content?.introduction ?? ''
  const paragraphs = introduction.split('\n\n').filter(Boolean)
  return [
    heading2('Introduction'),
    ...paragraphs.map((p) => bodyParagraph(p)),
  ]
}

function renderLearningTargets(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const competency: string = content?.learning_competency ?? ''
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const targets: Array<{ number: number; statement: string }> = content?.learning_targets ?? []

  return [
    heading2('Learning Targets'),
    ...(competency ? [boldParagraph(competency)] : []),
    ...targets.map((t) => bulletParagraph(`${t.statement}`)),
  ]
}

function renderWarmup(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.activity_title ?? 'Warm-Up Activity'
  const instructions: string = content?.instructions ?? ''
  const purpose: string = content?.purpose ?? ''

  const steps = instructions
    .split(/\d+\.\s+/)
    .filter(Boolean)
    .map((s, i) => numberedParagraph(i + 1, s.trim()))

  return [
    heading2('Warm-Up: ' + title),
    ...(steps.length > 0 ? steps : [bodyParagraph(instructions)]),
    ...(purpose ? [new Paragraph({
      children: [
        new TextRun({ text: 'Purpose: ', bold: true, size: 24 }),
        new TextRun({ text: purpose, size: 24, italics: true }),
      ],
      spacing: { before: 100, after: 100 },
    })] : []),
  ]
}

function renderVocabularyBox(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const vocab: Array<{ word: string; part_of_speech: string; definition: string; example_sentence: string }> =
    content?.vocabulary_box ?? []

  const headerRow = new TableRow({
    children: [
      simpleTableCell('Word', true, true),
      simpleTableCell('Part of Speech', true, true),
      simpleTableCell('Definition', true, true),
      simpleTableCell('Example Sentence', true, true),
    ],
    tableHeader: true,
  })

  const dataRows = vocab.map(
    (v) =>
      new TableRow({
        children: [
          simpleTableCell(v.word ?? ''),
          simpleTableCell(v.part_of_speech ?? ''),
          simpleTableCell(v.definition ?? ''),
          simpleTableCell(v.example_sentence ?? ''),
        ],
      })
  )

  const table = new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  })

  return [heading2('Vocabulary Box'), table]
}

function renderConceptExplainer(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.section_title ?? 'Concept Explainer'
  const opening: string = content?.opening_paragraph ?? ''
  const overview: string = content?.concept_overview ?? ''

  return [
    heading2(title),
    ...(opening ? [bodyParagraph(opening)] : []),
    ...(overview ? [bodyParagraph(overview)] : []),
  ]
}

function renderSubconceptBlock(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.subconcept_title ?? 'Subconcept'
  const explanation: string = content?.explanation ?? ''
  const exampleText: string = content?.example_text ?? ''
  const analysis: string = content?.analysis ?? ''

  return [
    heading3(title),
    ...(explanation ? [bodyParagraph(explanation)] : []),
    ...(exampleText
      ? [
          new Paragraph({
            children: [new TextRun({ text: 'Example:', bold: true, size: 24 })],
            spacing: { before: 100, after: 60 },
          }),
          shadedBox(exampleText),
        ]
      : []),
    ...(analysis ? [bodyParagraph(analysis)] : []),
  ]
}

function renderWorkedExample(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.example_title ?? 'Worked Example'
  const problem: string = content?.problem_statement ?? ''
  const steps: Array<{ step: number; action: string; explanation: string }> =
    content?.solution_steps ?? []
  const answer: string = content?.answer ?? ''

  return [
    heading2(title),
    ...(problem ? [new Paragraph({
      children: [
        new TextRun({ text: 'Problem: ', bold: true, size: 24 }),
        new TextRun({ text: problem, size: 24 }),
      ],
      spacing: { before: 120, after: 100 },
    })] : []),
    ...(steps.length > 0 ? [
      new Paragraph({
        children: [new TextRun({ text: 'Solution:', bold: true, size: 24 })],
        spacing: { before: 120, after: 60 },
      }),
      ...steps.map((s) =>
        new Paragraph({
          children: [
            new TextRun({ text: `Step ${s.step}: `, bold: true, size: 24 }),
            new TextRun({ text: `${s.action} `, size: 24 }),
            new TextRun({ text: `— ${s.explanation}`, size: 24, italics: true }),
          ],
          spacing: { before: 60, after: 60 },
          indent: { left: 300 },
        })
      ),
    ] : []),
    ...(answer ? [shadedBox(`Answer: ${answer}`)] : []),
  ]
}

function renderPracticeProblems(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const problems: Array<{ number: number; question: string; type: string }> =
    content?.problems ?? []

  return [
    heading2('Practice Problems'),
    ...problems.map((p) =>
      new Paragraph({
        children: [
          new TextRun({ text: `${p.number}. `, bold: true, size: 24 }),
          new TextRun({ text: p.question, size: 24 }),
          new TextRun({ text: ` (${p.type.replace(/_/g, ' ')})`, size: 20, italics: true, color: '666666' }),
        ],
        spacing: { before: 100, after: 100 },
      })
    ),
  ]
}

function renderExperimentDesign(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.experiment_title ?? 'Experiment'
  const objective: string = content?.objective ?? ''
  const materials: string[] = content?.materials ?? []
  const procedure: Array<{ step: number; instruction: string }> = content?.procedure ?? []
  const obsTable: { columns: string[]; rows: number } = content?.observations_table ?? { columns: [], rows: 3 }
  const analysisQuestions: string[] = content?.analysis_questions ?? []

  const obsColumns = obsTable.columns ?? []
  const obsRows = obsTable.rows ?? 3

  const tableHeaderRow = new TableRow({
    children: obsColumns.map((col: string) => simpleTableCell(col, true, true)),
    tableHeader: true,
  })
  const emptyDataRows = Array.from({ length: obsRows }, () =>
    new TableRow({
      children: obsColumns.map(() => simpleTableCell('')),
    })
  )
  const observationTable = new Table({
    rows: [tableHeaderRow, ...emptyDataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  })

  return [
    heading2(title),
    ...(objective ? [new Paragraph({
      children: [
        new TextRun({ text: 'Objective: ', bold: true, size: 24 }),
        new TextRun({ text: objective, size: 24 }),
      ],
      spacing: { before: 100, after: 100 },
    })] : []),
    ...(materials.length > 0 ? [
      new Paragraph({
        children: [new TextRun({ text: 'Materials:', bold: true, size: 24 })],
        spacing: { before: 150, after: 60 },
      }),
      ...materials.map((m) => bulletParagraph(m)),
    ] : []),
    ...(procedure.length > 0 ? [
      new Paragraph({
        children: [new TextRun({ text: 'Procedure:', bold: true, size: 24 })],
        spacing: { before: 150, after: 60 },
      }),
      ...procedure.map((step) => numberedParagraph(step.step, step.instruction)),
    ] : []),
    ...(obsColumns.length > 0 ? [
      new Paragraph({
        children: [new TextRun({ text: 'Observations:', bold: true, size: 24 })],
        spacing: { before: 150, after: 60 },
      }),
      observationTable,
    ] : []),
    ...(analysisQuestions.length > 0 ? [
      new Paragraph({
        children: [new TextRun({ text: 'Analysis Questions:', bold: true, size: 24 })],
        spacing: { before: 150, after: 60 },
      }),
      ...analysisQuestions.map((q, i) => numberedParagraph(i + 1, q)),
    ] : []),
  ]
}

function renderReadingPassage(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.passage_title ?? 'Reading Passage'
  const body: string = content?.passage_body ?? ''
  const purpose: string = content?.purpose_label ?? ''

  const paragraphs = body.split('\n\n').filter(Boolean)

  return [
    heading2(title),
    ...(purpose ? [new Paragraph({
      children: [
        new TextRun({ text: `Purpose: `, bold: true, size: 22, color: '555555' }),
        new TextRun({ text: purpose, size: 22, italics: true, color: '555555' }),
      ],
      spacing: { before: 60, after: 100 },
    })] : []),
    ...paragraphs.map((p) => bodyParagraph(p)),
  ]
}

function renderPassageQuestions(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const questions: Array<{ number: number; question: string; type: string }> =
    content?.questions ?? []

  return [
    heading2('Comprehension Questions'),
    ...questions.map((q) =>
      new Paragraph({
        children: [
          new TextRun({ text: `${q.number}. `, bold: true, size: 24 }),
          new TextRun({ text: q.question, size: 24 }),
        ],
        spacing: { before: 100, after: 200 },
      })
    ),
  ]
}

function renderStrategyList(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const strategies: Array<{ name: string; description: string; signal_words: string[] }> =
    content?.strategies ?? []

  const headerRow = new TableRow({
    children: [
      simpleTableCell('Strategy', true, true),
      simpleTableCell('Description', true, true),
      simpleTableCell('Signal Words', true, true),
    ],
    tableHeader: true,
  })

  const dataRows = strategies.map(
    (s) =>
      new TableRow({
        children: [
          simpleTableCell(s.name ?? ''),
          simpleTableCell(s.description ?? ''),
          simpleTableCell((s.signal_words ?? []).join(', ')),
        ],
      })
  )

  const table = new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  })

  return [heading2('Reading Strategies'), table]
}

function renderDeepDive(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.section_title ?? 'Deep Dive'
  const body: string = content?.body ?? ''

  const paragraphs = body.split('\n\n').filter(Boolean)
  return [heading2(title), ...paragraphs.map((p) => bodyParagraph(p))]
}

function renderCheckIn(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const question: string = content?.question ?? ''
  const starter: string = content?.sentence_starter ?? ''

  return [
    heading2('Check-In'),
    ...(question ? [shadedBox(question)] : []),
    ...(starter ? [new Paragraph({
      children: [
        new TextRun({ text: 'Sentence starter: ', bold: true, size: 24 }),
        new TextRun({ text: starter, size: 24, italics: true }),
      ],
      spacing: { before: 100, after: 100 },
    })] : []),
  ]
}

function renderKeyPoints(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const points: Array<{ number: number; statement: string }> = content?.key_points ?? []

  return [
    heading2('Key Points'),
    ...points.map((p) =>
      new Paragraph({
        children: [
          new TextRun({ text: `${p.number}. `, bold: true, size: 24 }),
          new TextRun({ text: p.statement, bold: true, size: 24 }),
        ],
        spacing: { before: 100, after: 100 },
      })
    ),
  ]
}

function renderAssessmentPassage(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const title: string = content?.passage_title ?? 'Assessment Passage'
  const body: string = content?.passage_body ?? ''
  const purpose: string = content?.purpose_label ?? ''

  const paragraphs = body.split('\n\n').filter(Boolean)

  return [
    pageBreakParagraph(),
    heading2(title),
    ...(purpose ? [new Paragraph({
      children: [
        new TextRun({ text: `Purpose: `, bold: true, size: 22, color: '555555' }),
        new TextRun({ text: purpose, size: 22, italics: true, color: '555555' }),
      ],
      spacing: { before: 60, after: 100 },
    })] : []),
    ...paragraphs.map((p) => bodyParagraph(p)),
  ]
}

function renderAssessmentQuestions(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const questions: Array<{ number: number; question: string; type: string }> =
    content?.questions ?? []

  return [
    heading2('Assessment Questions'),
    ...questions.map((q) =>
      new Paragraph({
        children: [
          new TextRun({ text: `${q.number}. `, bold: true, size: 24 }),
          new TextRun({ text: q.question, size: 24 }),
        ],
        spacing: { before: 100, after: 200 },
      })
    ),
  ]
}

function renderStepUp(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const prompt: string = content?.prompt ?? ''

  return [
    heading2('Step Up'),
    ...(prompt ? [shadedBox(prompt)] : []),
  ]
}

function renderSelfAssessment(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const rows: Array<{ skill: string; columns: string[] }> =
    content?.self_assessment?.rows ?? []
  const stems: string[] = content?.reflection_stems ?? []

  const headerRow = new TableRow({
    children: [
      simpleTableCell('Skill / Learning Target', true, true),
      simpleTableCell('Needs Assistance', true, true),
      simpleTableCell('Minimal Understanding', true, true),
      simpleTableCell('Confident', true, true),
    ],
    tableHeader: true,
  })

  const dataRows = rows.map(
    (r) =>
      new TableRow({
        children: [
          simpleTableCell(r.skill ?? ''),
          simpleTableCell(''),
          simpleTableCell(''),
          simpleTableCell(''),
        ],
      })
  )

  const table = new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  })

  return [
    heading2('Self-Assessment'),
    table,
    ...(stems.length > 0 ? [
      new Paragraph({
        children: [new TextRun({ text: 'Reflection Stems:', bold: true, size: 24 })],
        spacing: { before: 200, after: 80 },
      }),
      ...stems.map((s) => bulletParagraph(s)),
    ] : []),
  ]
}

function renderAnswerKey(output: SectionOutput): (Paragraph | Table)[] {
  const content = safeContent(output)
  const answers: Array<{ section_id: string; question: string; possible_answer: string }> =
    content?.answers ?? []

  const answerElements: (Paragraph | Table)[] = [
    pageBreakParagraph(),
    heading1('Answer Key'),
  ]

  for (const answer of answers) {
    answerElements.push(
      new Paragraph({
        children: [new TextRun({ text: answer.question ?? '', size: 24, italics: true })],
        spacing: { before: 150, after: 60 },
      })
    )
    answerElements.push(
      new Paragraph({
        children: [new TextRun({ text: answer.possible_answer ?? '', size: 24 })],
        spacing: { before: 60, after: 120 },
        indent: { left: 200 },
      })
    )
  }

  return answerElements
}

// ── Section renderer map ──────────────────────────────────────

type SectionRendererFn = (output: SectionOutput) => (Paragraph | Table)[]

const SECTION_RENDERER_MAP: Record<SectionType, SectionRendererFn> = {
  intro: renderIntro,
  learning_targets: renderLearningTargets,
  warmup: renderWarmup,
  vocabulary_box: renderVocabularyBox,
  concept_explainer: renderConceptExplainer,
  subconcept_block: renderSubconceptBlock,
  worked_example: renderWorkedExample,
  practice_problems: renderPracticeProblems,
  experiment_design: renderExperimentDesign,
  reading_passage: renderReadingPassage,
  passage_questions: renderPassageQuestions,
  strategy_list: renderStrategyList,
  deep_dive: renderDeepDive,
  check_in: renderCheckIn,
  key_points: renderKeyPoints,
  assessment_passage: renderAssessmentPassage,
  assessment_questions: renderAssessmentQuestions,
  step_up: renderStepUp,
  self_assessment: renderSelfAssessment,
  answer_key: renderAnswerKey,
}

// ── Main render function ──────────────────────────────────────

export async function renderDocx(params: {
  plan: SectionPlan
  blueprint: Blueprint
  sections: SectionOutput[]
  lessonMetadata: LessonMetadata
}): Promise<Buffer> {
  const { plan, blueprint, sections, lessonMetadata } = params

  // Build a lookup map for quick section access
  const sectionMap = new Map<string, SectionOutput>()
  for (const s of sections) {
    sectionMap.set(s.section_id, s)
  }

  // Title page elements
  const titleElements: (Paragraph | Table)[] = [
    new Paragraph({
      children: [
        new TextRun({
          text: blueprint.title || lessonMetadata.lesson_title,
          bold: true,
          size: 48,
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { before: 400, after: 200 },
    }),
    new Paragraph({
      children: [
        new TextRun({
          text: `${lessonMetadata.subject} | Grade ${lessonMetadata.grade_level} | ${lessonMetadata.market}`,
          size: 28,
          color: '555555',
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { before: 100, after: 100 },
    }),
    new Paragraph({
      children: [
        new TextRun({
          text: `Unit ${lessonMetadata.unit_number}: ${lessonMetadata.unit_title} — Lesson ${lessonMetadata.lesson_number}`,
          size: 24,
          color: '777777',
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { before: 60, after: 60 },
    }),
    new Paragraph({
      children: [
        new TextRun({
          text: `Essential Question: ${blueprint.essential_question}`,
          size: 24,
          italics: true,
          color: '333333',
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 400 },
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ]

  // Iterate plan sorted by order
  const sortedPlan = [...plan].sort((a, b) => a.order - b.order)
  const sectionElements: (Paragraph | Table)[] = []

  for (const spec of sortedPlan) {
    const output = sectionMap.get(spec.section_id)
    if (!output) {
      // Section missing — add a placeholder
      sectionElements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `[Section "${spec.section_id}" not generated]`,
              color: 'FF0000',
              italics: true,
              size: 22,
            }),
          ],
          spacing: { before: 100, after: 100 },
        })
      )
      continue
    }

    const rendererFn = SECTION_RENDERER_MAP[spec.section_type]
    if (!rendererFn) {
      sectionElements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `[No renderer for section_type "${spec.section_type}"]`,
              color: 'FF0000',
              italics: true,
              size: 22,
            }),
          ],
          spacing: { before: 100, after: 100 },
        })
      )
      continue
    }

    const elements = rendererFn(output)
    sectionElements.push(...elements)
  }

  const doc = new Document({
    sections: [
      {
        children: [...titleElements, ...sectionElements],
      },
    ],
    styles: {
      paragraphStyles: [
        {
          id: 'Normal',
          name: 'Normal',
          run: {
            font: 'Calibri',
            size: 24,
          },
        },
      ],
    },
  })

  const buffer = await Packer.toBuffer(doc)
  return buffer
}
