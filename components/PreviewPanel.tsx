'use client'

import type { Blueprint, SectionOutput, SectionPlan } from '@/lib/types'

interface PreviewPanelProps {
  blueprint?: Blueprint
  sections?: SectionOutput[]
  plan?: SectionPlan
}

function truncate(text: string, maxLen: number): string {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getContentPreview(content: unknown): string {
  if (!content || typeof content !== 'object') return ''
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const c = content as any
  // Try common text fields in order of preference
  if (typeof c.introduction === 'string') return c.introduction
  if (typeof c.body === 'string') return c.body
  if (typeof c.passage_body === 'string') return c.passage_body
  if (typeof c.explanation === 'string') return c.explanation
  if (typeof c.opening_paragraph === 'string') return c.opening_paragraph
  if (typeof c.problem_statement === 'string') return c.problem_statement
  if (typeof c.objective === 'string') return c.objective
  if (typeof c.prompt === 'string') return c.prompt
  if (typeof c.question === 'string') return c.question
  // Fallback: stringify first value
  const firstVal = Object.values(c)[0]
  if (typeof firstVal === 'string') return firstVal
  return JSON.stringify(c).slice(0, 120)
}

export default function PreviewPanel({ blueprint, sections, plan }: PreviewPanelProps) {
  if (!blueprint && !sections) return null

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-5">
      <h2 className="text-base font-semibold text-gray-700">Preview</h2>

      {/* Blueprint summary */}
      {blueprint && (
        <div className="space-y-3">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{blueprint.title}</h3>
            <p className="text-sm text-gray-500 italic mt-1">{blueprint.essential_question}</p>
          </div>

          {blueprint.learning_targets && blueprint.learning_targets.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                Learning Targets
              </p>
              <ul className="space-y-1">
                {blueprint.learning_targets.map((lt) => (
                  <li key={lt.number} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-blue-500 font-medium">{lt.number}.</span>
                    <span>
                      I can <strong>{lt.bloom_verb}</strong> {lt.objective}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {blueprint.vocabulary && blueprint.vocabulary.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Vocabulary
              </p>
              <div className="flex flex-wrap gap-2">
                {blueprint.vocabulary.map((v) => (
                  <span
                    key={v.word}
                    className="inline-block bg-blue-100 text-blue-700 text-xs font-medium px-2 py-1 rounded-full"
                  >
                    {v.word}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sections list */}
      {sections && sections.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
            Generated Sections ({sections.length}{plan ? ` / ${plan.length}` : ''})
          </p>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {sections
              .slice()
              .sort((a, b) => a.order - b.order)
              .map((s) => {
                const preview = truncate(getContentPreview(s.content), 120)
                return (
                  <div
                    key={s.section_id}
                    className="border border-gray-100 rounded p-2.5 bg-gray-50"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded font-mono">
                        {s.section_type}
                      </span>
                      <span className="text-xs text-gray-500">{s.section_id}</span>
                    </div>
                    {preview && (
                      <p className="text-xs text-gray-600 leading-relaxed">{preview}</p>
                    )}
                  </div>
                )
              })}
          </div>
        </div>
      )}
    </div>
  )
}
