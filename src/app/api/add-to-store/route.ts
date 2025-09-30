import { NextRequest, NextResponse } from 'next/server';
import { addDocumentsToStore } from '@/lib/vector-store';

export async function POST(request: NextRequest) {
  try {
    const { docId, chunks, metadata } = await request.json();

    if (!docId || !chunks || !Array.isArray(chunks)) {
      return NextResponse.json(
        { success: false, error: 'Invalid request data' },
        { status: 400 }
      );
    }

    const result = await addDocumentsToStore(docId, chunks, metadata);

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Documents added to vector store successfully'
    });
  } catch (error) {
    console.error('Add to store error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to add documents to store' },
      { status: 500 }
    );
  }
}
