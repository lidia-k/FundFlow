import * as React from "react";
import { useDropzone } from "react-dropzone";
import { Upload, File, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onFileRemove?: () => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
  className?: string;
  selectedFile?: File | null;
  disabled?: boolean;
}

export function FileUpload({
  onFileSelect,
  onFileRemove,
  accept = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-excel": [".xls"],
  },
  maxSize = 10 * 1024 * 1024, // 10MB
  className,
  selectedFile,
  disabled = false,
}: FileUploadProps) {
  const onDrop = React.useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept,
      maxSize,
      multiple: false,
      disabled,
    });

  const errors = fileRejections.map((file) =>
    file.errors.map((err) => err.message).join(", ")
  );

  return (
    <div className={cn("w-full", className)}>
      {!selectedFile ? (
        <Card
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed cursor-pointer transition-colors",
            isDragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          <CardContent className="flex flex-col items-center justify-center p-8 text-center">
            <input {...getInputProps()} />
            <Upload className="h-8 w-8 text-muted-foreground mb-4" />
            <div className="space-y-2">
              <p className="text-sm font-medium">
                {isDragActive
                  ? "Drop your Excel file here"
                  : "Drag & drop your Excel file here"}
              </p>
              <p className="text-xs text-muted-foreground">
                or click to browse files
              </p>
              <p className="text-xs text-muted-foreground">
                Supports .xlsx and .xls files up to 10MB
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-3">
              <File className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            {onFileRemove && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onFileRemove}
                disabled={disabled}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {errors.length > 0 && (
        <div className="mt-2 text-sm text-destructive">
          {errors.map((error, index) => (
            <p key={index}>{error}</p>
          ))}
        </div>
      )}
    </div>
  );
}