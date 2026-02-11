interface DoctorAnalysis {
  doctor_name: string
  methodology: string
  findings: (string | object)[]
  organ_correlations: Record<string, string | object>
  recommendations: (string | object)[]
  confidence_notes: string
}

// Helper to safely convert any value to a displayable string
const toDisplayString = (value: unknown): string => {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') {
    // Handle objects by extracting meaningful values
    const obj = value as Record<string, unknown>
    if (obj.condition) return String(obj.condition)
    if (obj.description) return String(obj.description)
    if (obj.notes) return String(obj.notes)
    // Fallback: join all string values
    return Object.values(obj)
      .filter(v => typeof v === 'string')
      .join(' - ') || JSON.stringify(value)
  }
  return String(value)
}

interface DoctorInfo {
  key: string
  name: string
  fullName: string
  years: string
  color: string
  icon: string
}

interface DoctorInsightCardProps {
  analysis: DoctorAnalysis
  doctorInfo: DoctorInfo
}

function DoctorInsightCard({ analysis, doctorInfo }: DoctorInsightCardProps) {
  const getBorderColor = () => {
    switch (doctorInfo.color) {
      case 'blue':
        return 'border-blue-500'
      case 'green':
        return 'border-green-500'
      case 'purple':
        return 'border-purple-500'
      default:
        return 'border-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`border-l-4 ${getBorderColor()} pl-4`}>
        <h3 className="text-xl font-bold">{analysis.doctor_name}</h3>
        <p className="text-gray-400 text-sm">{analysis.methodology}</p>
      </div>

      {/* Findings */}
      <div>
        <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <span>🔍</span> Key Findings
        </h4>
        {analysis.findings.length > 0 ? (
          <ul className="space-y-2">
            {analysis.findings.map((finding, index) => (
              <li
                key={index}
                className="bg-gray-700 rounded-lg p-3 flex items-start gap-3"
              >
                <span className="text-blue-400 font-bold">{index + 1}.</span>
                <span>{toDisplayString(finding)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 italic">No specific findings reported</p>
        )}
      </div>

      {/* Organ Correlations */}
      <div>
        <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <span>🫀</span> Organ Correlations
        </h4>
        {Object.keys(analysis.organ_correlations).length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(analysis.organ_correlations).map(([organ, condition]) => (
              <div
                key={organ}
                className="bg-gray-700 rounded-lg p-3 flex items-center gap-3"
              >
                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                <div>
                  <span className="font-medium">{organ}:</span>
                  <span className="text-gray-300 ml-2">{toDisplayString(condition)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 italic">No organ correlations identified</p>
        )}
      </div>

      {/* Recommendations */}
      <div>
        <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <span>💡</span> Recommendations
        </h4>
        {analysis.recommendations.length > 0 ? (
          <ul className="space-y-2">
            {analysis.recommendations.map((rec, index) => (
              <li
                key={index}
                className="bg-green-900/30 border border-green-700 rounded-lg p-3 flex items-start gap-3"
              >
                <span className="text-green-400">✓</span>
                <span>{toDisplayString(rec)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 italic">No specific recommendations</p>
        )}
      </div>

      {/* Confidence Notes */}
      <div className="bg-gray-700/50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-400 mb-2">
          Analysis Notes
        </h4>
        <p className="text-gray-300 text-sm">{toDisplayString(analysis.confidence_notes)}</p>
      </div>
    </div>
  )
}

export default DoctorInsightCard
