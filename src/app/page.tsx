"use client";

import { useState, useCallback, useEffect } from "react";
import { PDFUpload } from "@/components/pdf-upload";
import { ChatInterface } from "@/components/chat-interface";
import { DocumentList } from "@/components/document-list";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, MessageSquare, Upload } from "lucide-react";
import { api } from "@/lib/api-client";

interface Document {
  id: string;
  name: string;
  size: number;
  uploadDate: Date;
  status: "processing" | "ready" | "error";
}

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
}

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "connected" | "error"
  >("checking");

  // Load existing documents and check backend health on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        console.log("🔍 Checking backend health...");
        const health = await api.healthCheck();
        console.log("✅ Backend health check passed:", health);
        setBackendStatus("connected");

        // Load existing documents
        console.log("📄 Loading existing documents...");
        const documentsResponse = await api.listDocuments();
        console.log("✅ Documents loaded:", documentsResponse);

        // Convert backend document format to frontend format
        const existingDocuments: Document[] = documentsResponse.documents.map(
          (doc: {
            id: string;
            filename: string;
            size: number;
            upload_date: string;
            status: string;
          }) => ({
            id: doc.id,
            name: doc.filename,
            size: doc.size,
            uploadDate: new Date(doc.upload_date),
            status: doc.status === "processed" ? "ready" : "processing",
          })
        );

        console.log("📄 Converted documents:", existingDocuments);
        setDocuments(existingDocuments);
      } catch (error) {
        console.error("❌ Backend health check failed:", error);
        setBackendStatus("error");
      } finally {
        setIsLoadingDocuments(false);
      }
    };

    loadData();
  }, []);

  const handleFileUpload = useCallback(async (file: File) => {
    const documentId = Math.random().toString(36).substr(2, 9);
    const newDocument: Document = {
      id: documentId,
      name: file.name,
      size: file.size,
      uploadDate: new Date(),
      status: "processing",
    };

    setDocuments((prev) => [...prev, newDocument]);
    setIsProcessing(true);

    try {
      console.log("🚀 Starting file upload:", file.name);

      // Upload file to backend using API client
      const uploadResult = await api.uploadDocument(file);

      console.log("✅ Upload successful:", uploadResult);

      // Update document status with backend response
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === documentId
            ? {
                ...doc,
                id: uploadResult.document_id || documentId,
                status: "ready",
              }
            : doc
        )
      );
    } catch (error) {
      console.error("❌ File processing error:", error);

      // Handle different types of errors
      let errorMessage = "Upload failed";
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (
        typeof error === "object" &&
        error !== null &&
        "response" in error
      ) {
        const axiosError = error as {
          response?: { data?: { detail?: string } };
          message?: string;
        };
        errorMessage =
          axiosError.response?.data?.detail ||
          axiosError.message ||
          "Upload failed";
      }

      console.error("Error details:", errorMessage);

      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === documentId ? { ...doc, status: "error" } : doc
        )
      );
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleSendMessage = useCallback(
    async (message: string) => {
      const userMessage: Message = {
        id: Math.random().toString(36).substr(2, 9),
        content: message,
        role: "user",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        console.log("🚀 Sending message:", message);
        console.log(
          "📄 Available documents:",
          documents.map((doc) => doc.id)
        );

        const result = await api.sendMessage(
          message,
          documents.map((doc) => doc.id)
        );

        console.log("✅ Chat response received:", result);

        const assistantMessage: Message = {
          id: Math.random().toString(36).substr(2, 9),
          content: result.response,
          role: "assistant",
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        console.error("❌ Chat error:", error);

        // Handle different types of errors
        let errorMessage =
          "Sorry, I encountered an error processing your request. Please try again.";
        if (error instanceof Error) {
          errorMessage = `Error: ${error.message}`;
        } else if (
          typeof error === "object" &&
          error !== null &&
          "response" in error
        ) {
          const axiosError = error as {
            response?: { data?: { detail?: string } };
            message?: string;
          };
          errorMessage = `Error: ${
            axiosError.response?.data?.detail ||
            axiosError.message ||
            "Request failed"
          }`;
        }

        const errorResponse: Message = {
          id: Math.random().toString(36).substr(2, 9),
          content: errorMessage,
          role: "assistant",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorResponse]);
      } finally {
        setIsLoading(false);
      }
    },
    [documents]
  );

  const handleDeleteDocument = useCallback(async (id: string) => {
    try {
      console.log("🗑️ Deleting document:", id);
      await api.deleteDocument(id);
      console.log("✅ Document deleted successfully");

      // Remove from local state
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    } catch (error) {
      console.error("❌ Failed to delete document:", error);
      // Still remove from local state even if backend call fails
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    }
  }, []);

  const handleViewDocument = useCallback((id: string) => {
    // Implement document viewing functionality
    console.log("View document:", id);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">AI PDF Analyzer</h1>
          <p className="text-muted-foreground">
            Upload PDF documents and chat with AI to get insights, summaries,
            and answers
          </p>
          <div className="mt-4">
            {backendStatus === "checking" && (
              <div className="text-yellow-600">
                🔍 Checking backend connection...
              </div>
            )}
            {backendStatus === "connected" && (
              <div className="text-green-600">✅ Backend connected</div>
            )}
            {backendStatus === "error" && (
              <div className="text-red-600">
                ❌ Backend connection failed. Please ensure the backend is
                running on http://localhost:8000
              </div>
            )}
          </div>
        </div>

        <Tabs defaultValue="upload" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="documents" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <PDFUpload
              onFileUpload={handleFileUpload}
              isProcessing={isProcessing}
            />
          </TabsContent>

          <TabsContent value="documents" className="mt-6">
            <DocumentList
              documents={documents}
              onDeleteDocument={handleDeleteDocument}
              onViewDocument={handleViewDocument}
              isLoading={isLoadingDocuments}
            />
          </TabsContent>

          <TabsContent value="chat" className="mt-6">
            <ChatInterface
              onSendMessage={handleSendMessage}
              messages={messages}
              isLoading={isLoading}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
