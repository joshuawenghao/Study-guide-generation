'use client'

import { useState } from 'react'
import type { GenerateRequest, SubCompetency } from '@/lib/types'

interface InputFormProps {
  onSubmit: (data: GenerateRequest) => void
  isLoading: boolean
}

export default function InputForm({ onSubmit, isLoading }: InputFormProps) {
  const [subject, setSubject] = useState('')
  const [gradeLevel, setGradeLevel] = useState(6)
  const [market, setMarket] = useState('PH')
  const [language, setLanguage] = useState('en')
  const [unitNumber, setUnitNumber] = useState(1)
  const [unitTitle, setUnitTitle] = useState('')
  const [lessonNumber, setLessonNumber] = useState(1)
  const [lessonTitle, setLessonTitle] = useState('')
  const [lessonCode, setLessonCode] = useState('')

  const [competencyCode, setCompetencyCode] = useState('')
  const [competencyDescription, setCompetencyDescription] = useState('')
  const [subCompetencies, setSubCompetencies] = useState<SubCompetency[]>([
    { id: 'SC1', label: '' },
    { id: 'SC2', label: '' },
  ])

  const [coreConcept, setCoreConcept] = useState('')
  const [bloomTarget1, setBloomTarget1] = useState('')
  const [bloomTarget2, setBloomTarget2] = useState('')
  const [bloomTarget3, setBloomTarget3] = useState('')
  const [essentialQuestionSeed, setEssentialQuestionSeed] = useState('')

  const [showOptional, setShowOptional] = useState(false)
  const [vocabularySeeds, setVocabularySeeds] = useState('')
  const [toneRegister, setToneRegister] = useState('warm-formal')

  function addSubCompetency() {
    setSubCompetencies((prev) => [
      ...prev,
      { id: `SC${prev.length + 1}`, label: '' },
    ])
  }

  function removeSubCompetency(index: number) {
    setSubCompetencies((prev) => prev.filter((_, i) => i !== index))
  }

  function updateSubCompetency(index: number, field: 'id' | 'label', value: string) {
    setSubCompetencies((prev) =>
      prev.map((sc, i) => (i === index ? { ...sc, [field]: value } : sc))
    )
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const data: GenerateRequest = {
      lesson_metadata: {
        subject,
        grade_level: gradeLevel,
        market,
        language,
        unit_number: unitNumber,
        unit_title: unitTitle,
        lesson_number: lessonNumber,
        lesson_title: lessonTitle,
        lesson_code: lessonCode,
      },
      curriculum: {
        competency_code: competencyCode,
        competency_description: competencyDescription,
        sub_competencies: subCompetencies.filter((sc) => sc.label.trim() !== ''),
      },
      instructional_design: {
        core_concept: coreConcept,
        bloom_targets: [bloomTarget1, bloomTarget2, bloomTarget3],
        essential_question_seed: essentialQuestionSeed,
      },
      optional: {
        vocabulary_seeds: vocabularySeeds
          ? vocabularySeeds.split(',').map((s) => s.trim()).filter(Boolean)
          : undefined,
        tone_register: toneRegister || undefined,
      },
    }

    onSubmit(data)
  }

  const inputClass =
    'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1'
  const sectionClass = 'space-y-4'

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Lesson Metadata */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Lesson Metadata</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Subject *</label>
            <input
              type="text"
              className={inputClass}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Mathematics, English, Science"
              required
            />
          </div>
          <div>
            <label className={labelClass}>Grade Level (1–12) *</label>
            <input
              type="number"
              className={inputClass}
              value={gradeLevel}
              onChange={(e) => setGradeLevel(Number(e.target.value))}
              min={1}
              max={12}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Market *</label>
            <select
              className={inputClass}
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              required
            >
              <option value="PH">Philippines (PH)</option>
              <option value="JP">Japan (JP)</option>
              <option value="VN">Vietnam (VN)</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Language</label>
            <input
              type="text"
              className={inputClass}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="e.g. en, ja, vi"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Unit Number *</label>
            <input
              type="number"
              className={inputClass}
              value={unitNumber}
              onChange={(e) => setUnitNumber(Number(e.target.value))}
              min={1}
              required
            />
          </div>
          <div>
            <label className={labelClass}>Unit Title *</label>
            <input
              type="text"
              className={inputClass}
              value={unitTitle}
              onChange={(e) => setUnitTitle(e.target.value)}
              placeholder="e.g. Numbers and Operations"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Lesson Number *</label>
            <input
              type="number"
              className={inputClass}
              value={lessonNumber}
              onChange={(e) => setLessonNumber(Number(e.target.value))}
              min={1}
              required
            />
          </div>
          <div>
            <label className={labelClass}>Lesson Title *</label>
            <input
              type="text"
              className={inputClass}
              value={lessonTitle}
              onChange={(e) => setLessonTitle(e.target.value)}
              placeholder="e.g. Introduction to Fractions"
              required
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Lesson Code</label>
          <input
            type="text"
            className={inputClass}
            value={lessonCode}
            onChange={(e) => setLessonCode(e.target.value)}
            placeholder="e.g. MATH6-U1-L1"
          />
        </div>
      </div>

      {/* Curriculum */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Curriculum</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Competency Code *</label>
            <input
              type="text"
              className={inputClass}
              value={competencyCode}
              onChange={(e) => setCompetencyCode(e.target.value)}
              placeholder="e.g. M6NS-Ia-86"
              required
            />
          </div>
          <div className="col-span-1">
            <label className={labelClass}>Competency Description *</label>
            <input
              type="text"
              className={inputClass}
              value={competencyDescription}
              onChange={(e) => setCompetencyDescription(e.target.value)}
              placeholder="e.g. Identifies and compares fractions"
              required
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Sub-competencies</label>
          <div className="space-y-2">
            {subCompetencies.map((sc, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={sc.id}
                  onChange={(e) => updateSubCompetency(index, 'id', e.target.value)}
                  placeholder="ID"
                />
                <input
                  type="text"
                  className={`${inputClass} flex-1`}
                  value={sc.label}
                  onChange={(e) => updateSubCompetency(index, 'label', e.target.value)}
                  placeholder="Sub-competency label"
                />
                {subCompetencies.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeSubCompetency(index)}
                    className="text-red-500 hover:text-red-700 px-2 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addSubCompetency}
            className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            + Add sub-competency
          </button>
        </div>
      </div>

      {/* Instructional Design */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Instructional Design</h2>

        <div>
          <label className={labelClass}>Core Concept *</label>
          <textarea
            className={`${inputClass} h-20 resize-none`}
            value={coreConcept}
            onChange={(e) => setCoreConcept(e.target.value)}
            placeholder="e.g. Understanding that fractions represent parts of a whole or parts of a set"
            required
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className={labelClass}>Bloom Target 1 *</label>
            <input
              type="text"
              className={inputClass}
              value={bloomTarget1}
              onChange={(e) => setBloomTarget1(e.target.value)}
              placeholder="e.g. identify"
              required
            />
          </div>
          <div>
            <label className={labelClass}>Bloom Target 2 *</label>
            <input
              type="text"
              className={inputClass}
              value={bloomTarget2}
              onChange={(e) => setBloomTarget2(e.target.value)}
              placeholder="e.g. compare"
              required
            />
          </div>
          <div>
            <label className={labelClass}>Bloom Target 3 *</label>
            <input
              type="text"
              className={inputClass}
              value={bloomTarget3}
              onChange={(e) => setBloomTarget3(e.target.value)}
              placeholder="e.g. apply"
              required
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Essential Question Seed *</label>
          <input
            type="text"
            className={inputClass}
            value={essentialQuestionSeed}
            onChange={(e) => setEssentialQuestionSeed(e.target.value)}
            placeholder="e.g. How do fractions help us understand the world around us?"
            required
          />
        </div>
      </div>

      {/* Optional Inputs */}
      <div>
        <button
          type="button"
          onClick={() => setShowOptional(!showOptional)}
          className="text-sm text-gray-600 hover:text-gray-800 font-medium flex items-center gap-1"
        >
          <span>{showOptional ? '▼' : '▶'}</span>
          Optional Settings
        </button>

        {showOptional && (
          <div className="mt-3 space-y-4 pl-4 border-l-2 border-gray-200">
            <div>
              <label className={labelClass}>Vocabulary Seeds (comma-separated)</label>
              <input
                type="text"
                className={inputClass}
                value={vocabularySeeds}
                onChange={(e) => setVocabularySeeds(e.target.value)}
                placeholder="e.g. numerator, denominator, equivalent"
              />
            </div>
            <div>
              <label className={labelClass}>Tone Register</label>
              <input
                type="text"
                className={inputClass}
                value={toneRegister}
                onChange={(e) => setToneRegister(e.target.value)}
                placeholder="e.g. warm-formal"
              />
            </div>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
      >
        {isLoading ? 'Generating...' : 'Generate Study Guide'}
      </button>
    </form>
  )
}
