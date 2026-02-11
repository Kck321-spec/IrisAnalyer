interface PatientFormProps {
  patientName: string
  setPatientName: (name: string) => void
  notes: string
  setNotes: (notes: string) => void
}

function PatientForm({ patientName, setPatientName, notes, setNotes }: PatientFormProps) {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="patientName" className="block text-sm font-medium text-gray-300 mb-1">
          Patient Name *
        </label>
        <input
          type="text"
          id="patientName"
          value={patientName}
          onChange={(e) => setPatientName(e.target.value)}
          placeholder="Enter patient name"
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-300 mb-1">
          Notes (optional)
        </label>
        <textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Any additional notes or symptoms..."
          rows={4}
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>
    </div>
  )
}

export default PatientForm
