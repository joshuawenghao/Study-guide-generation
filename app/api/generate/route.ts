import { z } from 'zod'
import { buildSystemPrompt } from '@/lib/config'
import { runPipeline } from '@/lib/orchestrator'
import { renderDocx } from '@/lib/renderer'
import type { GenerateRequest } from '@/lib/types'

export const maxDuration = 90

const SubCompetencySchema = z.object({
  id: z.string(),
  label: z.string(),
})

const LessonMetadataSchema = z.object({
  subject: z.string(),
  grade_level: z.number().int().min(1).max(12),
  market: z.string(),
  language: z.string(),
  unit_number: z.number().int(),
  unit_title: z.string(),
  lesson_number: z.number().int(),
  lesson_title: z.string(),
  lesson_code: z.string(),
})

const CurriculumSchema = z.object({
  competency_code: z.string(),
  competency_description: z.string(),
  sub_competencies: z.array(SubCompetencySchema),
})

const InstructionalDesignSchema = z.object({
  core_concept: z.string(),
  bloom_targets: z.tuple([z.string(), z.string(), z.string()]),
  essential_question_seed: z.string(),
})

const OptionalInputsSchema = z.object({
  vocabulary_seeds: z.array(z.string()).optional(),
  topic_domains: z.record(z.string()).optional(),
  tone_register: z.string().optional(),
  length_preset: z.enum(['standard', 'short', 'long']).optional(),
}).optional()

const GenerateRequestSchema = z.object({
  lesson_metadata: LessonMetadataSchema,
  curriculum: CurriculumSchema,
  instructional_design: InstructionalDesignSchema,
  optional: OptionalInputsSchema,
})

export async function POST(req: Request): Promise<Response> {
  try {
    const body = await req.json()
    const parsed = GenerateRequestSchema.safeParse(body)

    if (!parsed.success) {
      return Response.json(
        {
          success: false,
          error: `Invalid request: ${parsed.error.issues.map((i) => i.message).join(', ')}`,
        },
        { status: 400 }
      )
    }

    const generateRequest = parsed.data as GenerateRequest

    const systemPrompt = buildSystemPrompt({
      brand: 'Study Guide Generator',
      market: generateRequest.lesson_metadata.market,
      grade_level: generateRequest.lesson_metadata.grade_level,
      subject: generateRequest.lesson_metadata.subject,
    })

    const { plan, blueprint, sections, warnings } = await runPipeline(
      generateRequest,
      systemPrompt
    )

    const docxBuffer = await renderDocx({
      plan,
      blueprint,
      sections,
      lessonMetadata: generateRequest.lesson_metadata,
    })

    const docxBase64 = docxBuffer.toString('base64')

    return Response.json({
      success: true,
      plan,
      blueprint,
      sections,
      docxBase64,
      warnings,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error occurred'
    return Response.json({ success: false, error: message }, { status: 500 })
  }
}
