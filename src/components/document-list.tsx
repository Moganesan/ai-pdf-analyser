"use client";

import { FileText, Trash2, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Document {
  id: string;
  name: string;
  size: number;
  uploadDate: Date;
  status: 'processing' | 'ready' | 'error';
}

interface DocumentListProps {
  documents: Document[];
  onDeleteDocument: (id: string) => Promise<void>;
  onViewDocument: (id: string) => void;
  isLoading?: boolean;
}

export function DocumentList({ documents, onDeleteDocument, onViewDocument, isLoading = false }: DocumentListProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'processing':
        return 'text-yellow-600';
      case 'ready':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-muted-foreground';
    }
  };

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'processing':
        return 'Processing...';
      case 'ready':
        return 'Ready';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Documents ({documents.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="mx-auto h-12 w-12 mb-4 opacity-50 animate-pulse" />
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>No documents uploaded yet</p>
            <p className="text-sm">Upload PDF files to start analyzing</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{doc.name}</p>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{formatFileSize(doc.size)}</span>
                      <span>{doc.uploadDate.toLocaleDateString()}</span>
                      <span className={`font-medium ${getStatusColor(doc.status)}`}>
                        {getStatusText(doc.status)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {doc.status === 'ready' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewDocument(doc.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDeleteDocument(doc.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
