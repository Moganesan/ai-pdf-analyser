import { NextRequest, NextResponse } from 'next/server';
import { searchSimilarDocuments } from '@/lib/vector-store';
import { generateResponse } from '@/lib/llm';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (!message || typeof message !== 'string') {
      return NextResponse.json(
        { success: false, error: 'Message is required' },
        { status: 400 }
      );
    }

    // Search for relevant documents
    const searchResult = await searchSimilarDocuments(message, 4);
    
    if (!searchResult.success) {
      return NextResponse.json(
        { success: false, error: 'Failed to search documents' },
        { status: 500 }
      );
    }

    // Prepare context from search results
    const context = searchResult.results
      .map((doc, index) => `Context ${index + 1}:\n${doc.pageContent}`)
      .join('\n\n');

    // Generate response using LLM
    const response = await generateResponse(message, context);

    return NextResponse.json({
      success: true,
      response,
      sources: searchResult.results.map(doc => ({
        content: doc.pageContent.substring(0, 200) + '...',
        metadata: doc.metadata
      }))
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to process chat message' },
      { status: 500 }
    );
  }
}
