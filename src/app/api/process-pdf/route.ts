import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

export async function POST(request: NextRequest) {
  try {
    const { filename } = await request.json();

    if (!filename) {
      return NextResponse.json({ success: false, error: 'No filename provided' });
    }

    const filepath = join(process.cwd(), 'uploads', filename);
    
    try {
      const dataBuffer = await readFile(filepath);
      
      // Import pdf-parse with error handling
      const pdf = (await import('pdf-parse')).default;
      const pdfData = await pdf(dataBuffer);
      
      // Extract text content
      const text = pdfData.text || 'No text content found in PDF';
      
      // Split text into chunks for better processing
      const chunks = splitTextIntoChunks(text, 1000, 200);
      
      return NextResponse.json({
        success: true,
        text,
        chunks,
        numPages: pdfData.numpages || 1,
        info: pdfData.info || { title: 'PDF Document' }
      });
    } catch (error) {
      console.error('PDF processing error:', error);
      return NextResponse.json(
        { success: false, error: 'Failed to process PDF' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Process PDF error:', error);
    return NextResponse.json(
      { success: false, error: 'Invalid request' },
      { status: 400 }
    );
  }
}

function splitTextIntoChunks(text: string, chunkSize: number, overlap: number): string[] {
  const chunks: string[] = [];
  let start = 0;
  
  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    let chunk = text.slice(start, end);
    
    // Try to break at sentence boundaries
    if (end < text.length) {
      const lastPeriod = chunk.lastIndexOf('.');
      const lastNewline = chunk.lastIndexOf('\n');
      const breakPoint = Math.max(lastPeriod, lastNewline);
      
      if (breakPoint > start + chunkSize * 0.5) {
        chunk = chunk.slice(0, breakPoint + 1);
        start = start + breakPoint + 1 - overlap;
      } else {
        start = end - overlap;
      }
    } else {
      start = end;
    }
    
    if (chunk.trim().length > 0) {
      chunks.push(chunk.trim());
    }
  }
  
  return chunks;
}
