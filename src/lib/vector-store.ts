import { LocalEmbeddings } from './local-embeddings';

// Simple in-memory document storage
interface DocumentChunk {
  id: string;
  content: string;
  docId: string;
  metadata: any;
  embedding: number[];
}

let documents: DocumentChunk[] = [];
const embeddings = new LocalEmbeddings();

export async function initializeVectorStore() {
  // Simple initialization - no complex setup needed
  return true;
}

export async function addDocumentsToStore(docId: string, textChunks: string[], metadata: any = {}) {
  try {
    // Create embeddings for each chunk
    const chunkEmbeddings = await embeddings.embedDocuments(textChunks);

    // Store documents with embeddings
    for (let i = 0; i < textChunks.length; i++) {
      documents.push({
        id: `${docId}-${i}`,
        content: textChunks[i],
        docId,
        metadata: { ...metadata, chunkIndex: i },
        embedding: chunkEmbeddings[i]
      });
    }

    return { success: true };
  } catch (error) {
    const err = error as Error;
    console.error('Failed to add documents to store:', err);
    return { success: false, error: err.message };
  }
}

export async function searchSimilarDocuments(query: string, k: number = 4) {
  try {
    // Create embedding for query
    const queryEmbedding = await embeddings.embedQuery(query);

    // Calculate similarity scores (simple cosine similarity)
    const similarities = documents.map(doc => ({
      doc,
      similarity: cosineSimilarity(queryEmbedding, doc.embedding)
    }));

    // Sort by similarity and return top k
    const results = similarities
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, k)
      .map(item => ({
        pageContent: item.doc.content,
        metadata: item.doc.metadata
      }));

    return { success: true, results };
  } catch (error) {
    const err = error as Error;
    console.error('Failed to search documents:', err);
    return { success: false, error: err.message };
  }
}

// Simple cosine similarity calculation
function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

export async function deleteDocumentFromStore(docId: string) {
  try {
    // Remove documents with matching docId
    documents = documents.filter(doc => doc.docId !== docId);
    return { success: true };
  } catch (error) {
    const err = error as Error;
    console.error('Failed to delete document from store:', err);
    return { success: false, error: err.message };
  }
}

export function getDocumentCount(): number {
  return documents.length;
}

export function getAllDocuments(): DocumentChunk[] {
  return documents;
}
