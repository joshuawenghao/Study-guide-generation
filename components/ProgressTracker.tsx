'use client'

import type { SectionPlan, ProgressStage } from '@/lib/types'

interface ProgressTrackerProps {
  stage: ProgressStage
  plan?: SectionPlan
  completedSections?: string[]
  error?: string
}

const STEPS: { key: ProgressStage | string; label: string }[] = [
  { key: 'planning', label: 'Planning sections' },
  { key: 'blueprint', label: 'Generating blueprint' },
  { key: 'sections', label: 'Writing sections' },
  { key: 'validating', label: 'Validating content' },
  { key: 'rendering', label: 'Rendering document' },
  { key: 'done', label: 'Ready to download' },
]

const STAGE_ORDER: Record<ProgressStage, number> = {
  idle: -1,
  planning: 0,
  blueprint: 1,
  sections: 2,
  validating: 3,
  rendering: 4,
  done: 5,
  error: 99,
}

export default function ProgressTracker({
  stage,
  plan,
  completedSections = [],
  error,
}: ProgressTrackerProps) {
  if (stage === 'idle') return null

  const currentOrder = STAGE_ORDER[stage]

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <h2 className="text-base font-semibold text-gray-700 mb-4">Generation Progress</h2>

      {stage === 'error' && error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700 font-medium">Error</p>
          <p className="text-sm text-red-600 mt-1">{error}</p>
        </div>
      )}

      <div className="space-y-3">
        {STEPS.map((step, index) => {
          const stepOrder = index
          const isDone = currentOrder > stepOrder || stage === 'done'
          const isActive = currentOrder === stepOrder && stage !== 'done' && stage !== 'error'
          const isPending = currentOrder < stepOrder && stage !== 'error'

          return (
            <div key={step.key}>
              <div className="flex items-center gap-3">
                {/* Step icon */}
                <div
                  className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                    isDone
                      ? 'bg-green-500 text-white'
                      : isActive
                      ? 'bg-blue-500 text-white animate-pulse'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {isDone ? '✓' : index + 1}
                </div>

                {/* Step label */}
                <span
                  className={`text-sm font-medium ${
                    isDone
                      ? 'text-green-700'
                      : isActive
                      ? 'text-blue-700'
                      : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Sub-list for sections step */}
              {step.key === 'sections' && isActive && plan && plan.length > 0 && (
                <div className="ml-9 mt-2 space-y-1">
                  {plan.map((spec) => {
                    const isCompleted = completedSections.includes(spec.section_id)
                    return (
                      <div key={spec.section_id} className="flex items-center gap-2">
                        <span
                          className={`text-xs ${
                            isCompleted ? 'text-green-600' : 'text-gray-400'
                          }`}
                        >
                          {isCompleted ? '✓' : '○'}
                        </span>
                        <span
                          className={`text-xs ${
                            isCompleted ? 'text-green-700' : 'text-gray-400'
                          }`}
                        >
                          {spec.section_id}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Sub-list for sections done */}
              {step.key === 'sections' && isDone && plan && plan.length > 0 && (
                <div className="ml-9 mt-1">
                  <span className="text-xs text-green-600">
                    {plan.length} section{plan.length !== 1 ? 's' : ''} generated
                  </span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
