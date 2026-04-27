'use client'

import { useState } from 'react'
import InputForm from '@/components/InputForm'
import ProgressTracker from '@/components/ProgressTracker'
import PreviewPanel from '@/components/PreviewPanel'
import DownloadButton from '@/components/DownloadButton'
import type {
  Blueprint,
  GenerateRequest,
  GenerateResponse,
  ProgressStage,
  SectionOutput,
  SectionPlan,
} from '@/lib/types'

export default function HomePage() {
  const [stage, setStage] = useState<ProgressStage>('idle')
  const [plan, setPlan] = useState<SectionPlan | undefined>()
  const [blueprint, setBlueprint] = useState<Blueprint | undefined>()
  const [sections, setSections] = useState<SectionOutput[]>([])
  const [docxBase64, setDocxBase64] = useState<string | undefined>()
  const [error, setError] = useState<string | undefined>()
  const [warnings, setWarnings] = useState<string[]>([])
  const [lessonTitle, setLessonTitle] = useState<string>('')

  async function handleSubmit(data: GenerateRequest) {
    // Reset state
    setStage('planning')
    setPlan(undefined)
    setBlueprint(undefined)
    setSections([])
    setDocxBase64(undefined)
    setError(undefined)
    setWarnings([])
    setLessonTitle(data.lesson_metadata.lesson_title)

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      const result: GenerateResponse = await response.json()

      if (!result.success) {
        setStage('error')
        setError(result.error ?? 'Generation failed')
        return
      }

      if (result.plan) setPlan(result.plan)
      if (result.blueprint) setBlueprint(result.blueprint)
      if (result.sections) setSections(result.sections)
      if (result.docxBase64) setDocxBase64(result.docxBase64)
      if (result.warnings) setWarnings(result.warnings)

      setStage('done')
    } catch (err) {
      setStage('error')
      setError(err instanceof Error ? err.message : 'Network error. Please try again.')
    }
  }

  const isLoading =
    stage !== 'idle' && stage !== 'done' && stage !== 'error'

  const filename = `study-guide-${lessonTitle.replace(/\s+/g, '-').toLowerCase() || 'lesson'}.docx`

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left column: Input form */}
      <div className="space-y-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-5">Lesson Details</h2>
          <InputForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
      </div>

      {/* Right column: Progress + Preview + Download */}
      <div className="space-y-4">
        {stage !== 'idle' && (
          <ProgressTracker
            stage={stage}
            plan={plan}
            completedSections={sections.map((s) => s.section_id)}
            error={error}
          />
        )}

        {(blueprint || sections.length > 0) && (
          <PreviewPanel blueprint={blueprint} sections={sections} plan={plan} />
        )}

        {docxBase64 && stage === 'done' && (
          <div className="space-y-3">
            <DownloadButton docxBase64={docxBase64} filename={filename} />

            {warnings.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-yellow-800 mb-2">
                  Generation Warnings ({warnings.length})
                </p>
                <ul className="space-y-1">
                  {warnings.map((w, i) => (
                    <li key={i} className="text-sm text-yellow-700 flex gap-2">
                      <span>⚠</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {stage === 'idle' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 text-center">
            <div className="text-4xl mb-3">📚</div>
            <h3 className="text-base font-semibold text-blue-800 mb-1">
              Ready to Generate
            </h3>
            <p className="text-sm text-blue-600">
              Fill in the lesson details on the left and click Generate Study Guide to create a downloadable .docx study guide.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
