import { useState } from 'react'

interface IrisViewerProps {
  leftImage: string | null
  rightImage: string | null
}

function IrisViewer({ leftImage, rightImage }: IrisViewerProps) {
  const [zoom, setZoom] = useState(1)
  const [selectedImage, setSelectedImage] = useState<'left' | 'right' | null>(null)

  const handleZoom = (direction: 'in' | 'out') => {
    setZoom((prev) => {
      if (direction === 'in') return Math.min(prev + 0.25, 3)
      return Math.max(prev - 0.25, 0.5)
    })
  }

  const renderImage = (image: string | null, side: 'left' | 'right') => {
    if (!image) {
      return (
        <div className="aspect-square bg-gray-700 rounded-full flex items-center justify-center">
          <p className="text-gray-500 text-center text-xs md:text-sm px-2">No {side} iris</p>
        </div>
      )
    }

    return (
      <div className="flex flex-col items-center">
        <div
          className="aspect-square bg-gray-800 rounded-full overflow-hidden cursor-zoom-in relative group border-2 border-gray-600"
          onClick={() => setSelectedImage(side)}
        >
          <img
            src={image}
            alt={`${side} iris`}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors rounded-full flex items-center justify-center">
            <span className="opacity-0 group-hover:opacity-100 text-white text-sm font-medium">
              Enlarge
            </span>
          </div>
        </div>
        <div className="mt-2 text-center text-sm text-gray-400">
          {side === 'left' ? 'OS (Left)' : 'OD (Right)'}
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Side by side view - always 2 columns, even on mobile */}
      <div className="grid grid-cols-2 gap-2 md:gap-4">
        {renderImage(rightImage, 'right')}
        {renderImage(leftImage, 'left')}
      </div>

      {/* Enlarged modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => {
            setSelectedImage(null)
            setZoom(1)
          }}
        >
          <div className="relative max-w-4xl w-full" onClick={(e) => e.stopPropagation()}>
            {/* Controls */}
            <div className="absolute top-4 right-4 flex gap-2 z-10">
              <button
                onClick={() => handleZoom('out')}
                className="bg-gray-800 hover:bg-gray-700 p-2 rounded-lg"
                title="Zoom out"
              >
                ➖
              </button>
              <span className="bg-gray-800 px-3 py-2 rounded-lg">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => handleZoom('in')}
                className="bg-gray-800 hover:bg-gray-700 p-2 rounded-lg"
                title="Zoom in"
              >
                ➕
              </button>
              <button
                onClick={() => {
                  setSelectedImage(null)
                  setZoom(1)
                }}
                className="bg-gray-800 hover:bg-gray-700 p-2 rounded-lg"
                title="Close"
              >
                ✕
              </button>
            </div>

            {/* Image */}
            <div className="overflow-auto max-h-[80vh] rounded-lg">
              <img
                src={selectedImage === 'left' ? leftImage! : rightImage!}
                alt={`${selectedImage} iris enlarged`}
                style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
                className="w-full transition-transform"
              />
            </div>

            {/* Label */}
            <div className="text-center mt-4 text-xl">
              {selectedImage === 'left' ? 'Left Iris (OS)' : 'Right Iris (OD)'}
            </div>

            {/* Navigation */}
            <div className="flex justify-center gap-4 mt-4">
              {leftImage && (
                <button
                  onClick={() => setSelectedImage('left')}
                  className={`px-4 py-2 rounded-lg ${
                    selectedImage === 'left'
                      ? 'bg-blue-600'
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                >
                  Left Eye
                </button>
              )}
              {rightImage && (
                <button
                  onClick={() => setSelectedImage('right')}
                  className={`px-4 py-2 rounded-lg ${
                    selectedImage === 'right'
                      ? 'bg-blue-600'
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                >
                  Right Eye
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default IrisViewer
