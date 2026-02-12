import { useState } from 'react'
import DoctorInsightCard from './DoctorInsightCard'

// Helper to ensure value is always an array
const ensureArray = (value: unknown): unknown[] => {
  if (Array.isArray(value)) return value
  if (value === null || value === undefined) return []
  if (typeof value === 'string') return value ? [value] : []
  if (typeof value === 'object') return Object.values(value)
  return [value]
}

// Helper to ensure value is always an object
const ensureObject = (value: unknown): Record<string, unknown> => {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return {}
}

interface DoctorAnalysis {
  doctor_name: string
  methodology: string
  findings: string[] | unknown
  organ_correlations: Record<string, string> | unknown
  recommendations: string[] | unknown
  confidence_notes: string
}

interface AnalysisPanelProps {
  analyses: {
    peczely: DoctorAnalysis
    jensen: DoctorAnalysis
    morse: DoctorAnalysis
  }
}

function AnalysisPanel({ analyses }: AnalysisPanelProps) {
  const [activeTab, setActiveTab] = useState<'peczely' | 'jensen' | 'morse'>('peczely')

  const doctors = [
    {
      key: 'peczely' as const,
      name: 'Peczely',
      fullName: 'Ignaz von Peczely',
      years: '1826-1911',
      color: 'blue',
      icon: '🦉',
    },
    {
      key: 'jensen' as const,
      name: 'Jensen',
      fullName: 'Bernard Jensen',
      years: '1908-2001',
      color: 'green',
      icon: '📊',
    },
    {
      key: 'morse' as const,
      name: 'Morse',
      fullName: 'Dr. Robert Morse',
      years: 'Active',
      color: 'purple',
      icon: '🍇',
    },
  ]

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Tab Headers */}
      <div className="flex border-b border-gray-700">
        {doctors.map((doctor) => (
          <button
            key={doctor.key}
            onClick={() => setActiveTab(doctor.key)}
            className={`
              flex-1 px-6 py-4 text-center transition-colors relative
              ${
                activeTab === doctor.key
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-750'
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <span className="text-xl">{doctor.icon}</span>
              <div>
                <div className="font-semibold">{doctor.name}</div>
                <div className="text-xs text-gray-500">{doctor.years}</div>
              </div>
            </div>
            {activeTab === doctor.key && (
              <div
                className={`absolute bottom-0 left-0 right-0 h-1 bg-${doctor.color}-500`}
                style={{
                  backgroundColor:
                    doctor.color === 'blue'
                      ? '#3b82f6'
                      : doctor.color === 'green'
                      ? '#22c55e'
                      : '#a855f7',
                }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {doctors.map((doctor) => (
          <div
            key={doctor.key}
            className={activeTab === doctor.key ? 'block' : 'hidden'}
          >
            <DoctorInsightCard
              analysis={analyses[doctor.key]}
              doctorInfo={doctor}
            />
          </div>
        ))}
      </div>

      {/* Combined Summary Section */}
      <div className="border-t border-gray-700 p-6 bg-gradient-to-b from-gray-800 to-gray-900">
        <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
          <span>📋</span> Combined Analysis Summary
        </h3>

        {/* All Organs Mentioned */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-3 text-yellow-400">
            Organs & Systems of Interest
          </h4>
          <div className="bg-gray-700/50 rounded-lg p-4">
            {(() => {
              const allOrgans = new Map<string, string[]>()
              doctors.forEach((doctor) => {
                const correlations = ensureObject(analyses[doctor.key].organ_correlations)
                Object.entries(correlations).forEach(
                  ([organ, condition]) => {
                    const key = organ.toLowerCase().trim()
                    if (!allOrgans.has(key)) {
                      allOrgans.set(key, [])
                    }
                    const condStr = typeof condition === 'string' ? condition : JSON.stringify(condition)
                    allOrgans.get(key)?.push(`${doctor.name}: ${condStr}`)
                  }
                )
              })

              if (allOrgans.size === 0) {
                return <p className="text-gray-500 italic">No organ correlations identified</p>
              }

              return (
                <div className="space-y-3">
                  {Array.from(allOrgans.entries()).map(([organ, notes]) => (
                    <div key={organ} className="border-l-2 border-yellow-500 pl-3">
                      <div className="font-medium text-white capitalize">{organ}</div>
                      <div className="text-sm text-gray-300 space-y-1">
                        {notes.map((note, idx) => (
                          <div key={idx} className="flex items-start gap-2">
                            <span className="text-yellow-500">•</span>
                            <span>{note}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })()}
          </div>
        </div>

        {/* Key Findings from All Doctors */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-3 text-blue-400">
            Key Findings Across All Methodologies
          </h4>
          <div className="bg-gray-700/50 rounded-lg p-4">
            <div className="space-y-4">
              {doctors.map((doctor) => {
                const findings = ensureArray(analyses[doctor.key].findings)
                if (findings.length === 0) return null

                return (
                  <div key={doctor.key}>
                    <div className="flex items-center gap-2 mb-2">
                      <span>{doctor.icon}</span>
                      <span className="font-medium text-gray-300">{doctor.fullName}:</span>
                    </div>
                    <ul className="ml-6 space-y-1">
                      {findings.map((finding, idx) => (
                        <li key={idx} className="text-sm text-gray-400 flex items-start gap-2">
                          <span className="text-blue-400">→</span>
                          <span>{typeof finding === 'string' ? finding : JSON.stringify(finding)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Combined Recommendations - Organized by Body Area */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-3 text-green-400">
            Combined Recommendations by Body System
          </h4>
          <div className="bg-gray-700/50 rounded-lg p-4">
            {(() => {
              // Define body system categories with keywords
              const categories: { name: string; icon: string; keywords: string[] }[] = [
                { name: 'Digestive System', icon: '🫃', keywords: ['digest', 'stomach', 'bowel', 'colon', 'intestin', 'gut', 'liver', 'gallbladder', 'bile', 'enzyme', 'probiotic', 'fiber', 'food combining', 'eating'] },
                { name: 'Lymphatic System', icon: '💧', keywords: ['lymph', 'lymphatic', 'drainage', 'congestion', 'swelling', 'rebounding', 'skin brush', 'dry brush'] },
                { name: 'Kidneys & Adrenals', icon: '🫘', keywords: ['kidney', 'adrenal', 'urinary', 'bladder', 'filtration', 'watermelon', 'hydration', 'water'] },
                { name: 'Nervous System', icon: '🧠', keywords: ['nerve', 'nervous', 'stress', 'anxiety', 'relax', 'calm', 'sleep', 'rest', 'meditation', 'magnesium', 'brain', 'mental'] },
                { name: 'Cardiovascular', icon: '❤️', keywords: ['heart', 'cardio', 'circulation', 'blood', 'cholesterol', 'vascular', 'artery', 'vein'] },
                { name: 'Respiratory', icon: '🫁', keywords: ['lung', 'breath', 'respiratory', 'bronchi', 'oxygen', 'sinus'] },
                { name: 'Endocrine & Hormonal', icon: '⚡', keywords: ['thyroid', 'hormone', 'gland', 'endocrine', 'pituitary', 'pancreas', 'blood sugar', 'insulin', 'metabol'] },
                { name: 'Diet & Nutrition', icon: '🥗', keywords: ['diet', 'fruit', 'vegetable', 'nutrition', 'vitamin', 'mineral', 'supplement', 'herb', 'food', 'eat', 'juice', 'fast', 'cleanse', 'detox'] },
                { name: 'Lifestyle & Exercise', icon: '🏃', keywords: ['exercise', 'movement', 'walk', 'yoga', 'lifestyle', 'habit', 'routine', 'physical'] },
                { name: 'Skin & Elimination', icon: '🧴', keywords: ['skin', 'eliminat', 'sweat', 'toxin', 'excret'] },
              ]

              // Collect all recommendations
              const allRecs: { doctor: string; rec: string }[] = []
              doctors.forEach((doctor) => {
                const recs = ensureArray(analyses[doctor.key].recommendations)
                recs.forEach((rec) => {
                  const recStr = typeof rec === 'string' ? rec : JSON.stringify(rec)
                  allRecs.push({ doctor: doctor.name, rec: recStr })
                })
              })

              if (allRecs.length === 0) {
                return <p className="text-gray-500 italic">No recommendations provided</p>
              }

              // Categorize recommendations
              const categorizedRecs = new Map<string, { doctor: string; rec: string }[]>()
              const uncategorized: { doctor: string; rec: string }[] = []

              allRecs.forEach((item) => {
                const recLower = item.rec.toLowerCase()
                let matched = false

                for (const category of categories) {
                  if (category.keywords.some(keyword => recLower.includes(keyword))) {
                    if (!categorizedRecs.has(category.name)) {
                      categorizedRecs.set(category.name, [])
                    }
                    categorizedRecs.get(category.name)?.push(item)
                    matched = true
                    break
                  }
                }

                if (!matched) {
                  uncategorized.push(item)
                }
              })

              return (
                <div className="space-y-6">
                  {categories.map((category) => {
                    const recs = categorizedRecs.get(category.name)
                    if (!recs || recs.length === 0) return null

                    return (
                      <div key={category.name}>
                        <div className="flex items-center gap-2 mb-3 border-b border-gray-600 pb-2">
                          <span className="text-xl">{category.icon}</span>
                          <span className="font-semibold text-green-300">{category.name}</span>
                          <span className="text-gray-500 text-sm">({recs.length})</span>
                        </div>
                        <ul className="space-y-2 ml-2">
                          {recs.map((item, idx) => (
                            <li
                              key={idx}
                              className="flex items-start gap-3 bg-green-900/20 border border-green-800/50 rounded p-2"
                            >
                              <span className="text-green-400">✓</span>
                              <div>
                                <span className="text-gray-300">{item.rec}</span>
                                <span className="text-gray-500 text-xs ml-2">— {item.doctor}</span>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )
                  })}

                  {uncategorized.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-3 border-b border-gray-600 pb-2">
                        <span className="text-xl">📌</span>
                        <span className="font-semibold text-green-300">General Recommendations</span>
                        <span className="text-gray-500 text-sm">({uncategorized.length})</span>
                      </div>
                      <ul className="space-y-2 ml-2">
                        {uncategorized.map((item, idx) => (
                          <li
                            key={idx}
                            className="flex items-start gap-3 bg-green-900/20 border border-green-800/50 rounded p-2"
                          >
                            <span className="text-green-400">✓</span>
                            <div>
                              <span className="text-gray-300">{item.rec}</span>
                              <span className="text-gray-500 text-xs ml-2">— {item.doctor}</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-700">
          {doctors.map((doctor) => (
            <div key={doctor.key} className="text-center">
              <div className="text-2xl mb-1">{doctor.icon}</div>
              <div className="text-sm font-medium">{doctor.name}</div>
              <div className="text-xs text-gray-500">
                {ensureArray(analyses[doctor.key].findings).length} findings • {Object.keys(ensureObject(analyses[doctor.key].organ_correlations)).length} organs • {ensureArray(analyses[doctor.key].recommendations).length} recs
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AnalysisPanel
