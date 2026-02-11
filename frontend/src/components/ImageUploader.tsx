import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

interface ImageUploaderProps {
  onUpload: (file: File) => void
  preview: string | null
  label: string
}

function ImageUploader({ onUpload, preview, label }: ImageUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0])
      }
    },
    [onUpload]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp'],
    },
    maxFiles: 1,
  })

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
        ${isDragActive ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'}
        ${preview ? 'border-green-500' : ''}
      `}
    >
      <input {...getInputProps()} />
      {preview ? (
        <div className="space-y-3">
          <img
            src={preview}
            alt={label}
            className="max-h-40 mx-auto rounded-lg object-contain"
          />
          <p className="text-sm text-gray-400">Click or drag to replace</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-4xl">👁️</div>
          <p className="text-gray-300">
            {isDragActive ? 'Drop the image here' : `Drag & drop ${label} image`}
          </p>
          <p className="text-sm text-gray-500">or click to select</p>
          <p className="text-xs text-gray-600">Supports: JPEG, PNG, WebP</p>
        </div>
      )}
    </div>
  )
}

export default ImageUploader
